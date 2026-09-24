"""The contract every topic implements (STRUCTURE §3)."""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from fractions import Fraction
from typing import Protocol

from app.core.verify import VerificationResult


@dataclass(frozen=True)
class Step:
    label_key: str
    latex: str
    note_key: str | None = None


@dataclass(frozen=True)
class Answer:
    latex: str
    kind: str                                   # value | set | interval | region | scalar_with_unit
    payload: dict[str, list[str]] = field(default_factory=dict)


@dataclass(frozen=True)
class Item:
    topic: str
    difficulty: str
    seed: int
    index: int
    params: dict[str, Fraction]                 # exact; stringified only at the wire
    statement_key: str
    steps: tuple[Step, ...]
    answer: Answer
    figure: dict | None = None


class Topic(Protocol):
    id: str
    family: str                                 # "math" | "physics"
    difficulties: tuple[str, ...]
    label_key: str
    scenarios: tuple[str, ...]

    # `options` carries the page configurator's choices (STRUCTURE §4.2). Topics that
    # expose a configurator validate them through `validate_options`; every other topic
    # accepts the argument and ignores it, so one call site serves both kinds.
    def generate(self, rng: random.Random, difficulty: str, seed: int, index: int,
                 options: dict | None = None) -> Item: ...
    def verify(self, item: Item) -> VerificationResult: ...
    def validate_options(self, options: dict) -> dict: ...


def wire_params(params: dict[str, Fraction]) -> dict[str, str]:
    """Exact rationals cross the wire as strings — never floats."""
    return {key: str(value) for key, value in sorted(params.items())}
