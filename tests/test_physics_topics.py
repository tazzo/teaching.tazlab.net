"""The three physics topics: determinism, a verifier that can fail, physical predicates.

Every check here is a predicate on *derived* values (DESIGN §2.10, STRUCTURE §5): the
point is that a plausible generator bug — a corrupted answer, a figure that is not the
model, a phase that is not monotone, a meeting outside the window, a value off the
magnitude table — must produce a rejection rather than a plausible-looking worksheet.
"""

from __future__ import annotations

from fractions import Fraction

import pytest
from sympy import Rational, Symbol

from app.core.rng import make_rng
from app.core.units import speed_of_sound
from app.core.verify import no_floats, real_solutions
from app.generators.base import wire_params
from app.generators.physics import circular as circular_module
from app.generators.physics import multi_phase as multi_phase_module
from app.generators.physics import relative as relative_module
from app.generators.physics.circular import TOPIC as CIRCULAR
from app.generators.physics.multi_phase import TOPIC as MULTI_PHASE
from app.generators.physics.relative import TOPIC as RELATIVE

TOPICS = (CIRCULAR, MULTI_PHASE, RELATIVE)
DIFFICULTIES = ("easy", "medium", "hard")
SEEDS = (1, 7, 42, 20260924)


def make(topic, difficulty: str, seed: int = 11, index: int = 0):
    return topic.generate(make_rng(seed, topic.id, difficulty, index), difficulty, seed, index)


def rebuilt(item, **changes):
    return type(item)(**{**item.__dict__, **changes})


def with_answer_value(item, value: str):
    """The honest item with one other number in the answer — every label otherwise intact."""
    return rebuilt(item, answer=type(item.answer)(
        latex=item.answer.latex,
        kind=item.answer.kind,
        payload={**item.answer.payload, "value": [value]},
    ))


def rational(value: Fraction) -> Rational:
    return Rational(value.numerator, value.denominator)


# --------------------------------------------------------------------- contract
def test_topic_contract() -> None:
    assert [topic.id for topic in TOPICS] == [
        "physics.kinematics.circular",
        "physics.kinematics.multi_phase",
        "physics.kinematics.relative",
    ]
    for topic in TOPICS:
        assert topic.family == "physics"
        assert topic.difficulties == DIFFICULTIES
        assert topic.scenarios and len(topic.scenarios) == 3
        assert topic.label_key.startswith("topic.")
        for difficulty in DIFFICULTIES:
            item = make(topic, difficulty)
            assert item.statement_key == f"stmt.{topic.label_key.removeprefix('topic.')}_{difficulty}"
            assert item.steps and all(step.label_key.startswith("step.") for step in item.steps)


def test_wire_params_are_exact_rational_strings() -> None:
    for topic in TOPICS:
        for difficulty in DIFFICULTIES:
            item = make(topic, difficulty)
            assert no_floats(*item.params.values())
            for key, value in wire_params(item.params).items():
                assert isinstance(value, str) and "." not in value
                assert Fraction(value) == item.params[key]
            assert all("." not in text and "e-" not in text
                       for text in item.answer.payload.get("value", []))


# ---------------------------------------------------------------- determinism
def test_same_seed_difficulty_and_index_is_the_same_item() -> None:
    for topic in TOPICS:
        for difficulty in DIFFICULTIES:
            assert make(topic, difficulty, 20260924, 3) == make(topic, difficulty, 20260924, 3)


def test_other_seed_or_index_is_a_different_item() -> None:
    for topic in TOPICS:
        for difficulty in DIFFICULTIES:
            base = make(topic, difficulty, 5, 0).params
            assert make(topic, difficulty, 6, 0).params != base
            assert make(topic, difficulty, 5, 1).params != base


# ------------------------------------------------ honest items verify, always
@pytest.mark.parametrize("topic", TOPICS, ids=lambda topic: topic.id)
@pytest.mark.parametrize("difficulty", DIFFICULTIES)
def test_every_item_verifies_across_seeds(topic, difficulty: str) -> None:
    for seed in SEEDS:
        for index in range(5):
            result = topic.verify(make(topic, difficulty, seed, index))
            assert result.ok, (seed, index, result.reason)


@pytest.mark.parametrize("topic", TOPICS, ids=lambda topic: topic.id)
@pytest.mark.parametrize("difficulty", DIFFICULTIES)
def test_corrupted_answer_is_rejected(topic, difficulty: str) -> None:
    item = make(topic, difficulty)
    honest = Fraction(item.answer.payload["value"][0])
    result = topic.verify(with_answer_value(item, str(honest + 1)))
    assert not result.ok and result.reason == "answer_mismatch"


