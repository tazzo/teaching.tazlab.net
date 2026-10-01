"""The page configurator's contract over HTTP (STRUCTURE §4.2).

The frontend builds its form from `/api/pages` and sends the choices back as a JSON
`options` query parameter. Four things must hold, and each is a way the form could
silently become a decoration:

* the catalogue describes the controls a topic accepts;
* the choices reach the generator — same seed, different options, different exercise;
* an unusable combination is refused with a machine reason, not answered with something else;
* the page says how many exercises a click produces and whether it prints the statement.
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
    assert set(controls) == {"count", "kinds", "quantity", "units"}
    assert controls["count"]["kind"] == "select"
    assert [choice["value"] for choice in controls["count"]["choices"]] == ["3", "4", "5"]
    # one motion selector per segment, as many as the count field says
    assert controls["kinds"]["kind"] == "segment_kinds"
    assert controls["kinds"]["count_from"] == "count"
    assert [choice["value"] for choice in controls["kinds"]["choices"]] == [
        "random", "uniform", "accelerate", "decelerate"]
    # an untouched form is a random draw: the teacher's first click must already be varied
    assert page["defaults"] == {"count": 3, "kinds": ["random"] * 3,
                                "quantity": "random", "units": "random"}
    # a page without a configurator must not advertise one
    plain = next(p for p in body["pages"] if p["topic"] == "math.equations.first_degree")
    assert plain["config"] == []


def test_the_graph_reading_page_asks_for_one_graph_and_nothing_else():
    """The teacher clicks, gets a graph to question a student on, and nothing to read."""
    body = client.get("/api/pages").json()
    page = next(p for p in body["pages"] if p["id"] == "cinematica-grafici-lettura")
    assert page["count"] == 1
    assert page["bare_graph"] is True
    # a page the student reads still gets the ordinary treatment
    other = next(p for p in body["pages"] if p["id"] == "cinematica-problemi")
    assert other["count"] is None and other["bare_graph"] is False


def test_the_bare_figure_carries_the_drawing_and_none_of_the_reading():
    """What a mill page may show: the motion. Not what would answer a question about it —
    no marker naming the asked instant or stretch, no phase naming the kind of motion, and
    no per-kind code for a renderer to colour by."""
    body = client.get(f"{BASE}&figure=bare").json()
    figure = body["items"][0]["figure"]
    full = client.get(f"{BASE}&figure=full").json()["items"][0]["figure"]
    assert "markers" not in figure and "phases" not in figure
    assert all("kind" not in trace for trace in figure["traces"])
    assert all("kind" not in vertex for vertex in figure["vertices"])
    # the drawing itself is untouched: the same samples the full payload carries
    assert [trace["samples"] for trace in figure["traces"]] == [
        trace["samples"] for trace in full["traces"]]
    assert figure["y_unit"] == full["y_unit"] and figure["y_label"] == full["y_label"]
    assert full["markers"] and full["phases"], "the full payload is what the bare one strips"


def test_the_options_are_echoed_back_resolved():
    body = generate('{"count":4,"kinds":["uniform","accelerate","random","random"],'
                    '"quantity":"position","units":"kmh"}')
    assert body["options"] == {"count": 4,
                               "kinds": ["uniform", "accelerate", "random", "random"],
                               "quantity": "position", "units": "kmh"}


def test_the_configuration_changes_the_exercise_at_the_same_seed():
    velocity = generate('{"count":3,"kinds":["accelerate","random","random"],"quantity":"velocity",'
                        '"units":"si"}')
    position = generate('{"count":3,"kinds":["accelerate","random","random"],"quantity":"position",'
                        '"units":"si"}')
    assert velocity["items"][0]["figure"]["y_unit"] == "m/s"
    assert position["items"][0]["figure"]["y_unit"] == "m"


def test_the_number_of_segments_reaches_the_generator():
    body = generate('{"count":5,"kinds":["uniform","accelerate","decelerate","random","random"]}')
    figure = body["items"][0]["figure"]
    assert len(figure["traces"]) == 5
    assert len(figure["guides"]) == 4, "five segments have four internal boundaries"
    assert figure["origin"] == "corner"


def test_the_random_defaults_produce_a_verified_exercise():
    """What the untouched form sends: no options at all, every choice drawn."""
    response = client.get(f"{BASE}&options={{}}")
    assert response.status_code == 200, response.text
    item = response.json()["items"][0]
    assert len(item["figure"]["traces"]) == 3
    assert item["figure"]["y_unit"] in ("m/s", "km/h", "cm/s")


def test_a_unit_system_reaches_the_axis_and_the_answer_together():
    for system, unit in (("si", "m/s"), ("kmh", "km/h"), ("cm", "cm/s")):
        body = generate('{"count":3,"kinds":["uniform","random","random"],"quantity":"velocity",'
                        f'"units":"{system}","ask":"velocity_at"}}')
        item = body["items"][0]
        assert item["figure"]["y_unit"] == unit
        assert item["answer"]["payload"]["unit"] == [unit]


def test_an_impossible_configuration_is_refused_with_a_reason():
    options = '{"count":3,"kinds":["uniform","uniform","uniform"],"ask":"acceleration"}'
    response = client.get(f"{BASE}&options={options}")
    assert response.status_code == 400
    body = response.json()
    assert body["error"]["code"] == "invalid_options"
    assert "accelerated" in body["error"]["detail"]


def test_a_draw_that_cannot_answer_the_requested_reading_is_refused_with_the_same_reason():
    """The kinds are drawn after validation: the refusal has to survive the draw too."""
    for seed in range(1, 60):
        response = client.get(
            f"/api/generate?topic={SEGMENTS}&difficulty=medium&seed={seed}&count=1"
            '&options={"count":3,"kinds":["random","random","random"],"units":"si",'
            '"ask":"acceleration"}')
        if response.status_code == 400:
            assert response.json()["error"]["code"] == "invalid_options"
            assert "accelerated" in response.json()["error"]["detail"]
        else:
            assert response.status_code == 200, response.text


def test_broken_options_json_is_refused():
    response = client.get(f"{BASE}&options=not-json")
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "invalid_options_json"


def test_options_sent_to_a_topic_without_a_configurator_are_refused():
    """Silently ignoring them would hide a client bug behind a plausible exercise."""
    response = client.get(
        "/api/generate?topic=math.equations.first_degree&difficulty=easy&seed=1&count=1"
        '&options={"count":3,"kinds":["uniform","random","random"]}')
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "options_not_supported"


def test_a_page_without_options_still_generates():
    response = client.get(
        "/api/generate?topic=math.equations.first_degree&difficulty=easy&seed=1&count=1")
    assert response.status_code == 200
    assert response.json()["options"] == {}