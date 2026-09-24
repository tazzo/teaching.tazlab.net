"""Second-degree equations ``a x² + b x + c = 0`` — reverse construction (DESIGN §2.10).

The answer is chosen first (two roots for Easy/Medium, a radical pair or a special case
for Hard) and the coefficients are *derived* from it, so the derivation template and the
answer are projections of one parameter tuple and cannot disagree. Every step is written
against that same tuple; an item whose ``solveset`` disagrees with the constructed answer
is rejected by :meth:`SecondDegree.verify` before it reaches a student.

Display convention: the statement template fixes the *operator*, so the parameters carry
the magnitude of each coefficient (``b = |B|``) and the sign lives in the statement key.
The verifier maps ``(statement_key, params)`` back to the canonical ``(A, B, C)`` — that
reconstruction is what makes a tampered key or magnitude a rejection, not a silent pass.
"""

from __future__ import annotations

import random
from fractions import Fraction

from sympy import Float, Integer, Rational, Symbol, sqrt, sympify
from sympy.core.sorting import default_sort_key

from app.core.latex import to_latex
from app.core.verify import VerificationResult, no_floats, real_solutions, satisfies
from app.generators.base import Answer, Item, Step

X = Symbol("x")

_MONIC = "stmt.second_degree"
_NON_MONIC = "stmt.second_degree_gen"
_B0 = "stmt.second_degree_b0"
_B0_NEG = "stmt.second_degree_b0_neg"
_C0 = "stmt.second_degree_c0"

_PATTERNS: dict[str, tuple[int, int]] = {
    "pp": (1, 1),
    "pm": (1, -1),
    "mp": (-1, 1),
    "mm": (-1, -1),
}
_SIGNS = {(sign_b > 0, sign_c > 0): name for name, (sign_b, sign_c) in _PATTERNS.items()}

def _statement_key(monic: bool, b: Fraction, c: Fraction) -> str:
    return f"{_MONIC if monic else _NON_MONIC}_{_SIGNS[(b > 0, c > 0)]}"


def _rebuild(key: str, params: dict[str, Fraction]) -> tuple[Fraction, Fraction, Fraction] | None:
    """(A, B, C) of the canonical ``A x² + B x + C = 0`` shown by ``key``/``params``."""
    b = params.get("b", Fraction(0))
    c = params.get("c", Fraction(0))
    if key == _B0:
        return Fraction(1), Fraction(0), -c
    if key == _B0_NEG:
        return Fraction(1), Fraction(0), c
    if key == _C0:
        return Fraction(1), -b, Fraction(0)
    for name, monic in ((_NON_MONIC, False), (_MONIC, True)):
        prefix = f"{name}_"
        if not key.startswith(prefix):
            continue
        sign_pair = _PATTERNS.get(key[len(prefix):])
        if sign_pair is None:
            return None
        a = Fraction(1) if monic else params.get("a", Fraction(0))
        if a <= 0:
            return None
        return a, sign_pair[0] * abs(b), sign_pair[1] * abs(c)
    return None


def _exact(value: Fraction) -> Integer | Rational:
    return Integer(value.numerator) if value.denominator == 1 else Rational(value.numerator, value.denominator)


def _signed(latex: str, value: Fraction) -> str:
    """Parenthesise a substituted negative coefficient: ``(-8)^2``, not ``-8^2``."""
    return f"({latex})" if value < 0 else latex


def _parse_exact(text: str):
    try:
        value = sympify(text, rational=True)
    except Exception:  # SympifyError and friends: a corrupted payload must not crash the verifier
        return None
    if getattr(value, "atoms", None) is not None and value.atoms(Float):
        return None
    return value


