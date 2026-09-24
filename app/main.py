"""FastAPI application entrypoint for teaching.tazlab.net."""

from __future__ import annotations

import logging
import os
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from app.api.routes import VERSION, router
from app.logging_setup import configure_logging, get_request_id, set_request_id, startup_banner

configure_logging()
logger = logging.getLogger("teaching")

WEB_DIST = os.path.join(os.path.dirname(os.path.dirname(__file__)), "web", "dist")


@asynccontextmanager
async def lifespan(_: FastAPI):
    startup_banner(
        logger,
        version=VERSION,
        git_sha=os.getenv("TEACHING_GIT_SHA", "unknown"),
        log_level=os.getenv("TEACHING_LOG_LEVEL", "INFO"),
        llm_base_url=os.getenv("TEACHING_LLM_BASE_URL", "https://opencode.ai/zen/go/v1"),
        llm_model=os.getenv("TEACHING_LLM_MODEL", "deepseek-v4.1-flash"),
        llm_session=bool(os.getenv("TEACHING_LLM_SESSION_ID")),
        web_dist=os.path.isdir(WEB_DIST),
    )
    yield
    logger.info("service stopping")


# Paths that are hit by cluster probes on a fixed schedule.
_QUIET_PATHS = {"/api/healthz"}

app = FastAPI(title="teaching.tazlab.net", version=VERSION, lifespan=lifespan)


@app.middleware("http")
async def request_logging(request: Request, call_next):
    request_id = set_request_id(request.headers.get("x-request-id"))
    started = time.perf_counter()
    try:
        response = await call_next(request)
    except Exception:
        logger.exception(
            "unhandled error",
            extra={"path": request.url.path, "method": request.method, "request_id": request_id},
        )
        # the id must also come back on failures, so a reported error is traceable
        return JSONResponse(
            status_code=500,
            content={"error": {"code": "internal_error", "message_key": "error.internal"}},
            headers={"x-request-id": request_id},
        )
    duration_ms = round((time.perf_counter() - started) * 1000, 2)
    if response.status_code >= 400:
        level = logging.WARNING          # a 4xx is worth seeing, but it is not an incident
    elif request.url.path in _QUIET_PATHS:
        level = logging.DEBUG            # liveness/readiness probes must not flood INFO
    else:
        level = logging.INFO
    logger.log(
        level,
        "request",
        extra={
            "request_id": request_id,
            "method": request.method,
            "path": request.url.path,
            "status": response.status_code,
            "duration_ms": duration_ms,
            "client_ip": _client_ip(request),
        },
    )
    response.headers["x-request-id"] = request_id
    return response


def _client_ip(request: Request) -> str:
    """Trust X-Forwarded-For only for the cluster's pod CIDR (DESIGN §2.11)."""
    peer = request.client.host if request.client else "-"
    forwarded = request.headers.get("x-forwarded-for", "")
    if forwarded and peer.startswith("10.244."):
        return forwarded.split(",")[0].strip()
    return peer


@app.exception_handler(RequestValidationError)
async def validation_error_handler(request: Request, exc: RequestValidationError):
    """FastAPI's own validation answers 422; the documented contract is 400 invalid_parameter.

    A bad parameter is a client error, not an incident: WARN, with the offending field named.
    """
    fields = [".".join(str(part) for part in err.get("loc", ())) for err in exc.errors()]
    logger.warning(
        "invalid request parameters",
        extra={"path": request.url.path, "fields": fields},
    )
    return JSONResponse(
        status_code=400,
        content={
            "error": {
                "code": "invalid_parameter",
                "message_key": "error.invalid_parameter",
                "detail": ", ".join(fields),
            }
        },
        headers={"x-request-id": get_request_id()},
    )


app.include_router(router)

if os.path.isdir(WEB_DIST):
    app.mount("/", StaticFiles(directory=WEB_DIST, html=True), name="web")
else:
    logger.warning("web/dist is missing: the API is served without a frontend bundle")
