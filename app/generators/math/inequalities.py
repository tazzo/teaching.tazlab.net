"""Inequalities — first degree, second degree, rational (DESIGN §2.10).

The answer is **constructed first**: the parameter tuple fixes the critical points (zeros
and poles), a sign table over them decides which cells and which endpoints belong to the
solution, and the steps are printed from the same tuple. ``solveset`` is the *second*
opinion, never the source: an item is rejected unless the constructive set, the solved set
and the rendered LaTeX all agree.

On top of that the verifier runs a deterministic sampler over integers, halves and every
claimed boundary — including the endpoints themselves, which is what makes an open/closed
corruption visible.

Interval versus finite set is carried in ``Answer.kind``; the machine-readable form of the
claim is ``srepr`` of the set, so the verifier compares sets rather than strings.
"""

from __future__ import annotations

import random
from fractions import Fraction

from sympy import (ConditionSet, EmptySet, FiniteSet, Ge, Gt, Integer, Interval, Le, Lt,
                   Rational, Reals, S, Set, Symbol, Union, nan, oo, solveset, srepr,
                   sympify, zoo)

from app.core.latex import to_latex
from app.core.verify import VerificationResult, no_floats
from app.generators.base import Answer, Item, Step

X = Symbol("x")

_FIRST_GT = "stmt.ineq_first_gt"
_FIRST_NEG = "stmt.ineq_first_neg"
_FIRST_CHAIN = "stmt.ineq_first_chain"
_SECOND_MONIC = "stmt.ineq2_monic_gt"
_SECOND_GEN = "stmt.ineq2_gen_lt"
_SECOND_NEG = "stmt.ineq2_hard_neg"
_SECOND_FACTORED = "stmt.ineq2_hard_factored"
_RAT_EASY = "stmt.ineq_rat_easy_gt"
_RAT_MEDIUM = "stmt.ineq_rat_medium_ge"
_RAT_HARD_NUM = "stmt.ineq_rat_hard_num"
_RAT_HARD_DEN = "stmt.ineq_rat_hard_den"

_SET_LOCALS = {
    "Interval": Interval,
    "Union": Union,
    "FiniteSet": FiniteSet,
    "EmptySet": EmptySet,
    "Reals": Reals,
    "S": S,
    "oo": oo,
}


def _q(value: Fraction) -> Integer | Rational:
    return Integer(value.numerator) if value.denominator == 1 else Rational(value.numerator, value.denominator)


def _parse_set(text: str) -> Set | None:
    try:
        value = sympify(text, locals=_SET_LOCALS, rational=True)
    except Exception:
        return None
    return value if isinstance(value, Set) else None


def _holds(expr, op: str, value) -> bool:
    """Evaluate ``expr op 0`` at ``value``: exact, and ``False`` where it is undefined."""
    substituted = expr.subs(X, value)
    if substituted.has(zoo, nan, oo, -oo) or substituted.is_real is not True:
        return False
    if op == ">":
        return substituted.is_positive is True
    if op == ">=":
        return substituted.is_positive is True or substituted.is_zero is True
    if op == "<":
        return substituted.is_negative is True
    return substituted.is_negative is True or substituted.is_zero is True


def _solve(expr, op: str) -> Set | None:
    relations = {">": Gt, ">=": Ge, "<": Lt, "<=": Le}
    relation = relations[op](expr, 0)
    result = solveset(relation, X, domain=Reals)
    return None if isinstance(result, ConditionSet) else result


def _test_point(left, right):
    if left is None and right is None:
        return Integer(0)
    if left is None:
        return right - 1
    if right is None:
        return left + 1
    return (left + right) / 2


