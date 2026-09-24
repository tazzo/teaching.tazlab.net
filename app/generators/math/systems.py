"""Systems of equations — linear 2×2 and linear + quadratic (DESIGN §2.10).

Reverse construction: the solution tuple (or the two intersection points) is chosen first
and the equations are built *through* it, so substitution back into every equation is an
equality by construction. The verifier re-solves with ``linsolve``/``nonlinsolve`` and
rejects the documented silent-failure modes — a parametric tuple for 2×2, free symbols in
an intersection — as well as any point that does not satisfy both equations.

Display convention: every variable coefficient is positive, constants are signed, and each
statement template fixes the operators, so no item can print ``+ -3y``.

Linear + quadratic has no Easy cell in DESIGN §2.10 (the cell is ``—``), so the topic
advertises Medium and Hard only.
"""

from __future__ import annotations

import math
import random
from fractions import Fraction

from sympy import (EmptySet, Float, Integer, Rational, Symbol, Tuple, checksol, linsolve,
                   nonlinsolve, sqrt, sympify)
from sympy.core.sorting import default_sort_key

from app.core.latex import to_latex
from app.core.verify import VerificationResult, no_floats
from app.generators.base import Answer, Item, Step

X = Symbol("x")
Y = Symbol("y")

_LINEAR_EASY = "stmt.system_linear_easy"
_LINEAR_GENERAL = "stmt.system_linear_gen"
_LINEAR_QUADRATIC = "stmt.system_linear_quad"


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


def _point_latex(point: Tuple) -> str:
    return f"\\left({to_latex(point[0])}, {to_latex(point[1])}\\right)"


def _answers_latex(points: list[Tuple]) -> str:
    return ", \\quad ".join(_point_latex(point) for point in sorted(points, key=default_sort_key))


def _parse_point(text: str) -> Tuple | None:
    parts = text.split("|")
    if len(parts) != 2:
        return None
    values = [_parse_exact(part) for part in parts]
    if any(value is None for value in values):
        return None
    return Tuple(*values)


def _satisfies_all(equations, point: Tuple) -> bool:
    mapping = {X: point[0], Y: point[1]}
    return all(checksol(equation, mapping) is True for equation in equations)


