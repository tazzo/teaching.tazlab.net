"""The LLM variant path: no network, and a verifier that can actually fail.

Every test drives the provider through an injected ``httpx.MockTransport``, so the suite
proves the whole path — request shape, spec validation, solving, verification, degradation
— without a key and without egress.
"""

from __future__ import annotations

import asyncio
import json
import logging

import httpx
import pytest

from app.generators.physics.variants import spec_to_item
from app.generators.registry import TOPICS
from app.llm.client import LLMClient, ProviderConfig, fetch_variant_specs, fetch_variant_specs_report
from app.llm.spec import SCENARIOS, SpecError, parse_and_validate
from app.llm.variants import fallback_seed, generate_variants

SECRET = "sk-test-secret-must-never-be-logged"
MODEL = "deepseek-v4.1-flash-test"

SAMPLE_GIVENS: dict[str, list[tuple[str, object, str]]] = {
    "uniform_one_object": [("v", 13, "m/s"), ("t", 21, "s")],
    "uniform_unit_conversion": [("v_kmh", 72, "km/h"), ("t", 10, "s")],
    "uniform_graph_reading": [("t1", 3, "s"), ("s1", 39, "m"), ("t2", 8, "s"), ("s2", 104, "m")],
    "uniform_sound_distance": [("c", 343, "m/s"), ("t", 3, "s")],
    "accelerated_from_rest": [("a", 4, "m/s^2"), ("t", 10, "s")],
    "accelerated_with_v0": [("v0", 20, "m/s"), ("a", -7, "m/s^2")],
    "accelerated_derive_a": [("t1", 4, "s"), ("v1", 12, "m/s"), ("t2", 9, "s"), ("v2", 27, "m/s")],
}


def spec_payload(scenario: str, **overrides: object) -> dict:
    declared = SCENARIOS[scenario]
    payload: dict = {
        "scenario": scenario,
        "givens": [
            {"symbol": symbol, "value": value, "unit": unit}
            for symbol, value, unit in SAMPLE_GIVENS[scenario]
        ],
        "unknown": declared.unknown.symbol,
        "ask": "quanto vale la grandezza richiesta?",
        "result_units": declared.unknown.unit,
    }
    payload.update(overrides)
    return payload


def content(payloads: list | dict) -> str:
    return json.dumps(payloads)


def body_for(text: str) -> dict:
    return {"choices": [{"message": {"content": text}}]}


def config(**overrides: object) -> ProviderConfig:
    values: dict = {
        "base_url": "https://provider.test/v1",
        "model": MODEL,
        "api_key": SECRET,
        "session_id": "session-under-test",
        "reasoning_effort": "none",
        "timeout": 5.0,
        "max_concurrency": 2,
    }
    values.update(overrides)
    return ProviderConfig(**values)


class Recorder:
    """A MockTransport handler that remembers the requests it saw."""

    def __init__(self, responder) -> None:
        self.requests: list[httpx.Request] = []
        self._responder = responder

    def __call__(self, request: httpx.Request) -> httpx.Response:
        self.requests.append(request)
        return self._responder(request, len(self.requests))


def ok(text: str) -> Recorder:
    return Recorder(lambda _request, _n: httpx.Response(200, json=body_for(text)))


def client_for(recorder: Recorder, **overrides: object) -> LLMClient:
    return LLMClient(config(**overrides), transport=httpx.MockTransport(recorder))


def run(coro):
    return asyncio.run(coro)


# --------------------------------------------------------------- (a) happy path
def test_one_call_returns_n_verified_items() -> None:
    recorder = ok(content([spec_payload("uniform_one_object") for _ in range(3)]))
    items, degraded, reason = run(generate_variants("uniform_one_object", "easy", 3, client=client_for(recorder)))

    assert degraded is False and reason is None
    assert len(items) == 3
    topic = TOPICS["physics.kinematics.uniform"]
    for item in items:
        assert topic.verify(item).ok, topic.verify(item).reason
        assert item.topic == "physics.kinematics.uniform"
        assert item.difficulty == "easy"
        assert item.figure is not None
    assert len(recorder.requests) == 1  # one call returns N specs