def _constraint_solution(expr, op: str, zeros: list, poles: list) -> Set:
    """Sign table over the critical points: the answer is *constructed*, not solved for.

    The cells between consecutive critical points are kept when a probe inside them
    satisfies the relation, and the critical points themselves are kept when the relation
    holds there (never at a pole — the substitution is undefined, which ``_holds`` reports
    as ``False``). Consecutive kept cells merge into one maximal interval, so the set is
    built the way a student builds it, and ``solveset`` stays a second, independent opinion.
    """
    criticals = sorted(set(zeros) | set(poles))
    atoms: list[tuple] = []
    bounds = [None, *criticals, None]
    for index, (left, right) in enumerate(zip(bounds, bounds[1:])):
        atoms.append((left, right, False, _holds(expr, op, _test_point(left, right))))
        if index < len(criticals):
            point = criticals[index]
            atoms.append((point, point, True, _holds(expr, op, point)))

    pieces: list[Set] = []
    run: list[tuple] = []
    for atom in [*atoms, None]:
        if atom is not None and atom[3]:
            run.append(atom)
            continue
        if not run:
            continue
        first, last = run[0], run[-1]
        if first[2] and last[2]:
            pieces.append(FiniteSet(first[0]))
        else:
            pieces.append(
                Interval(
                    -oo if first[0] is None else first[0],
                    oo if last[1] is None else last[1],
                    not first[2],
                    not last[2],
                )
            )
        run = []
    return Union(*pieces) if pieces else EmptySet


def _solution(key: str, params: dict[str, Fraction], criticals: list[tuple[list, list]]) -> Set:
    model = _model(key, params)
    assert model is not None and len(model) == len(criticals), key
    solution: Set = Reals
    for (expr, op), (zeros, poles) in zip(model, criticals):
        solution = solution.intersect(_constraint_solution(expr, op, zeros, poles))
    return solution


def _boundaries(claimed: Set) -> list:
    if isinstance(claimed, Interval):
        return [value for value in (claimed.start, claimed.end) if value is not None]
    if isinstance(claimed, Union):
        found: list = []
        for part in claimed.args:
            found += _boundaries(part)
        return found
    return []


def _probes(claimed: Set) -> list:
    """Deterministic sample: integers, halves, every claimed boundary and its neighbours."""
    points = [Integer(value) for value in range(-12, 13)]
    points += [Rational(value, 2) for value in range(-25, 26) if value % 2]
    for boundary in _boundaries(claimed):
        if boundary.is_real is not True or boundary.is_finite is not True:
            continue
        points += [
            boundary,
            boundary + 1,
            boundary - 1,
            boundary + Rational(1, 2),
            boundary - Rational(1, 2),
            boundary + 2,
            boundary - 2,
        ]
    if isinstance(claimed, FiniteSet):
        points += list(claimed)
    unique: dict[str, object] = {}
    for point in points:
        unique[str(point)] = point
    return [unique[key] for key in sorted(unique)]


def _verify_inequality(item: Item, model: list[tuple[object, str]] | None) -> VerificationResult:
    if model is None:
        return VerificationResult(False, "unknown_statement")
    if not no_floats(*item.params.values()):
        return VerificationResult(False, "float_atom")
    claimed = _parse_set((item.answer.payload.get("set") or [""])[0])
    if claimed is None:
        return VerificationResult(False, "unparsable_set")

    recomputed: Set = Reals
    for expr, op in model:
        part = _solve(expr, op)
        if part is None:
            return VerificationResult(False, "undecidable")
        recomputed = recomputed.intersect(part)
    if recomputed != claimed:
        return VerificationResult(False, "solution_set_mismatch")
    if item.answer.latex != to_latex(claimed):
        return VerificationResult(False, "answer_latex_mismatch")

    for point in _probes(claimed):
        inside = claimed.contains(point)
        if inside is None:
            return VerificationResult(False, "undecidable")
        if bool(inside) != all(_holds(expr, op, point) for expr, op in model):
            return VerificationResult(False, "sampling_disagrees")
    return VerificationResult(True)


def _answer(solution: Set) -> Answer:
    kind = "set" if solution in (EmptySet, Reals) else "interval"
    return Answer(latex=to_latex(solution), kind=kind, payload={"set": [srepr(solution)]})


