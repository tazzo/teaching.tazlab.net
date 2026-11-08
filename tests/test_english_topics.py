"""Tests for English grammar generators and multiple choice exercises."""

from __future__ import annotations

import random
import re
from fastapi.testclient import TestClient
import pytest

from app.core.rng import make_rng
from app.core.strings import load_strings
from app.generators.english.present_perfect import TOPIC as PPS_TOPIC, EASY_QUESTIONS as PPS_EASY
from app.generators.english.relative_clauses import TOPIC as RELATIVE_TOPIC, EASY_QUESTIONS as RC_EASY
from app.generators.english.relative_defining_non_defining import (
    TOPIC as RDN_TOPIC,
    EASY_QUESTIONS as RDN_EASY,
    MEDIUM_QUESTIONS as RDN_MEDIUM,
    option_classification,
    sentence_classification,
    PRONOUNS as RDN_PRONOUNS,
)
from app.generators.registry import TOPICS
from app.main import app
from app.pages import PAGES, find_page
from app.render.pdf import worksheet_html

client = TestClient(app)


@pytest.mark.parametrize("topic", [PPS_TOPIC, RELATIVE_TOPIC, RDN_TOPIC])
@pytest.mark.parametrize("difficulty", ["easy", "medium"])
def test_english_topic_generation_and_verification(topic, difficulty: str) -> None:
    rng = make_rng(42, topic.id, difficulty, 0)
    item = topic.generate(rng, difficulty, 42, 0)

    assert item.topic == topic.id
    assert item.difficulty == difficulty
    assert item.answer.kind == "multiple_choice"

    payload = item.answer.payload
    assert "options" in payload
    assert "correct" in payload
    assert "explanation" in payload

    options = payload["options"]
    assert len(options) == 4
    assert len(set(options)) == 4
    assert payload["correct"][0] in options

    result = topic.verify(item)
    assert result.ok, result.reason


@pytest.mark.parametrize("topic", [PPS_TOPIC, RELATIVE_TOPIC, RDN_TOPIC])
def test_corrupted_english_item_is_rejected(topic) -> None:
    rng = make_rng(100, topic.id, "easy", 0)
    item = topic.generate(rng, "easy", 100, 0)

    # Corrupt by removing the correct answer from options
    corrupted_options = ["wrong1", "wrong2", "wrong3", "wrong4"]
    corrupted_answer = type(item.answer)(
        latex=item.answer.latex,
        kind=item.answer.kind,
        payload={
            **item.answer.payload,
            "options": corrupted_options,
            "correct": ["not_in_options"],
        },
    )
    corrupted_item = type(item)(**{**item.__dict__, "answer": corrupted_answer})
    result = topic.verify(corrupted_item)
    assert not result.ok
    assert result.reason == "invalid_or_missing_correct_answer"


def test_twenty_items_are_all_distinct_in_a_single_run() -> None:
    """A batch of 20 requested exercises must contain 20 distinct questions."""
    for topic_id in (
        "english.grammar.present_perfect",
        "english.grammar.relative_clauses",
        "english.grammar.relative_defining_non_defining",
    ):
        for diff in ("easy", "medium"):
            response = client.get(f"/api/generate?topic={topic_id}&difficulty={diff}&seed=12345&count=20")
            assert response.status_code == 200, response.text
            body = response.json()
            statements = [item["statement"]["key"] for item in body["items"]]
            assert len(statements) == 20
            assert len(set(statements)) == 20, f"Found duplicate questions in {topic_id} {diff}"


def test_catalogue_contains_english_macro_and_pages() -> None:
    response = client.get("/api/pages")
    assert response.status_code == 200
    body = response.json()
    assert "english" in body["macros"]
    assert "grammatica" in body["subs"].get("english", [])

    pps_page = find_page("english-present-perfect")
    assert pps_page is not None
    assert pps_page.macro == "english"
    assert pps_page.kind == "multiple_choice"
    assert pps_page.count == 20

    rc_page = find_page("english-relative-clauses")
    assert rc_page is not None
    assert rc_page.macro == "english"
    assert rc_page.kind == "multiple_choice"
    assert rc_page.count == 20

    rdn_page = find_page("english-relative-defining-non-defining")
    assert rdn_page is not None
    assert rdn_page.macro == "english"
    assert rdn_page.sub == "grammatica"
    assert rdn_page.kind == "multiple_choice"
    assert rdn_page.count == 20


def test_english_steps_and_explanations_are_in_italian() -> None:
    """Step explanations and clues must be written in Italian while keeping target English words."""
    rng = make_rng(42, PPS_TOPIC.id, "easy", 0)
    item_pps = PPS_TOPIC.generate(rng, "easy", 42, 0)
    # Check that clue and rule contain Italian words
    assert "verbo" in item_pps.steps[0].latex.lower() or "indicatore" in item_pps.steps[0].latex.lower()
    assert "verbi" in item_pps.steps[1].latex.lower() or "forma" in item_pps.steps[1].latex.lower()
    assert "verbo" in item_pps.answer.payload["explanation"][0].lower() or "forma" in item_pps.answer.payload["explanation"][0].lower()

    rng = make_rng(42, RELATIVE_TOPIC.id, "easy", 0)
    item_rc = RELATIVE_TOPIC.generate(rng, "easy", 42, 0)
    assert "persona" in item_rc.steps[0].latex.lower() or "antecedente" in item_rc.steps[0].latex.lower()
    assert "relative" in item_rc.steps[1].latex.lower() or "persone" in item_rc.steps[1].latex.lower()