@pytest.mark.parametrize("topic", TOPICS, ids=lambda topic: topic.id)
@pytest.mark.parametrize("difficulty", DIFFICULTIES)
def test_corrupted_answer_latex_is_rejected(topic, difficulty: str) -> None:
    item = make(topic, difficulty)
    result = topic.verify(rebuilt(item, answer=type(item.answer)(
        latex="999", kind=item.answer.kind, payload=item.answer.payload
    )))
    assert not result.ok and result.reason == "answer_latex_mismatch"


@pytest.mark.parametrize("topic", TOPICS, ids=lambda topic: topic.id)
@pytest.mark.parametrize("difficulty", DIFFICULTIES)
def test_figure_that_is_not_the_model_is_rejected(topic, difficulty: str) -> None:
    item = make(topic, difficulty)
    if item.figure is None:
        # a deliberately figureless item refuses a figure that is not its model
        assert not topic.verify(rebuilt(item, figure={"kind": "kinematics", "traces": []})).ok
        return
    tampered = {
        **item.figure,
        "traces": [{**item.figure["traces"][0], "samples": [["0", "0"], ["1", "999"]]}]
        + item.figure["traces"][1:],
    }
    result = topic.verify(rebuilt(item, figure=tampered))
    assert not result.ok and result.reason == "figure_disagrees_with_model"


@pytest.mark.parametrize("topic", TOPICS, ids=lambda topic: topic.id)
@pytest.mark.parametrize("difficulty", DIFFICULTIES)
def test_missing_figure_is_rejected(topic, difficulty: str) -> None:
    item = make(topic, difficulty)
    if item.figure is None:
        # circular hard is figureless on purpose: the only figure this schema can carry
        # is a periodic trace, which would print the period on the axis
        assert topic.id == "physics.kinematics.circular" and difficulty == "hard"
        return
    assert topic.verify(rebuilt(item, figure=None)).reason == "missing_figure"


def test_corrupted_physics_parameter_is_rejected() -> None:
    item = make(CIRCULAR, "easy")
    flipped = rebuilt(item, params={**item.params, "T": item.params["T"] + 1})
    assert not CIRCULAR.verify(flipped).ok

    item = make(RELATIVE, "medium")
    moved = rebuilt(item, params={**item.params, "d0": item.params["d0"] + 1})
    assert not RELATIVE.verify(moved).ok

    item = make(MULTI_PHASE, "hard")
    broken = rebuilt(item, params={**item.params, "s_total": item.params["s_total"] + 1})
    assert not MULTI_PHASE.verify(broken).ok


def test_steps_end_with_the_exact_answer() -> None:
    for topic in TOPICS:
        for difficulty in DIFFICULTIES:
            for seed in SEEDS:
                item = make(topic, difficulty, seed)
                assert item.answer.latex in item.steps[-1].latex


@pytest.mark.parametrize("topic", TOPICS, ids=lambda topic: topic.id)
@pytest.mark.parametrize("difficulty", DIFFICULTIES)
def test_figure_numbers_are_exact_rational_strings(topic, difficulty: str) -> None:
    item = make(topic, difficulty)
    if item.figure is None:
        assert topic.id == "physics.kinematics.circular" and difficulty == "hard"
        return
    figure = item.figure
    assert Fraction(figure["domain"]["t_min"]) == 0
    assert Fraction(figure["domain"]["t_max"]) > 0
    for phase in figure["phases"]:
        assert Fraction(phase["t_from"]) < Fraction(phase["t_to"])
    for trace in figure["traces"]:
        for x, y in trace["samples"]:
            assert str(Fraction(x)) == x and str(Fraction(y)) == y
    for marker in figure["markers"]:
        assert all(str(Fraction(value)) == value for value in marker["at"])


@pytest.mark.parametrize("topic", TOPICS, ids=lambda topic: topic.id)
@pytest.mark.parametrize("difficulty", DIFFICULTIES)
def test_figure_carries_one_measured_quantity(topic, difficulty: str) -> None:
    """One y-unit per figure: a second series is only allowed in the same unit."""
    item = make(topic, difficulty)
    if item.figure is None:
        return
    figure = item.figure
    assert isinstance(figure["y_unit"], str) and figure["y_unit"]
    # relative motion draws two bodies, but both are positions in metres — one unit;
    # the other topics draw the single quantity the exercise asks about
    assert len(figure["traces"]) == (2 if topic is RELATIVE else 1)
    if topic is MULTI_PHASE:
        extra = {**item.figure, "traces": item.figure["traces"] * 2}
        assert topic.verify(rebuilt(item, figure=extra)).reason == "unexpected_extra_trace"


