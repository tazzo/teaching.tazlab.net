"""The single place where SymPy expressions become LaTeX.

Nothing else in the codebase may format mathematics: one renderer means the screen
(KaTeX) and the PDF (WeasyPrint + KaTeX) always agree, and a SymPy upgrade that
changes rendering fails a golden test instead of surprising a teacher.
"""

from __future__ import annotations

from collections.abc import Iterable

from sympy import Expr, latex as _sympy_latex
from sympy.core.sorting import default_sort_key


def to_latex(expr: Expr | int) -> str:
    return _sympy_latex(expr)


def sorted_by_math(exprs: Iterable[Expr]) -> list[Expr]:
    """Deterministic order for anything set-derived (FiniteSet is unordered)."""
    return sorted(exprs, key=default_sort_key)


def join_latex(exprs: Iterable[Expr], separator: str = ", \\; ") -> str:
    return separator.join(to_latex(e) for e in sorted_by_math(exprs))
