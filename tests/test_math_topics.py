"""Mathematics topics: determinism, honest verification, and rejection of corruption.

The load-bearing property is the last one. A verifier that accepts everything looks like a
guarantee while being decoration, so every topic here is fed a deliberately corrupted item
and must refuse it — including the two cases DESIGN §2.10 calls out explicitly: a
fractional equation whose "solution" is an excluded value, and an inequality system whose
vertex set has been tampered with.
"""

from __future__ import annotations

import dataclasses
import re
from fractions import Fraction

import pytest
from sympy import Interval, Union, oo, srepr

from app.api.schemas import WireAnswer, WireStatement
from app.core.rng import make_rng
from app.generators.base import wire_params
from app.generators.math.fractional import TOPIC as FRACTIONAL
from app.generators.math.inequalities import TOPICS as INEQUALITY_TOPICS
from app.generators.math.second_degree import TOPIC as SECOND_DEGREE
from app.generators.math.systems import TOPICS as SYSTEM_TOPICS
from app.generators.math.systems_inequalities import TOPIC as INEQUALITY_SYSTEM

TOPICS = [
    SECOND_DEGREE,
    FRACTIONAL,
    *INEQUALITY_TOPICS.values(),
    *SYSTEM_TOPICS.values(),
    INEQUALITY_SYSTEM,
]
CASES = [(topic, difficulty) for topic in TOPICS for difficulty in topic.difficulties]
CASES_IDS = [f"{topic.id}:{difficulty}" for topic, difficulty in CASES]

SEED = 20260924


def build(topic, difficulty: str, index: int = 0, seed: int = SEED):
    return topic.generate(make_rng(seed, topic.id, difficulty, index), difficulty, seed, index)


def with_answer(item, **payload):
    return dataclasses.replace(item, answer=dataclasses.replace(item.answer, payload=payload))


def _parse(text: str):
    from app.generators.math.inequalities import _parse_set

    parsed = _parse_set(text)
    assert parsed is not None
    return parsed


# --------------------------------------------------------------------- contracts
@pytest.mark.parametrize("topic", TOPICS, ids=[topic.id for topic in TOPICS])
def test_every_topic_declares_its_contract(topic) -> None:
    assert topic.family == "math"
    assert topic.difficulties
    assert topic.label_key.startswith("topic.")
    assert set(topic.difficulties) <= {"easy", "medium", "hard"}


@pytest.mark.parametrize("topic,difficulty", CASES, ids=CASES_IDS)
def test_same_seed_twice_is_the_same_item(topic, difficulty: str) -> None:
    first = build(topic, difficulty)
    second = build(topic, difficulty)
    assert first == second
    assert build(topic, difficulty, index=1) != first
    assert build(topic, difficulty, seed=SEED + 1) != first


@pytest.mark.parametrize("topic,difficulty", CASES, ids=CASES_IDS)
def test_honest_item_verifies(topic, difficulty: str) -> None:
    item = build(topic, difficulty)
    result = topic.verify(item)
    assert result.ok, result.reason


@pytest.mark.parametrize("topic,difficulty", CASES, ids=CASES_IDS)
def test_generated_items_always_verify(topic, difficulty: str) -> None:
    for seed in range(25):
        item = build(topic, difficulty, index=seed % 5, seed=seed)
        result = topic.verify(item)
        assert result.ok, (seed, result.reason, item.params)


@pytest.mark.parametrize("topic,difficulty", CASES, ids=CASES_IDS)
def test_params_stay_exact_rationals(topic, difficulty: str) -> None:
    item = build(topic, difficulty)
    assert all(isinstance(value, Fraction) for value in item.params.values())
    assert item.figure is None


@pytest.mark.parametrize("topic,difficulty", CASES, ids=CASES_IDS)
def test_item_is_wire_legal(topic, difficulty: str) -> None:
    item = build(topic, difficulty)
    WireStatement(key=item.statement_key, params=wire_params(item.params))
    WireAnswer(latex=item.answer.latex, kind=item.answer.kind, payload=item.answer.payload)


_DECIMAL = re.compile(r"\d+\.\d")


@pytest.mark.parametrize("topic", TOPICS, ids=[topic.id for topic in TOPICS])
def test_no_output_leaks_a_float(topic) -> None:
    for difficulty in topic.difficulties:
        item = build(topic, difficulty)
        rendered = [item.answer.latex, *(step.latex for step in item.steps)]
        assert not any(_DECIMAL.search(fragment) for fragment in rendered), rendered


# -------------------------------------------------------------------- corruption
def test_second_degree_corrupted_root_is_rejected() -> None:
    item = build(SECOND_DEGREE, "easy")
    assert not SECOND_DEGREE.verify(with_answer(item, solutions=["999"])).ok


def test_second_degree_corrupted_params_are_rejected() -> None:
    item = build(SECOND_DEGREE, "medium")
    tampered = dataclasses.replace(item, params={**item.params, "c": item.params["c"] + 1})
    assert not SECOND_DEGREE.verify(tampered).ok


def test_second_degree_corrupted_statement_key_is_rejected() -> None:
    flips = {"pp": "mp", "mp": "pp", "pm": "mm", "mm": "pm"}
    for difficulty in SECOND_DEGREE.difficulties:
        item = build(SECOND_DEGREE, difficulty)
        suffix = item.statement_key.rsplit("_", 1)[-1]
        if suffix not in flips:
            continue
        flipped = item.statement_key[: -len(suffix)] + flips[suffix]
        assert not SECOND_DEGREE.verify(dataclasses.replace(item, statement_key=flipped)).ok