class LinearSystem2x2:
    id = "math.systems.linear_2x2"
    family = "math"
    difficulties = ("easy", "medium", "hard")
    label_key = "topic.systems_linear_2x2"
    scenarios: tuple[str, ...] = ()

    # ---------------------------------------------------------------- generate
    def generate(self, rng: random.Random, difficulty: str, seed: int, index: int) -> Item:
        if difficulty == "easy":
            key, params, solution, steps = self._easy(rng)
        elif difficulty == "medium":
            key, params, solution, steps = self._medium(rng)
        else:
            key, params, solution, steps = self._hard(rng)
        return Item(
            topic=self.id,
            difficulty=difficulty,
            seed=seed,
            index=index,
            params=params,
            statement_key=key,
            steps=steps,
            answer=Answer(
                latex=_point_latex(solution),
                kind="value",
                payload={"solution": [f"{solution[0]}|{solution[1]}"]},
            ),
        )

    # ------------------------------------------------------------------ shapes
    def _easy(self, rng: random.Random):
        """One variable already isolated — solved by substitution."""
        m = rng.randint(1, 4)
        q = rng.randint(1, 5)
        a = rng.randint(1, 5)
        b = rng.randint(1, 5)
        x0 = rng.randint(1, 6)
        y0 = m * x0 + q
        c = a * x0 + b * y0
        params = {"m": Fraction(m), "q": Fraction(q), "a": Fraction(a), "b": Fraction(b), "c": Fraction(c)}
        solution = Tuple(Integer(x0), Integer(y0))
        steps = (
            Step(
                "step.substitute",
                f"{to_latex(Integer(a) * X + Integer(b) * (Integer(m) * X + Integer(q)))} = {to_latex(Integer(c))}",
            ),
            Step("step.solve_x", f"{to_latex(Integer(a + b * m) * X)} = {to_latex(Integer(c - b * q))}"),
            Step("step.solve_y", f"{to_latex(X)} = {to_latex(Integer(x0))}, \\; {to_latex(Y)} = {to_latex(Integer(y0))}"),
        )
        return _LINEAR_EASY, params, solution, steps

    def _medium(self, rng: random.Random):
        """General 2×2 through an integer solution."""
        while True:
            a1, b1, a2, b2 = (rng.randint(1, 5) for _ in range(4))
            if a1 * b2 != a2 * b1:
                break
        x0 = Fraction(rng.randint(-5, 5))
        y0 = Fraction(rng.randint(-5, 5))
        c1 = a1 * x0 + b1 * y0
        c2 = a2 * x0 + b2 * y0
        params = {
            "a1": Fraction(a1), "b1": Fraction(b1), "c1": c1,
            "a2": Fraction(a2), "b2": Fraction(b2), "c2": c2,
        }
        solution = Tuple(_q(x0), _q(y0))
        steps = self._elimination_steps(a1, b1, c1, a2, b2, c2, x0, y0)
        return _LINEAR_GENERAL, params, solution, steps

    def _hard(self, rng: random.Random):
        """Rational solution with non-integer components."""
        while True:
            a1, b1, a2, b2 = (rng.randint(1, 4) for _ in range(4))
            if a1 * b2 != a2 * b1:
                break
        while True:
            x0 = Fraction(rng.choice([-5, -3, -1, 1, 3, 5]), rng.choice([2, 3]))
            y0 = Fraction(rng.choice([-5, -3, -1, 1, 3, 5]), rng.choice([2, 3]))
            if x0.denominator != 1 or y0.denominator != 1:
                break
        c1 = a1 * x0 + b1 * y0
        c2 = a2 * x0 + b2 * y0
        params = {
            "a1": Fraction(a1), "b1": Fraction(b1), "c1": c1,
            "a2": Fraction(a2), "b2": Fraction(b2), "c2": c2,
        }
        solution = Tuple(_q(x0), _q(y0))
        steps = self._elimination_steps(a1, b1, c1, a2, b2, c2, x0, y0)
        return _LINEAR_GENERAL, params, solution, steps

    @staticmethod
    def _elimination_steps(a1, b1, c1, a2, b2, c2, x0: Fraction, y0: Fraction) -> tuple[Step, ...]:
        coefficient = Fraction(b1 * a2 - b2 * a1)
        constant = Fraction(c1 * a2 - c2 * a1)
        return (
            Step(
                "step.eliminate",
                f"{to_latex(_q(Fraction(a2)))} \\cdot ({to_latex(Integer(a1) * X + Integer(b1) * Y)}) - "
                f"{to_latex(_q(Fraction(a1)))} \\cdot ({to_latex(Integer(a2) * X + Integer(b2) * Y)}) = "
                f"{to_latex(_q(Fraction(c1 * a2)))} - {to_latex(_q(Fraction(c2 * a1)))}",
            ),
            Step("step.solve_y", f"{to_latex(_q(coefficient) * Y)} = {to_latex(_q(constant))} \\;\\Rightarrow\\; {to_latex(Y)} = {to_latex(_q(y0))}"),
            Step("step.solve_x", f"{to_latex(X)} = {to_latex(_q(x0))}"),
        )

    # ------------------------------------------------------------------ verify
    def verify(self, item: Item) -> VerificationResult:
        if not no_floats(*item.params.values()):
            return VerificationResult(False, "float_atom")
        rebuilt = _linear_equations(item.statement_key, item.params)
        if rebuilt is None:
            return VerificationResult(False, "unknown_statement")
        equations = [lhs - rhs for lhs, rhs in rebuilt]
        (a1, b1), (a2, b2) = [(equation.coeff(X), equation.coeff(Y)) for equation in equations]
        if a1 * b2 - a2 * b1 == 0:
            return VerificationResult(False, "singular_system")

        claimed_raw = item.answer.payload.get("solution")
        if not claimed_raw:
            return VerificationResult(False, "no_solution_claimed")
        point = _parse_point(claimed_raw[0])
        if point is None:
            return VerificationResult(False, "unparsable_solution")
        if not no_floats(*point):
            return VerificationResult(False, "float_atom")

        recomputed = linsolve(equations, [X, Y])
        if recomputed is EmptySet:
            return VerificationResult(False, "inconsistent_system")
        if len(recomputed) != 1:
            return VerificationResult(False, "not_unique")
        (expected,) = recomputed
        if any(value.free_symbols for value in expected):
            return VerificationResult(False, "parametric_solution")  # the documented silent failure
        if Tuple(*expected) != point:
            return VerificationResult(False, "solution_set_mismatch")
        if not _satisfies_all(equations, point):
            return VerificationResult(False, "solution_does_not_satisfy")
        if item.answer.latex != _point_latex(point):
            return VerificationResult(False, "answer_latex_mismatch")
        return VerificationResult(True)