class FirstDegreeInequality:
    id = "math.inequalities.first_degree"
    family = "math"
    difficulties = ("easy", "medium", "hard")
    label_key = "topic.inequalities_first_degree"
    scenarios: tuple[str, ...] = ()

    def generate(self, rng: random.Random, difficulty: str, seed: int, index: int,
                 options: dict | None = None) -> Item:
        if difficulty == "easy":
            a = rng.randint(2, 6)
            boundary = rng.choice([value for value in range(-8, 9) if value != 0])
            key = _FIRST_GT
            params = {"a": Fraction(a), "b": Fraction(a * boundary)}
            criticals = [([Fraction(boundary)], [])]
            steps = (Step("step.divide", f"{to_latex(X)} > {to_latex(Integer(boundary))}"),)
        elif difficulty == "medium":
            a = rng.randint(2, 9)
            b = rng.choice([value for value in range(-20, 21) if value % a != 0])
            key = _FIRST_NEG
            params = {"a": Fraction(a), "b": Fraction(b)}
            criticals = [([Fraction(-b, a)], [])]
            steps = (Step("step.sign_flip", f"{to_latex(X)} < {to_latex(_q(Fraction(-b, a)))}"),)
        else:
            a = rng.randint(2, 5)
            b = rng.randint(1, 8)
            lower = rng.randint(-6, 6)
            upper = lower + rng.randint(2, 8)
            key = _FIRST_CHAIN
            params = {"p": Fraction(lower), "a": Fraction(a), "b": Fraction(b), "q": Fraction(upper)}
            criticals = [
                ([Fraction(lower - b, a)], []),
                ([Fraction(upper - b, a)], []),
            ]
            steps = (
                Step(
                    "step.subtract",
                    f"{to_latex(_q(Fraction(lower - b)))} < {to_latex(Integer(a) * X)} < {to_latex(_q(Fraction(upper - b)))}",
                ),
            )
        solution = _solution(key, params, criticals)
        return Item(
            topic=self.id,
            difficulty=difficulty,
            seed=seed,
            index=index,
            params=params,
            statement_key=key,
            steps=steps + (Step("step.solutions", to_latex(solution)),),
            answer=_answer(solution),
        )

    def verify(self, item: Item) -> VerificationResult:
        return _verify_inequality(item, _model(item.statement_key, item.params))


class SecondDegreeInequality:
    id = "math.inequalities.second_degree"
    family = "math"
    difficulties = ("easy", "medium", "hard")
    label_key = "topic.inequalities_second_degree"
    scenarios: tuple[str, ...] = ()

    def generate(self, rng: random.Random, difficulty: str, seed: int, index: int,
                 options: dict | None = None) -> Item:
        if difficulty == "easy":
            r1 = rng.randint(1, 4)
            r2 = r1 + rng.randint(1, 4)
            b, c = r1 + r2, r1 * r2
            key = _SECOND_MONIC
            params = {"b": Fraction(b), "c": Fraction(c)}
            criticals = [([Fraction(r1), Fraction(r2)], [])]
            steps = (
                Step("step.discriminant", f"\\Delta = {to_latex(Integer(b))}^2 - 4 \\cdot {to_latex(Integer(c))} = {to_latex(Integer((r1 - r2) ** 2))}"),
                Step("step.factorise", f"{to_latex((X - r1) * (X - r2))} > 0"),
            )
        elif difficulty == "medium":
            a = rng.randint(2, 5)
            r1 = rng.randint(1, 4)
            r2 = r1 + rng.randint(0, 4)
            b, c = a * (r1 + r2), a * r1 * r2
            key = _SECOND_GEN
            params = {"a": Fraction(a), "b": Fraction(b), "c": Fraction(c)}
            criticals = [([Fraction(r1), Fraction(r2)], [])]
            if r1 == r2:
                steps = (
                    Step("step.discriminant", "\\Delta = 0"),
                    Step("step.double_root", f"{to_latex(Integer(a) * (X - r1) ** 2)} < 0"),
                )
            else:
                steps = (
                    Step(
                        "step.discriminant",
                        f"\\Delta = {to_latex(Integer(b))}^2 - 4 \\cdot {to_latex(Integer(a))} \\cdot {to_latex(Integer(c))} = {to_latex(Integer(a * a * (r1 - r2) ** 2))}",
                    ),
                    Step("step.factorise", f"{to_latex(Integer(a) * (X - r1) * (X - r2))} < 0"),
                )
        elif rng.random() < 0.5:
            a = rng.randint(2, 4)
            b = rng.randint(1, 8)
            c = b * b // (4 * a) + rng.randint(1, 6)
            key = _SECOND_NEG
            params = {"a": Fraction(a), "b": Fraction(b), "c": Fraction(c)}
            criticals = [([], [])]
            steps = (
                Step(
                    "step.discriminant",
                    f"\\Delta = {to_latex(Integer(b))}^2 - 4 \\cdot {to_latex(Integer(a))} \\cdot {to_latex(Integer(c))} = {to_latex(Integer(b * b - 4 * a * c))}",
                ),
                Step("step.sign_analysis", f"\\Delta < 0 \\Rightarrow {to_latex(Integer(a) * X**2 - Integer(b) * X + Integer(c))} > 0"),
            )
        else:
            p = rng.randint(1, 4)
            q = p + rng.randint(1, 4)
            key = _SECOND_FACTORED
            params = {"p": Fraction(p), "q": Fraction(q)}
            criticals = [([Fraction(p), Fraction(q)], [])]
            steps = (
                Step("step.factorise", f"{to_latex((X - p) * (X - q))} > 0"),
                Step("step.sign_analysis", f"{to_latex(X)} < {to_latex(Integer(p))} \\;\\vee\\; {to_latex(X)} > {to_latex(Integer(q))}"),
            )
        solution = _solution(key, params, criticals)
        return Item(
            topic=self.id,
            difficulty=difficulty,
            seed=seed,
            index=index,
            params=params,
            statement_key=key,
            steps=steps + (Step("step.solutions", to_latex(solution)),),
            answer=_answer(solution),
        )

    def verify(self, item: Item) -> VerificationResult:
        return _verify_inequality(item, _model(item.statement_key, item.params))


