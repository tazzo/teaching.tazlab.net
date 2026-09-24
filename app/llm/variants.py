"""The LLM-assisted variant path: propose, then verify, then degrade gracefully.

    scenario + difficulty + count
      → one provider call returns N specs        # similarity comes from the scenario
      → spec validation                          # units, magnitudes, a unit-bearing ask
      → spec_to_item + topic.verify()            # the model never produces the answer
      → Item(…) or template fallback             # degraded=true when nothing survived

Degradation is normal, not an error (DESIGN §2.5): an unavailable provider, a timeout, an
empty answer or an invalid spec falls back to the deterministic template generator for the
same scenario, and the caller is told. This module never raises on provider failure.

The scenario is the *shape*, not a label: each scenario id already corresponds to one
difficulty whose verification predicates are the ones ``Topic.verify()`` branches on
(``uniform_graph_reading`` is the hard uniform shape). The requested ``difficulty`` is
therefore used only on the deterministic fallback path; a client asking for a shape that
does not exist still gets a well-formed item of the scenario's own shape rather than a
degraded one.
"""

from __future__ import annotations

import hashlib
import logging
import os

from app.core.rng import make_rng
from app.generators.base import Item
from app.generators.physics.variants import spec_to_item
from app.generators.registry import TOPICS
from app.llm.client import LLMClient, fetch_variant_specs_report
from app.llm.spec import SCENARIOS, SpecError

logger = logging.getLogger("teaching.llm")

MAX_ATTEMPTS = int(os.getenv("TEACHING_MAX_ATTEMPTS", "8"))


def fallback_seed(scenario: str, difficulty: str) -> int:
    """A deterministic seed for the template fallback — the request carries none.

    Seeded from the *string* (never ``hash()``, which is salted per interpreter), so the
    fallback sheet is reproducible across pod restarts.
    """
    digest = hashlib.sha256(f"variants:{scenario}:{difficulty}".encode()).digest()
    return int.from_bytes(digest[:8], "big")


def _topic_for_scenario(scenario: str):
    for topic in TOPICS.values():
        if scenario in getattr(topic, "scenarios", ()):
            return topic
    return None


def template_items(topic, difficulty: str, count: int, seed: int) -> list[Item]:
    """The deterministic baseline — exactly the ``/api/generate`` loop, bounded.

    This is the safety net, so it may not itself fall over: a verifier that *raises*
    (several do, on a missing param key) is treated as a discard and the next attempt is
    tried, rather than escaping and turning a degraded answer into a crashed request.
    """
    items: list[Item] = []
    for index in range(count):
        for attempt in range(MAX_ATTEMPTS):
            rng = make_rng(seed, topic.id, difficulty, index, attempt)
            try:
                candidate = topic.generate(rng, difficulty, seed, index)
                result = topic.verify(candidate)
                ok, reason = bool(result.ok), result.reason
            except Exception as exc:  # noqa: BLE001 - see docstring
                ok, reason = False, f"raised:{type(exc).__name__}"
            if ok:
                items.append(candidate)
                break
            logger.warning(
                "item discarded",
                extra={"topic": topic.id, "difficulty": difficulty, "seed": seed, "index": index,
                       "attempt": attempt + 1, "reason": reason, "source": "template_fallback"},
            )
    return items


async def generate_variants(
    scenario: str,
    difficulty: str,
    count: int,
    *,
    client: LLMClient | None = None,
    seed: int | None = None,
) -> tuple[list[Item], bool, str | None]:
    """``(items, degraded, reason)`` — never raises; ``degraded`` means template items."""
    if count < 1:
        return [], True, "invalid_count"

    fallback = seed if seed is not None else fallback_seed(scenario, difficulty)
    declared = SCENARIOS.get(scenario)

    if declared is None:
        topic = _topic_for_scenario(scenario)
        if topic is None:
            logger.warning("variants degraded", extra={"scenario": scenario, "reason": "unknown_scenario"})
            return [], True, "unknown_scenario"
        # A catalog scenario with no variant builder yet: serve the template at the
        # requested difficulty when the topic supports it, at its own shape otherwise.
        fallback_difficulty = difficulty if difficulty in topic.difficulties else topic.difficulties[0]
        items = template_items(topic, fallback_difficulty, count, fallback)
        logger.warning(
            "variants degraded",
            extra={"scenario": scenario, "reason": "no_variant_for_scenario",
                   "difficulty": fallback_difficulty, "items": len(items)},
        )
        return items, True, "no_variant_for_scenario"

    topic = TOPICS[declared.topic_id]
    outcome = await fetch_variant_specs_report(scenario, difficulty, count, client=client)

    items: list[Item] = []
    discarded: list[str] = []
    for spec in outcome.specs:
        if len(items) >= count:
            break
        try:
            # Solving *and* verification live behind this call: an item that cannot be
            # verified is discarded, never silently repaired (DESIGN §2.5).
            items.append(spec_to_item(spec, seed=fallback, index=len(items)))
        except SpecError as exc:
            discarded.append(exc.reason)
            logger.warning(
                "variant spec discarded",
                extra={"scenario": scenario, "reason": exc.reason, "detail": exc.detail},
            )

    if outcome.error is None and items:
        logger.info(
            "variants served",
            extra={"scenario": scenario, "requested": count, "accepted": len(items),
                   "rejected_specs": len(outcome.rejected), "discarded_items": len(discarded),
                   "attempts": outcome.attempts, "degraded": False},
        )
        return items, False, None

    reason = outcome.error or f"invalid_specs:{len(outcome.rejected) + len(discarded)}"
    degraded_items = template_items(topic, declared.difficulty, count, fallback)
    logger.warning(
        "variants degraded",
        extra={"scenario": scenario, "reason": reason, "provider_error": outcome.error,
               "rejected_specs": len(outcome.rejected), "discarded_items": len(discarded),
               "items": len(degraded_items)},
    )
    return degraded_items, True, reason