def test_request_shape_matches_the_verified_provider_contract() -> None:
    recorder = ok(content([spec_payload("accelerated_from_rest")]))
    run(fetch_variant_specs("accelerated_from_rest", "easy", 1, client=client_for(recorder)))

    request = recorder.requests[0]
    assert str(request.url) == "https://provider.test/v1/chat/completions"
    assert request.headers["authorization"] == f"Bearer {SECRET}"
    assert request.headers["x-opencode-session"] == "session-under-test"
    body = json.loads(request.content)
    assert body["model"] == MODEL
    assert body["reasoning_effort"] == "none"  # otherwise a small budget returns empty content
    assert body["messages"][0]["role"] == "user"


@pytest.mark.parametrize("scenario", sorted(SAMPLE_GIVENS))
def test_every_scenario_solves_and_verifies(scenario: str) -> None:
    recorder = ok(content([spec_payload(scenario)]))
    items, degraded, reason = run(generate_variants(scenario, "medium", 1, client=client_for(recorder)))

    assert (degraded, reason) == (False, None)
    declared = SCENARIOS[scenario]
    assert TOPICS[declared.topic_id].verify(items[0]).ok
    assert items[0].difficulty == declared.difficulty


def test_partial_provider_success_returns_only_real_variants() -> None:
    payloads = [spec_payload("uniform_one_object"), spec_payload("uniform_one_object", givens=[
        {"symbol": "v", "value": 9999, "unit": "m/s"}, {"symbol": "t", "value": 3, "unit": "s"},
    ])]
    recorder = ok(content(payloads))
    items, degraded, reason = run(generate_variants("uniform_one_object", "easy", 2, client=client_for(recorder)))

    assert degraded is False and reason is None
    assert len(items) == 1  # the invalid one is dropped, never silently repaired


# ------------------------------------------------- (b) invalid spec → fallback
def test_invalid_spec_degrades_to_the_template_generator() -> None:
    bad = spec_payload("uniform_one_object", givens=[
        {"symbol": "v", "value": 343, "unit": "m/s"},   # 343 m/s in a cycling problem
        {"symbol": "t", "value": 21, "unit": "s"},
    ])
    recorder = ok(content([bad]))
    items, degraded, reason = run(generate_variants("uniform_one_object", "easy", 2, client=client_for(recorder)))

    assert degraded is True
    assert reason == "invalid_specs:1"
    assert len(items) == 2
    topic = TOPICS["physics.kinematics.uniform"]
    assert all(topic.verify(item).ok for item in items)
    assert all(item.difficulty == "easy" for item in items)


def test_unparseable_content_degrades() -> None:
    recorder = ok("I am sorry, here are your exercises:")
    items, degraded, reason = run(generate_variants("uniform_one_object", "easy", 1, client=client_for(recorder)))

    assert degraded is True and reason == "invalid_specs:1"
    assert TOPICS["physics.kinematics.uniform"].verify(items[0]).ok


def test_spec_that_solves_but_fails_verification_is_discarded() -> None:
    # Both points are in range and the slope is plausible, but the segment does not pass
    # through the origin, so the graph does not describe motion from rest.
    payload = spec_payload("uniform_graph_reading", givens=[
        {"symbol": "t1", "value": 3, "unit": "s"},
        {"symbol": "s1", "value": 40, "unit": "m"},
        {"symbol": "t2", "value": 8, "unit": "s"},
        {"symbol": "s2", "value": 104, "unit": "m"},
    ])
    recorder = ok(content([payload]))
    items, degraded, reason = run(generate_variants("uniform_graph_reading", "hard", 1, client=client_for(recorder)))

    assert degraded is True and reason == "invalid_specs:1"
    topic = TOPICS["physics.kinematics.uniform"]
    assert topic.verify(items[0]).ok and items[0].difficulty == "hard"


@pytest.mark.parametrize(
    ("overrides", "expected"),
    [
        ({"givens": [{"symbol": "v", "value": 10, "unit": "furlong/fortnight"}]}, "unknown_unit"),
        ({"givens": [{"symbol": "v", "value": "fast", "unit": "m/s"}]}, "non_numeric_value"),
        (
            {"givens": [
                {"symbol": "v", "value": 300, "unit": "m/s"},
                {"symbol": "t", "value": 10, "unit": "s"},
            ]},
            "implausible_magnitude",
        ),
        ({"result_units": ""}, "scaleless_ask"),
        ({"result_units": "m", "unknown": "a"}, "unexpected_unknown"),
        ({"givens": []}, "missing_givens"),
        ({"givens": [{"symbol": "s", "value": 3, "unit": "m"}]}, "unknown_is_given"),
        ({"ask": "  "}, "missing_ask"),
    ],
)
def test_spec_validation_rejects_bad_proposals(overrides: dict, expected: str) -> None:
    with pytest.raises(SpecError) as caught:
        parse_and_validate(spec_payload("uniform_one_object", **overrides), "uniform_one_object")
    assert caught.value.reason == expected


