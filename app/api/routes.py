"""HTTP surface (STRUCTURE §4)."""

from __future__ import annotations

import logging
import os
import time

from fastapi import APIRouter, HTTPException, Query, Request

from app.api.schemas import (
    Catalog,
    GenerateResponse,
    Health,
    TopicInfo,
    WireAnswer,
    WireItem,
    WireStatement,
    WireStep,
)
from app.core.rng import make_rng
from app.generators.base import Item, wire_params
from app.generators.registry import TOPICS

router = APIRouter(prefix="/api")
logger = logging.getLogger("teaching.api")

VERSION = "0.1.0"
MAX_ATTEMPTS = int(os.getenv("TEACHING_MAX_ATTEMPTS", "8"))
MAX_COUNT = 20


def _failure(request: Request, status: int, code: str, detail: str | None = None) -> HTTPException:
    return HTTPException(
        status_code=status,
        detail={"error": {"code": code, "message_key": f"error.{code}", "detail": detail}},
    )


def _to_wire(item: Item) -> WireItem:
    return WireItem(
        index=item.index,
        statement=WireStatement(key=item.statement_key, params=wire_params(item.params)),
        steps=[WireStep(label_key=s.label_key, latex=s.latex, note_key=s.note_key) for s in item.steps],
        answer=WireAnswer(latex=item.answer.latex, kind=item.answer.kind, payload=item.answer.payload),
        figure=item.figure,
    )


@router.get("/healthz", response_model=Health)
async def healthz() -> Health:
    # DEBUG on purpose: probes must not flood the log stream (DESIGN §2.11).
    logger.debug("health check")
    return Health(version=VERSION)


@router.get("/catalog", response_model=Catalog)
async def catalog() -> Catalog:
    topics = [
        TopicInfo(
            id=topic.id,
            family=topic.family,
            difficulties=list(topic.difficulties),
            label_key=topic.label_key,
            scenarios=list(getattr(topic, "scenarios", ())),
        )
        for topic in sorted(TOPICS.values(), key=lambda item: item.id)
    ]
    logger.info("catalog served", extra={"topic_count": len(topics)})
    return Catalog(topics=topics)


@router.get("/generate", response_model=GenerateResponse)
async def generate(
    request: Request,
    topic: str = Query(...),
    difficulty: str = Query(...),
    seed: int = Query(...),
    count: int = Query(5, ge=1, le=MAX_COUNT),
) -> GenerateResponse:
    impl = TOPICS.get(topic)
    if impl is None:
        raise _failure(request, 400, "unknown_topic", topic)
    if difficulty not in impl.difficulties:
        raise _failure(request, 400, "invalid_difficulty", difficulty)

    started = time.perf_counter()
    items: list[WireItem] = []
    discarded: list[str] = []

    for index in range(count):
        item = None
        last_reason = "no_attempt"
        for attempt in range(MAX_ATTEMPTS):
            rng = make_rng(seed, topic, difficulty, index, attempt)
            candidate = impl.generate(rng, difficulty, seed, index)
            result = impl.verify(candidate)
            if result.ok:
                item = candidate
                break
            last_reason = result.reason or "unknown"
            # A discarded item is a bug signal, not noise (DESIGN §2.11).
            logger.warning(
                "item discarded",
                extra={
                    "topic": topic,
                    "difficulty": difficulty,
                    "seed": seed,
                    "index": index,
                    "attempt": attempt + 1,
                    "reason": last_reason,
                },
            )
        if item is None:
            discarded.append(f"{index}:{last_reason}")
            continue
        items.append(_to_wire(item))

    if discarded:
        logger.error(
            "generation_failed: verification budget exhausted",
            extra={"topic": topic, "difficulty": difficulty, "seed": seed,
                   "discarded": discarded, "max_attempts": MAX_ATTEMPTS},
        )
        raise _failure(request, 503, "generation_failed", ",".join(discarded))

    logger.info(
        "generated",
        extra={
            "topic": topic,
            "difficulty": difficulty,
            "seed": seed,
            "count": len(items),
            "duration_ms": round((time.perf_counter() - started) * 1000, 2),
        },
    )
    return GenerateResponse(topic=topic, difficulty=difficulty, seed=seed, items=items)
