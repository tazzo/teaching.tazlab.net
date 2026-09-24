"""The configurable piecewise-motion topic (`physics.kinematics.segments`).

Two properties matter here, and both are the kind that ship silently when unchecked:

* the printed answer must follow from the graph **as drawn** — this topic is the one that
  shipped a statement and an answer that disagreed (x²+2x+8=0 answered x=-4, x=2), so the
  verifier reads the drawn samples back instead of trusting the generator's own numbers;
* the configurator's choices must reach the generator: the same seed with different options
  is a different exercise, and every combination the page can produce must verify.
"""

from __future__ import annotations

from fractions import Fraction

import pytest

from app.core.rng import make_rng
from app.core.units import fmt_reading
from app.generators.physics.segments import (
    ACCELERATION,
    ACCELERATE,
    DECELERATE,
    DISTANCE,
    POSITION,
    RANDOM,
    SI,
    UNIFORM,
    VELOCITY,
    VELOCITY_AT,
    TOPIC,
)

DIFFICULTIES = ("easy", "medium", "hard")
KIND_SETS = (
    [UNIFORM],
    [ACCELERATE],
    [DECELERATE],
    [UNIFORM, ACCELERATE],
    [DECELERATE, ACCELERATE],
    [ACCELERATE, UNIFORM, DECELERATE, ACCELERATE],
    [ACCELERATE, DECELERATE, UNIFORM],
)


def make(kinds, quantity, units, ask, difficulty="medium", seed=11):
    options = {"kinds": kinds, "quantity": quantity, "units": units, "ask": ask}
    return TOPIC.generate(make_rng(seed, TOPIC.id, difficulty, 0), difficulty, seed, 0, options)


def combinations():
    for kinds in KIND_SETS:
        for quantity in (VELOCITY, POSITION):
            for units in (SI, RANDOM):
                for ask in (VELOCITY_AT, DISTANCE, ACCELERATION):
                    if ask == ACCELERATION and all(kind == UNIFORM for kind in kinds):
                        continue
                    yield kinds, quantity, units, ask


@pytest.mark.parametrize("kinds,quantity,units,ask", list(combinations()))
def test_every_configurator_combination_verifies(kinds, quantity, units, ask):
    """The page can produce these; none may be rejected, and none may disagree with its graph."""
    for difficulty in DIFFICULTIES:
        item = make(kinds, quantity, units, ask, difficulty=difficulty, seed=7)
        result = TOPIC.verify(item)
        assert result.ok, f"{quantity}/{units}/{ask}/{difficulty}: {result.reason}"


def test_the_verifier_catches_an_answer_that_contradicts_the_graph():
    """The defect class this topic exists to prevent: a plausible answer, not the drawn one."""
    item = make([UNIFORM, ACCELERATE], VELOCITY, SI, DISTANCE, seed=5)
    tampered = type(item)(**{**item.__dict__, "answer": type(item.answer)(
        latex=item.answer.latex, kind=item.answer.kind,
        payload={**item.answer.payload, "value": ["999"]})})
    result = TOPIC.verify(tampered)
    assert not result.ok
    assert "answer_disagrees_with_graph" in (result.reason or "")


def test_a_velocity_reading_lied_about_on_the_graph_is_rejected():
    """Moving the marker without moving the motion must break the answer's agreement."""
    item = make([ACCELERATE], VELOCITY, SI, VELOCITY_AT, seed=3)
    figure = {**item.figure, "markers": [{**item.figure["markers"][0], "at": ["0", "0"]}]}
    result = TOPIC.verify(type(item)(**{**item.__dict__, "figure": figure}))
    assert not result.ok, "a marker at the origin cannot still read the same velocity"


def test_the_figure_starts_at_the_origin_with_no_negative_time():
    """The operator's rule: graphs run from zero, so the axes meet in the bottom-left corner."""
    for kinds, quantity, units, ask in combinations():
        item = make(kinds, quantity, units, ask, seed=13)
        assert item.figure["origin"] == "corner"
        assert item.figure["domain"]["t_min"] == "0"
        first_times = [trace["samples"][0][0] for trace in item.figure["traces"]]
        assert first_times[0] == "0"
        for trace in item.figure["traces"]:
            values = [Fraction(value) for _, value in trace["samples"]]
            assert all(value >= 0 for value in values), "no negative speed or position is drawn"


