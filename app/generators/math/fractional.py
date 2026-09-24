"""Fractional (rational) equations — reverse construction (DESIGN §2.10).

Easy: one fraction with an integer solution. Medium: cross-multiplication with a rational
solution. Hard: three terms over a common denominator *built so that the cleared equation
has an excluded value among its roots* — so the extraneous-root check is load-bearing, not
decorative. The verifier rejects any claimed solution that is an excluded value, and any
item whose ``solveset`` disagrees with the constructed answer.

Display convention: the statement template fixes every operator, so the parameters carry
magnitudes only and ``(statement_key, params)`` reconstructs the canonical equation.
"""

from __future__ import annotations

import random
from fractions import Fraction

from sympy import Float, Integer, Rational, Symbol, sympify

from app.core.latex import to_latex
from app.core.verify import VerificationResult, no_floats, real_solutions, satisfies
from app.generators.base import Answer, Item, Step

X = Symbol("x")

_EASY = "stmt.fractional_easy"
_MEDIUM = "stmt.fractional_medium"
_HARD = "stmt.fractional_hard"


def _q(value: Fraction) -> Integer | Rational:
    return Integer(value.numerator) if value.denominator == 1 else Rational(value.numerator, value.denominator)


def _parse_exact(text: str):
    try:
        value = sympify(text, rational=True)
    except Exception:
        return None
    if getattr(value, "atoms", None) is not None and value.atoms(Float):
        return None
    return value


def _equation(statement_key: str, params: dict[str, Fraction]) -> tuple[object, set[Fraction]] | None:
    """Canonical ``lhs - rhs`` expression plus the excluded values the statement shows."""
    if statement_key == _EASY:
        p, e, c = params.get("p"), params.get("e"), params.get("c")
        if p is None or e is None or c is None or min(p, e, c) <= 0 or c == 1:
            return None
        return (X - _q(p)) / (X - _q(e)) - _q(c), {e}
    if statement_key == _MEDIUM:
        values = [params.get(name) for name in ("a", "b", "c", "d", "e")]
        if any(value is None for value in values):
            return None
        a, b, c, d, e = values
        if min(a, b, c, d, e) <= 0 or a * d == c:
            return None
        return (_q(a) * X - _q(b)) / (X - _q(e)) - _q(c) / _q(d), {e}
    if statement_key == _HARD:
        values = [params.get(name) for name in ("a", "b", "c", "e", "f")]
        if any(value is None for value in values):
            return None
        a, b, c, e, f = values
        if min(a, b, c, e, f) <= 0 or e == f:
            return None
        expr = (X - _q(a)) / (X - _q(e)) + _q(b) / ((X - _q(e)) * (X - _q(f))) - _q(c) / (X - _q(f))
        return expr, {e, f}
    return None