def test_scenario_mismatch_and_unknown_scenario_are_rejected() -> None:
    with pytest.raises(SpecError) as wrong_scenario:
        parse_and_validate(spec_payload("accelerated_from_rest"), "uniform_one_object")
    assert wrong_scenario.value.reason == "scenario_mismatch"

    with pytest.raises(SpecError) as unknown:
        parse_and_validate(spec_payload("uniform_one_object"), "no_such_scenario")
    assert unknown.value.reason == "unknown_scenario"


def test_sound_scenario_pins_the_speed_of_sound() -> None:
    assert SAMPLE_GIVENS["uniform_sound_distance"][0][1] == 343
    with pytest.raises(SpecError) as caught:
        parse_and_validate(
            spec_payload("uniform_sound_distance", givens=[
                {"symbol": "c", "value": 340, "unit": "m/s"},
                {"symbol": "t", "value": 3, "unit": "s"},
            ]),
            "uniform_sound_distance",
        )
    assert caught.value.reason == "implausible_magnitude"


# -------------------------------------------- (c) provider failure → degrade
def test_provider_500_degrades_without_raising() -> None:
    recorder = Recorder(lambda _request, _n: httpx.Response(500, text="upstream exploded"))
    items, degraded, reason = run(generate_variants("uniform_one_object", "easy", 2, client=client_for(recorder)))

    assert degraded is True and reason == "http_500"
    assert len(items) == 2 and all(TOPICS["physics.kinematics.uniform"].verify(i).ok for i in items)
    assert len(recorder.requests) == 2  # a 5xx is retried, within the bounded budget


def test_provider_400_degrades_and_is_not_retried() -> None:
    recorder = Recorder(lambda _request, _n: httpx.Response(400, text="MissingSessionID"))
    outcome = run(fetch_variant_specs_report("uniform_one_object", "easy", 1, client=client_for(recorder)))

    assert outcome.specs == () and outcome.error == "http_400"
    assert outcome.attempts == 1 and len(recorder.requests) == 1


def test_timeout_degrades() -> None:
    def explode(_request: httpx.Request, _n: int) -> httpx.Response:
        raise httpx.ReadTimeout("provider too slow")

    recorder = Recorder(explode)
    items, degraded, reason = run(generate_variants("uniform_one_object", "easy", 1, client=client_for(recorder)))

    assert degraded is True and reason == "provider_timeout"
    assert TOPICS["physics.kinematics.uniform"].verify(items[0]).ok


def test_empty_content_degrades() -> None:
    recorder = ok("")
    items, degraded, reason = run(generate_variants("uniform_one_object", "easy", 1, client=client_for(recorder)))

    assert degraded is True and reason == "empty_content"
    assert items and TOPICS["physics.kinematics.uniform"].verify(items[0]).ok


def test_missing_api_key_degrades_without_calling_the_provider() -> None:
    recorder = ok(content([spec_payload("uniform_one_object")]))
    items, degraded, reason = run(
        generate_variants("uniform_one_object", "easy", 1, client=client_for(recorder, api_key=None))
    )

    assert degraded is True and reason == "missing_api_key"
    assert recorder.requests == []


def test_unknown_scenario_degrades_to_the_topic_template() -> None:
    items, degraded, reason = run(generate_variants("no_such_scenario", "easy", 2))
    assert (degraded, reason) == (True, "unknown_scenario")
    assert items == []


def test_scenario_a_topic_declares_but_no_builder_knows(monkeypatch: pytest.MonkeyPatch) -> None:
    """A catalog scenario with no variant builder degenerates to the template deterministically."""
    import app.llm.variants as variants_module

    real = TOPICS["physics.kinematics.uniform"]

    class DeclaredButNotBuilt:
        id = real.id
        difficulties = real.difficulties
        scenarios = ("declared_but_not_built",)

        def generate(self, *args: object):
            return real.generate(*args)

        def verify(self, item):
            return real.verify(item)

    monkeypatch.setattr(variants_module, "TOPICS", {**TOPICS, real.id: DeclaredButNotBuilt()})
    items, degraded, reason = run(generate_variants("declared_but_not_built", "easy", 2))

    assert (degraded, reason) == (True, "unknown_scenario")
    assert len(items) == 2 and all(real.verify(item).ok for item in items)


