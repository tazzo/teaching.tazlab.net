"""Relative motion — two objects meeting, parameterised *from the meeting*.

The research artifact (physics-kinematics-generation-units §1 Q3) is explicit: draw the
window ``T``, the meeting instant ``t* ∈ [T/3, 2T/3]``, the closing speed and its split;
then derive ``d₀`` and ``x*``. Drawing positions and speeds independently and hoping
they meet inside the window fails ~85% of the time, and the resulting item has no
unique admissible time to verify. Here the meeting is inside the window by
construction, both speeds are positive, and the closing speed is never zero.

The window is a multiple of 8 s and the meeting instant is ``3T/8``, ``T/2`` or ``5T/8``,
so ``t*`` is an exact integer strictly inside ``(T/3, 2T/3)`` and every derived distance
stays rational.
"""

from __future__ import annotations

import random
from fractions import Fraction

from app.core.units import fmt
from app.core.verify import VerificationResult, no_floats
from app.generators.base import Answer, Item, Step
from app.render.figure import cartesian_trace, linear_samples

# DESIGN §2.10, "Everyday motion" row: v 1-25 m/s, t 1-60 s.
SPEED_RANGE = (Fraction(1), Fraction(25))
DURATION_RANGE = (Fraction(1), Fraction(60))
# RESEARCH §1 Q3: a catch-up item needs a minimum closing speed, or t* explodes and the
# two speeds are nearly equal.
MIN_CLOSING_SPEED = Fraction(2)
# RESEARCH §4.5: distances stay at "a few km" even for the fastest head-on draw.
MAX_DISTANCE = Fraction(1000)

_WINDOWS = tuple(Fraction(value) for value in (8, 16, 24, 32, 40, 48, 56))
_MEETING_FRACTIONS = (Fraction(3, 8), Fraction(1, 2), Fraction(5, 8))
_HEAD_ON_CLOSINGS = tuple(Fraction(value) for value in (4, 6, 8, 10, 12, 15, 18, 20, 24))
_CATCH_UP_CLOSINGS = tuple(Fraction(value) for value in (2, 3, 4, 5, 6, 8, 10, 12))
_SCENARIO_FOR = {
    "easy": "same_direction",
    "medium": "opposite_direction",
    "hard": "delayed_start",
}


