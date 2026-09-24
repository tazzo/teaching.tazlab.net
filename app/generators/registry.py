"""Topic registry — the only place topic ids exist (STRUCTURE §3)."""

from __future__ import annotations

from typing import Protocol


class Topic(Protocol):
    id: str
    family: str          # "math" | "physics"
    difficulties: tuple[str, ...]
    label_key: str
    scenarios: tuple[str, ...]


# Populated by the topic modules (Phase C).
TOPICS: dict[str, Topic] = {}
