"""The configurable piecewise-motion topic (`physics.kinematics.segments`).

Three properties matter here, and all three are the kind that ship silently when unchecked:

* the printed answer must follow from the graph **as drawn** — this topic is the one that
  shipped a statement and an answer that disagreed (x²+2x+8=0 answered x=-4, x=2), so the
  verifier reads the drawn samples back instead of trusting the generator's own numbers;
* the configurator's choices must reach the generator: the same seed with different options
  is a different exercise, and every combination the page can produce must verify;
* every `random` choice must resolve into a motion that verifies. The page now offers
  "random" for the kinds, the quantity and the unit system, so the *default* page is a
  random draw: a defect that only a random draw can reach is a defect the teacher hits.
"""

from __future__ import annotations

from fractions import Fraction

import pytest

from app.core.rng import make_rng
from app.core.units import fmt, fmt_reading
from app.generators.physics.segments import (
    ACCELERATION,
    ACCELERATE,
    CM_SYSTEM,
    DECELERATE,
    DISTANCE,
    KMH_SYSTEM,
    POSITION,
    RANDOM,
    SEGMENT_COUNTS,
    SI_SYSTEM,
    UNIFORM,
    VELOCITY,
    VELOCITY_AT,
    TOPIC,
)

DIFFICULTIES = ("easy", "medium", "hard")
KIND_SETS = (
    [UNIFORM, ACCELERATE, DECELERATE],
    [DECELERATE, DECELERATE, DECELERATE],
    [ACCELERATE, UNIFORM, DECELERATE, ACCELERATE],
    [DECELERATE, ACCELERATE, UNIFORM, DECELERATE],
    [ACCELERATE, DECELERATE, UNIFORM, DECELERATE, DECELERATE],
    [UNIFORM, UNIFORM, UNIFORM, UNIFORM, ACCELERATE],
)


def make(kinds, quantity, units, ask=None, difficulty="medium", seed=11, count=None):
    options = {"count": len(kinds) if count is None else count,
               "kinds": kinds, "quantity": quantity, "units": units}
    if ask is not None:
        options["ask"] = ask
    return TOPIC.generate(make_rng(seed, TOPIC.id, difficulty, 0), difficulty, seed, 0, options)


def combinations():
    for kinds in KIND_SETS:
        for quantity in (VELOCITY, POSITION):
            for system in (SI_SYSTEM, KMH_SYSTEM, CM_SYSTEM):
                for ask in (VELOCITY_AT, DISTANCE, ACCELERATION):
                    if ask == ACCELERATION and all(kind == UNIFORM for kind in kinds):
                        continue
                    yield kinds, quantity, system, ask


@pytest.mark.parametrize("kinds,quantity,system,ask", list(combinations()))
def test_every_configurator_combination_verifies(kinds, quantity, system, ask):
    """The page can produce these; none may be rejected, and none may disagree with its graph."""
    for difficulty in DIFFICULTIES:
        item = make(kinds, quantity, system.id, ask, difficulty=difficulty, seed=7)
        result = TOPIC.verify(item)
        assert result.ok, f"{quantity}/{system.id}/{ask}/{difficulty}: {result.reason}"


@pytest.mark.parametrize("seed", range(1, 25))
def test_the_default_page_random_draw_always_verifies(seed):
    """What the page does with an untouched form: every seed, every difficulty, all random."""
    for difficulty in DIFFICULTIES:
        item = TOPIC.generate(make_rng(seed, TOPIC.id, difficulty, 0), difficulty, seed, 0, {})
        result = TOPIC.verify(item)
        assert result.ok, f"seed {seed}/{difficulty}: {result.reason}"


def test_the_random_draw_really_varies():
    """A "random" that always answered the same would make the page a fixed exercise."""
    drawn = {(TOPIC.generate(make_rng(seed, TOPIC.id, "medium", 0), "medium", seed, 0, {})
              .figure["y_unit"]) for seed in range(1, 30)}
    assert len(drawn) > 1, "the unit system is drawn, not constant"