class RationalInequality:
    id = "math.inequalities.rational"
    family = "math"
    difficulties = ("easy", "medium", "hard")
    label_key = "topic.inequalities_rational"
    scenarios: tuple[str, ...] = ()

    def generate(self, rng: random.Random, difficulty: str, seed: int, index: int,
                 options: dict | None = None) -> Item:
        if difficulty == "easy":
            p, q = rng.sample(range(1, 7), 2)
            key = _RAT_EASY
            params = {"p": Fraction(p), "q": Fraction(q)}
            criticals = [([Fraction(p)], [Fraction(q)])]
            low, high = sorted([p, q])
            steps = (
                Step("step.critical_points", f"{to_latex(X)} = {to_latex(Integer(low))}, \\; {to_latex(X)} = {to_latex(Integer(high))}"),
                Step("step.sign_analysis", f"{to_latex(X)} < {to_latex(Integer(low))} \\;\\vee\\; {to_latex(X)} > {to_latex(Integer(high))}"),
            )
        elif difficulty == "medium":
            a = rng.randint(2, 5)
            b = rng.randint(1, 15)
            q = rng.choice([value for value in range(1, 8) if value * a != b])
            key = _RAT_MEDIUM
            params = {"a": Fraction(a), "b": Fraction(b), "q": Fraction(q)}
            criticals = [([Fraction(b, a)], [Fraction(q)])]
            steps = (
                Step("step.critical_points", f"{to_latex(X)} = {to_latex(_q(Fraction(b, a)))}, \\; {to_latex(X)} \\ne {to_latex(Integer(q))}"),
                Step("step.sign_analysis", f"{to_latex(Integer(a) * X - b)} \\ge 0 \\;\\wedge\\; {to_latex(X)} \\ne {to_latex(Integer(q))}"),
            )
        else:
            p, q, r = rng.sample(range(1, 8), 3)
            params = {"p": Fraction(p), "q": Fraction(q), "r": Fraction(r)}
            critical = ", \\; ".join(f"{to_latex(X)} = {to_latex(Integer(value))}" for value in sorted([p, q, r]))
            if rng.random() < 0.5:
                key = _RAT_HARD_NUM
                criticals = [([Fraction(p), Fraction(q)], [Fraction(r)])]
                steps = (
                    Step("step.critical_points", critical),
                    Step("step.sign_analysis", f"{to_latex(X)} \\ne {to_latex(Integer(r))}"),
                )
            else:
                key = _RAT_HARD_DEN
                criticals = [([Fraction(p)], [Fraction(q), Fraction(r)])]
                steps = (
                    Step("step.critical_points", critical),
                    Step("step.sign_analysis", f"{to_latex(X)} \\ne {to_latex(Integer(q))}, \\; {to_latex(X)} \\ne {to_latex(Integer(r))}"),
                )
        solution = _solution(key, params, criticals)
        return Item(
            topic=self.id,
            difficulty=difficulty,
            seed=seed,
            index=index,
            params=params,
            statement_key=key,
            steps=steps + (Step("step.solutions", to_latex(solution)),),
            answer=_answer(solution),
        )

    def verify(self, item: Item) -> VerificationResult:
        return _verify_inequality(item, _model(item.statement_key, item.params))


