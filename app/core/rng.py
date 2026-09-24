"""Seeded RNG discipline (STRUCTURE §6).

The seed is derived from a *string* on purpose: ``random.Random(str)`` is stable
across processes, while ``hash()`` is salted per interpreter — using it would
silently break reproducibility between a request and a replay after a pod restart.
"""

from __future__ import annotations

import random


def seed_token(seed: int, topic: str, difficulty: str, index: int, attempt: int = 0) -> str:
    """The exact tuple that makes an item reproducible.

    ``attempt`` is 0 for the primary candidate; retries append it so that a seed
    which fails verification does not retry the identical item forever.
    """
    base = f"{seed}:{topic}:{difficulty}:{index}"
    return base if attempt == 0 else f"{base}:{attempt}"


def make_rng(seed: int, topic: str, difficulty: str, index: int, attempt: int = 0) -> random.Random:
    return random.Random(seed_token(seed, topic, difficulty, index, attempt))
