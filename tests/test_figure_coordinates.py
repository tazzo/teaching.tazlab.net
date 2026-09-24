"""The wire contract the browser's figure renderer depends on.

Figure coordinates cross the wire as canonical exact rationals (``"7/2"``, ``"-3"``,
``"0"``). The client turns them into floats at the boundary — and it must do so with an
exact parser, because ``Number("21/4")`` is ``NaN``: that is how every trace of a graph
once collapsed to nothing while its legend, its axis and its vertices were all drawn.

The server-side checks could not see it: they parse with ``Fraction``, which reads ``a/b``
happily. So this test asserts the *shape* of what is sent, for every topic and for the
figure elements the older test does not know about (guides, vertices).
"""

from __future__ import annotations

import re
from fractions import Fraction

import pytest

from app.core.rng import make_rng
from app.generators.registry import TOPICS

DIFFICULTIES = ("easy", "medium", "hard")
SEEDS = (1, 7, 42)
# integers and rationals, and nothing else: no decimals, no exponents, no empty string
RATIONAL = re.compile(r"^-?\d+(/\d+)?$")


def coordinates(figure: dict) -> list[tuple[str, str]]:
    """Every coordinate the client will parse, with where it came from."""
    found: list[tuple[str, str]] = []
    for trace in figure.get("traces", []):
        for x, y in trace["samples"]:
            found.append((x, f"trace:{trace.get('kind')}:x"))
            found.append((y, f"trace:{trace.get('kind')}:y"))
    for vertex in figure.get("vertices", []):
        found.append((vertex["at"][0], "vertex:x"))
        found.append((vertex["at"][1], "vertex:y"))
    for marker in figure.get("markers", []):
        found.append((marker["at"][0], "marker:x"))
        found.append((marker["at"][1], "marker:y"))
    for guide in figure.get("guides", []):
        found.append((guide["at"], "guide"))
    for phase in figure.get("phases", []):
        found.append((phase["t_from"], "phase:t_from"))
        found.append((phase["t_to"], "phase:t_to"))
    domain = figure.get("domain", {})
    for key, value in domain.items():
        found.append((value, f"domain:{key}"))
    return found


def test_every_coordinate_is_a_canonical_rational():
    checked = 0
    for topic_id, topic in sorted(TOPICS.items()):
        for difficulty in DIFFICULTIES:
            for seed in SEEDS:
                item = topic.generate(make_rng(seed, topic.id, difficulty, 0), difficulty, seed, 0)
                if not item.figure:
                    continue
                for value, origin in coordinates(item.figure):
                    checked += 1
                    assert RATIONAL.match(value), (
                        f"{topic_id} {difficulty} seed {seed} {origin}={value!r} is not a "
                        f"canonical rational: the client's parser would reject it")
                    assert str(Fraction(value)) == value, (
                        f"{topic_id} {origin}={value!r} is not in canonical form")
    assert checked > 100, "the sweep must cover the real figures"


def test_the_client_parser_accepts_every_coordinate():
    """The two forms the client must handle, exercised exactly as it does."""
    def to_number(value: str) -> float:                   # mirrors web/src/figure.js
        rational = re.match(r"^(-?\d+)/(\d+)$", value)
        return int(rational.group(1)) / int(rational.group(2)) if rational else float(value)

    for value in ("0", "-3", "7/2", "-21/4", "14"):
        assert to_number(value) == pytest.approx(float(Fraction(value)))
    with pytest.raises(ValueError):
        to_number("")