def _model(statement_key: str, params: dict[str, Fraction]) -> list[tuple[object, str]] | None:
    """The canonical constraints ``expr op 0`` that the statement displays."""
    if statement_key == _FIRST_GT:
        a, b = params.get("a"), params.get("b")
        if a is None or b is None or a <= 0:
            return None
        return [(_q(a) * X - _q(b), ">")]
    if statement_key == _FIRST_NEG:
        a, b = params.get("a"), params.get("b")
        if a is None or b is None or a <= 0:
            return None
        return [(-_q(a) * X - _q(b), ">")]
    if statement_key == _FIRST_CHAIN:
        p, a, b, q = (params.get(name) for name in ("p", "a", "b", "q"))
        if None in (p, a, b, q) or a <= 0 or b <= 0 or q <= p:
            return None
        middle = _q(a) * X + _q(b)
        return [(middle - _q(p), ">"), (_q(q) - middle, ">")]
    if statement_key == _SECOND_MONIC:
        b, c = params.get("b"), params.get("c")
        if b is None or c is None or b <= 0 or c <= 0:
            return None
        return [(X**2 - _q(b) * X + _q(c), ">")]
    if statement_key == _SECOND_GEN:
        a, b, c = (params.get(name) for name in ("a", "b", "c"))
        if None in (a, b, c) or min(a, b, c) <= 0 or a == 1:
            return None
        return [(_q(a) * X**2 - _q(b) * X + _q(c), "<")]
    if statement_key == _SECOND_NEG:
        a, b, c = (params.get(name) for name in ("a", "b", "c"))
        if None in (a, b, c) or min(a, b, c) <= 0 or a == 1:
            return None
        return [(-_q(a) * X**2 + _q(b) * X - _q(c), ">")]
    if statement_key == _SECOND_FACTORED:
        p, q = params.get("p"), params.get("q")
        if p is None or q is None or min(p, q) <= 0 or p == q:
            return None
        return [((X - _q(p)) * (X - _q(q)), ">")]
    if statement_key == _RAT_EASY:
        p, q = params.get("p"), params.get("q")
        if p is None or q is None or min(p, q) <= 0 or p == q:
            return None
        return [((X - _q(p)) / (X - _q(q)), ">")]
    if statement_key == _RAT_MEDIUM:
        a, b, q = (params.get(name) for name in ("a", "b", "q"))
        if None in (a, b, q) or min(a, b, q) <= 0 or a == 1:
            return None
        return [((_q(a) * X - _q(b)) / (X - _q(q)), ">=")]
    if statement_key == _RAT_HARD_NUM:
        p, q, r = (params.get(name) for name in ("p", "q", "r"))
        if None in (p, q, r) or min(p, q, r) <= 0 or len({p, q, r}) != 3:
            return None
        return [((X - _q(p)) * (X - _q(q)) / (X - _q(r)), ">")]
    if statement_key == _RAT_HARD_DEN:
        p, q, r = (params.get(name) for name in ("p", "q", "r"))
        if None in (p, q, r) or min(p, q, r) <= 0 or len({p, q, r}) != 3:
            return None
        return [((X - _q(p)) / ((X - _q(q)) * (X - _q(r))), ">")]
    return None


TOPICS = {
    FirstDegreeInequality.id: FirstDegreeInequality(),
    SecondDegreeInequality.id: SecondDegreeInequality(),
    RationalInequality.id: RationalInequality(),
}
