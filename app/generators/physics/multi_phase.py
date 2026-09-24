"""Multi-phase motion — a forward state timeline whose dependent quantities are derived.

The parameterisation follows the research artifact (physics-kinematics-generation-units
§1 Q2): the phases are drawn in physical order and anything that must satisfy a
constraint is *derived*, never drawn independently. The accelerated phase takes its
final speed from ``[v₁/2, 3v₁]`` intersected with the DESIGN §2.10 magnitude row and
derives ``a = Δv/t``; because every phase starts from the previous phase's exit state,
position continuity (``x(t₁)`` from both branches) and velocity continuity
(``v_out = next v_in``) hold by construction. Drawing ``v₁, a, t`` independently instead
leaves ~33% of items with ``v₂ ≤ 0`` on the same distribution.

The figure is the **position** timeline: one ``phases[]`` entry per phase with the exact
boundary vertices (both branches kept, so the payload shows continuity at the boundary)
and a single trace under a single ``y_unit``. Velocity is not a second trace — one figure
carries one measured quantity — it is asserted symbolically instead (``x`` and ``v``
continuous at every boundary), where it is exact rather than eyeballed.
"""

from __future__ import annotations

import random
from fractions import Fraction

from sympy import Rational as SymRational
from sympy import Symbol, simplify

from app.core.units import fmt
from app.core.verify import VerificationResult, no_floats, real_solutions, satisfies
from app.generators.base import Answer, Item, Step
from app.render.figure import cartesian_trace, quadratic_samples

# DESIGN §2.10, "Everyday motion" row: v 1-25 m/s, a 0.5-4 m/s², t 1-60 s.
SPEED_RANGE = (Fraction(1), Fraction(25))
ACCELERATION_RANGE = (Fraction(1, 2), Fraction(4))
DURATION_RANGE = (Fraction(1), Fraction(60))
MAX_TOTAL_DURATION = Fraction(60)

# Accelerations are never drawn: a = Δv/t with |Δv| ≤ 4 (the speed window below) and
# t ≥ 1 gives |a| ≤ 4, while the filter t ≤ 2|Δv| gives |a| ≥ 1/2. t = 1 s always
# satisfies both, so the filtered tuple is never empty.
_PHASE_DURATIONS = tuple(Fraction(value) for value in (1, 2, 3, 4, 5, 6, 8))
_FIRST_DURATIONS = tuple(Fraction(value) for value in (1, 2, 3, 4, 5, 6, 8, 10, 12, 15, 20, 30))

T = Symbol("t")