def _split_closing(rng: random.Random, closing: Fraction) -> tuple[Fraction, Fraction]:
    """Split the closing speed with both parts between a quarter and three quarters.

    The research artifact's split fraction ``f ∈ [0.25, 0.75]``, kept integral so the
    statement shows integers: ``v_A ∈ [⌈closing/4⌉, ⌊3·closing/4⌋]``.
    """
    low = -(-(closing / 4) // 1)
    high = (3 * closing / 4) // 1
    speed_a = Fraction(rng.randint(int(low), int(high)))
    return speed_a, closing - speed_a


def _meeting(rng: random.Random) -> tuple[Fraction, Fraction]:
    """``(window, meeting instant)`` — t* strictly inside (T/3, 2T/3), exactly."""
    window = Fraction(rng.choice(_WINDOWS))
    return window, window * Fraction(rng.choice(_MEETING_FRACTIONS))


def _traces(scenario: str, params: dict[str, Fraction]) -> tuple[list, list]:
    """The two position traces; the delayed start gets an exact vertex at δ."""
    window = params["t_window"]
    speed_a, speed_b, gap = params["v_a"], params["v_b"], params["d0"]
    object_a = linear_samples(speed_a, window)
    if scenario == "same_direction":
        object_b = linear_samples(speed_b, window, x0=gap)
    elif scenario == "opposite_direction":
        object_b = linear_samples(-speed_b, window, x0=gap)
    else:
        delay = params["delta"]
        object_b = [(Fraction(0), gap), (delay, gap)]
        object_b.extend(
            [(x + delay, y) for x, y in linear_samples(-speed_b, window - delay, x0=gap)][1:]
        )
    return object_a, object_b


def _position_a(params: dict[str, Fraction], at: Fraction) -> Fraction:
    return params["v_a"] * at


def _position_b(scenario: str, params: dict[str, Fraction], at: Fraction) -> Fraction:
    gap, speed_b = params["d0"], params["v_b"]
    if scenario == "same_direction":
        return gap + speed_b * at
    if scenario == "opposite_direction":
        return gap - speed_b * at
    delay = params["delta"]
    if at < delay:
        return gap
    return gap - speed_b * (at - delay)


class RelativeMotion:
    id = "physics.kinematics.relative"
    family = "physics"
    difficulties = ("easy", "medium", "hard")
    label_key = "topic.relative"
    scenarios = ("same_direction", "opposite_direction", "delayed_start")

    # ---------------------------------------------------------------- generate
    def generate(self, rng: random.Random, difficulty: str, seed: int, index: int) -> Item:
        window, meet_time = _meeting(rng)

        if difficulty == "easy":
            closing = Fraction(rng.choice(_CATCH_UP_CLOSINGS))
            slow = Fraction(rng.randint(1, int(SPEED_RANGE[1] - closing)))
            speed_a, speed_b = slow + closing, slow
            distance = closing * meet_time
            params = {
                "v_a": speed_a, "v_b": speed_b, "d0": distance,
                "t_window": window, "t_meet": meet_time, "x_meet": speed_a * meet_time,
            }
            steps = (
                Step("step.formula", "v_{rel} = v_A - v_B"),
                Step("step.substitute",
                     f"v_{{rel}} = {fmt(speed_a)} - {fmt(speed_b)} = {fmt(closing)}\\,\\text{{m/s}}"),
                Step("step.solve_time",
                     f"t = \\frac{{d}}{{v_{{rel}}}} = \\frac{{{fmt(distance)}}}{{{fmt(closing)}}}"),
                Step("step.result", f"t = {fmt(meet_time)}\\,\\text{{s}}"),
            )
            answer = Answer(f"{fmt(meet_time)}\\,\\text{{s}}", "scalar_with_unit",
                            {"value": [fmt(meet_time)], "unit": ["s"]})
            markers = [(Fraction(0), distance, "marker.start_b"),
                       (meet_time, speed_a * meet_time, "marker.meeting")]
        elif difficulty == "medium":
            closing = Fraction(rng.choice(_HEAD_ON_CLOSINGS))
            speed_a, speed_b = _split_closing(rng, closing)
            distance = closing * meet_time
            params = {
                "v_a": speed_a, "v_b": speed_b, "d0": distance,
                "t_window": window, "t_meet": meet_time, "x_meet": speed_a * meet_time,
            }
            steps = (
                Step("step.formula", "v_{rel} = v_A + v_B"),
                Step("step.substitute",
                     f"v_{{rel}} = {fmt(speed_a)} + {fmt(speed_b)} = {fmt(closing)}\\,\\text{{m/s}}"),
                Step("step.meet",
                     f"x = v_A \\cdot \\frac{{d}}{{v_{{rel}}}} = {fmt(speed_a)} \\cdot "
                     f"\\frac{{{fmt(distance)}}}{{{fmt(closing)}}}"),
                Step("step.result", f"x = {fmt(speed_a * meet_time)}\\,\\text{{m}}"),
            )
            answer = Answer(f"{fmt(speed_a * meet_time)}\\,\\text{{m}}", "scalar_with_unit",
                            {"value": [fmt(speed_a * meet_time)], "unit": ["m"]})
            markers = [(Fraction(0), distance, "marker.start_b"),
                       (meet_time, speed_a * meet_time, "marker.meeting")]
        else:
            closing = Fraction(rng.choice(_HEAD_ON_CLOSINGS))
            speed_a, speed_b = _split_closing(rng, closing)
            delay = Fraction(rng.randint(1, int(meet_time) - 1))
            distance = speed_a * meet_time + speed_b * (meet_time - delay)
            params = {
                "v_a": speed_a, "v_b": speed_b, "d0": distance, "delta": delay,
                "t_window": window, "t_meet": meet_time, "x_meet": speed_a * meet_time,
            }
            steps = (
                Step("step.formula", "v_A t = d - v_B (t - \\delta)"),
                Step("step.substitute",
                     f"{fmt(speed_a)} t = {fmt(distance)} - {fmt(speed_b)} (t - {fmt(delay)})"),
                Step("step.solve_time",
                     f"t = \\frac{{d + v_B \\delta}}{{v_A + v_B}} = "
                     f"\\frac{{{fmt(distance)} + {fmt(speed_b)} \\cdot {fmt(delay)}}}{{{fmt(closing)}}}"),
                Step("step.result", f"t = {fmt(meet_time)}\\,\\text{{s}}"),
            )
            answer = Answer(f"{fmt(meet_time)}\\,\\text{{s}}", "scalar_with_unit",
                            {"value": [fmt(meet_time)], "unit": ["s"]})
            markers = [(delay, distance, "marker.delayed_start"),
                       (meet_time, speed_a * meet_time, "marker.meeting")]

        object_a, object_b = _traces(_SCENARIO_FOR[difficulty], params)
        figure = cartesian_trace(
            x_unit="s",
            y_unit="m",
            t_max=window,
            samples=object_a,
            trace_label="trace.object_a",
            phase_label="phase.approach",
            markers=markers,
            extra_traces=[("trace.object_b", object_b)],
        )
        return Item(
            topic=self.id,
            difficulty=difficulty,
            seed=seed,
            index=index,
            params=params,
            statement_key=f"stmt.relative_{difficulty}",
            steps=steps,
            answer=answer,
            figure=figure,
        )

    # ------------------------------------------------------------------ verify
    def verify(self, item: Item) -> VerificationResult:
        if not no_floats(*item.params.values()):
            return VerificationResult(False, "float_atom")
        figure = item.figure
        if not isinstance(figure, dict) or figure.get("kind") != "kinematics":
            return VerificationResult(False, "missing_figure")
        scenario = _SCENARIO_FOR[item.difficulty]

        speed_a, speed_b = Fraction(item.params["v_a"]), Fraction(item.params["v_b"])
        gap = Fraction(item.params["d0"])
        window = Fraction(item.params["t_window"])
        meet_time = Fraction(item.params["t_meet"])
        meet_point = Fraction(item.params["x_meet"])

        for speed in (speed_a, speed_b):
            if not SPEED_RANGE[0] <= speed <= SPEED_RANGE[1]:
                return VerificationResult(False, "speed_out_of_scale")
        if not DURATION_RANGE[0] <= window <= DURATION_RANGE[1]:
            return VerificationResult(False, "duration_out_of_scale")
        if not 0 < gap <= MAX_DISTANCE:
            return VerificationResult(False, "distance_out_of_scale")
        if meet_time <= 0:
            return VerificationResult(False, "non_positive_time")
        # the meeting is strictly inside the window, never on a boundary
        if not window / 3 < meet_time < 2 * window / 3:
            return VerificationResult(False, "meeting_outside_window")

        if scenario == "same_direction":
            closing = speed_a - speed_b
            if closing < MIN_CLOSING_SPEED:
                return VerificationResult(False, "closing_speed_too_small")
            expected_time = gap / closing
            expected_point = speed_a * expected_time
        elif scenario == "opposite_direction":
            closing = speed_a + speed_b
            if closing == 0:
                return VerificationResult(False, "zero_closing_speed")
            expected_time = gap / closing
            expected_point = speed_a * expected_time
        else:
            delay = Fraction(item.params["delta"])
            if delay < 1 or delay >= meet_time:
                return VerificationResult(False, "delay_outside_the_window")
            closing = speed_a + speed_b
            if closing == 0:
                return VerificationResult(False, "zero_closing_speed")
            expected_time = (gap + speed_b * delay) / closing
            expected_point = speed_a * expected_time

        if meet_time != expected_time or meet_point != expected_point:
            return VerificationResult(False, "meeting_mismatch")
        # A starts behind B, passes it inside the window: exactly one crossing
        if _position_a(item.params, Fraction(0)) >= _position_b(scenario, item.params, Fraction(0)):
            return VerificationResult(False, "no_initial_separation")
        if _position_a(item.params, window) <= _position_b(scenario, item.params, window):
            return VerificationResult(False, "no_crossing_inside_the_window")
        # in a catch-up the meeting lies past B's starting point, head-on short of it
        if meet_point <= 0:
            return VerificationResult(False, "non_positive_meeting_point")
        if scenario == "same_direction":
            if meet_point <= gap:
                return VerificationResult(False, "meeting_point_outside_the_gap")
        elif meet_point >= gap:
            return VerificationResult(False, "meeting_point_outside_the_gap")

        traces = figure.get("traces") or []
        if len(traces) != 2:
            return VerificationResult(False, "missing_second_object")
        for index, trace in enumerate(traces):
            for x, y in trace.get("samples") or []:
                at = Fraction(x)
                model = (
                    _position_a(item.params, at) if index == 0
                    else _position_b(scenario, item.params, at)
                )
                if Fraction(y) != model:
                    return VerificationResult(False, "figure_disagrees_with_model")
        markers = figure.get("markers") or []
        meeting = [m for m in markers if m.get("label_key") == "marker.meeting"]
        if len(meeting) != 1:
            return VerificationResult(False, "missing_meeting_marker")
        if Fraction(meeting[0]["at"][0]) != meet_time or Fraction(meeting[0]["at"][1]) != meet_point:
            return VerificationResult(False, "marker_disagrees_with_model")
        if scenario == "delayed_start":
            delay = Fraction(item.params["delta"])
            if not any(Fraction(x) == delay for x, _ in traces[1]["samples"]):
                return VerificationResult(False, "missing_delay_vertex")

        claimed = item.answer.payload.get("value")
        if not claimed:
            return VerificationResult(False, "no_answer_claimed")
        expected, unit = (
            (meet_point, "m") if scenario == "opposite_direction" else (meet_time, "s")
        )
        if Fraction(claimed[0]) != expected:
            return VerificationResult(False, "answer_mismatch")
        if item.answer.latex != f"{fmt(expected)}\\,\\text{{{unit}}}":
            return VerificationResult(False, "answer_latex_mismatch")
        return VerificationResult(True)


TOPIC = RelativeMotion()
