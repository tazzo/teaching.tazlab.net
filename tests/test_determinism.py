"""Same seed twice must produce byte-identical output (STRUCTURE §6)."""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)
URL = "/api/generate?topic=math.equations.first_degree&difficulty=easy&seed=20260924&count=5"


def test_same_seed_is_byte_identical() -> None:
    first, second = client.get(URL), client.get(URL)
    assert first.status_code == 200, first.text
    assert first.content == second.content


def test_different_seed_changes_the_items() -> None:
    other = client.get(URL.replace("seed=20260924", "seed=1"))
    assert other.status_code == 200
    assert other.content != client.get(URL).content


def test_different_index_is_a_different_item() -> None:
    body = client.get(URL).json()
    statements = [item["statement"]["params"] for item in body["items"]]
    assert len(set(map(str, statements))) > 1
