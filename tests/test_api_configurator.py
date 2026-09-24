"""The page configurator's contract over HTTP (STRUCTURE §4.2).

The frontend builds its form from `/api/pages` and sends the choices back as a JSON
`options` query parameter. Three things must hold, and each is a way the form could
silently become a decoration:

* the catalogue describes the controls a topic accepts;
* the choices reach the generator — same seed, different options, different exercise;
* an unusable combination is refused with a machine reason, not answered with something else.
"""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)
SEGMENTS = "physics.kinematics.segments"
BASE = f"/api/generate?topic={SEGMENTS}&difficulty=medium&seed=20260924&count=1"


def generate(options: str) -> dict:
    response = client.get(f"{BASE}&options={options}")
    assert response.status_code == 200, response.text
    return response.json()


def test_the_catalogue_describes_the_configurator_for_the_page_that_has_one():
    body = client.get("/api/pages").json()
    page = next(p for p in body["pages"] if p["topic"] == SEGMENTS)
    controls = {control["id"]: control for control in page["config"]}
    assert set(controls) == {"kinds", "quantity", "units", "ask"}
    assert controls["kinds"]["kind"] == "segment_list"
    assert controls["kinds"]["min"] == 1 and controls["kinds"]["max"] == 4
    assert [choice["value"] for choice in controls["kinds"]["choices"]] == [
        "uniform", "accelerate", "decelerate"]
    assert page["defaults"]["quantity"] == "velocity"
    # a page without a configurator must not advertise one
    plain = next(p for p in body["pages"] if p["topic"] == "math.equations.first_degree")
    assert plain["config"] == []


def test_the_options_are_echoed_back_resolved():
    body = generate('{"kinds":["uniform","accelerate"],"quantity":"position","units":"random",'
                    '"ask":"distance"}')
    assert body["options"] == {"kinds": ["uniform", "accelerate"], "quantity": "position",
                               "units": "random", "ask": "distance"}


def test_the_configuration_changes_the_exercise_at_the_same_seed():
    velocity = generate('{"kinds":["accelerate"],"quantity":"velocity","units":"si",'
                        '"ask":"distance"}')
    position = generate('{"kinds":["accelerate"],"quantity":"position","units":"si",'
                        '"ask":"distance"}')
    assert velocity["items"][0]["figure"]["y_unit"] == "m/s"
    assert position["items"][0]["figure"]["y_unit"] == "m"
    assert velocity["content"] != position["content"] if "content" in velocity else True


def test_the_number_of_segments_reaches_the_generator():
    body = generate('{"kinds":["uniform","accelerate","decelerate","uniform"]}')
    figure = body["items"][0]["figure"]
    assert len(figure["traces"]) == 4
    assert len(figure["guides"]) == 3, "four segments have three internal boundaries"
    assert figure["origin"] == "corner"


def test_an_impossible_configuration_is_refused_with_a_reason():
    response = client.get(f'{BASE}&options={{"kinds":["uniform"],"ask":"acceleration"}}')
    assert response.status_code == 400
    body = response.json()
    assert body["error"]["code"] == "invalid_options"
    assert "accelerated" in body["error"]["detail"]


def test_broken_options_json_is_refused():
    response = client.get(f"{BASE}&options=not-json")
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "invalid_options_json"


def test_options_sent_to_a_topic_without_a_configurator_are_refused():
    """Silently ignoring them would hide a client bug behind a plausible exercise."""
    response = client.get(
        "/api/generate?topic=math.equations.first_degree&difficulty=easy&seed=1&count=1"
        '&options={"kinds":["uniform"]}')
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "options_not_supported"


def test_a_page_without_options_still_generates():
    response = client.get(
        "/api/generate?topic=math.equations.first_degree&difficulty=easy&seed=1&count=1")
    assert response.status_code == 200
    assert response.json()["options"] == {}