class LinearQuadraticSystem:
    id = "math.systems.linear_quadratic"
    family = "math"
    difficulties = ("medium", "hard")
    label_key = "topic.systems_linear_quadratic"
    scenarios: tuple[str, ...] = ()

    # ---------------------------------------------------------------- generate
    def generate(self, rng: random.Random, difficulty: str, seed: int, index: int) -> Item:
        if difficulty == "medium":
            points, params, steps = self._integer(rng)
        elif rng.random() < 0.5:
            points, params, steps = self._irrational(rng)
        else:
            points, params, steps = self._tangent(rng)
        ordered = sorted(points, key=default_sort_key)
        return Item(
            topic=self.id,
            difficulty=difficulty,
            seed=seed,
            index=index,
            params=params,
            statement_key=_LINEAR_QUADRATIC,
            steps=steps,
            answer=Answer(
                latex=_answers_latex(ordered),
                kind="value",
                payload={"solutions": [f"{point[0]}|{point[1]}" for point in ordered]},
            ),
        )

    @staticmethod
    def _split(rng: random.Random, total: int) -> tuple[int, int]:
        """Split the root sum between the parabola (-b) and the line (+m): both positive."""
        m = rng.randint(1, total - 1)
        return total - m, m

    def _integer(self, rng: random.Random):
        while True:
            x1 = rng.randint(-3, 4)
            x2 = x1 + rng.randint(1, 6)
            if x1 + x2 >= 2:
                break
        b, m = self._split(rng, x1 + x2)
        n = abs(x1 * x2) + rng.randint(1, 3)
        c = n + x1 * x2
        params = {"b": Fraction(b), "c": Fraction(c), "m": Fraction(m), "n": Fraction(n)}
        points = [Tuple(Integer(x1), Integer(m * x1 + n)), Tuple(Integer(x2), Integer(m * x2 + n))]
        steps = (
            Step("step.substitute", f"{to_latex(X**2 - b * X + c)} = {to_latex(m * X + n)}"),
            Step("step.normal_form", f"{to_latex(X**2 - (b + m) * X + (c - n))} = 0"),
            Step("step.factorise", f"{to_latex((X - x1) * (X - x2))} = 0"),
            Step("step.solve_x", ", \\; ".join(f"{to_latex(X)} = {to_latex(Integer(root))}" for root in (x1, x2))),
            Step("step.solutions", _answers_latex(points)),
        )
        return points, params, steps

    def _irrational(self, rng: random.Random):
        options = [
            (t, s, k)
            for t in range(2, 10)
            for s in (2, 3, 5, 6, 7)
            for k in (1, 2)
            if (t * t - s * k * k) % 4 == 0 and math.isqrt(s * k * k) ** 2 != s * k * k
        ]
        rng.shuffle(options)
        t, s, k = options[0]
        discriminant = s * k * k
        difference = Fraction(t * t - discriminant, 4)
        b, m = self._split(rng, t)
        n = Fraction(math.ceil(-difference) + rng.randint(1, 3))
        c = n + difference
        params = {"b": Fraction(b), "c": c, "m": Fraction(m), "n": n}
        radical = sqrt(discriminant)
        points = [
            Tuple(Rational(t, 2) - radical / 2, Rational(m * t, 2) + n - m * radical / 2),
            Tuple(Rational(t, 2) + radical / 2, Rational(m * t, 2) + n + m * radical / 2),
        ]
        steps = (
            Step("step.substitute", f"{to_latex(X**2 - b * X + _q(c))} = {to_latex(m * X + _q(n))}"),
            Step("step.normal_form", f"{to_latex(X**2 - t * X + _q(difference))} = 0"),
            Step(
                "step.formula",
                f"{to_latex(X)} = \\frac{{{to_latex(Integer(t))} \\pm {to_latex(radical)}}}{{2}}",
            ),
            Step("step.solutions", _answers_latex(points)),
        )
        return points, params, steps

    def _tangent(self, rng: random.Random):
        x0 = rng.randint(2, 5)
        t = 2 * x0
        b, m = self._split(rng, t)
        n = rng.randint(1, 5)
        c = n + x0 * x0
        params = {"b": Fraction(b), "c": Fraction(c), "m": Fraction(m), "n": Fraction(n)}
        point = Tuple(Integer(x0), Integer(m * x0 + n))
        steps = (
            Step("step.substitute", f"{to_latex(X**2 - b * X + c)} = {to_latex(m * X + n)}"),
            Step("step.normal_form", f"{to_latex((X - x0) ** 2)} = 0"),
            Step("step.double_root", f"{to_latex(X)} = {to_latex(Integer(x0))}"),
            Step("step.solutions", _answers_latex([point])),
        )
        return [point], params, steps

    # ------------------------------------------------------------------ verify
    def verify(self, item: Item) -> VerificationResult:
        if not no_floats(*item.params.values()):
            return VerificationResult(False, "float_atom")
        rebuilt = _quadratic_equations(item.statement_key, item.params)
        if rebuilt is None:
            return VerificationResult(False, "unknown_statement")
        equations = [lhs - rhs for lhs, rhs in rebuilt]

        claimed_raw = item.answer.payload.get("solutions")
        if not claimed_raw:
            return VerificationResult(False, "no_solution_claimed")
        claimed = [_parse_point(text) for text in claimed_raw]
        if any(point is None for point in claimed):
            return VerificationResult(False, "unparsable_solution")

        recomputed = nonlinsolve(equations, [X, Y])
        if recomputed is EmptySet or not recomputed:
            return VerificationResult(False, "no_intersection")
        expected = [Tuple(*solution) for solution in recomputed]
        if any(any(value.free_symbols for value in solution) for solution in expected):
            return VerificationResult(False, "parametric_solution")
        if sorted(expected, key=default_sort_key) != sorted(claimed, key=default_sort_key):
            return VerificationResult(False, "solution_set_mismatch")
        for point in claimed:
            if not _satisfies_all(equations, point):
                return VerificationResult(False, "solution_does_not_satisfy")
        if item.answer.latex != _answers_latex(claimed):
            return VerificationResult(False, "answer_latex_mismatch")
        return VerificationResult(True)


