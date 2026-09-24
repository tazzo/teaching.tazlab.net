"""Golden-file harness for LaTeX output (task C.9).

Why this exists: ``latex()`` is not a versioned contract across SymPy bumps. Without a
golden file, an upgrade can silently change how a formula is rendered — and the only
person who notices is a teacher looking at a printed sheet.

Regenerate deliberately: ``TEACHING_UPDATE_GOLDEN=1 python -m pytest tests/test_latex_golden.py``
then inspect the diff before committing it.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

from app.core.rng import make_rng
from app.generators.registry import TOPICS

GOLDEN = Path(__file__).resolve().parent / "latex.json"


def collect() -> dict[str, list[str]]:
    """One deterministic item per (topic, difficulty); every LaTeX string it emits."""
    snapshot: dict[str, list[str]] = {}
    for topic_id in sorted(TOPICS):
        topic = TOPICS[topic_id]
        for difficulty in topic.difficulties:
            rng = make_rng(4242, topic_id, difficulty, 0)
            item = topic.generate(rng, difficulty, 4242, 0)
            strings = [step.latex for step in item.steps] + [item.answer.latex]
            snapshot[f"{topic_id}|{difficulty}"] = strings
    return snapshot


def load() -> dict[str, list[str]]:
    if not GOLDEN.exists():
        return {}
    return json.loads(GOLDEN.read_text(encoding="utf-8"))


def save(snapshot: dict[str, list[str]]) -> None:
    GOLDEN.write_text(json.dumps(snapshot, indent=2, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")


def updating() -> bool:
    return os.getenv("TEACHING_UPDATE_GOLDEN") == "1"
