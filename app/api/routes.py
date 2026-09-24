"""HTTP surface (STRUCTURE §4)."""

from __future__ import annotations

import json
import logging
import os
import time
from fractions import Fraction

from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import Response

from app.api.schemas import (
    Catalog,
    ExportRequest,
    GenerateResponse,
    Health,
    PageInfo,
    PagesResponse,
    TopicInfo,
    VariantsRequest,
    VariantsResponse,
    WireAnswer,
    WireItem,
    WireStatement,
    WireStep,
)
from app.core.rng import make_rng
from app.core.strings import load_strings
from app.generators.base import Answer, Item, Step, wire_params
from app.generators.registry import TOPICS
from app.pages import MACROS, PAGES, pages_for, subs

router = APIRouter(prefix="/api")
logger = logging.getLogger("teaching.api")

VERSION = "0.1.0"
MAX_ATTEMPTS = int(os.getenv("TEACHING_MAX_ATTEMPTS", "8"))
MAX_COUNT = 20


def _fail(status: int, code: str, detail: str | None = None) -> HTTPException:
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


def _from_wire(topic_id: str, difficulty: str, seed: int, wire: WireItem) -> Item:
    """Rebuild an internal Item from posted wire data so it can be re-verified.

    Posted items are untrusted input on a public, ungated endpoint: they are never
    rendered straight to PDF (STRUCTURE §4.4).
    """
    return Item(
        topic=topic_id,
        difficulty=difficulty,
        seed=seed,
        index=wire.index,
        params={key: Fraction(value) for key, value in wire.statement.params.items()},
        statement_key=wire.statement.key,
        steps=tuple(Step(s.label_key, s.latex, s.note_key) for s in wire.steps),
        answer=Answer(
            latex=wire.answer.latex,
            kind=wire.answer.kind,
            payload={key: list(values) for key, values in wire.answer.payload.items()},
        ),
        figure=wire.figure,
    )


@router.get("/healthz", response_model=Health)
async def healthz() -> Health:
    # DEBUG on purpose: probes must not flood the log stream (DESIGN §2.11).
    logger.debug("health check")
    return Health(version=VERSION)


@router.get("/i18n")
async def i18n() -> dict[str, str]:
    """The label table, so the frontend and the PDF share one source of truth."""
    try:
        return load_strings("it")
    except FileNotFoundError as exc:  # a packaging bug, not a client error
        logger.error("strings missing", extra={"error": str(exc)})
        raise _fail(500, "strings_unavailable") from exc


def _hidden_figure(figure: dict) -> dict:
    """Strip the answer but keep the frame: axes, units and the scale to draw on.

    A "fill in the empty graph" page needs a grid the student can plot on. The scale is
    not the answer — the problem statement already gives the data — but without it the
    grid would have no meaningful extent.
    """
    ys: list[Fraction] = []
    for trace in figure.get("traces", []):
        ys.extend(Fraction(y) for _, y in trace.get("samples", []))
    ys.extend(Fraction(marker["at"][1]) for marker in figure.get("markers", []))
    hidden = {**figure, "traces": [], "markers": [], "vectors": []}
    # the stripped trace still tells us what the student is expected to plot
    if figure.get("traces"):
        hidden["y_label"] = figure["traces"][0].get("label_key")
    if ys:
        hidden["y_range"] = [str(min(ys)), str(max(ys))]
    return hidden


def _configurer(topic) -> list[dict]:
    """The topic's own description of its configurator; topics without one return []."""
    configurer = getattr(topic, "configurer", None)
    return configurer() if configurer is not None else []


@router.get("/pages", response_model=PagesResponse)
async def pages() -> PagesResponse:
    """The information architecture: macros -> sub-topics -> pages."""
    known = set(TOPICS)
    available = [p for p in PAGES if p.topic in known]
    return PagesResponse(
        macros=[m for m in MACROS if any(p.macro == m for p in available)],
        subs={m: [s for s in subs(m) if pages_for(m, s)] for m in MACROS},
        pages=[
            PageInfo(id=p.id, macro=p.macro, sub=p.sub, kind=p.kind, topic=p.topic,
                     difficulty=p.difficulty,
                     difficulties=list(TOPICS[p.topic].difficulties) if p.topic in known else [],
                     label_key=p.label_key,
                     # the configurator a page exposes, described by its own topic
                     config=(_configurer(TOPICS[p.topic]) if p.configurable and p.topic in known
                             else []),
                     defaults=(TOPICS[p.topic].default_options()
                               if p.configurable and p.topic in known
                               and hasattr(TOPICS[p.topic], "default_options") else {}))
            for p in available
        ],
    )