def _half_grid(low: Fraction, high: Fraction, exclude: Fraction, above: bool) -> tuple[Fraction, ...]:
    """Exact half-integer speeds in [low, high], deterministic order, one value dropped."""
    first = int(-(-(2 * low) // 1))
    last = int((2 * high) // 1)
    return tuple(
        Fraction(k, 2)
        for k in range(first, last + 1)
        if Fraction(k, 2) != exclude and not (above and Fraction(k, 2) <= exclude)
    )


def _draw_next_speed(rng: random.Random, previous: Fraction, *, above: bool) -> Fraction:
    """The speed entering the next accelerated phase, drawn inside the admissible window.

    ``[previous/2, 3·previous]`` is the research artifact's bound (it is what makes the
    phase strictly forward-moving); the intersection with ``previous ± 4`` keeps the
    derived ``|a| = |Δv|/t`` inside the magnitude row, and with the row itself.
    """
    low = max(previous / 2, SPEED_RANGE[0], previous - 4)
    high = min(3 * previous, SPEED_RANGE[1], previous + 4)
    # the window always contains half-integer speeds (previous ∈ [1, 25] is the only
    # input), so an empty grid is a programming error, not a draw to recover from
    return rng.choice(_half_grid(low, high, previous, above))


def _draw_phase_duration(rng: random.Random, speed_change: Fraction) -> Fraction:
    delta = abs(speed_change)
    allowed = tuple(d for d in _PHASE_DURATIONS if delta / 4 <= d <= 2 * delta)
    return rng.choice(allowed or (Fraction(1),))


def _phases_from_params(difficulty: str, params: dict[str, Fraction]) -> list[tuple]:
    """``(t_from, t_to, v_in, a, s_from, phase_label)`` per phase — the single source.

    Both the emitted steps/figure and the verifier read the timeline from here, so a
    disagreement between the two is a bug in one projection, not a matter of opinion.
    """
    v1, t1 = Fraction(params["v1"]), Fraction(params["t1"])
    t2, a2, v2 = Fraction(params["t2"]), Fraction(params["a2"]), Fraction(params["v2"])
    phases = [
        (Fraction(0), t1, v1, Fraction(0), Fraction(0), "phase.uniform"),
        (t1, t1 + t2, v1, a2, v1 * t1, "phase.accelerated"),
    ]
    if difficulty == "medium":
        t3, a3 = Fraction(params["t3"]), Fraction(params["a3"])
        phases.append((t1 + t2, t1 + t2 + t3, v2, a3, phases[1][4] + v1 * t2 + a2 * t2 * t2 / 2,
                       "phase.accelerated"))
    return phases


def _exit(phase: tuple) -> tuple[Fraction, Fraction, Fraction]:
    """``(t_to, v_out, s_to)`` for one phase."""
    t_from, t_to, v_in, a, s_from, _ = phase
    span = t_to - t_from
    return t_to, v_in + a * span, s_from + v_in * span + a * span * span / 2


def _model_position(phases: list[tuple], at: Fraction) -> Fraction | None:
    for t_from, t_to, v_in, a, s_from, _ in phases:
        if t_from <= at <= t_to:
            span = at - t_from
            return s_from + v_in * span + a * span * span / 2
    return None


def _timeline(phases: list[tuple], markers: list[tuple[Fraction, Fraction, str]]) -> dict:
    """The position timeline — one measured quantity, one y-unit (STRUCTURE §4.3).

    The velocity story is *not* a second trace: a figure carries a single ``y_unit``, so a
    ``v(t)`` trace in m/s under a ``[m]`` axis would be a lie. Velocity continuity is
    asserted symbolically in ``verify`` instead (``v_out`` of one phase is ``v_in`` of the
    next), where it is exact rather than eyeballed.
    """
    t_max = phases[-1][1]
    position: list[tuple[Fraction, Fraction]] = []
    entries = []
    for t_from, t_to, v_in, a, s_from, label in phases:
        span = t_to - t_from
        # both branches keep their endpoint at a shared boundary, so the payload itself
        # carries the continuity evidence (two samples at one instant, equal values)
        position.extend(
            (x + t_from, y) for x, y in quadratic_samples(v_in, a, span, x0=s_from, steps=4)
        )
        entries.append({"label_key": label, "t_from": fmt(t_from), "t_to": fmt(t_to),
                        "style": "solid"})
    figure = cartesian_trace(
        x_unit="s",
        y_unit="m",
        t_max=t_max,
        samples=position,
        trace_label="trace.position",
        phase_label=phases[0][5],
        markers=markers,
    )
    figure["phases"] = entries
    return figure


class MultiPhaseMotion:
    id = "physics.kinematics.multi_phase"
    family = "physics"
    difficulties = ("easy", "medium", "hard")
    label_key = "topic.multi_phase"
    scenarios = ("two_phases", "three_phases", "unknown_duration")

    # ---------------------------------------------------------------- generate
    def generate(self, rng: random.Random, difficulty: str, seed: int, index: int) -> Item:
        v1 = Fraction(rng.randint(2, 21))
        t1 = Fraction(rng.choice(_FIRST_DURATIONS))
        params: dict[str, Fraction] = {"v1": v1, "t1": t1}

        # hard draws the final speed above the entry speed, which makes the quadratic in
        # t₂ have exactly one positive root; the other scenarios may accelerate or brake
        v2 = _draw_next_speed(rng, v1, above=difficulty == "hard")
        t2 = _draw_phase_duration(rng, v2 - v1)
        params.update({"v2": v2, "t2": t2, "a2": (v2 - v1) / t2})
        if difficulty == "medium":
            v3 = _draw_next_speed(rng, v2, above=False)
            t3 = _draw_phase_duration(rng, v3 - v2)
            params.update({"v3": v3, "t3": t3, "a3": (v3 - v2) / t3})

        phases = _phases_from_params(difficulty, params)
        t_total, _, s_total = _exit(phases[-1])
        s1 = v1 * t1
        s2 = _exit(phases[1])[2] - s1
        params["s1"] = s1
        params["s2"] = s2
        if difficulty == "medium":
            params["s3"] = _exit(phases[2])[2] - _exit(phases[1])[2]
        params["s_total"] = s_total
        params["t_total"] = t_total

        if difficulty == "easy":
            steps = (
                Step("step.formula", "s = s_1 + s_2"),
                Step("step.phase_1", f"s_1 = v_1 t_1 = {fmt(v1)} \\cdot {fmt(t1)} = {fmt(s1)}\\,\\text{{m}}"),
                Step("step.phase_2",
                     f"v_2 = v_1 + a_2 t_2 = {fmt(v2)}\\,\\text{{m/s}};\\quad "
                     f"s_2 = v_1 t_2 + \\frac{{a_2 t_2^2}}{{2}} = {fmt(v1)} \\cdot {fmt(params['t2'])} + "
                     f"\\frac{{{fmt(params['a2'])} \\cdot {fmt(params['t2'])}^2}}{{2}} = {fmt(s2)}\\,\\text{{m}}"),
                Step("step.total", f"s = {fmt(s_total)}\\,\\text{{m}}"),
            )
            answer = Answer(f"{fmt(s_total)}\\,\\text{{m}}", "scalar_with_unit",
                            {"value": [fmt(s_total)], "unit": ["m"]})
            markers = [(t_total, s_total, "marker.asked_instant")]
        elif difficulty == "medium":
            steps = (
                Step("step.formula", "s = s_1 + s_2 + s_3"),
                Step("step.phase_1", f"s_1 = v_1 t_1 = {fmt(s1)}\\,\\text{{m}}"),
                Step("step.phase_2", f"s_2 = v_1 t_2 + \\frac{{a_2 t_2^2}}{{2}} = {fmt(s2)}\\,\\text{{m}}"),
                Step("step.phase_3",
                     f"v_2 = v_1 + a_2 t_2 = {fmt(v2)}\\,\\text{{m/s}};\\quad "
                     f"s_3 = v_2 t_3 + \\frac{{a_3 t_3^2}}{{2}} = {fmt(params['s3'])}\\,\\text{{m}}"),
                Step("step.total", f"s = {fmt(s_total)}\\,\\text{{m}}"),
            )
            answer = Answer(f"{fmt(s_total)}\\,\\text{{m}}", "scalar_with_unit",
                            {"value": [fmt(s_total)], "unit": ["m"]})
            markers = [(t_total, s_total, "marker.asked_instant")]
        else:
            steps = (
                Step("step.formula",
                     "s = v_1 t_1 + v_1 t_2 + \\frac{a_2 t_2^2}{2}"),
                Step("step.substitute",
                     f"{fmt(s_total)} = {fmt(v1)} \\cdot {fmt(t1)} + {fmt(v1)} t_2 + "
                     f"\\frac{{{fmt(params['a2'])} t_2^2}}{{2}}"),
                Step("step.solve_time", "Risolvo l'equazione di secondo grado in t_2"),
                Step("step.result", f"t_2 = {fmt(params['t2'])}\\,\\text{{s}}"),
            )
            answer = Answer(f"{fmt(params['t2'])}\\,\\text{{s}}", "scalar_with_unit",
                            {"value": [fmt(params["t2"])], "unit": ["s"]})
            markers = [(t1, s1, "marker.phase_boundary")]

        return Item(
            topic=self.id,
            difficulty=difficulty,
            seed=seed,
            index=index,
            params=params,
            statement_key=f"stmt.multi_phase_{difficulty}",
            steps=steps,
            answer=answer,
            figure=_timeline(phases, markers),
        )

    # ------------------------------------------------------------------ verify
    def verify(self, item: Item) -> VerificationResult:
        if not no_floats(*item.params.values()):
            return VerificationResult(False, "float_atom")
        figure = item.figure
        if not isinstance(figure, dict) or figure.get("kind") != "kinematics":
            return VerificationResult(False, "missing_figure")
        phases = _phases_from_params(item.difficulty, item.params)
        if len(phases) != (3 if item.difficulty == "medium" else 2):
            return VerificationResult(False, "scenario_mismatch")

        # 1. every phase is admissible on its own: positive, monotone, inside the row
        for position, phase in enumerate(phases):
            t_from, t_to, v_in, a, _, _ = phase
            span = t_to - t_from
            if span <= 0:
                return VerificationResult(False, "non_positive_duration")
            if not DURATION_RANGE[0] <= span <= DURATION_RANGE[1]:
                return VerificationResult(False, "duration_out_of_scale")
            if position and a == 0:
                return VerificationResult(False, "degenerate_accelerated_phase")
            if a != 0 and not ACCELERATION_RANGE[0] <= abs(a) <= ACCELERATION_RANGE[1]:
                return VerificationResult(False, "acceleration_out_of_scale")
            v_out = v_in + a * span
            # monotone position: the minimum speed over a constant-acceleration phase
            # sits at an endpoint, so both endpoints positive is the whole check
            if min(v_in, v_out) <= 0:
                return VerificationResult(False, "non_monotone_position")
            if not all(SPEED_RANGE[0] <= v <= SPEED_RANGE[1] for v in (v_in, v_out)):
                return VerificationResult(False, "speed_out_of_scale")

        t_total, s_total = _exit(phases[-1])[0], _exit(phases[-1])[2]
        if t_total > MAX_TOTAL_DURATION:
            return VerificationResult(False, "duration_out_of_scale")
        if Fraction(item.params["t_total"]) != t_total:
            return VerificationResult(False, "parameter_inconsistent")
        if Fraction(item.params["s_total"]) != s_total:
            return VerificationResult(False, "parameter_inconsistent")
        if Fraction(item.params["s1"]) != _exit(phases[0])[2]:
            return VerificationResult(False, "parameter_inconsistent")
        if Fraction(item.params["s2"]) != _exit(phases[1])[2] - _exit(phases[0])[2]:
            return VerificationResult(False, "parameter_inconsistent")
        if item.difficulty == "medium" and Fraction(item.params["s3"]) != (
            _exit(phases[2])[2] - _exit(phases[1])[2]
        ):
            return VerificationResult(False, "parameter_inconsistent")

        # 2. boundaries: continuity asserted on the laws, and visible in the payload
        for step in range(1, len(phases)):
            previous = _exit(phases[step - 1])
            # position continuity: x_branch2(t₁) − x_branch1(t₁) == 0
            if previous[2] != phases[step][4]:
                return VerificationResult(False, "position_discontinuity")
            # velocity continuity: v_out of one phase is v_in of the next
            if previous[1] != phases[step][2]:
                return VerificationResult(False, "velocity_discontinuity")

        declared = figure.get("phases") or []
        if len(declared) != len(phases):
            return VerificationResult(False, "phase_count_mismatch")
        for entry, phase in zip(declared, phases, strict=True):
            if Fraction(entry["t_from"]) != phase[0] or Fraction(entry["t_to"]) != phase[1]:
                return VerificationResult(False, "phase_boundary_mismatch")
        traces = figure.get("traces") or []
        # one measured quantity per figure: the timeline is a position graph, so a second
        # trace would need its own y-unit (and this schema has exactly one)
        if len(traces) != 1:
            return VerificationResult(False, "unexpected_extra_trace")
        for x, y in traces[0]["samples"]:
            model = _model_position(phases, Fraction(x))
            if model is None or Fraction(y) != model:
                return VerificationResult(False, "figure_disagrees_with_model")
        for boundary in (phase[1] for phase in phases[:-1]):
            at_boundary = [Fraction(y) for x, y in traces[0]["samples"] if Fraction(x) == boundary]
            # position continuity, read off the payload: both branches are vertices at
            # the boundary instant and they must agree there
            if len(at_boundary) != 2 or at_boundary[0] != at_boundary[1]:
                return VerificationResult(False, "position_discontinuity")

        # 3. the ask, recomputed through a second path
        if item.difficulty == "hard":
            v1, t1 = Fraction(item.params["v1"]), Fraction(item.params["t1"])
            a2, t2 = Fraction(item.params["a2"]), Fraction(item.params["t2"])
            if a2 <= 0:
                return VerificationResult(False, "unknown_duration_needs_acceleration")
            equation = a2 * T**2 / 2 + v1 * T - (s_total - v1 * t1)
            roots = real_solutions(equation, T)
            if roots is None:
                return VerificationResult(False, "undecidable")
            positive = [root for root in roots if root > 0]
            if len(positive) != 1:
                return VerificationResult(False, "ambiguous_admissible_time")
            if simplify(positive[0]) != SymRational(t2.numerator, t2.denominator):
                return VerificationResult(False, "time_mismatch")
            if not satisfies(equation, T, SymRational(t2.numerator, t2.denominator)):
                return VerificationResult(False, "root_does_not_satisfy")
            expected, unit = t2, "s"
        else:
            expected, unit = s_total, "m"

        claimed = item.answer.payload.get("value")
        if not claimed:
            return VerificationResult(False, "no_answer_claimed")
        if Fraction(claimed[0]) != expected:
            return VerificationResult(False, "answer_mismatch")
        if item.answer.latex != f"{fmt(expected)}\\,\\text{{{unit}}}":
            return VerificationResult(False, "answer_latex_mismatch")
        return VerificationResult(True)


TOPIC = MultiPhaseMotion()
