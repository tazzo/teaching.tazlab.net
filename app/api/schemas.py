"""Wire models (STRUCTURE §4.1-§4.5). Numbers cross the wire as exact strings."""

from __future__ import annotations

from pydantic import BaseModel, Field, field_validator


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


class VariantsRequest(BaseModel):
    scenario: str
    difficulty: str = "medium"
    count: int = Field(5, ge=1, le=10)


class VariantsResponse(BaseModel):
    scenario: str
    degraded: bool
    reason: str | None = None
    items: list[WireItem]


class ExportRequest(BaseModel):
    """The rendered items travel in the body: with D9 there is no URL that could
    regenerate a sheet, and nothing is stored server-side."""

    topic: str
    difficulty: str = "easy"
    seed: int = 0
    items: list[WireItem] = Field(..., min_length=1, max_length=50)
    answers: bool = False

    @field_validator("items")
    @classmethod
    def at_least_one(cls, value: list[WireItem]) -> list[WireItem]:
        if not value:
            raise ValueError("items must not be empty")
        return value


class ErrorBody(BaseModel):
    code: str
    message_key: str
    detail: str | None = None


class ErrorResponse(BaseModel):
    error: ErrorBody
