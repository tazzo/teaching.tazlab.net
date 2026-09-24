"""Uniform circular motion — v = 2πr/T, ω = 2π/T, a_c = v²/r.

Reverse construction (DESIGN §2.5): ``r`` and one rate (``T``, an rpm reading, or an
acceleration) are drawn, and every asked quantity is a projection of that same tuple,
so the steps and the answer cannot disagree.

π is never evaluated. Every quantity here is an exact rational times a power of π, and
the payload carries the two separately — ``{"value": ["2/3"], "pi": ["1"]}`` is
``2π/3`` — so the wire stays rational strings (STRUCTURE §4.2) and ``no_floats`` holds.

Figure. The figure schema is time-domain (STRUCTURE §4.3) and the browser reads samples
with ``Number()``, which cannot parse π: a trace through quadrant vertices would be a
diamond, and a densely sampled circle would be a float. The one projection of this
tuple that stays exact is the revolution count ``n(t) = t/T``, marked at the full turn.
The hard item carries **no figure at all**: its answer is the period, and any
revolutions-vs-time plot of the solved state would print the answer on its own axis.
"""

from __future__ import annotations

import random
from fractions import Fraction

from sympy import Rational as SymRational
from sympy import pi, sqrt

from app.core.latex import to_latex
from app.core.units import unit_latex, fmt
from app.core.verify import VerificationResult, no_floats
from app.generators.base import Answer, Item, Step
from app.render.figure import cartesian_trace, linear_samples

# DESIGN §2.10, "Circular motion" row: radius 0.1-50 m, period 0.5-60 s, ω from those.
RADIUS_RANGE = (Fraction(1, 10), Fraction(50))
PERIOD_RANGE = (Fraction(1, 2), Fraction(60))
# ω = 2π/T with T in the row gives ω/π ∈ [1/30, 4]; the hard draw stays in [1, 4),
# which implies T ∈ (π/2, 2π] ⊆ [1/2, 60] without ever evaluating π.
OMEGA_RANGE = (Fraction(1), Fraction(4))

_RADII = tuple(Fraction(value) for value in (1, 3, 2, 5, 4, 6, 8, 10, 12, 15, 20, 25, 30, 40, 50))
_PERIODS = tuple(
    Fraction(numerator, denominator)
    for numerator, denominator in ((1, 2), (3, 4), (1, 1), (3, 2), (2, 1), (5, 2), (3, 1),
                                   (4, 1), (5, 1), (6, 1), (8, 1), (10, 1), (12, 1), (15, 1),
                                   (20, 1), (30, 1), (45, 1), (60, 1))
)
# rev/min readings whose period 60/n stays inside the row: n ∈ [6, 120] ⇒ T ∈ [1/2, 10] s
_RATES_PER_MINUTE = (6, 10, 12, 15, 20, 24, 30, 36, 40, 45, 48, 60, 72, 90, 120)
_OMEGAS = tuple(Fraction(numerator, 2) for numerator in (2, 3, 4, 5, 6, 7))




def _sym(value: Fraction) -> SymRational:
    return SymRational(value.numerator, value.denominator)


def pi_times(coefficient: Fraction, power: int = 1) -> str:
    """LaTeX for ``coefficient · π^power`` — π stays symbolic, never a float."""
    return to_latex(pi ** power * _sym(coefficient))


def _value_latex(coefficient: Fraction, power: int, unit: str) -> str:
    return f"{pi_times(coefficient, power)}\\,{unit_latex(unit)}"


def _result_latex(symbol: str, coefficient: Fraction, power: int, unit: str) -> str:
    return f"{symbol} = {_value_latex(coefficient, power, unit)}"


def _answer_ok(
    item: Item, coefficient: Fraction, power: int, unit: str
) -> VerificationResult:
    claimed = item.answer.payload.get("value")
    reported = item.answer.payload.get("pi")
    if not claimed or not reported:
        return VerificationResult(False, "no_answer_claimed")
    if Fraction(claimed[0]) != coefficient or int(reported[0]) != power:
        return VerificationResult(False, "answer_mismatch")
    if item.answer.latex != _value_latex(coefficient, power, unit):
        return VerificationResult(False, "answer_latex_mismatch")
    return VerificationResult(True)


