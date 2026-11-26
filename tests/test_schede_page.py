"""The sheets page: a stable link, a stated version, and the bytes that match.

The operator's order (26/11/2026): one place in the site where the sheets are published, so
that a link he saves always gives the latest version — and the page must say *which* version
it is, because a stable address is otherwise a promise nobody can check.

These tests are that contract, measured:

* the address is **stable** — no date in the file name, one address per sheet;
* the page is **in the menu**, with no generator behind it (it lists a folder);
* the sha256 the API announces is the sha256 of **the bytes the route serves**;
* a PDF that is **not declared** is not served: publishing is a decision;
* the **date and the commit** are the ones git says, and a `versions.json` describing
  other bytes is thrown away instead of repeated (a version naming another file is worse
  than no version).
"""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

import app.schede as schede_module
from app.main import app

client = TestClient(app)
ROOT = Path(__file__).resolve().parent.parent
SCHEDE_DIR = ROOT / "schede"
MANIFEST = SCHEDE_DIR / "schede.json"


def payloads() -> list[dict]:
    response = client.get("/api/schede")
    assert response.status_code == 200, response.text
    return response.json()["schede"]


def one_sheet() -> dict:
    sheets = payloads()
    assert sheets, "no sheet is published: schede/schede.json lists none that exists"
    return sheets[0]


def git(*args: str) -> str:
    done = subprocess.run(["git", "-C", str(ROOT), *args], capture_output=True, text=True)
    assert done.returncode == 0, done.stderr
    return done.stdout


def test_the_page_is_in_the_menu_and_needs_no_generator() -> None:
    """A section of its own that `/api/pages` serves although no topic backs it."""
    body = client.get("/api/pages").json()
    assert "schede" in body["macros"]
    assert body["subs"]["schede"], "the sheets section has no sub-topic: it is unreachable"
    pages = [page for page in body["pages"] if page["macro"] == "schede"]
    assert [page["kind"] for page in pages] == ["schede_list"]
    assert pages[0]["topic"] == ""


def test_the_sheets_are_listed_with_a_stable_address() -> None:
    """The point of the page: the link does not change when the sheet does."""
    sheet = one_sheet()
    assert sheet["url"] == f"/schede/{sheet['file']}"
    # a name with a date in it would break the saved link at the next rebuild
    assert not re.search(r"20\d{2}[-_]?\d{2}[-_]?\d{2}", sheet["file"]), sheet["file"]
    assert re.fullmatch(r"/schede/[a-z0-9][a-z0-9_-]*/[a-z0-9][a-z0-9_-]*\.pdf", sheet["url"])
    assert sheet["title"], "a sheet with no title cannot be chosen"
    assert sheet["bytes"] > 0


def test_the_announced_sha256_is_the_sha256_of_the_served_bytes() -> None:
    """The declaration and the download are one thing, or the check the operator does fails."""
    for sheet in payloads():
        response = client.get(sheet["url"])
        assert response.status_code == 200, response.text
        assert response.headers["content-type"] == "application/pdf"
        digest = hashlib.sha256(response.content).hexdigest()
        assert digest == sheet["sha256"], (
            f"{sheet['url']}: the page announces {sheet['sha256']} but serves {digest}"
        )
        assert len(response.content) == sheet["bytes"]
        # the digest also travels as a header, so `curl -I` answers without downloading
        assert response.headers["x-scheda-sha256"] == sheet["sha256"]
        assert "inline" in response.headers["content-disposition"]


def test_the_sheet_is_the_file_the_manifest_declares() -> None:
    declared = json.loads(MANIFEST.read_text(encoding="utf-8"))["schede"]
    published = {sheet["file"] for sheet in payloads()}
    assert {entry["file"] for entry in declared} == published
    for entry in declared:
        path = SCHEDE_DIR / entry["file"]
        assert path.is_file(), f"declared but missing: {entry['file']}"
        assert hashlib.sha256(path.read_bytes()).hexdigest() == next(
            sheet["sha256"] for sheet in payloads() if sheet["file"] == entry["file"]
        )


def test_a_pdf_that_is_not_declared_is_not_served() -> None:
    """Publishing is a decision: a compiled sheet sitting in the tree is not published."""
    undeclared = sorted(
        path.relative_to(SCHEDE_DIR).as_posix()
        for path in SCHEDE_DIR.glob("*/*.pdf")
        if path.relative_to(SCHEDE_DIR).as_posix() not in
        {sheet["file"] for sheet in payloads()}
    )
    for rel in undeclared:
        assert client.get(f"/schede/{rel}").status_code == 404, rel


