"""Uniformly accelerated motion — v(t) = v0 + a t, s(t) = v0 t + a t²/2, with graphs.

Easy: from rest. Medium: v0 ≠ 0 and the stopping time. Hard: derive the acceleration
from two data points. v(t) is emitted as a second trace so the graph shows both laws.
"""

from __future__ import annotations

import random
from fractions import Fraction

from app.core.units import fmt
from app.core.verify import VerificationResult, no_floats
from app.generators.base import Answer, Item, Step
from app.render.figure import cartesian_trace


class AcceleratedMotion:
    id = "physics.kinematics.accelerated"
    family = "physics"
    difficulties = ("easy", "medium", "hard")
    label_key = "topic.accelerated"
    scenarios = ("accelerated_from_rest", "accelerated_with_v0", "accelerated_derive_a")

    def generate(self, rng: random.Random, difficulty: str, seed: int, index: int) -> Item:
        if difficulty == "easy":
            a = Fraction(rng.randint(1, 6))
            t = Fraction(rng.randint(2, 12))
            v0 = Fraction(0)
            v = v0 + a * t
            s = v0 * t + a * t * t / 2
            params = {"a": a, "t": t, "v0": v0, "v": v, "s": s}
            steps = (
                Step("step.formula_v", "v = a \\cdot t"),
                Step("step.substitute", f"v = {fmt(a)} \\cdot {fmt(t)}"),
                Step("step.result", f"v = {fmt(v)}\\,\\text{{m/s}}"),
            )
            answer = Answer(f"{fmt(v)}\\,\\text{{m/s}}", "scalar_with_unit", {"value": [fmt(v)], "unit": ["m/s"]})
            marker = (t, v, "marker.asked_instant")
            t_plot = t
        elif difficulty == "medium":
            a = -Fraction(rng.randint(2, 8))          # braking
            v0 = Fraction(rng.choice([10, 12, 15, 20, 24]))
            t_stop = -v0 / a
            s_stop = v0 * t_stop + a * t_stop * t_stop / 2
            params = {"a": a, "v0": v0, "t_stop": t_stop, "s_stop": s_stop}
            steps = (
                Step("step.formula", "0 = v_0 + a\\,t"),
                Step("step.substitute", f"t = \\frac{{-{fmt(v0)}}}{{{fmt(a)}}}"),
                Step("step.result", f"t = {fmt(t_stop)}\\,\\text{{s}}"),
            )
            answer = Answer(f"{fmt(t_stop)}\\,\\text{{s}}", "scalar_with_unit", {"value": [fmt(t_stop)], "unit": ["s"]})
            marker = (t_stop, Fraction(0), "marker.stop")
            t_plot = t_stop
        else:
            # Read the acceleration off a v(t) graph: two speed readings.
            # The earlier version used a = 2Δs/Δt², which is only valid from rest —
            # the verifier rejected it, which is exactly what the verifier is for.
            v0 = Fraction(rng.choice([0, 2, 4, 5]))
            a = Fraction(rng.randint(1, 4))
            t1 = Fraction(rng.randint(2, 5))
            t2 = t1 + Fraction(rng.randint(2, 6))
            v1 = v0 + a * t1
            v2 = v0 + a * t2
            params = {"a": a, "v0": v0, "t1": t1, "t2": t2, "v1": v1, "v2": v2}
            steps = (
                Step("step.read_points", f"v({fmt(t1)}) = {fmt(v1)}\\,\\text{{m/s}},\\quad v({fmt(t2)}) = {fmt(v2)}\\,\\text{{m/s}}"),
                Step("step.slope", f"a = \\frac{{\\Delta v}}{{\\Delta t}} = \\frac{{{fmt(v2 - v1)}}}{{{fmt(t2 - t1)}}}"),
                Step("step.result", f"a = {fmt(a)}\\,\\text{{m/s}}^2"),
            )
            answer = Answer(f"{fmt(a)}\\,\\text{{m/s}}^2", "scalar_with_unit", {"value": [fmt(a)], "unit": ["m/s^2"]})
            marker = (t2, v2, "marker.second_reading")
            t_plot = t2

        t_max = Fraction(t_plot) * Fraction(5, 4)
        v0 = Fraction(params["v0"])
        a = Fraction(params["a"])
        # ONE measured quantity per figure: a shared y-axis cannot be captioned "[m]" while
        # also carrying metres per second. Every difficulty here asks about velocity, so the
        # figure is the v(t) line — where the braking case visibly crosses zero.
        figure = cartesian_trace(
            x_unit="s",
            y_unit="m/s",
            t_max=t_max,
            samples=[(Fraction(0), v0), (t_max, v0 + a * t_max)],
            trace_label="trace.velocity",
            phase_label="phase.accelerated",
            markers=[marker],
        )
        return Item(
            topic=self.id,
            difficulty=difficulty,
            seed=seed,
            index=index,
            params=params,
            statement_key=f"stmt.accelerated_{difficulty}",
            steps=steps,
            answer=answer,
            figure=figure,
        )

    def verify(self, item: Item) -> VerificationResult:
        if not no_floats(*item.params.values()):
            return VerificationResult(False, "float_atom")
        if item.figure is None or not item.figure.get("traces"):
            return VerificationResult(False, "missing_figure")

        a = Fraction(item.params["a"])
        claimed = Fraction(item.answer.payload["value"][0])
        difficulty = item.difficulty

        if difficulty == "easy":
            expected = a * Fraction(item.params["t"])
            if Fraction(item.params["v0"]) != 0:
                return VerificationResult(False, "should_start_from_rest")
        elif difficulty == "medium":
            v0 = Fraction(item.params["v0"])
            expected = -v0 / a
            if a >= 0:
                return VerificationResult(False, "not_a_braking_case")
            stop_distance = v0 * expected + a * expected * expected / 2
            if Fraction(item.params["s_stop"]) != stop_distance:
                return VerificationResult(False, "stopping_distance_mismatch")
        else:
            v0 = Fraction(item.params["v0"])
            t1, t2 = Fraction(item.params["t1"]), Fraction(item.params["t2"])
            if t2 <= t1:
                return VerificationResult(False, "degenerate_interval")
            v1, v2 = Fraction(item.params["v1"]), Fraction(item.params["v2"])
            if v1 != v0 + a * t1 or v2 != v0 + a * t2:
                return VerificationResult(False, "reading_not_on_the_line")
            expected = (v2 - v1) / (t2 - t1)

        if claimed != expected:
            return VerificationResult(False, "answer_mismatch")
        if expected <= 0 and difficulty != "medium":
            return VerificationResult(False, "non_positive_acceleration")
        # the marked point must lie on whichever law the figure plots
        x = Fraction(item.figure["markers"][0]["at"][0])
        y = Fraction(item.figure["markers"][0]["at"][1])
        # the figure is v(t) for every difficulty, so the marked point must satisfy that law
        on_law = y == item.params["v0"] + a * x
        if not on_law:
            return VerificationResult(False, "figure_disagrees_with_model")
        return VerificationResult(True)


TOPIC = AcceleratedMotion()
