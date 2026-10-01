"""Rewrite the frontend's fixtures from the running application.

    python web/test/refresh_fixtures.py

`tests/test_web_fixture.py` fails when a fixture no longer matches what the server
serves, and this is the other half of that: the one command that puts them back in
step. The suite must render descriptors and items the server really produces, so the
fixtures are generated from the API rather than written by hand.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))          # run from anywhere: the app package lives at the root

from fastapi.testclient import TestClient   # noqa: E402

from app.main import app                    # noqa: E402

HERE = Path(__file__).resolve().parent
FIXTURES = HERE / "fixtures"

# the page the configurator suite renders: the one the catalogue marks configurable
SEGMENTS = "physics.kinematics.segments"
# a seed that makes the generated items reproducible
SEED = 4242
# the shape a <select> hands back — strings, one entry per segment, control ids as keys
CLIENT_OPTIONS = {"count": "3", "kinds": ["random"] * 3,
                  "quantity": "random", "units": "random"}


def write(name: str, payload: object) -> Path:
    path = FIXTURES / name
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
                    encoding="utf-8")
    print(f"wrote {path.relative_to(HERE.parents[1])} ({path.stat().st_size} bytes)")
    return path


def main() -> None:
    client = TestClient(app)
    write("pages.json", client.get("/api/pages").json())

    # the three figure modes a page can ask for: `hidden` is what a graph_filling page asks
    # for first, `full` the model it reveals, and `bare` the drawing alone a mill page shows.
    # The segments topic is the one the configurator suite drives.
    query = f"topic={SEGMENTS}&difficulty=easy&seed={SEED}&count=1"
    options = json.dumps(CLIENT_OPTIONS, separators=(",", ":"))
    items = {
        figure: {"url": f"/api/generate?{query}&figure={figure}&options={options}",
                 "body": None}
        for figure in ("hidden", "bare", "full")
    }
    # the two pages the suite navigates to without a configurator: a problem page that
    # renders statement + steps + answer, and the graph_filling page's own topic
    items["problem"] = {"url": "/api/generate?topic=math.equations.first_degree"
                               f"&difficulty=easy&seed={SEED}&count=2", "body": None}
    items["uniform"] = {"url": "/api/generate?topic=physics.kinematics.uniform"
                                f"&difficulty=easy&seed={SEED}&count=1&figure=hidden",
                        "body": None}

    for fixture in items.values():
        response = client.get(fixture["url"])
        response.raise_for_status()
        fixture["body"] = response.json()
    write("items.json", items)


if __name__ == "__main__":
    main()
