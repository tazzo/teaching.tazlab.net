"""Wire models (STRUCTURE §4.1). Numbers cross the wire as exact strings."""

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