@pytest.mark.parametrize("count", SEGMENT_COUNTS)
def test_the_segment_count_reaches_the_graph(count):
    item = make([UNIFORM] * count, VELOCITY, SI_SYSTEM.id, DISTANCE, count=count, seed=4)
    assert len(item.figure["traces"]) == count
    assert len(item.figure["guides"]) == count - 1, "n segments have n-1 internal boundaries"


def test_a_random_kind_row_is_resolved_per_item():
    item = make([RANDOM, UNIFORM, RANDOM], VELOCITY, SI_SYSTEM.id, DISTANCE, seed=2)
    kinds = [trace["kind"] for trace in item.figure["traces"]]
    assert kinds[1] == UNIFORM, "the pinned row stays what the operator chose"
    assert all(kind != RANDOM for kind in kinds), "no row reaches the figure undrawn"


def test_the_verifier_catches_an_answer_that_contradicts_the_graph():
    """The defect class this topic exists to prevent: a plausible answer, not the drawn one."""
    item = make([UNIFORM, ACCELERATE, UNIFORM], VELOCITY, SI_SYSTEM.id, DISTANCE, seed=5)
    tampered = type(item)(**{**item.__dict__, "answer": type(item.answer)(
        latex=item.answer.latex, kind=item.answer.kind,
        payload={**item.answer.payload, "value": ["999"]})})
    result = TOPIC.verify(tampered)
    assert not result.ok
    assert "answer_disagrees_with_graph" in (result.reason or "")


def test_a_velocity_reading_lied_about_on_the_graph_is_rejected():
    """Moving the marker without moving the motion must break the answer's agreement."""
    item = make([ACCELERATE] * 3, VELOCITY, SI_SYSTEM.id, VELOCITY_AT, seed=3)
    figure = {**item.figure, "markers": [{**item.figure["markers"][0], "at": ["0", "0"]}]}
    result = TOPIC.verify(type(item)(**{**item.__dict__, "figure": figure}))
    assert not result.ok, "a marker at the origin cannot still read the same velocity"


def test_the_figure_starts_at_the_origin_with_no_negative_time():
    """The operator's rule: time never runs backwards, so the graph starts at zero.

    The *value* on the y axis is a different matter: a motion running the other way is
    drawn below the axis and a body at rest on it, so only the time axis is pinned.
    """
    for kinds, quantity, system, ask in combinations():
        item = make(kinds, quantity, system.id, ask, seed=13)
        assert item.figure["origin"] == "corner"
        assert item.figure["domain"]["t_min"] == "0"
        first_times = [trace["samples"][0][0] for trace in item.figure["traces"]]
        assert first_times[0] == "0"
        for trace in item.figure["traces"]:
            times = [Fraction(time) for time, _ in trace["samples"]]
            assert min(times) >= 0, "no stretch is drawn before the origin"


def test_the_segments_are_drawn_as_separate_traces_with_a_guide_between_them():
    """The operator asked to *see* the division: one trace per segment, one dashed guide each."""
    item = make([ACCELERATE, UNIFORM, DECELERATE], VELOCITY, SI_SYSTEM.id, ACCELERATION, seed=9)
    assert len(item.figure["traces"]) == 3
    assert len(item.figure["guides"]) == 2, "three segments have exactly two boundaries"
    boundaries = [Fraction(guide["at"]) for guide in item.figure["guides"]]
    assert boundaries == sorted(boundaries)
    # a guide marks the boundary of the drawn motion, not a point in empty space
    end = Fraction(item.figure["traces"][-1]["samples"][-1][0])
    assert all(0 < boundary < end for boundary in boundaries)


def test_the_segments_are_continuous_where_they_meet():
    """A graph of one motion: the last sample of a segment is the first sample of the next."""
    for kinds, quantity, system, ask in combinations():
        item = make(kinds, quantity, system.id, ask, seed=17)
        traces = item.figure["traces"]
        for previous, following in zip(traces, traces[1:]):
            assert previous["samples"][-1] == following["samples"][0], (
                f"{kinds}/{quantity}/{system.id}/{ask} breaks the motion")


