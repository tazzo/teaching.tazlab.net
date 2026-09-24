"""Uniform rectilinear motion — s(t) = x0 + v t, with a graph.

Easy: one object, find the distance. Medium: convert km/h to m/s first. Hard: read the
speed off the graph (two marked points) — which is why this topic needs the figure.
Scenario magnitudes come from the DESIGN §2.10 table; every value is exact.
"""

from __future__ import annotations

import random
from fractions import Fraction

from app.core.latex import to_latex
from app.core.units import convert, fmt
from app.core.verify import VerificationResult, no_floats
from app.generators.base import Answer, Item, Step
from app.render.figure import cartesian_trace, linear_samples

S = '"s"'  # noqa: F841 (documentation aid for the LaTeX templates below, if used)


class UniformMotion:
    id = "physics.kinematics.uniform"
    family = "physics"
    difficulties = ("easy", "medium", "hard")
    label_key = "topic.uniform"
    scenarios = ("uniform_one_object", "uniform_unit_conversion", "uniform_graph_reading", "uniform_sound_distance")

    # ---------------------------------------------------------------- generate
    def generate(self, rng: random.Random, difficulty: str, seed: int, index: int,
                 options: dict | None = None) -> Item:
        if difficulty == "easy":
            # everyday scale: v 1-25 m/s, t 1-60 s
            v = Fraction(rng.randint(2, 20))
            t = Fraction(rng.randint(2, 30))
            s = v * t
            params = {"v": v, "t": t, "s": s}
            steps = (
                Step("step.formula", "s = v \\cdot t"),
                Step("step.substitute", f"s = {fmt(v)}\\,\\text{{m/s}} \\cdot {fmt(t)}\\,\\text{{s}}"),
                Step("step.result", f"s = {fmt(s)}\\,\\text{{m}}"),
            )
            answer = Answer(f"{fmt(s)}\\,\\text{{m}}", "scalar_with_unit", {"value": [fmt(s)], "unit": ["m"]})
            markers = [(t, s, "marker.asked_instant")]
        elif difficulty == "medium":
            # km/h -> m/s conversion, exact (5/18)
            v_kmh = Fraction(rng.choice([36, 54, 72, 90, 108]))
            t = Fraction(rng.choice([4, 5, 8, 10, 12, 15]))
            v = convert(v_kmh, "km/h", "m/s")
            s = v * t
            params = {"v_kmh": v_kmh, "v": v, "t": t, "s": s}
            steps = (
                Step("step.convert", f"{fmt(v_kmh)}\\,\\text{{km/h}} = {fmt(v)}\\,\\text{{m/s}}"),
                Step("step.formula", "s = v \\cdot t"),
                Step("step.result", f"s = {fmt(s)}\\,\\text{{m}}"),
            )
            answer = Answer(f"{fmt(s)}\\,\\text{{m}}", "scalar_with_unit", {"value": [fmt(s)], "unit": ["m"]})
            markers = [(t, s, "marker.asked_instant")]
        else:
            # read the speed off the graph: two marked points on s(t)
            v = Fraction(rng.randint(3, 18))
            t1 = Fraction(rng.randint(1, 4))
            t2 = t1 + Fraction(rng.randint(2, 6))
            s1, s2 = v * t1, v * t2
            params = {"v": v, "t1": t1, "t2": t2, "s1": s1, "s2": s2}
            steps = (
                Step("step.read_points", f"P_1({fmt(t1)}; {fmt(s1)})\\quad P_2({fmt(t2)}; {fmt(s2)})"),
                Step("step.slope", f"v = \\frac{{\\Delta s}}{{\\Delta t}} = \\frac{{{fmt(s2 - s1)}}}{{{fmt(t2 - t1)}}}"),
                Step("step.result", f"v = {fmt(v)}\\,\\text{{m/s}}"),
            )
            answer = Answer(f"{fmt(v)}\\,\\text{{m/s}}", "scalar_with_unit", {"value": [fmt(v)], "unit": ["m/s"]})
            markers = [(t1, s1, "marker.point_1"), (t2, s2, "marker.point_2")]

        t_max = (markers[-1][0] if difficulty == "hard" else params["t"])
        t_max = Fraction(t_max) * Fraction(6, 5) if difficulty == "hard" else Fraction(t_max)
        figure = cartesian_trace(
            x_unit="s",
            y_unit="m",
            t_max=t_max,
            samples=linear_samples(params["v"], t_max),
            trace_label="trace.position",
            phase_label="phase.uniform",
            markers=markers,
        )
        return Item(
            topic=self.id,
            difficulty=difficulty,
            seed=seed,
            index=index,
            params=params,
            statement_key=f"stmt.uniform_{difficulty}",
            steps=steps,
            answer=answer,
            figure=figure,
        )

    # ------------------------------------------------------------------ verify
    def verify(self, item: Item) -> VerificationResult:
        if not no_floats(*item.params.values()):
            return VerificationResult(False, "float_atom")
        if item.figure is None:
            return VerificationResult(False, "missing_figure")
        if not item.figure.get("traces"):
            return VerificationResult(False, "empty_figure")

        v = Fraction(item.params["v"])
        claimed = Fraction(item.answer.payload["value"][0])
        difficulty = item.difficulty

        if difficulty == "easy":
            expected = v * Fraction(item.params["t"])
        elif difficulty == "medium":
            expected = v * Fraction(item.params["t"])
            if Fraction(item.params["v_kmh"]) * Fraction(5, 18) != v:
                return VerificationResult(False, "conversion_mismatch")
        else:
            # the answer is the slope of the two marked points
            ds = Fraction(item.params["s2"]) - Fraction(item.params["s1"])
            dt = Fraction(item.params["t2"]) - Fraction(item.params["t1"])
            if dt == 0:
                return VerificationResult(False, "degenerate_interval")
            expected = ds / dt
            if Fraction(item.params["s1"]) != v * Fraction(item.params["t1"]):
                return VerificationResult(False, "point_not_on_the_line")

        if claimed != expected:
            return VerificationResult(False, "answer_mismatch")
        if expected < 0:
            return VerificationResult(False, "negative_magnitude")
        # the plotted trace must actually agree with the model at every sample
        for x, y in item.figure["traces"][0]["samples"]:
            if Fraction(y) != v * Fraction(x):
                return VerificationResult(False, "figure_disagrees_with_model")
        return VerificationResult(True)


TOPIC = UniformMotion()