@router.get("/catalog", response_model=Catalog)
async def catalog() -> Catalog:
    topics = [
        TopicInfo(
            id=topic.id,
            family=topic.family,
            difficulties=list(topic.difficulties),
            label_key=topic.label_key,
            scenarios=list(getattr(topic, "scenarios", ())),
            # a topic with a figure belongs to the graph area too; the figure is a
            # property of the generated item, so only the family can decide it here
            modes=["problemi", "grafici"] if topic.family == "physics" else ["problemi"],
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
    # "full" draws the figure; "hidden" keeps the axes and drops every trace and marker,
    # which is what a "fill in the empty graph" page needs (the solution is fetched
    # separately from the same seed, so the two calls describe the same item).
    figure: str = Query("full", pattern="^(full|hidden)$"),
    # The page configurator's choices, as a JSON object (STRUCTURE §4.2). Part of the
    # item's identity: the same seed with different options is a different exercise.
    options: str | None = Query(None, max_length=512),
) -> GenerateResponse:
    impl = TOPICS.get(topic)
    if impl is None:
        raise _fail(400, "unknown_topic", topic)
    if difficulty not in impl.difficulties:
        raise _fail(400, "invalid_difficulty", difficulty)

    raw_options: dict = {}
    if options:
        try:
            raw_options = json.loads(options)
        except json.JSONDecodeError as exc:
            raise _fail(400, "invalid_options_json", str(exc)) from exc
        if not isinstance(raw_options, dict):
            raise _fail(400, "invalid_options_json", "options must be a JSON object")
    validator = getattr(impl, "validate_options", None)
    if validator is None:
        if raw_options:
            raise _fail(400, "options_not_supported", topic)
        resolved_options: dict = {}
    else:
        try:
            resolved_options = validator(raw_options)
        except ValueError as exc:
            raise _fail(400, "invalid_options", str(exc)) from exc

    started = time.perf_counter()
    items: list[WireItem] = []
    discarded: list[str] = []

    for index in range(count):
        item = None
        last_reason = "no_attempt"
        for attempt in range(MAX_ATTEMPTS):
            rng = make_rng(seed, topic, difficulty, index, attempt)
            candidate = impl.generate(rng, difficulty, seed, index, resolved_options)
            result = impl.verify(candidate)
            if result.ok:
                item = candidate
                break
            last_reason = result.reason or "unknown"
            # A discarded item is a bug signal, not noise (DESIGN §2.11).
            logger.warning(
                "item discarded",
                extra={"topic": topic, "difficulty": difficulty, "seed": seed, "index": index,
                       "attempt": attempt + 1, "reason": last_reason},
            )
        if item is None:
            discarded.append(f"{index}:{last_reason}")
            continue
        wire = _to_wire(item)
        if figure == "hidden" and wire.figure:
            wire.figure = _hidden_figure(wire.figure)
        items.append(wire)

    if discarded:
        logger.error(
            "generation_failed: verification budget exhausted",
            extra={"topic": topic, "difficulty": difficulty, "seed": seed,
                   "discarded": discarded, "max_attempts": MAX_ATTEMPTS},
        )
        raise _fail(503, "generation_failed", ",".join(discarded))

    logger.info("generated", extra={"topic": topic, "difficulty": difficulty, "seed": seed,
                                    "options": resolved_options or None,
                                    "count": len(items),
                                    "duration_ms": round((time.perf_counter() - started) * 1000, 2)})
    return GenerateResponse(topic=topic, difficulty=difficulty, seed=seed, items=items,
                            options=resolved_options)


@router.post("/variants", response_model=VariantsResponse)
async def variants(payload: VariantsRequest) -> VariantsResponse:
    """LLM-assisted physics variants: the model proposes a spec, SymPy solves and verifies it.

    Degradation is normal, not an error: an unavailable provider, a timeout or an invalid
    spec falls back to the deterministic template generator and says so (DESIGN §2.5).
    """
    from app.llm.variants import generate_variants  # lazy: keeps the API importable without it

    started = time.perf_counter()
    items, degraded, reason = await generate_variants(payload.scenario, payload.difficulty, payload.count)
    logger.info(
        "variants served",
        extra={"scenario": payload.scenario, "difficulty": payload.difficulty,
               "count": len(items), "degraded": degraded, "reason": reason,
               "duration_ms": round((time.perf_counter() - started) * 1000, 2)},
    )
    if not items:
        raise _fail(503, "generation_failed", reason or "no_items")
    return VariantsResponse(
        scenario=payload.scenario, degraded=degraded, reason=reason,
        items=[_to_wire(item) for item in items],
    )


@router.post("/export")
async def export(payload: ExportRequest, request: Request) -> Response:
    """Worksheet PDF. The body is untrusted: schema-validated, re-verified, and capped."""
    impl = TOPICS.get(payload.topic)
    if impl is None:
        raise _fail(400, "unknown_topic", payload.topic)
    if payload.difficulty not in impl.difficulties:
        raise _fail(400, "invalid_difficulty", payload.difficulty)

    rebuilt: list[Item] = []
    for wire in payload.items:
        try:
            item = _from_wire(payload.topic, payload.difficulty, payload.seed, wire)
        except (ValueError, ZeroDivisionError) as exc:
            logger.warning("invalid export body", extra={"topic": payload.topic, "error": str(exc)})
            raise _fail(400, "invalid_body", f"item {wire.index}: {exc}") from exc
        result = impl.verify(item)
        if not result.ok:
            logger.warning(
                "export rejected: posted item failed verification",
                extra={"topic": payload.topic, "index": wire.index, "reason": result.reason},
            )
            raise _fail(400, "invalid_body", f"item {wire.index}: {result.reason}")
        rebuilt.append(item)

    from app.render.pdf import render_worksheet  # lazy: WeasyPrint is heavy

    try:
        pdf = render_worksheet(rebuilt, answers=payload.answers, strings=load_strings("it"))
    except Exception as exc:  # rendering failure is ours, not the caller's
        logger.exception("export failed", extra={"topic": payload.topic, "items": len(rebuilt)})
        raise _fail(500, "export_failed", str(exc)) from exc

    logger.info("exported", extra={"topic": payload.topic, "items": len(rebuilt),
                                  "answers": payload.answers, "bytes": len(pdf)})
    return Response(
        content=pdf,
        media_type="application/pdf",
        headers={"content-disposition": 'attachment; filename="esercizi.pdf"'},
    )
