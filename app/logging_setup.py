"""Structured logging for the teaching service.

Contract (DESIGN §2.11): one JSON object per line on stdout, a request id on
every nested line, a loud WARN when something is wrong, and never a secret.
"""

from __future__ import annotations

import json
import logging
import os
import sys
import uuid
from contextvars import ContextVar

_request_id: ContextVar[str] = ContextVar("request_id", default="-")

# Fields that belong to the LogRecord itself and must not be re-emitted as context.
_STANDARD = set(
    logging.LogRecord("", 0, "", 0, "", (), None).__dict__
) | {"message", "asctime", "taskName"}

# uvicorn's `color_message` carries ANSI escapes and duplicates `msg`.
_DROP = {"color_message"}


def set_request_id(value: str | None = None) -> str:
    rid = value or uuid.uuid4().hex[:16]
    _request_id.set(rid)
    return rid


def get_request_id() -> str:
    return _request_id.get()


class JsonFormatter(logging.Formatter):
    """Minimal, allocation-light JSON formatter."""

    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "ts": self.formatTime(record, "%Y-%m-%dT%H:%M:%S%z"),
            "level": record.levelname,
            "logger": record.name,
            "msg": record.getMessage(),
            "request_id": get_request_id(),
        }
        for key, value in record.__dict__.items():
            if key in _DROP or key in _STANDARD or key.startswith("_"):
                continue
            payload[key] = value
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=False, default=str)


def configure_logging() -> None:
    level = os.getenv("TEACHING_LOG_LEVEL", "INFO").upper()
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())

    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(level)

    # uvicorn's own handlers would duplicate and lose the JSON shape; its INFO
    # chatter ("Started server process", "Uvicorn running on …") is redundant with
    # the startup banner, so only its warnings and errors are kept.
    for name in ("uvicorn", "uvicorn.error"):
        lg = logging.getLogger(name)
        lg.handlers.clear()
        lg.propagate = True
        lg.setLevel("WARNING")
    logging.getLogger("uvicorn.access").disabled = True
    for noisy in ("httpx", "httpcore", "weasyprint", "fontTools"):
        logging.getLogger(noisy).setLevel("WARNING")


def startup_banner(logger: logging.Logger, **config: object) -> None:
    """Log the resolved configuration, and shout if a required key is missing."""
    logger.info("service starting", extra={"config": config})
    if not os.getenv("OPENCODE_API_KEY"):
        logger.warning(
            "OPENCODE_API_KEY is not set: the LLM variant endpoint will answer with "
            "template items and degraded=true",
            extra={"impact": "llm_variants_unavailable", "action": "check the VaultStaticSecret"},
        )
