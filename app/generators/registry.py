"""Topic registry — the only place topic ids exist (STRUCTURE §3)."""

from __future__ import annotations

from typing import Protocol

from app.generators.math.first_degree import TOPIC as FIRST_DEGREE


class Topic(Protocol):
    id: str
    family: str          # "math" | "physics"
    difficulties: tuple[str, ...]
    label_key: str
    scenarios: tuple[str, ...]


TOPICS: dict[str, Topic] = {
    FIRST_DEGREE.id: FIRST_DEGREE,
}
