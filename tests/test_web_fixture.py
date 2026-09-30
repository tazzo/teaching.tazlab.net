"""The frontend's fixtures must be what the server actually serves (TD-110).

`web/test/fixtures/pages.json` is what the JavaScript suite renders the configurator
from, and `items.json` is what it renders exercises from. The client is not a second
source of truth: it draws the form the server describes, so a fixture that drifts from
`/api/pages` would make the suite certify a page nobody serves. These tests are the
drift alarm — regenerate the fixtures with the command below when the catalogue moves.

The last test is the contract itself: the values a `<select>` hands back are strings,
and the generator has to accept the strings the browser produces, not a tidier version
of them.
"""

from __future__ import annotations

import json
from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)
FIXTURES = Path(__file__).resolve().parent.parent / "web" / "test" / "fixtures"
PAGES = FIXTURES / "pages.json"
ITEMS = FIXTURES / "items.json"
SEGMENTS = "physics.kinematics.segments"
BASE = f"/api/generate?topic={SEGMENTS}&difficulty=medium&seed=20260924&count=1"
REGENERATE = "python web/test/refresh_fixtures.py"


def served_pages() -> dict:
    return client.get("/api/pages").json()


def configurable_page(body: dict | None = None) -> dict:
    pages = (body or served_pages())["pages"]
    return next(page for page in pages if page["config"])


def test_the_frontend_fixture_is_the_catalogue_the_server_serves() -> None:
    served = served_pages()
    assert PAGES.exists(), f"missing frontend fixture; create it with:\n  {REGENERATE}"
    fixture = json.loads(PAGES.read_text(encoding="utf-8"))
    assert fixture == served, (
        "web/test/fixtures/pages.json has drifted from /api/pages, so the JavaScript "
        "suite would be testing a page the server no longer serves. Regenerate it with:\n"
        f"  {REGENERATE}"
    )
    # a fixture with no configurator in it would make the frontend suite vacuous
    assert configurable_page(fixture)["id"] == configurable_page(served)["id"]


def test_the_items_the_frontend_suite_renders_are_the_ones_the_server_sends() -> None:
    """A wire-format change cannot hide behind a rendering change: the pin fails as
    soon as either side moves."""
    assert ITEMS.exists(), f"missing frontend fixture; create it with:\n  {REGENERATE}"
    fixtures = json.loads(ITEMS.read_text(encoding="utf-8"))
    assert fixtures, "items.json is empty: the suite would render nothing"
    for name, fixture in fixtures.items():
        response = client.get(fixture["url"])
        assert response.status_code == 200, f"{name}: {response.text}"
        assert response.json() == fixture["body"], (
            f"web/test/fixtures/items.json[{name!r}] has drifted from {fixture['url']}. "
            f"Regenerate it with:\n  {REGENERATE}"
        )


def test_the_values_the_browser_sends_are_ones_the_generator_accepts() -> None:
    """`read()` hands the server what the DOM holds: strings, one per segment.

    The JavaScript suite proves the client *builds* that payload; this proves the server
    does not refuse it. Neither test re-implements the other.
    """
    page = configurable_page()
    defaults = page["defaults"]
    count = str(defaults["count"])
    as_sent_by_the_dom = {
        "count": count,                                   # a <select> value is a string
        "kinds": [str(kind) for kind in defaults["kinds"]],
        "quantity": str(defaults["quantity"]),
        "units": str(defaults["units"]),
    }
    assert len(as_sent_by_the_dom["kinds"]) == int(count)

    response = client.get(f"{BASE}&options={json.dumps(as_sent_by_the_dom)}")
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["options"] == {"count": int(count), "kinds": as_sent_by_the_dom["kinds"],
                               "quantity": as_sent_by_the_dom["quantity"],
                               "units": as_sent_by_the_dom["units"]}

    # one segment per count, the way the rows are built: a form whose two fields
    # contradict each other is refused with a reason, not quietly repaired
    wrong_length = dict(as_sent_by_the_dom, kinds=as_sent_by_the_dom["kinds"][:-1])
    refused = client.get(f"{BASE}&options={json.dumps(wrong_length)}")
    assert refused.status_code == 400
    assert refused.json()["error"]["code"] == "invalid_options"
