"""Wire models (STRUCTURE §4.1-§4.3). Numbers cross the wire as exact strings."""

from __future__ import annotations

from pydantic import BaseModel, Field


class TopicInfo(BaseModel):
    id: str
    family: str
    difficulties: list[str]
    label_key: str
    scenarios: list[str] = Field(default_factory=list)


class Catalog(BaseModel):
    version: str = "1"
    languages: list[str] = ["it"]
    topics: list[TopicInfo]


class Health(BaseModel):
    status: str = "ok"
    version: str


class WireStatement(BaseModel):
    key: str
    params: dict[str, str]


class WireStep(BaseModel):
    label_key: str
    latex: str
    note_key: str | None = None


class WireAnswer(BaseModel):
    latex: str
    kind: str
    payload: dict[str, list[str]] = Field(default_factory=dict)


class WireItem(BaseModel):
    index: int
    statement: WireStatement
    steps: list[WireStep]
    answer: WireAnswer
    figure: dict | None = None


class GenerateResponse(BaseModel):
    topic: str
    difficulty: str
    seed: int
    items: list[WireItem]


class ErrorBody(BaseModel):
    code: str
    message_key: str
    detail: str | None = None


class ErrorResponse(BaseModel):
    error: ErrorBody