def test_sequential_question_order() -> None:
    """Questions are generated in stable sequential order without random jumps."""
    rng = make_rng(1, PPS_TOPIC.id, "easy", 0)
    for i in range(20):
        item = PPS_TOPIC.generate(rng, "easy", 1, i)
        assert item.statement_key == PPS_EASY[i].sentence

    for i in range(20):
        item = RELATIVE_TOPIC.generate(rng, "easy", 1, i)
        assert item.statement_key == RC_EASY[i].sentence


def test_relative_defining_non_defining_offers_pronoun_and_classification() -> None:
    """The new exercise asks two things at once, and the commas decide the second one.

    A defining clause has no commas and admits 'that'; a non-defining clause sits between
    commas and forbids it. The invariants below are what make the exercise answerable: one
    correct option, three distractors that fail for a stated reason, and 'that' never
    correct inside a non-defining clause.
    """
    for pool in (RDN_EASY, RDN_MEDIUM):
        assert len(pool) >= 20, "a batch of 20 needs at least 20 questions"
        assert len({spec.sentence for spec in pool}) == len(pool), "duplicate sentence in the pool"
        for spec in pool:
            assert len(spec.options) == 4
            assert len(set(spec.options)) == 4, spec.sentence
            assert spec.correct in spec.options, spec.sentence

            # every option carries both facts, or it cannot be answered
            assert all(option_classification(option) for option in spec.options), spec.sentence

            # the classification claimed by the answer is the one the punctuation shows
            assert option_classification(spec.correct) == sentence_classification(spec.sentence), spec.sentence

            # 'that' is forbidden in a non-defining clause, never the right answer there
            assert spec.correct != "that (non-defining)", spec.sentence

            for text in (spec.explanation, spec.clue, spec.rule):
                assert text.strip(), spec.sentence
                # the text is wrapped in \text{...}: a LaTeX special would break the render
                assert not set(text) & set("%&$#_\\{}"), (spec.sentence, text)

            # The depth bar, taken from the present-perfect topic: the explanation says WHY
            # the clause is defining or non-defining before it says which pronoun fits.
            explanation = spec.explanation.lower()
            assert explanation.startswith(("defining:", "non-defining:")), spec.sentence
            assert "virgol" in explanation, spec.sentence
            assert option_classification(spec.correct) in explanation, spec.sentence
            # ... and the clue carries the diagnostic signal without naming a pronoun, so it
            # puts the student on the road without handing over the answer.
            for pronoun in RDN_PRONOUNS:
                assert not re.search(rf"\b{pronoun}\b", spec.clue, re.I), (spec.sentence, pronoun)


def test_the_comma_is_the_only_thing_that_changes_the_answer() -> None:
    """At least one question offers the right pronoun under both classifications.

    When the same pronoun appears as 'defining' and as 'non-defining', the pronoun cannot be
    what decides: the commas are. Those are the cards that teach the rule instead of
    rewarding a guess.
    """
    for pool in (RDN_EASY, RDN_MEDIUM):
        comma_traps = [
            spec for spec in pool
            if any(
                other.split(" (")[0] == spec.correct.split(" (")[0]
                and other != spec.correct
                for other in spec.options
            )
        ]
        assert comma_traps, "no question where the comma alone decides the answer"


def test_a_that_non_defining_answer_is_refused_by_verify() -> None:
    """The grammar truth is enforced, not merely respected by the data."""
    rng = make_rng(7, RDN_TOPIC.id, "easy", 0)
    # a card whose punctuation really makes the clause non-defining
    index = next(
        i for i in range(len(RDN_EASY))
        if sentence_classification(RDN_EASY[i].sentence) == "non-defining"
    )
    item = RDN_TOPIC.generate(rng, "easy", 7, index)
    forged = type(item.answer)(
        latex=item.answer.latex,
        kind=item.answer.kind,
        payload={**item.answer.payload, "correct": ["that (non-defining)"]},
    )
    result = RDN_TOPIC.verify(type(item)(**{**item.__dict__, "answer": forged}))
    assert not result.ok
    assert result.reason == "that_in_non_defining"


def test_a_classification_that_contradicts_the_commas_is_refused() -> None:
    """A defining sentence whose answer claims to be non-defining is a broken question."""
    rng = make_rng(7, RDN_TOPIC.id, "easy", 0)
    index = next(
        i for i in range(len(RDN_EASY))
        if sentence_classification(RDN_EASY[i].sentence) == "defining"
    )
    item = RDN_TOPIC.generate(rng, "easy", 7, index)
    pronoun = item.answer.payload["correct"][0].split(" (")[0]
    forged = type(item.answer)(
        latex=item.answer.latex,
        kind=item.answer.kind,
        payload={**item.answer.payload, "correct": [f"{pronoun} (non-defining)"]},
    )
    result = RDN_TOPIC.verify(type(item)(**{**item.__dict__, "answer": forged}))
    assert not result.ok
    assert result.reason == "classification_mismatch"


def test_english_worksheet_html_rendering() -> None:
    rng = make_rng(42, PPS_TOPIC.id, "easy", 0)
    items = [PPS_TOPIC.generate(rng, "easy", 42, i) for i in range(3)]
    strings = load_strings("it")

    # Statements only
    html = worksheet_html(items, answers=False, strings=strings)
    assert '<ol class="options"' in html
    assert items[0].statement_key in html

    # With answers key
    html_answers = worksheet_html(items, answers=True, strings=strings)
    assert '<section class="key">' in html_answers
    assert '<span class="answer-label">' in html_answers