def test_a_decelerating_segment_always_slows_down():
    """A stretch labelled "moto decelerato" that draws flat is a graph that lies about itself.

    The kind names what the *speed* does, so the test reads the speed and not the sign of
    the line: a motion running the other way approaches the time axis from below while it
    slows down. On a velocity graph that is the magnitude of the drawn value; on a position
    graph the speed is the *slope*, so the second half has to climb less steeply than the
    first.
    """
    for kinds, quantity, system, ask in combinations():
        item = make(kinds, quantity, system.id, ask, seed=23)
        positions = item.figure["y_label"] == "trace.position"
        for trace in item.figure["traces"]:
            if trace["kind"] != DECELERATE:
                continue
            samples = [(Fraction(x), Fraction(y)) for x, y in trace["samples"]]
            first, middle, last = samples[0], samples[len(samples) // 2], samples[-1]
            if positions:
                early = abs((middle[1] - first[1]) / (middle[0] - first[0]))
                late = abs((last[1] - middle[1]) / (last[0] - middle[0]))
                assert late < early, f"the speed did not fall: {trace['samples']}"
            else:
                assert abs(last[1]) < abs(first[1]), (
                    f"a decelerating stretch did not slow down: {samples}")


def test_a_stretch_that_turns_back_is_rejected():
    """The invariant the area and the slope readings rest on: one motion, one direction.

    Without it a stretch that reverses would be drawn as two motions and every reading off
    it — the space it covers, the velocity at an instant — would describe another one.
    """
    item = make([ACCELERATE, UNIFORM, UNIFORM], VELOCITY, SI_SYSTEM.id, VELOCITY_AT, seed=6)
    trace = item.figure["traces"][0]
    samples = [list(sample) for sample in trace["samples"]]
    entry, exit_ = Fraction(samples[0][1]), Fraction(samples[-1][1])
    # one sample on the far side of the entry value, in a stretch that only moves one way
    samples[2][1] = fmt(entry - 4 if exit_ > entry else entry + 4)
    traces = [dict(trace, samples=samples), *item.figure["traces"][1:]]
    result = TOPIC.verify(type(item)(**{**item.__dict__, "figure": {**item.figure, "traces": traces}}))
    assert not result.ok
    assert "stretch_reverses" in (result.reason or "")


def test_an_acceleration_question_on_a_uniform_motion_is_refused_with_a_reason():
    with pytest.raises(ValueError, match="at least one accelerated"):
        TOPIC.validate_options({"count": 3, "kinds": [UNIFORM] * 3, "ask": ACCELERATION})


def test_a_draw_that_cannot_answer_an_explicit_acceleration_is_refused_with_a_reason():
    """The kinds are drawn after validation, so the refusal has to survive the draw."""
    for seed in range(1, 40):
        try:
            item = TOPIC.generate(make_rng(seed, TOPIC.id, "medium", 0), "medium", seed, 0,
                                  {"count": 3, "kinds": [RANDOM] * 3, "quantity": VELOCITY,
                                   "units": SI_SYSTEM.id, "ask": ACCELERATION})
        except ValueError as exc:
            assert "at least one accelerated" in str(exc)
            continue
        assert TOPIC.verify(item).ok


def test_the_drawed_reading_is_one_the_motion_can_answer():
    """Without an ask in the form, the reading must still be readable off the graph."""
    for seed in range(1, 40):
        item = TOPIC.generate(make_rng(seed, TOPIC.id, "medium", 0), "medium", seed, 0, {})
        ask = item.statement_key.split("_")[1]
        if ask == ACCELERATION:
            segment = int(item.params["seg"]) - 1
            trace = item.figure["traces"][segment]
            assert trace["kind"] != UNIFORM, "an acceleration was asked of a uniform segment"


@pytest.mark.parametrize("options,reason", [
    ({"count": 2}, "segment count must be one of"),
    ({"count": 6}, "segment count must be one of"),
    ({"count": "many"}, "segment count must be one of"),
    ({"count": 4, "kinds": [UNIFORM, UNIFORM]}, "one entry per segment"),
    ({"kinds": [UNIFORM, UNIFORM, UNIFORM, UNIFORM]}, "one entry per segment"),
    ({"kinds": [UNIFORM, "hyperspace", UNIFORM]}, "unknown segment kinds"),
    ({"quantity": "acceleration"}, "unknown quantity"),
    ({"units": "imperial"}, "unknown unit system"),
    ({"ask": "colour"}, "unknown ask"),
])
def test_unusable_configurations_are_rejected_with_a_machine_reason(options, reason):
    with pytest.raises(ValueError, match=reason):
        TOPIC.validate_options(options)


def test_the_same_seed_and_configuration_reproduce_the_same_exercise():
    first = make([UNIFORM, ACCELERATE, UNIFORM], VELOCITY, SI_SYSTEM.id, DISTANCE, seed=20260924)
    second = make([UNIFORM, ACCELERATE, UNIFORM], VELOCITY, SI_SYSTEM.id, DISTANCE, seed=20260924)
    assert first == second


def test_changing_a_configuration_changes_the_exercise():
    """Options are part of the item's identity — otherwise the form would be a decoration."""
    base = make([UNIFORM, ACCELERATE, UNIFORM], VELOCITY, SI_SYSTEM.id, DISTANCE, seed=20260924)
    other = make([UNIFORM, ACCELERATE, UNIFORM], POSITION, SI_SYSTEM.id, DISTANCE, seed=20260924)
    assert base.figure["y_unit"] != other.figure["y_unit"]


def test_a_reading_is_a_decimal_where_the_decimal_terminates():
    """7/2 m/s is not how a student reads a graph; the value stays exact either way."""
    item = make([ACCELERATE] * 3, VELOCITY, SI_SYSTEM.id, ACCELERATION, seed=1)
    for step in item.steps:
        assert "}{" not in step.latex.split("\\frac")[0], "no raw fraction where a reading is shown"
    assert fmt_reading(Fraction(7, 2)) == "3.5"
    assert fmt_reading(Fraction(1, 3)) == "1/3", "a non-terminating value stays exact"


def test_the_converted_units_are_exact_multiples_of_the_si_exercise():
    """km and cm are conversions of the same motion, never a redrawn one."""
    si_item = make([UNIFORM, ACCELERATE, UNIFORM], VELOCITY, SI_SYSTEM.id, DISTANCE, seed=21)
    km_item = make([UNIFORM, ACCELERATE, UNIFORM], VELOCITY, KMH_SYSTEM.id, DISTANCE, seed=21)
    travelled_si = Fraction(si_item.answer.payload["value"][0].replace(",", ""))
    travelled_km = Fraction(km_item.answer.payload["value"][0].replace(",", ""))
    assert abs(travelled_km * 1000 - travelled_si) < Fraction(1, 10), "same motion, converted"
    cm_item = make([UNIFORM, ACCELERATE, UNIFORM], VELOCITY, CM_SYSTEM.id, DISTANCE, seed=21)
    travelled_cm = Fraction(cm_item.answer.payload["value"][0].replace(",", ""))
    assert abs(travelled_cm / 100 - travelled_si) < Fraction(1, 10), "same motion, converted"


def test_a_velocity_read_off_a_converted_position_graph_is_labelled_with_its_own_unit():
    """The step must carry the number the axis carries: 3.5 m/s is not 3.5 km/h."""
    for system in (KMH_SYSTEM, CM_SYSTEM):
        item = make([ACCELERATE] * 3, POSITION, system.id, VELOCITY_AT, seed=31)
        step = next(step for step in item.steps if step.label_key == "step.convert")
        value = Fraction(item.answer.payload["value"][0])
        assert f"\\text{{{system.velocity_unit}}}" in step.latex
        assert fmt_reading(value) in step.latex, "the answer's value is the one converted"


def test_no_float_reaches_the_item():
    item = make([ACCELERATE, DECELERATE, UNIFORM], POSITION, RANDOM, ACCELERATION, seed=4)
    assert all(isinstance(value, Fraction) for value in item.params.values())


def uniform_stretches(items):
    """Every (item, stretch) whose velocity is drawn constant, with its drawn values."""
    for item in items:
        for trace in item.figure["traces"]:
            if trace["kind"] == UNIFORM:
                yield item, [Fraction(value) for _, value in trace["samples"]]


def random_motion(seed, quantity=VELOCITY, ask=DISTANCE, count=4, kinds=None):
    return TOPIC.generate(make_rng(seed, TOPIC.id, "easy", 0), "easy", seed, 0,
                          {"count": count, "kinds": kinds or [RANDOM] * count,
                           "quantity": quantity, "units": SI_SYSTEM.id, "ask": ask})


def space_shown_by(item) -> Fraction:
    """The space the drawn graph covers, read off it a second way than the generator did.

    On a position graph the curve's rise or fall per stretch; on a velocity graph the area
    under each stretch, in magnitude. Both are exact because a stretch never reverses.
    """
    total = Fraction(0)
    for trace in item.figure["traces"]:
        samples = [(Fraction(x), Fraction(y)) for x, y in trace["samples"]]
        if item.figure["y_label"] == "trace.position":
            total += abs(samples[-1][1] - samples[0][1])
        else:
            for (x1, y1), (x2, y2) in zip(samples, samples[1:]):
                total += abs((x2 - x1) * (y1 + y2) / 2)
    return total


def test_a_uniform_stretch_is_drawn_below_the_time_axis_sometimes():
    """The operator's ask: a uniform stretch reads a negative velocity as readily as a
    positive one, so the student has to look at which side of the axis it sits on."""
    items = [random_motion(seed) for seed in range(1, 30)]
    below = [values for _, values in uniform_stretches(items) if all(v < 0 for v in values)]
    assert below, "no uniform stretch was ever drawn with a negative velocity"
    for item in items:
        signs = {Fraction(value) > 0 for trace in item.figure["traces"]
                 for _, value in trace["samples"] if Fraction(value) != 0}
        assert len(signs) <= 1, f"one motion keeps one direction: {item.figure['traces']}"


def test_a_uniform_stretch_stands_still_sometimes():
    """The other half of the ask: a body at rest for a stretch is a flat line *on* the axis,
    which is a reading a student makes and not a graph with nothing on it."""
    items = [random_motion(seed) for seed in range(1, 200)]
    at_rest = [values for _, values in uniform_stretches(items) if all(v == 0 for v in values)]
    assert at_rest, "no uniform stretch was ever drawn at v = 0"
    for item, _ in uniform_stretches(items):
        assert TOPIC.verify(item).ok


@pytest.mark.parametrize("quantity", [VELOCITY, POSITION])
def test_the_space_covered_is_a_length_whatever_the_direction(quantity):
    """"Spazio totale percorso" is ground covered, not a signed displacement: a motion that
    runs the other way has covered just as much, and an answer with a minus on it would be
    a length nobody walked."""
    for seed in range(1, 60):
        item = random_motion(seed, quantity=quantity)
        covered = Fraction(item.answer.payload["value"][0])
        assert covered >= 0, f"seed {seed}: a distance cannot be negative ({covered})"
        assert covered == space_shown_by(item), (
            f"seed {seed}: the answer is not the space the graph shows")


def test_a_backwards_motion_reads_its_distance_off_the_position_graph_too():
    """The same exercise on the other axis: a falling curve covers the same ground, and the
    derivation has to say it is reading a magnitude rather than a signed displacement."""
    for seed in range(1, 200):
        item = random_motion(seed, quantity=POSITION)
        values = [Fraction(value) for trace in item.figure["traces"]
                  for _, value in trace["samples"]]
        if min(values) >= 0:
            continue
        covered = Fraction(item.answer.payload["value"][0])
        assert covered == space_shown_by(item) > 0
        assert any(step.label_key == "step.read_path" for step in item.steps)
        return
    raise AssertionError("no motion was ever drawn running the other way")