def _linear_equations(statement_key: str, params: dict[str, Fraction]):
    if statement_key == _LINEAR_EASY:
        names = ("m", "q", "a", "b", "c")
        if any(name not in params for name in names):
            return None
        m, q, a, b, c = (params[name] for name in names)
        if min(q, a, b) <= 0 or m <= 0:
            return None
        return [(_q(a) * X + _q(b) * Y, _q(c)), (-_q(m) * X + Y, _q(q))]
    if statement_key == _LINEAR_GENERAL:
        names = ("a1", "b1", "c1", "a2", "b2", "c2")
        if any(name not in params for name in names):
            return None
        a1, b1, c1, a2, b2, c2 = (params[name] for name in names)
        if min(a1, b1, a2, b2) <= 0:
            return None
        return [(_q(a1) * X + _q(b1) * Y, _q(c1)), (_q(a2) * X + _q(b2) * Y, _q(c2))]
    return None


def _quadratic_equations(statement_key: str, params: dict[str, Fraction]):
    if statement_key != _LINEAR_QUADRATIC:
        return None
    names = ("b", "c", "m", "n")
    if any(name not in params for name in names):
        return None
    b, c, m, n = (params[name] for name in names)
    if min(b, m) <= 0:
        return None
    return [(Y, X**2 - _q(b) * X + _q(c)), (Y, _q(m) * X + _q(n))]


TOPICS = {
    LinearSystem2x2.id: LinearSystem2x2(),
    LinearQuadraticSystem.id: LinearQuadraticSystem(),
}
