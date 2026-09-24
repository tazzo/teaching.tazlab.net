"""HTTP surface (STRUCTURE §4)."""

from __future__ import annotations

import logging

from fastapi import APIRouter

from app.api.schemas import Catalog, Health, TopicInfo
from app.generators.registry import TOPICS

router = APIRouter(prefix="/api")
logger = logging.getLogger("teaching.api")

VERSION = "0.1.0"


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
