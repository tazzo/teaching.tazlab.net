"""Physics generators: exactness, physics predicates, and figure/model agreement."""

from __future__ import annotations

from fractions import Fraction

import pytest

from app.core.rng import make_rng
from app.core.units import convert, speed_of_sound
from app.generators.physics.accelerated import TOPIC as ACCELERATED
from app.generators.physics.uniform import TOPIC as UNIFORM


def make(topic, difficulty: str, seed: int = 11):
    rng = make_rng(seed, topic.id, difficulty, 0)
    return topic.generate(rng, difficulty, seed, 0)


def test_conversions_are_exact() -> None:
    assert convert(Fraction(36), "km/h", "m/s") == Fraction(10)
    assert convert(Fraction(1), "h", "s") == Fraction(3600)
    assert convert(Fraction(1500), "m", "km") == Fraction(3, 2)
    assert speed_of_sound() == Fraction(343)


@pytest.mark.parametrize("difficulty", ["easy", "medium", "hard"])
def test_uniform_verifies_and_figure_matches(difficulty: str) -> None:
    item = make(UNIFORM, difficulty)
    assert UNIFORM.verify(item).ok, UNIFORM.verify(item).reason


@pytest.mark.parametrize("difficulty", ["easy", "medium", "hard"])
def test_accelerated_verifies(difficulty: str) -> None:
    item = make(ACCELERATED, difficulty)
    assert ACCELERATED.verify(item).ok, ACCELERATED.verify(item).reason


def test_physics_figures_carry_exact_string_coordinates() -> None:
    figure = make(UNIFORM, "easy").figure
    assert figure["kind"] == "kinematics"
    for x, y in figure["traces"][0]["samples"]:
        assert isinstance(x, str) and isinstance(y, str)
        Fraction(x), Fraction(y)          # must parse as exact rationals


def test_wrong_physical_claim_is_rejected() -> None:
    item = make(UNIFORM, "easy")
    corrupted = type(item)(**{**item.__dict__,
                              r"answer": type(item.answer)(r"s = 1\,\text{m}", "scalar_with_unit",
                                                          {"value": ["1"], "unit": ["m"]})})
    assert not UNIFORM.verify(corrupted).ok


def test_figure_disagreeing_with_the_model_is_rejected() -> None:
    item = make(UNIFORM, "easy")
    tampered_figure = {**item.figure,
                       "traces": [{"label_key": "trace.position", "samples": [["0", "0"], ["1", "999"]]}]}
    tampered = type(item)(**{**item.__dict__, "figure": tampered_figure})
    result = UNIFORM.verify(tampered)
    assert not result.ok and result.reason == "figure_disagrees_with_model"


def test_missing_figure_is_rejected() -> None:
    item = make(ACCELERATED, "easy")
    assert not ACCELERATED.verify(type(item)(**{**item.__dict__, "figure": None})).ok