def _figure_ok(figure: dict | None, revolutions_per_second: Fraction, turn_time: Fraction) -> bool:
    """The revolutions trace must be the model, with the full turn marked exactly."""
    if not isinstance(figure, dict) or figure.get("kind") != "kinematics":
        return False
    if figure.get("x_unit") != "s" or figure.get("y_unit") != "rev":
        return False
    domain = figure.get("domain") or {}
    if domain.get("t_min") != "0" or Fraction(domain.get("t_max", "0")) != 2 * turn_time:
        return False
    traces = figure.get("traces") or []
    if len(traces) != 1 or len(traces[0].get("samples") or []) < 2:
        return False
    for x, y in traces[0]["samples"]:
        if Fraction(y) != revolutions_per_second * Fraction(x):
            return False
    markers = figure.get("markers") or []
    if len(markers) != 1:
        return False
    if Fraction(markers[0]["at"][0]) != turn_time or Fraction(markers[0]["at"][1]) != 1:
        return False
    phases = figure.get("phases") or []
    return len(phases) == 1 and Fraction(phases[0]["t_to"]) == 2 * turn_time


class CircularMotion:
    id = "physics.kinematics.circular"
    family = "physics"
    difficulties = ("easy", "medium", "hard")
    label_key = "topic.circular"
    scenarios = ("circular_speed", "circular_acceleration", "circular_angular")

    # ---------------------------------------------------------------- generate
    def generate(self, rng: random.Random, difficulty: str, seed: int, index: int,
                 options: dict | None = None) -> Item:
        radius = Fraction(rng.choice(_RADII))

        if difficulty == "easy":
            # given r and T, find v = 2πr/T
            period = Fraction(rng.choice(_PERIODS))
            speed_over_pi = 2 * radius / period
            params = {"r": radius, "T": period, "v_over_pi": speed_over_pi}
            steps = (
                Step("step.formula", "v = \\frac{2\\pi r}{T}"),
                Step("step.substitute",
                     f"v = \\frac{{2\\pi \\cdot {to_latex(_sym(radius))}}}{{{to_latex(_sym(period))}}}"),
                Step("step.result", _result_latex("v", speed_over_pi, 1, "m/s")),
            )
            answer = Answer(
                _value_latex(speed_over_pi, 1, "m/s"),
                "scalar_with_unit",
                {"value": [fmt(speed_over_pi)], "pi": ["1"], "unit": ["m/s"]},
            )
        elif difficulty == "medium":
            # a wheel turning at n rev/min: rpm → rad/s first, then a_c = ω² r
            rpm = Fraction(rng.choice(_RATES_PER_MINUTE))
            period = Fraction(60, 1) / rpm
            omega_over_pi = rpm / 30
            accel_over_pi2 = omega_over_pi * omega_over_pi * radius
            params = {
                "r": radius,
                "n_rpm": rpm,
                "T": period,
                "omega_over_pi": omega_over_pi,
                "a_over_pi2": accel_over_pi2,
            }
            steps = (
                Step("step.convert",
                     f"{fmt(rpm)}\\,\\text{{rpm}} = {pi_times(omega_over_pi)}\\,\\text{{rad/s}}"),
                Step("step.formula", "a_c = \\omega^2 r"),
                Step("step.substitute",
                     f"a_c = \\left({pi_times(omega_over_pi)}\\right)^2 \\cdot "
                     f"{to_latex(_sym(radius))}"),
                Step("step.result", _result_latex("a_c", accel_over_pi2, 2, "m/s^2")),
            )
            answer = Answer(
                _value_latex(accel_over_pi2, 2, "m/s^2"),
                "scalar_with_unit",
                {"value": [fmt(accel_over_pi2)], "pi": ["2"], "unit": ["m/s^2"]},
            )
        else:
            # given a_c and r, combine: ω = √(a_c/r) exactly, then T = 2π/ω
            omega = Fraction(rng.choice(_OMEGAS))
            accel = omega * omega * radius
            period_over_pi = 2 / omega
            params = {"r": radius, "a_c": accel, "omega": omega, "T_over_pi": period_over_pi}
            steps = (
                Step("step.formula",
                     "a_c = \\omega^2 r \\;\\Rightarrow\\; \\omega = \\sqrt{\\frac{a_c}{r}}"),
                Step("step.solve_omega",
                     f"\\omega = \\sqrt{{\\frac{{{to_latex(_sym(accel))}}}"
                     f"{{{to_latex(_sym(radius))}}}}} = {to_latex(_sym(omega))}\\,\\text{{rad/s}}"),
                Step("step.period", "T = \\frac{2\\pi}{\\omega}"),
                Step("step.result", _result_latex("T", period_over_pi, 1, "s")),
            )
            answer = Answer(
                _value_latex(period_over_pi, 1, "s"),
                "scalar_with_unit",
                {"value": [fmt(period_over_pi)], "pi": ["1"], "unit": ["s"]},
            )

        figure = None
        if difficulty != "hard":
            period = Fraction(params["T"])
            figure = cartesian_trace(
                x_unit="s",
                y_unit="rev",
                t_max=2 * period,
                samples=linear_samples(Fraction(1) / period, 2 * period),
                trace_label="trace.revolutions",
                phase_label="phase.circular",
                markers=[(period, Fraction(1), "marker.full_turn")],
            )

        return Item(
            topic=self.id,
            difficulty=difficulty,
            seed=seed,
            index=index,
            params=params,
            statement_key=f"stmt.circular_{difficulty}",
            steps=steps,
            answer=answer,
            figure=figure,
        )

    # ------------------------------------------------------------------ verify
    def verify(self, item: Item) -> VerificationResult:
        if not no_floats(*item.params.values()):
            return VerificationResult(False, "float_atom")

        radius = Fraction(item.params["r"])
        if radius <= 0:
            return VerificationResult(False, "non_positive_radius")
        if not RADIUS_RANGE[0] <= radius <= RADIUS_RANGE[1]:
            return VerificationResult(False, "radius_out_of_scale")

        if item.difficulty == "easy":
            period = Fraction(item.params["T"])
            if not PERIOD_RANGE[0] <= period <= PERIOD_RANGE[1]:
                return VerificationResult(False, "period_out_of_scale")
            expected, power, unit = 2 * radius / period, 1, "m/s"
            if Fraction(item.params["v_over_pi"]) != expected:
                return VerificationResult(False, "parameter_inconsistent")
            if item.figure is None:
                return VerificationResult(False, "missing_figure")
            if not _figure_ok(item.figure, Fraction(1) / period, period):
                return VerificationResult(False, "figure_disagrees_with_model")

        elif item.difficulty == "medium":
            rpm = Fraction(item.params["n_rpm"])
            if rpm <= 0:
                return VerificationResult(False, "non_positive_rate")
            omega_over_pi = rpm / 30
            period = Fraction(60, 1) / rpm
            if not PERIOD_RANGE[0] <= period <= PERIOD_RANGE[1]:
                return VerificationResult(False, "period_out_of_scale")
            # the rpm → rad/s conversion and the period are recomputed, never trusted
            if Fraction(item.params["omega_over_pi"]) != omega_over_pi:
                return VerificationResult(False, "conversion_mismatch")
            if Fraction(item.params["T"]) != period:
                return VerificationResult(False, "period_mismatch")
            expected, power, unit = omega_over_pi * omega_over_pi * radius, 2, "m/s^2"
            if Fraction(item.params["a_over_pi2"]) != expected:
                return VerificationResult(False, "parameter_inconsistent")
            if item.figure is None:
                return VerificationResult(False, "missing_figure")
            if not _figure_ok(item.figure, Fraction(1) / period, period):
                return VerificationResult(False, "figure_disagrees_with_model")

        else:
            accel = Fraction(item.params["a_c"])
            if accel <= 0:
                return VerificationResult(False, "non_positive_acceleration")
            ratio = accel / radius
            root = sqrt(_sym(ratio))
            if not root.is_Rational or root <= 0:
                return VerificationResult(False, "no_exact_angular_speed")
            omega = Fraction(root.p, root.q)
            if omega * omega * radius != accel:
                return VerificationResult(False, "acceleration_mismatch")
            if not OMEGA_RANGE[0] <= omega < OMEGA_RANGE[1]:
                return VerificationResult(False, "angular_speed_out_of_scale")
            if Fraction(item.params["omega"]) != omega:
                return VerificationResult(False, "parameter_inconsistent")
            expected, power, unit = 2 / omega, 1, "s"
            if Fraction(item.params["T_over_pi"]) != expected:
                return VerificationResult(False, "parameter_inconsistent")
            # 2π/ω must sit in the period row, decided symbolically — never by a float
            period = 2 * pi / _sym(omega)
            if not (period >= PERIOD_RANGE[0] and period <= PERIOD_RANGE[1]):
                return VerificationResult(False, "period_out_of_scale")
            if item.figure is not None:
                # every figure this schema can carry is time-domain, and a periodic
                # trace prints the period on its own axis — see the module docstring
                return VerificationResult(False, "answer_leaked_into_figure")

        return _answer_ok(item, expected, power, unit)


TOPIC = CircularMotion()