def test_fractional_excluded_value_is_rejected() -> None:
    item = build(FRACTIONAL, "hard")
    excluded = item.params["e"]
    result = FRACTIONAL.verify(with_answer(item, solutions=[str(excluded)]))
    assert not result.ok
    assert result.reason == "excluded_value"


def test_fractional_other_excluded_value_is_rejected() -> None:
    item = build(FRACTIONAL, "hard")
    result = FRACTIONAL.verify(with_answer(item, solutions=[str(item.params["f"])]))
    assert not result.ok
    assert result.reason == "excluded_value"


def test_fractional_corrupted_root_is_rejected() -> None:
    item = build(FRACTIONAL, "easy")
    assert not FRACTIONAL.verify(with_answer(item, solutions=["999"])).ok


def test_fractional_medium_solution_is_not_an_integer() -> None:
    for index in range(10):
        item = build(FRACTIONAL, "medium", index=index)
        assert Fraction(item.answer.payload["solutions"][0]).denominator != 1


@pytest.mark.parametrize("topic_id", sorted(INEQUALITY_TOPICS))
def test_inequality_corrupted_set_is_rejected(topic_id: str) -> None:
    topic = INEQUALITY_TOPICS[topic_id]
    for difficulty in topic.difficulties:
        item = build(topic, difficulty)
        wrong = srepr(Union(Interval.open(-oo, 0), Interval.open(1, oo)))
        result = topic.verify(with_answer(item, set=[wrong]))
        assert not result.ok, difficulty


def _flip_closure(solution):
    """Turn every finite endpoint of the claimed set into the other closure."""
    if isinstance(solution, Interval):
        return Interval(
            solution.start,
            solution.end,
            not solution.left_open,
            not solution.right_open,
        )
    if isinstance(solution, Union):
        return Union(*[_flip_closure(argument) for argument in solution.args])
    return solution


@pytest.mark.parametrize("topic_id", sorted(INEQUALITY_TOPICS))
def test_inequality_open_closed_corruption_is_rejected(topic_id: str) -> None:
    """Flipping a bracket changes membership at one point only — it must still be caught."""
    topic = INEQUALITY_TOPICS[topic_id]
    for difficulty in topic.difficulties:
        item = build(topic, difficulty)
        (encoded,) = item.answer.payload["set"]
        claimed = _parse(encoded)
        flipped = _flip_closure(claimed)
        if flipped == claimed:
            continue  # an unbounded or empty answer has no finite endpoint to flip
        result = topic.verify(with_answer(item, set=[srepr(flipped)]))
        assert not result.ok, (topic_id, difficulty)


def test_systems_linear_corrupted_point_is_rejected() -> None:
    topic = SYSTEM_TOPICS["math.systems.linear_2x2"]
    item = build(topic, "medium")
    assert not topic.verify(with_answer(item, solution=["999|-999"])).ok


def test_systems_linear_rational_solution_is_exact() -> None:
    topic = SYSTEM_TOPICS["math.systems.linear_2x2"]
    item = build(topic, "hard")
    values = [Fraction(part) for part in item.answer.payload["solution"][0].split("|")]
    assert any(value.denominator != 1 for value in values)


def test_systems_quadratic_corrupted_point_is_rejected() -> None:
    topic = SYSTEM_TOPICS["math.systems.linear_quadratic"]
    item = build(topic, "medium")
    assert not topic.verify(with_answer(item, solutions=["0|0"])).ok


def test_inequality_system_tampered_vertex_is_rejected() -> None:
    item = build(INEQUALITY_SYSTEM, "hard")
    vertices = list(item.answer.payload["vertices"])
    assert len(vertices) == 4
    vertices[0] = "99|99"
    result = INEQUALITY_SYSTEM.verify(with_answer(item, **{**item.answer.payload, "vertices": vertices}))
    assert not result.ok
    assert result.reason == "vertex_set_mismatch"


def test_inequality_system_reordered_vertices_are_rejected() -> None:
    item = build(INEQUALITY_SYSTEM, "hard")
    vertices = list(item.answer.payload["vertices"])
    swapped = [vertices[1], vertices[0], *vertices[2:]]
    result = INEQUALITY_SYSTEM.verify(with_answer(item, **{**item.answer.payload, "vertices": swapped}))
    assert not result.ok
    assert result.reason == "vertex_order_mismatch"


def test_inequality_system_flipped_constraint_is_rejected() -> None:
    item = build(INEQUALITY_SYSTEM, "medium")
    constraints = list(item.answer.payload["constraints"])
    constraints[0] = "|".join(constraints[0].split("|")[:2] + [str(int(constraints[0].split("|")[2]) + 1)])
    result = INEQUALITY_SYSTEM.verify(with_answer(item, **{**item.answer.payload, "constraints": constraints}))
    assert not result.ok
    assert result.reason == "constraint_mismatch"


def test_inequality_system_has_bounded_and_unbounded_regions() -> None:
    kinds = set()
    for difficulty in INEQUALITY_SYSTEM.difficulties:
        for index in range(10):
            item = build(INEQUALITY_SYSTEM, difficulty, index=index)
            kinds.add(item.answer.payload["kind"][0])
    assert kinds == {"polygon", "unbounded"}
