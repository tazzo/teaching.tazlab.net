"""The rendered statement must agree with the answer.

Written after a real defect: a hand-authored template displayed ``x² + 2x + 8 = 0`` while
the answer said ``x = -4, x = 2``. A question whose printed equation does not have the
printed solution is worse than no question, and no amount of placeholder checking catches
it — the text has to be parsed back and solved.
"""

from __future__ import annotations

import re

import pytest
from sympy import Symbol, solveset, S, sympify
from sympy.core.sorting import default_sort_key

from app.core.rng import make_rng
from app.core.strings import load_strings, render_template
from app.generators.registry import TOPICS

X = Symbol("x")
STRINGS = load_strings("it")

# Topics whose statement is a single polynomial equation in x, plus the operator to use
# when turning the rendered text back into ``lhs = 0``.
EQUATION_TOPICS = ("math.equations.first_degree", "math.equations.second_degree")


def rendered_equation(item) -> str:
    """The displayed equation as a SymPy expression: normalise the human notation first."""
    text = render_template(STRINGS[item.statement_key], {k: str(v) for k, v in item.params.items()})
    body = text.split(":", 1)[1].strip()
    lhs, _, rhs = body.rpartition("=")
    expression = f"({lhs}) - ({rhs})"
    expression = expression.replace("²", "**2").replace("−", "-")
    expression = re.sub(r"(?<=\d)(?=[a-z])", "*", expression)      # 5x -> 5*x
    expression = re.sub(r"(?<=[a-z\)])(?=[a-z(])", "*", expression)  # x( -> x*(, )( -> )*(
    return expression


@pytest.mark.parametrize("topic_id", EQUATION_TOPICS)
def test_displayed_equation_has_the_given_roots(topic_id: str) -> None:
    topic = TOPICS[topic_id]
    checked = 0
    for difficulty in topic.difficulties:
        for attempt in range(4):
            item = topic.generate(make_rng(attempt, topic_id, difficulty, 0), difficulty, attempt, 0)
            # the payload carries exact values in SymPy's own text form ("-3 + sqrt(5)")
            claimed = [sympify(value) for value in item.answer.payload.get("solutions", [])]
            if not claimed:
                continue                       # "no real solution" cases have nothing to match
            expression = sympify(rendered_equation(item).replace("²", "**2").replace("−", "-"))
            found = solveset(expression, X, domain=S.Reals)
            assert found is not S.EmptySet, f"{topic_id}/{difficulty}: displayed equation has no real roots"
            found = sorted(found, key=default_sort_key)
            assert found == sorted(claimed, key=default_sort_key), (
                f"{topic_id}/{difficulty}: displayed {rendered_equation(item)!r} "
                f"has roots {found}, answer claims {claimed}"
            )
            checked += 1
    assert checked, f"{topic_id}: nothing was checked"
