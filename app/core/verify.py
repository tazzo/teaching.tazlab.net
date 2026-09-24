"""Shared verification predicates (STRUCTURE §5).

The contract they exist to enforce: a verifier that cannot fail is worse than no
verifier, because it looks like a guarantee. ``tests/test_verification.py`` proves
these can reject a deliberately corrupted item.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

from sympy import ConditionSet, Expr, Float, S, Symbol, checksol, solveset
from sympy.core.sorting import default_sort_key

logger = logging.getLogger("teaching.verify")


@dataclass(frozen=True)
class VerificationResult:
    ok: bool
    reason: str | None = None


def no_floats(*exprs: Expr) -> bool:
    """Exact arithmetic only: a single float leaks into the printed answer."""
    return not any(e.atoms(Float) for e in exprs)


def satisfies(expr: Expr, symbol: Symbol, value: Expr) -> bool:
    """Substitute and demand a definite True — ``checksol`` is three-valued.

    The 3-positional dict form raises TypeError on SymPy 1.14, so the mapping
    form is the one used here.
    """
    verdict = checksol(expr, {symbol: value})
    return verdict is True


def real_solutions(expr: Expr, symbol: Symbol) -> list[Expr] | None:
    """Sorted real solutions, or None when SymPy cannot decide.

    ``solveset(..., domain=S.Reals)`` is the only API that admits "I don't know"
    (``ConditionSet``) instead of returning a plausible-looking empty list.
    """
    result = solveset(expr, symbol, domain=S.Reals)
    if isinstance(result, ConditionSet):
        logger.warning("solveset returned ConditionSet: undecidable", extra={"expr": str(expr)})
        return None
    if result is S.EmptySet:
        return []
    if hasattr(result, "__iter__") and not isinstance(result, (Expr,)):
        return sorted(result, key=default_sort_key)
    return [result]


def solutions_match(expr: Expr, symbol: Symbol, expected: list[Expr]) -> VerificationResult:
    """Compare a claimed solution set with an independently recomputed one."""
    if not no_floats(expr, *expected):
        return VerificationResult(False, "float_atom")
    recomputed = real_solutions(expr, symbol)
    if recomputed is None:
        return VerificationResult(False, "undecidable")
    if sorted(recomputed, key=default_sort_key) != sorted(expected, key=default_sort_key):
        return VerificationResult(False, "solution_set_mismatch")
    for value in expected:
        if not satisfies(expr, symbol, value):
            return VerificationResult(False, "root_does_not_satisfy")
    return VerificationResult(True)