# ------------------------------------------------- zero denominators are rejected
def test_denominators_are_never_zero() -> None:
    item = make(CIRCULAR, "easy")
    assert not CIRCULAR.verify(rebuilt(item, params={**item.params, "T": Fraction(0)})).ok

    item = make(MULTI_PHASE, "easy")
    assert MULTI_PHASE.verify(rebuilt(item, params={**item.params, "t2": Fraction(0)})).reason \
        == "non_positive_duration"
    assert MULTI_PHASE.verify(rebuilt(item, params={**item.params, "a2": Fraction(0)})).reason \
        == "degenerate_accelerated_phase"

    item = make(RELATIVE, "easy")
    equal_speeds = rebuilt(item, params={**item.params, "v_b": item.params["v_a"]})
    assert RELATIVE.verify(equal_speeds).reason == "closing_speed_too_small"

    item = make(RELATIVE, "hard")
    no_delay = rebuilt(item, params={**item.params, "delta": Fraction(0)})
    assert RELATIVE.verify(no_delay).reason == "delay_outside_the_window"


# -------------------------------------------------- DESIGN §2.10 magnitudes
def test_circular_stays_inside_the_design_table() -> None:
    for difficulty in DIFFICULTIES:
        for seed in SEEDS:
            for index in range(5):
                item = make(CIRCULAR, difficulty, seed, index)
                params = item.params
                radius = params["r"]
                assert circular_module.RADIUS_RANGE[0] <= radius <= circular_module.RADIUS_RANGE[1]
                if difficulty == "easy":
                    period = params["T"]
                    assert circular_module.PERIOD_RANGE[0] <= period <= circular_module.PERIOD_RANGE[1]
                    assert params["v_over_pi"] == 2 * radius / period
                elif difficulty == "medium":
                    omega_over_pi = params["n_rpm"] / 30
                    assert params["omega_over_pi"] == omega_over_pi
                    assert params["T"] == 60 / params["n_rpm"]
                    assert params["a_over_pi2"] == omega_over_pi**2 * radius
                else:
                    omega = params["omega"]
                    assert omega * omega * radius == params["a_c"]
                    assert params["T_over_pi"] == 2 / omega
                    assert circular_module.OMEGA_RANGE[0] <= omega < circular_module.OMEGA_RANGE[1]
                    # the period this implies is inside the table row (π compared exactly)
                    assert Fraction(1, 2) < 2 * circular_module.pi / rational(omega) <= 60


def test_circular_hard_does_not_leak_the_period_into_the_figure() -> None:
    for seed in SEEDS:
        item = make(CIRCULAR, "hard", seed)
        assert item.figure is None
        # a figure would print the answer (the period) on its own axis
        assert not CIRCULAR.verify(rebuilt(item, figure={"kind": "kinematics", "traces": []})).ok
    for difficulty in ("easy", "medium"):
        item = make(CIRCULAR, difficulty)
        assert item.figure["y_unit"] == "rev"
        assert item.figure["markers"][0]["label_key"] == "marker.full_turn"


def test_multi_phase_stays_inside_the_design_table() -> None:
    for difficulty in DIFFICULTIES:
        for seed in SEEDS:
            for index in range(5):
                item = make(MULTI_PHASE, difficulty, seed, index)
                phases = multi_phase_module._phases_from_params(difficulty, item.params)
                for t_from, t_to, v_in, a, _, _ in phases:
                    span = t_to - t_from
                    assert multi_phase_module.DURATION_RANGE[0] <= span \
                        <= multi_phase_module.DURATION_RANGE[1]
                    if a != 0:
                        assert multi_phase_module.ACCELERATION_RANGE[0] <= abs(a) \
                            <= multi_phase_module.ACCELERATION_RANGE[1]
                    for speed in (v_in, v_in + a * span):
                        assert multi_phase_module.SPEED_RANGE[0] <= speed \
                            <= multi_phase_module.SPEED_RANGE[1]
                assert item.params["t_total"] <= multi_phase_module.MAX_TOTAL_DURATION


def test_relative_stays_inside_the_design_table() -> None:
    for difficulty in DIFFICULTIES:
        for seed in SEEDS:
            for index in range(5):
                params = make(RELATIVE, difficulty, seed, index).params
                for speed in (params["v_a"], params["v_b"]):
                    assert relative_module.SPEED_RANGE[0] <= speed <= relative_module.SPEED_RANGE[1]
                assert relative_module.DURATION_RANGE[0] <= params["t_window"] \
                    <= relative_module.DURATION_RANGE[1]
                assert 0 < params["d0"] <= relative_module.MAX_DISTANCE


