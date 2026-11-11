"""Topic registry — the only place topic ids exist (STRUCTURE §3)."""

from __future__ import annotations

from typing import Protocol

from app.generators.english.present_perfect import TOPIC as PRESENT_PERFECT
from app.generators.english.present_perfect_medium import TOPIC as PRESENT_PERFECT_MEDIUM
from app.generators.english.present_perfect_simple_continuous import (
    TOPIC as PRESENT_PERFECT_SIMPLE_CONTINUOUS,
)
from app.generators.english.relative_classification import TOPIC as RELATIVE_CLASSIFICATION
from app.generators.english.relative_clauses import TOPIC as RELATIVE_CLAUSES
from app.generators.english.relative_defining_non_defining import (
    TOPIC as RELATIVE_DEFINING_NON_DEFINING,
)
from app.generators.math.first_degree import TOPIC as FIRST_DEGREE
from app.generators.math.fractional import TOPIC as FRACTIONAL
from app.generators.math.inequalities import TOPICS as INEQUALITY_TOPICS
from app.generators.math.second_degree import TOPIC as SECOND_DEGREE
from app.generators.math.systems import TOPICS as SYSTEM_TOPICS
from app.generators.math.systems_inequalities import TOPIC as SYSTEM_INEQUALITIES
from app.generators.physics.accelerated import TOPIC as ACCELERATED
from app.generators.physics.circular import TOPIC as CIRCULAR
from app.generators.physics.multi_phase import TOPIC as MULTI_PHASE
from app.generators.physics.relative import TOPIC as RELATIVE
from app.generators.physics.segments import TOPIC as SEGMENTS
from app.generators.physics.uniform import TOPIC as UNIFORM


class Topic(Protocol):
    id: str
    family: str          # "math" | "physics" | "english"
    difficulties: tuple[str, ...]
    label_key: str
    scenarios: tuple[str, ...]


TOPICS: dict[str, Topic] = {
    # english — grammar
    PRESENT_PERFECT.id: PRESENT_PERFECT,
    PRESENT_PERFECT_MEDIUM.id: PRESENT_PERFECT_MEDIUM,
    PRESENT_PERFECT_SIMPLE_CONTINUOUS.id: PRESENT_PERFECT_SIMPLE_CONTINUOUS,
    RELATIVE_CLAUSES.id: RELATIVE_CLAUSES,
    RELATIVE_DEFINING_NON_DEFINING.id: RELATIVE_DEFINING_NON_DEFINING,
    RELATIVE_CLASSIFICATION.id: RELATIVE_CLASSIFICATION,
    # mathematics — equations
    FIRST_DEGREE.id: FIRST_DEGREE,
    SECOND_DEGREE.id: SECOND_DEGREE,
    FRACTIONAL.id: FRACTIONAL,
    # mathematics — inequalities and systems
    **INEQUALITY_TOPICS,
    **SYSTEM_TOPICS,
    SYSTEM_INEQUALITIES.id: SYSTEM_INEQUALITIES,
    # physics — kinematics
    UNIFORM.id: UNIFORM,
    ACCELERATED.id: ACCELERATED,
    CIRCULAR.id: CIRCULAR,
    MULTI_PHASE.id: MULTI_PHASE,
    RELATIVE.id: RELATIVE,
    SEGMENTS.id: SEGMENTS,
}