def test_nothing_outside_the_declared_sheets_can_be_fetched() -> None:
    """The lookup is the allowlist, so there is no path to traverse."""
    for attempt in ("/schede/../pyproject.toml",
                    "/schede/radicali/../../pyproject.toml",
                    "/schede/%2e%2e/pyproject.toml",
                    "/schede/radicali/..%2f..%2fpyproject.toml",
                    "/schede/",
                    "/schede/nope/x.pdf",
                    "/schede/README.md"):
        response = client.get(attempt)
        assert response.status_code == 404, attempt
        assert b"schede.json" not in response.content


def test_the_version_is_the_commit_that_last_changed_the_pdf() -> None:
    """`aggiornata al <data>, da <sha>` — the pair the page prints under the title.

    In a checkout the answer comes from git; inside the image it comes from
    `schede/versions.json`, written by `scripts/schede_versions.py` at build time. Either
    way the sha must be a real commit that touched the PDF, never the build's own HEAD.
    """
    sheet = one_sheet()
    path = SCHEDE_DIR / sheet["file"]
    assert sheet["updated"], "a sheet with no date cannot be told from yesterday's"
    has_git = (ROOT / ".git").exists()
    if not has_git and not schede_module.VERSIONS.is_file():
        pytest.skip("no checkout and no versions.json: nothing here can name a commit")
    assert sheet["commit"], (
        "no commit: run scripts/schede_versions.py (the CI runs it before the build) — "
        "the page would say only 'compilata il'"
    )
    if not has_git:
        pytest.skip("no checkout here: the version came from versions.json")
    last = git("log", "-1", "--format=%cs%x09%h", "--", str(path)).strip().split("\t")
    assert (sheet["updated"], sheet["commit"]) == (last[0], last[1]), (
        f"the page says {sheet['updated']} / {sheet['commit']}, git says {last[0]} / {last[1]}"
    )
    # and the commit named is one that really touched the PDF, in this repository
    changed = git("show", "--name-only", "--format=", sheet["commit"]).split()
    assert f"schede/{sheet['file']}" in changed, (
        f"{sheet['commit']} does not touch schede/{sheet['file']}"
    )


def test_a_version_describing_other_bytes_is_thrown_away(tmp_path, monkeypatch) -> None:
    """The integrity rule: a stale declaration must not be repeated as if it were true."""
    sheet = one_sheet()
    stale = tmp_path / "versions.json"
    stale.write_text(json.dumps({"sheets": {sheet["file"]: {
        "sha256": "0" * 64, "bytes": 1, "updated": "1999-01-01", "commit": "deadbee",
    }}}), encoding="utf-8")
    monkeypatch.setattr(schede_module, "VERSIONS", stale)
    monkeypatch.setattr(schede_module, "_CACHE", {})

    served = schede_module.find_scheda(sheet["file"])
    assert served is not None
    assert served.sha256 == sheet["sha256"], "the digest is always the file's own"
    assert served.commit != "deadbee"
    assert served.updated != "1999-01-01"


def test_a_declared_sheet_whose_file_is_missing_is_dropped(tmp_path, monkeypatch) -> None:
    """An entry pointing at nothing is not a page with a broken link."""
    empty = tmp_path / "schede"
    empty.mkdir()
    (empty / "schede.json").write_text(json.dumps({"schede": [
        {"file": "manca/manca-1.pdf", "title": "Manca", "order": 10},
    ]}), encoding="utf-8")
    monkeypatch.setattr(schede_module, "SCHEDE_DIR", empty)
    monkeypatch.setattr(schede_module, "MANIFEST", empty / "schede.json")
    monkeypatch.setattr(schede_module, "_CACHE", {})
    assert schede_module.list_schede() == []


def test_the_sheet_keeps_its_name_and_the_digest_changes_with_the_bytes() -> None:
    """The stable name is the whole point: same address, and the version moves with the file."""
    sheet = one_sheet()
    path = SCHEDE_DIR / sheet["file"]
    told = schede_module._build(sheet["file"], {"file": sheet["file"]}, {})
    assert told is not None
    assert told.url == sheet["url"]
    assert told.sha256 == hashlib.sha256(path.read_bytes()).hexdigest()