def test_sound_scale_values_are_rejected_for_everyday_scenarios() -> None:
    """A 343 m/s result in a cycling problem signals a bug, not a hard task (DESIGN §2.10)."""
    assert speed_of_sound() == Fraction(343)
    item = make(RELATIVE, "easy")
    fast = rebuilt(item, params={**item.params, "v_a": speed_of_sound()})
    assert RELATIVE.verify(fast).reason == "speed_out_of_scale"
    item = make(MULTI_PHASE, "easy")
    fast = rebuilt(item, params={**item.params, "v1": speed_of_sound()})
    assert not MULTI_PHASE.verify(fast).ok


# ------------------------------------------------- multi-phase physical predicates
def test_multi_phase_boundaries_are_exact_vertices_and_continuous() -> None:
    for difficulty in DIFFICULTIES:
        for seed in SEEDS:
            for index in range(5):
                item = make(MULTI_PHASE, difficulty, seed, index)
                phases = multi_phase_module._phases_from_params(difficulty, item.params)
                assert len(phases) == (3 if difficulty == "medium" else 2)
                assert len(item.figure["traces"]) == 1          # one measured quantity
                position = item.figure["traces"][0]["samples"]
                for phase_index, (t_from, t_to, v_in, a, s_from, _) in enumerate(phases):
                    assert multi_phase_module._model_position(phases, t_from) == s_from
                    if phase_index:
                        # position continuity: the second branch enters at the first's exit
                        assert multi_phase_module._exit(phases[phase_index - 1])[2] == s_from
                        # velocity continuity: v_out of one phase is v_in of the next
                        assert multi_phase_module._exit(phases[phase_index - 1])[1] == v_in
                        # both branches leave a vertex at the boundary and both agree:
                        # the continuity claim is visible in the payload, not just asserted
                        at_boundary = [y for x, y in position if Fraction(x) == t_from]
                        assert len(at_boundary) == 2 and at_boundary[0] == at_boundary[1]
                        assert Fraction(at_boundary[0]) == s_from
                    assert min(v_in, v_in + a * (t_to - t_from)) > 0     # monotone position
                assert [Fraction(x) for x, _ in position] == sorted(Fraction(x) for x, _ in position)
                assert Fraction(item.figure["domain"]["t_max"]) == item.params["t_total"]


def test_multi_phase_unknown_duration_has_exactly_one_admissible_time() -> None:
    for seed in SEEDS:
        item = make(MULTI_PHASE, "hard", seed)
        v1, t1 = item.params["v1"], item.params["t1"]
        a2, t2, total = item.params["a2"], item.params["t2"], item.params["s_total"]
        assert a2 > 0
        equation = a2 * Symbol("t")**2 / 2 + v1 * Symbol("t") - (total - v1 * t1)
        roots = real_solutions(equation, Symbol("t"))
        assert roots is not None and len(roots) == 2
        positive = [root for root in roots if root > 0]
        assert len(positive) == 1                       # unique admissible time
        assert Fraction(str(positive[0])) == t2
        assert item.answer.payload["value"] == [str(t2)]


# ----------------------------------------------------- relative physical predicates
def test_relative_meeting_is_unique_and_inside_the_window() -> None:
    for difficulty in DIFFICULTIES:
        for seed in SEEDS:
            for index in range(5):
                item = make(RELATIVE, difficulty, seed, index)
                params = item.params
                window, meet, point = params["t_window"], params["t_meet"], params["x_meet"]
                assert window / 3 < meet < 2 * window / 3
                assert meet == point / params["v_a"]
                scenario = relative_module._SCENARIO_FOR[difficulty]
                if difficulty == "easy":
                    closing = params["v_a"] - params["v_b"]
                    assert closing >= relative_module.MIN_CLOSING_SPEED
                    assert params["d0"] == closing * meet
                    assert point > params["d0"]
                else:
                    assert params["v_a"] + params["v_b"] > 0
                    if difficulty == "hard":
                        delay = params["delta"]
                        assert 1 <= delay < meet
                        assert params["d0"] == params["v_a"] * meet + params["v_b"] * (meet - delay)
                        assert any(Fraction(x) == delay for x, _ in item.figure["traces"][1]["samples"])
                    else:
                        assert params["d0"] == (params["v_a"] + params["v_b"]) * meet
                    assert point < params["d0"]
                assert relative_module._position_a(params, 0) < relative_module._position_b(scenario, params, 0)
                assert relative_module._position_a(params, window) > relative_module._position_b(scenario, params, window)
                marker = [m for m in item.figure["markers"] if m["label_key"] == "marker.meeting"][0]
                assert marker["at"] == [str(meet), str(point)]
