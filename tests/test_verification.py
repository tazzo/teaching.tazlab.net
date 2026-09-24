"""The verifier must be able to FAIL — otherwise it is decoration, not a guarantee."""

from __future__ import annotations

from fractions import Fraction

import pytest

from app.core.rng import make_rng
from app.generators.math.first_degree import TOPIC


def make_item(difficulty: str = "easy"):
    rng = make_rng(7, TOPIC.id, difficulty, 0)
    return TOPIC.generate(rng, difficulty, 7, 0)


@pytest.mark.parametrize("difficulty", ["easy", "medium", "hard"])
def test_honest_item_verifies(difficulty: str) -> None:
    assert TOPIC.verify(make_item(difficulty)).ok


def test_corrupted_answer_is_rejected() -> None:
    item = make_item()
    corrupted = type(item)(
        **{**item.__dict__, "answer": type(item.answer)(
            latex="x = 999", kind="value", payload={"solutions": ["999"]}
        )}
    )
    result = TOPIC.verify(corrupted)
    assert not result.ok
    assert result.reason in {"root_does_not_satisfy", "solution_set_mismatch"}


def test_float_parameters_are_rejected() -> None:
    item = make_item()
    with_floats = type(item)(**{**item.__dict__, "params": {**item.params, "a": Fraction(3, 2)}})
    assert TOPIC.verify(with_floats).ok is False


def test_degenerate_identity_is_rejected() -> None:
    item = make_item()
    degenerate = type(item)(**{**item.__dict__, "params": {"a": Fraction(0), "b": Fraction(0), "solution": Fraction(0)}})
    assert not TOPIC.verify(degenerate).ok
