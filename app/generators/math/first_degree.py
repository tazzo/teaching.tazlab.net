"""First-degree equations — the topic that proves the plumbing (C.1).

Reverse construction (DESIGN §2.5): choose the answer first, build the exercise from
it, then verify by an independent path. The derivation is a template over the same
parameter tuple, so the steps and the answer cannot disagree.
"""

from __future__ import annotations

import random
from fractions import Fraction

from sympy import Eq, Integer, Rational, Symbol, simplify

from app.core.latex import to_latex
from app.core.verify import VerificationResult, no_floats, real_solutions, satisfies
from app.generators.base import Answer, Item, Step

X = Symbol("x")


class FirstDegree:
    id = "math.equations.first_degree"
    family = "math"
    difficulties = ("easy", "medium", "hard")
    label_key = "topic.first_degree"
    scenarios: tuple[str, ...] = ()

    # ---------------------------------------------------------------- generate
    def generate(self, rng: random.Random, difficulty: str, seed: int, index: int) -> Item:
        if difficulty == "easy":
            a = rng.randint(1, 5)
            x0 = rng.randint(-5, 5)
            b = -a * x0
        elif difficulty == "medium":
            a = rng.choice([-6, -4, -3, -2, 2, 3, 4, 6])
            x0 = rng.randint(-6, 6)
            b = -a * x0
        else:
            a = rng.choice([-9, -6, -3, 3, 6, 9])
            x0 = Rational(rng.randint(-9, 9), rng.choice([2, 3]))
            b = -a * x0

        a_f, b_f, x0_f = Fraction(a), Fraction(b), Fraction(x0)
        params = {"a": a_f, "b": b_f, "solution": x0_f}

        lhs = Integer(a) * X + Integer(b)
        steps = (
            Step("step.isolate_term", f"{to_latex(Integer(a) * X)} = {to_latex(-Integer(b))}"),
            Step("step.divide", f"{to_latex(X)} = \\frac{{{to_latex(-Integer(b))}}}{{{to_latex(Integer(a))}}}"),
            Step("step.simplify", f"{to_latex(X)} = {to_latex(Rational(x0))}"),
        )
        answer = Answer(
            latex=f"{to_latex(X)} = {to_latex(Rational(x0))}",
            kind="value",
            payload={"solutions": [str(x0_f)]},
        )
        return Item(
            topic=self.id,
            difficulty=difficulty,
            seed=seed,
            index=index,
            params=params,
            statement_key="stmt.first_degree",
            steps=steps,
            answer=answer,
        )

    # ------------------------------------------------------------------ verify
    def verify(self, item: Item) -> VerificationResult:
        if not no_floats(*(Rational(v) for v in item.params.values())):
            return VerificationResult(False, "float_atom")
        claimed = item.answer.payload.get("solutions")
        if not claimed:
            return VerificationResult(False, "no_solution_claimed")

        a = Rational(item.params["a"])
        b = Rational(item.params["b"])
        expr = a * X + b
        expected = [Rational(claimed[0])]

        if not satisfies(expr, X, expected[0]):
            return VerificationResult(False, "root_does_not_satisfy")
        recomputed = real_solutions(expr, X)
        if recomputed is None:
            return VerificationResult(False, "undecidable")
        if [simplify(v) for v in recomputed] != [simplify(expected[0])]:
            return VerificationResult(False, "solution_set_mismatch")
        if simplify(Eq(expr, 0).lhs - Eq(expr, 0).rhs) == 0:
            return VerificationResult(False, "degenerate_identity")
        return VerificationResult(True)


TOPIC = FirstDegree()