class SecondDegree:
    id = "math.equations.second_degree"
    family = "math"
    difficulties = ("easy", "medium", "hard")
    label_key = "topic.second_degree"
    scenarios: tuple[str, ...] = ()

    # ---------------------------------------------------------------- generate
    def generate(self, rng: random.Random, difficulty: str, seed: int, index: int) -> Item:
        if difficulty == "easy":
            key, params, roots = self._easy(rng)
        elif difficulty == "medium":
            key, params, roots = self._medium(rng)
        else:
            key, params, roots = self._hard(rng)
        return self._assemble(key, params, roots, difficulty, seed, index)

    # ------------------------------------------------------------------ shapes
    def _easy(self, rng: random.Random) -> tuple[str, dict[str, Fraction], list]:
        while True:
            r1 = rng.randint(-6, 6)
            r2 = rng.randint(-6, 6)
            b = -(r1 + r2)
            # b == 0 would print "+ 0x" and c == 0 is the dedicated c = 0 template's job
            if r1 == r2 or r1 == 0 or r2 == 0 or b == 0:
                continue
            c = r1 * r2
            break
        params = {"b": Fraction(abs(b)), "c": Fraction(abs(c))}
        return _statement_key(True, b, c), params, [Rational(r1), Rational(r2)]

    def _medium(self, rng: random.Random) -> tuple[str, dict[str, Fraction], list]:
        while True:
            a = rng.choice([2, 3, 4, 5])
            r1 = rng.randint(-4, 4)
            r2 = rng.randint(-4, 4)
            b = -a * (r1 + r2)
            if r1 == r2 or r1 == 0 or r2 == 0 or b == 0:
                continue
            c = a * r1 * r2
            if abs(b) > 40 or abs(c) > 40:
                continue
            break
        params = {"a": Fraction(a), "b": Fraction(abs(b)), "c": Fraction(abs(c))}
        return _statement_key(False, b, c), params, [Rational(r1), Rational(r2)]

    def _hard(self, rng: random.Random) -> tuple[str, dict[str, Fraction], list]:
        variant = rng.choice(("irrational", "irrational", "c0", "b0", "b0_neg", "double", "delta_neg"))
        if variant == "irrational":
            options = [
                (r, s, m)
                for r in range(-5, 6)
                if r != 0
                for s in (1, 1, 2)
                for m in (2, 3, 5, 6, 7)
            ]
            rng.shuffle(options)
            for r, s, m in options:
                b = -2 * r
                c = r * r - s * s * m
                if b == 0 or c == 0:
                    continue
                params = {"b": Fraction(abs(b)), "c": Fraction(abs(c))}
                roots = [Rational(r) - s * sqrt(m), Rational(r) + s * sqrt(m)]
                return _statement_key(True, b, c), params, roots
            raise RuntimeError("irrational second degree: no candidate")
        if variant == "c0":
            b = rng.randint(2, 9)
            return _C0, {"b": Fraction(b)}, [Integer(0), Rational(b)]
        if variant == "b0":
            c = rng.choice([2, 3, 5, 6, 7, 8, 10, 11, 12])
            return _B0, {"c": Fraction(c)}, [-sqrt(c), sqrt(c)]
        if variant == "b0_neg":
            c = rng.choice([1, 2, 3, 4, 5, 6, 7, 8])
            return _B0_NEG, {"c": Fraction(c)}, []
        if variant == "double":
            r = rng.choice([-4, -3, -2, 2, 3, 4])
            b = -2 * r
            c = r * r
            params = {"b": Fraction(abs(b)), "c": Fraction(abs(c))}
            return _statement_key(True, b, c), params, [Rational(r)]
        a = rng.choice([1, 1, 2, 3])
        b = rng.choice([value for value in range(-4, 5) if value != 0])
        c = b * b // (4 * a) + rng.randint(1, 6)
        params = {"b": Fraction(abs(b)), "c": Fraction(abs(c))}
        if a != 1:
            params["a"] = Fraction(a)
        return _statement_key(a == 1, b, c), params, []

    # ---------------------------------------------------------------- assembly
    def _assemble(
        self,
        key: str,
        params: dict[str, Fraction],
        roots: list,
        difficulty: str,
        seed: int,
        index: int,
    ) -> Item:
        solved = sorted(roots, key=default_sort_key)
        rebuilt = _rebuild(key, params)
        assert rebuilt is not None, key
        a, b, c = rebuilt
        delta = b * b - 4 * a * c
        steps = self._steps(key, a, b, c, delta, solved)
        return Item(
            topic=self.id,
            difficulty=difficulty,
            seed=seed,
            index=index,
            params=params,
            statement_key=key,
            steps=steps,
            answer=Answer(
                latex=self.answer_latex(solved),
                kind="value" if solved else "set",
                payload={"solutions": [str(root) for root in solved]},
            ),
        )

    def _steps(self, key: str, a: Fraction, b: Fraction, c: Fraction, delta, solved: list) -> tuple[Step, ...]:
        a_l, b_l, c_l = to_latex(_exact(a)), to_latex(_exact(b)), to_latex(_exact(c))
        if key == _C0:
            return (
                Step(
                    "step.factor_common",
                    f"{to_latex(X**2 + _exact(b) * X)} = 0 \\;\\Rightarrow\\; "
                    f"{to_latex(X)}({to_latex(X + _exact(b))}) = 0",
                ),
                Step("step.solutions", self.answer_latex(solved)),
            )
        if key in (_B0, _B0_NEG):
            extracted = Step("step.extract_root", f"{to_latex(X**2)} = {to_latex(_exact(-c))}")
            if key == _B0_NEG:
                return (extracted, Step("step.no_real_roots", "\\Delta < 0"))
            return (extracted, Step("step.solutions", self.answer_latex(solved)))
        discriminant = Step(
            "step.discriminant",
            f"\\Delta = {_signed(b_l, b)}^2 - 4 \\cdot {a_l} \\cdot {_signed(c_l, c)} = {to_latex(_exact(delta))}",
        )
        if delta < 0:
            return (discriminant, Step("step.no_real_roots", "\\Delta < 0"))
        if delta == 0:
            root = to_latex(_exact(Fraction(-b, 2 * a)))
            return (
                discriminant,
                Step("step.double_root", f"{to_latex(X)} = \\frac{{{to_latex(_exact(-b))}}}{{{to_latex(_exact(2 * a))}}} = {root}"),
                Step("step.solutions", self.answer_latex(solved)),
            )
        centre = _exact(Fraction(-b, 2 * a))
        half = sqrt(_exact(delta)) / (2 * a)
        return (
            discriminant,
            Step(
                "step.quadratic_formula",
                f"{to_latex(X)} = \\frac{{{to_latex(_exact(-b))} \\pm \\sqrt{{{to_latex(_exact(delta))}}}}}{{{to_latex(_exact(2 * a))}}}"
                f" = {to_latex(centre)} \\pm {to_latex(half)}",
            ),
            Step("step.solutions", self.answer_latex(solved)),
        )

    @staticmethod
    def answer_latex(roots: list) -> str:
        if not roots:
            return "\\emptyset"
        if len(roots) == 1:
            return f"{to_latex(X)} = {to_latex(roots[0])}"
        return ", \\quad ".join(f"x_{{{i + 1}}} = {to_latex(root)}" for i, root in enumerate(roots))

    # ------------------------------------------------------------------ verify
    def verify(self, item: Item) -> VerificationResult:
        if not no_floats(*item.params.values()):
            return VerificationResult(False, "float_atom")
        rebuilt = _rebuild(item.statement_key, item.params)
        if rebuilt is None:
            return VerificationResult(False, "unknown_statement")
        a, b, c = rebuilt
        if a == 0:
            return VerificationResult(False, "degenerate_degree")
        claimed_raw = item.answer.payload.get("solutions")
        if claimed_raw is None:
            return VerificationResult(False, "no_solution_claimed")
        claimed = [_parse_exact(text) for text in claimed_raw]
        if any(value is None for value in claimed):
            return VerificationResult(False, "unparsable_solution")
        if not no_floats(*claimed):
            return VerificationResult(False, "float_atom")

        expr = _exact(a) * X**2 + _exact(b) * X + _exact(c)
        recomputed = real_solutions(expr, X)
        if recomputed is None:
            return VerificationResult(False, "undecidable")
        ordered_claimed = sorted(claimed, key=default_sort_key)
        if sorted(recomputed, key=default_sort_key) != ordered_claimed:
            return VerificationResult(False, "solution_set_mismatch")
        for value in ordered_claimed:
            if not satisfies(expr, X, value):
                return VerificationResult(False, "root_does_not_satisfy")
        if item.answer.latex != self.answer_latex(ordered_claimed):
            return VerificationResult(False, "answer_latex_mismatch")
        return VerificationResult(True)


TOPIC = SecondDegree()