def test_the_segments_are_drawn_as_separate_traces_with_a_guide_between_them():
    """The operator asked to *see* the division: one trace per segment, one dashed guide each."""
    item = make([ACCELERATE, UNIFORM, DECELERATE], VELOCITY, SI, ACCELERATION, seed=9)
    assert len(item.figure["traces"]) == 3
    assert len(item.figure["guides"]) == 2, "three segments have exactly two boundaries"
    boundaries = [Fraction(guide["at"]) for guide in item.figure["guides"]]
    assert boundaries == sorted(boundaries)
    # a guide marks the boundary of the drawn motion, not a point in empty space
    end = Fraction(item.figure["traces"][-1]["samples"][-1][0])
    assert all(0 < boundary < end for boundary in boundaries)


def test_the_segments_are_continuous_where_they_meet():
    """A graph of one motion: the last sample of a segment is the first sample of the next."""
    item = make([UNIFORM, ACCELERATE, DECELERATE], POSITION, SI, DISTANCE, seed=17)
    traces = item.figure["traces"]
    for previous, following in zip(traces, traces[1:]):
        assert previous["samples"][-1][1] == following["samples"][0][1]


def test_an_acceleration_question_on_a_uniform_motion_is_refused_with_a_reason():
    with pytest.raises(ValueError, match="at least one accelerated"):
        TOPIC.validate_options({"kinds": [UNIFORM, UNIFORM], "ask": ACCELERATION})


@pytest.mark.parametrize("options,reason", [
    ({"kinds": []}, "1\\.\\.4"),
    ({"kinds": ["uniform"] * 5}, "1\\.\\.4"),
    ({"kinds": ["hyperspace"]}, "unknown segment kinds"),
    ({"quantity": "acceleration"}, "unknown quantity"),
    ({"units": "imperial"}, "unknown unit system"),
    ({"ask": "colour"}, "unknown ask"),
])
def test_unusable_configurations_are_rejected_with_a_machine_reason(options, reason):
    with pytest.raises(ValueError, match=reason):
        TOPIC.validate_options(options)


def test_the_same_seed_and_configuration_reproduce_the_same_exercise():
    first = make([UNIFORM, ACCELERATE], VELOCITY, SI, DISTANCE, seed=20260924)
    second = make([UNIFORM, ACCELERATE], VELOCITY, SI, DISTANCE, seed=20260924)
    assert first == second


def test_changing_a_configuration_changes_the_exercise():
    """Options are part of the item's identity — otherwise the form would be a decoration."""
    base = make([UNIFORM, ACCELERATE], VELOCITY, SI, DISTANCE, seed=20260924)
    other = make([UNIFORM, ACCELERATE], POSITION, SI, DISTANCE, seed=20260924)
    assert base.figure["y_unit"] != other.figure["y_unit"]


def test_a_reading_is_a_decimal_where_the_decimal_terminates():
    """7/2 m/s is not how a student reads a graph; the value stays exact either way."""
    item = make([ACCELERATE], VELOCITY, SI, ACCELERATION, seed=1)
    for step in item.steps:
        assert "}{" not in step.latex.split("\\frac")[0], "no raw fraction where a reading is shown"
    assert fmt_reading(Fraction(7, 2)) == "3.5"
    assert fmt_reading(Fraction(1, 3)) == "1/3", "a non-terminating value stays exact"


def test_the_converted_units_are_exact_multiples_of_the_si_exercise():
    """km/h and km are conversions of the same motion, never a redrawn one."""
    si_item = make([UNIFORM, ACCELERATE], VELOCITY, SI, DISTANCE, seed=21)
    conv_item = make([UNIFORM, ACCELERATE], VELOCITY, RANDOM, DISTANCE, seed=21)
    travelled_si = Fraction(si_item.answer.payload["value"][0].replace(",", ""))
    travelled_km = Fraction(conv_item.answer.payload["value"][0].replace(",", ""))
    assert abs(travelled_km * 1000 - travelled_si) < Fraction(1, 10), "same motion, converted"


def test_no_float_reaches_the_item():
    item = make([ACCELERATE, DECELERATE], POSITION, RANDOM, ACCELERATION, seed=4)
    assert all(isinstance(value, Fraction) for value in item.params.values())