class FractionalEquation:
    id = "math.equations.fractional"
    family = "math"
    difficulties = ("easy", "medium", "hard")
    label_key = "topic.fractional"
    scenarios: tuple[str, ...] = ()

    # ---------------------------------------------------------------- generate
    def generate(self, rng: random.Random, difficulty: str, seed: int, index: int) -> Item:
        if difficulty == "easy":
            key, params, root = self._easy(rng)
        elif difficulty == "medium":
            key, params, root = self._medium(rng)
        else:
            key, params, root = self._hard(rng)
        return Item(
            topic=self.id,
            difficulty=difficulty,
            seed=seed,
            index=index,
            params=params,
            statement_key=key,
            steps=self._steps(key, params, root),
            answer=Answer(
                latex=f"{to_latex(X)} = {to_latex(root)}",
                kind="value",
                payload={"solutions": [str(root)]},
            ),
        )

    # ------------------------------------------------------------------ shapes
    def _easy(self, rng: random.Random) -> tuple[str, dict[str, Fraction], Rational]:
        options = [
            (c, e, x0)
            for c in (2, 3, 4)
            for e in range(1, 7)
            for x0 in range(-6, 12)
            if x0 != e and c * e - (c - 1) * x0 > 0
        ]
        rng.shuffle(options)
        c, e, x0 = options[0]
        p = c * e - (c - 1) * x0
        return _EASY, {"p": Fraction(p), "e": Fraction(e), "c": Fraction(c)}, Rational(x0)

    def _medium(self, rng: random.Random) -> tuple[str, dict[str, Fraction], Rational]:
        options = [
            (a, d, c, e, b)
            for a in range(2, 6)
            for d in range(2, 5)
            for c in range(1, 6)
            for e in range(1, 7)
            for b in range(1, 13)
        ]
        rng.shuffle(options)
        for a, d, c, e, b in options:
            if c in (a * d - 1, a * d, a * d + 1) or b == a * e:
                continue
            x0 = Rational(d * b - c * e, a * d - c)
            if x0.q == 1 or x0 == e or abs(x0) > 12:
                continue  # Medium must land on a genuine fraction, and never on the excluded value
            return _MEDIUM, {
                "a": Fraction(a),
                "b": Fraction(b),
                "c": Fraction(c),
                "d": Fraction(d),
                "e": Fraction(e),
            }, x0
        raise RuntimeError("medium fractional: no candidate")

    def _hard(self, rng: random.Random) -> tuple[str, dict[str, Fraction], Rational]:
        candidates = [
            (a, e, f, delta)
            for a in range(1, 7)
            for e in range(2, 9)
            for f in range(1, 9)
            for delta in (1, -1, 2, -2)
        ]
        rng.shuffle(candidates)
        for a, e, f, delta in candidates:
            if f == e:
                continue
            b = (a - e) * (e - f)
            c = delta + 2 * e - a - f
            x0 = e + delta
            if b <= 0 or c <= 0 or x0 == f:
                continue
            return _HARD, {
                "a": Fraction(a),
                "b": Fraction(b),
                "c": Fraction(c),
                "e": Fraction(e),
                "f": Fraction(f),
            }, Rational(x0)
        raise RuntimeError("hard fractional: no candidate")

    # ------------------------------------------------------------------- steps
    def _steps(self, key: str, params: dict[str, Fraction], root: Rational) -> tuple[Step, ...]:
        if key == _EASY:
            p, e, c = params["p"], params["e"], params["c"]
            return (
                Step("step.common_denominator", f"{to_latex(X - _q(p))} = {to_latex(_q(c))}\\,({to_latex(X - _q(e))})"),
                Step("step.solve", f"{to_latex(X)} = {to_latex(root)}"),
                Step("step.excluded_values", f"{to_latex(X)} \\ne {to_latex(_q(e))}"),
            )
        if key == _MEDIUM:
            a, b, c, d, e = (params[name] for name in ("a", "b", "c", "d", "e"))
            return (
                Step(
                    "step.common_denominator",
                    f"{to_latex(_q(d))}\\,({to_latex(_q(a) * X - _q(b))}) = {to_latex(_q(c))}\\,({to_latex(X - _q(e))})",
                ),
                Step("step.solve", f"{to_latex(X)} = {to_latex(root)}"),
                Step("step.excluded_values", f"{to_latex(X)} \\ne {to_latex(_q(e))}"),
            )
        a, b, c, e, f = (params[name] for name in ("a", "b", "c", "e", "f"))
        return (
            Step(
                "step.common_denominator",
                f"{to_latex((X - _q(a)) * (X - _q(f)) + _q(b))} = {to_latex(_q(c) * (X - _q(e)))}",
            ),
            Step(
                "step.factorise",
                f"{to_latex((X - _q(e)) * (X + _q(e) - _q(a) - _q(f)))} = {to_latex(_q(c) * (X - _q(e)))}",
            ),
            Step(
                "step.candidate_roots",
                f"{to_latex((X - _q(e)) * (X - root))} = 0",
            ),
            Step(
                "step.excluded_values",
                f"{to_latex(X)} \\ne {to_latex(_q(e))}, \\; {to_latex(X)} \\ne {to_latex(_q(f))}",
            ),
            Step("step.result", f"{to_latex(X)} = {to_latex(root)}"),
        )

    # ------------------------------------------------------------------ verify
    def verify(self, item: Item) -> VerificationResult:
        if not no_floats(*item.params.values()):
            return VerificationResult(False, "float_atom")
        rebuilt = _equation(item.statement_key, item.params)
        if rebuilt is None:
            return VerificationResult(False, "unknown_statement")
        expr, excluded = rebuilt
        claimed_raw = item.answer.payload.get("solutions")
        if not claimed_raw:
            return VerificationResult(False, "no_solution_claimed")
        claimed = [_parse_exact(text) for text in claimed_raw]
        if any(value is None for value in claimed):
            return VerificationResult(False, "unparsable_solution")
        if not no_floats(*claimed):
            return VerificationResult(False, "float_atom")

        for value in claimed:
            if value in excluded:
                return VerificationResult(False, "excluded_value")
            if not satisfies(expr, X, value):
                return VerificationResult(False, "root_does_not_satisfy")

        recomputed = real_solutions(expr, X)
        if recomputed is None:
            return VerificationResult(False, "undecidable")
        if sorted(recomputed) != sorted(claimed):
            return VerificationResult(False, "solution_set_mismatch")
        expected_latex = ", \\quad ".join(f"{to_latex(X)} = {to_latex(value)}" for value in claimed)
        if item.answer.latex != expected_latex:
            return VerificationResult(False, "answer_latex_mismatch")
        return VerificationResult(True)


TOPIC = FractionalEquation()
