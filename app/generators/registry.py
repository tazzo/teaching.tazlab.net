"""Topic registry — the only place topic ids exist (STRUCTURE §3)."""

from __future__ import annotations

from typing import Protocol

from app.generators.math.first_degree import TOPIC as FIRST_DEGREE
from app.generators.physics.accelerated import TOPIC as ACCELERATED
from app.generators.physics.circular import TOPIC as CIRCULAR
from app.generators.physics.multi_phase import TOPIC as MULTI_PHASE
from app.generators.physics.relative import TOPIC as RELATIVE
from app.generators.physics.uniform import TOPIC as UNIFORM


class Topic(Protocol):
    id: str
    family: str          # "math" | "physics"
    difficulties: tuple[str, ...]
    label_key: str
    scenarios: tuple[str, ...]


TOPICS: dict[str, Topic] = {
    FIRST_DEGREE.id: FIRST_DEGREE,
    UNIFORM.id: UNIFORM,
    ACCELERATED.id: ACCELERATED,
    CIRCULAR.id: CIRCULAR,
    MULTI_PHASE.id: MULTI_PHASE,
    RELATIVE.id: RELATIVE,
}