def test_fallback_is_reproducible_from_its_derived_seed() -> None:
    assert fallback_seed("uniform_one_object", "easy") == fallback_seed("uniform_one_object", "easy")
    assert fallback_seed("uniform_one_object", "easy") != fallback_seed("uniform_one_object", "medium")

    recorder = ok("not json at all")
    first = run(generate_variants("uniform_one_object", "easy", 2, client=client_for(recorder)))
    second = run(generate_variants("uniform_one_object", "easy", 2, client=client_for(recorder)))
    assert first == second


# ------------------------------------------------------ (d) no key in the logs
def test_the_api_key_never_reaches_a_log_line(caplog: pytest.LogCaptureFixture) -> None:
    with caplog.at_level(logging.DEBUG, logger="teaching.llm"):
        recorder = ok(content([spec_payload("uniform_one_object")]))
        run(generate_variants("uniform_one_object", "easy", 1, client=client_for(recorder)))
        failing = Recorder(lambda _request, _n: httpx.Response(500, text=f"boom {SECRET}"))
        run(generate_variants("uniform_one_object", "easy", 1, client=client_for(failing)))

    assert SECRET not in caplog.text
    for record in caplog.records:
        assert SECRET not in str(record.__dict__)
    assert "llm provider call" in caplog.text  # INFO on the call
    # WARN carries the cause; a provider message body is never copied into a line.
    assert any(getattr(r, "provider_error", None) == "http_500" for r in caplog.records)


def test_degradation_log_names_the_cause(caplog: pytest.LogCaptureFixture) -> None:
    bad = spec_payload("uniform_one_object", givens=[
        {"symbol": "v", "value": 300, "unit": "m/s"},
        {"symbol": "t", "value": 21, "unit": "s"},
    ])
    with caplog.at_level(logging.WARNING, logger="teaching.llm"):
        run(generate_variants("uniform_one_object", "easy", 1, client=client_for(ok(content([bad])))))

    degraded = [r for r in caplog.records if r.getMessage() == "variants degraded"]
    assert degraded and degraded[0].reason == "invalid_specs:1"
    assert degraded[0].rejected_specs == 1


# ------------------------------------------------------- the verifier can fail
def test_a_corrupted_variant_item_is_rejected_by_the_topic() -> None:
    spec = parse_and_validate(spec_payload("uniform_one_object"), "uniform_one_object")
    item = spec_to_item(spec, seed=1, index=0)
    topic = TOPICS["physics.kinematics.uniform"]
    assert topic.verify(item).ok

    corrupted = type(item)(**{**item.__dict__, "answer": type(item.answer)(
        latex="s = 1\\,\\text{m}", kind="scalar_with_unit", payload={"value": ["1"], "unit": ["m"]}
    )})
    assert topic.verify(corrupted).ok is False

    tampered_figure = {**item.figure, "traces": [
        {"label_key": "trace.position", "samples": [["0", "0"], ["1", "999"]]}
    ]}
    tampered = type(item)(**{**item.__dict__, "figure": tampered_figure})
    result = topic.verify(tampered)
    assert result.ok is False and result.reason == "figure_disagrees_with_model"


def test_ambiguous_or_contradictory_givens_are_refused() -> None:
    # t2 <= t1 has no unique admissible time interval.
    spec = parse_and_validate(spec_payload("uniform_graph_reading", givens=[
        {"symbol": "t1", "value": 8, "unit": "s"},
        {"symbol": "s1", "value": 96, "unit": "m"},
        {"symbol": "t2", "value": 3, "unit": "s"},
        {"symbol": "s2", "value": 39, "unit": "m"},
    ]), "uniform_graph_reading")
    with pytest.raises(SpecError) as caught:
        spec_to_item(spec, seed=1, index=0)
    assert caught.value.reason == "degenerate_interval"


def test_the_model_text_never_leaks_into_the_item() -> None:
    spec = parse_and_validate(
        spec_payload("uniform_one_object", ask="PROSA-DEL-MODELLO"), "uniform_one_object"
    )
    item = spec_to_item(spec, seed=1, index=0)
    rendered = " ".join([item.statement_key] + [s.latex for s in item.steps] + [item.answer.latex])
    assert "PROSA-DEL-MODELLO" not in rendered
