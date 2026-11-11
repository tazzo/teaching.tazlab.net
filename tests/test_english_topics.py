"""Tests for English grammar generators and multiple choice exercises."""

from __future__ import annotations

import random
import re
from fastapi.testclient import TestClient
import pytest

from app.core.rng import make_rng
from app.core.strings import load_strings
from app.generators.english.present_perfect import TOPIC as PPS_TOPIC, EASY_QUESTIONS as PPS_EASY
from app.generators.english.present_perfect_medium import (
    TOPIC as PPM_TOPIC,
    MEDIUM_QUESTIONS as PPM_MEDIUM,
    aspect,
    asks_for_a_continuous_form,
    verb_hint,
)
from app.generators.english.relative_classification import (
    TOPIC as RCK_TOPIC,
    QUESTIONS as RCK_QUESTIONS,
    PRONOUNS as RCK_PRONOUNS,
    CLASSIFICATIONS as RCK_CLASSIFICATIONS,
)
from app.generators.english.relative_grammar import sentence_classification
from app.generators.english.present_perfect_simple_continuous import (
    TOPIC as PPSC_TOPIC,
    QUESTIONS as PPSC_QUESTIONS,
    CLASSIFICATIONS as PPSC_CLASSIFICATIONS,
    aspect_of,
    expected_classification,
)
from app.generators.registry import TOPICS
from app.main import app
from app.pages import KINDS, PAGES, find_page
from app.render.pdf import worksheet_html

client = TestClient(app)


@pytest.mark.parametrize(("topic", "difficulty"), [
    (PPS_TOPIC, "easy"),
    (PPS_TOPIC, "medium"),
    (RCK_TOPIC, "easy"),
])
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


@pytest.mark.parametrize(("topic", "corrupted_options"), [
    (PPS_TOPIC, ["wrong1", "wrong2", "wrong3", "wrong4"]),
    # the relative page grades the shape of an option before the answer, so a corrupted
    # card there is four bare pronouns that do not contain the correct one
    (RCK_TOPIC, ["who", "which", "whose", "where"]),
])
def test_corrupted_english_item_is_rejected(topic, corrupted_options) -> None:
    rng = make_rng(100, topic.id, "easy", 0)
    item = topic.generate(rng, "easy", 100, 0)
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
    for topic_id, difficulty in (
        ("english.grammar.present_perfect", "easy"),
        ("english.grammar.present_perfect", "medium"),
        ("english.grammar.relative_classification", "easy"),
    ):
        response = client.get(
            f"/api/generate?topic={topic_id}&difficulty={difficulty}&seed=12345&count=20"
        )
        assert response.status_code == 200, response.text
        body = response.json()
        statements = [item["statement"]["key"] for item in body["items"]]
        assert len(statements) == 20
        assert len(set(statements)) == 20, (
            f"Found duplicate questions in {topic_id} {difficulty}"
        )


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

    # The catalogue changed on the operator's request (task-281711): the two
    # multiple-choice relative pages were fused into the classification page, so their
    # ids are gone from the catalogue and from the registry, not merely unlisted.
    for removed in ("english-relative-clauses", "english-relative-defining-non-defining"):
        assert find_page(removed) is None, f"{removed} is still in the catalogue"
    for removed_topic in (
        "english.grammar.relative_clauses",
        "english.grammar.relative_defining_non_defining",
    ):
        assert removed_topic not in TOPICS, f"{removed_topic} is still a served topic"

    relative_pages = [
        page for page in PAGES if page.macro == "english" and "relative" in page.id
    ]
    assert [page.id for page in relative_pages] == ["english-relative-classification"], (
        "one relative page only: two identical pages are a duplicate even when one is "
        "prettier"
    )


def test_english_steps_and_explanations_are_in_italian() -> None:
    """Step explanations and clues must be written in Italian while keeping target English words."""
    rng = make_rng(42, PPS_TOPIC.id, "easy", 0)
    item_pps = PPS_TOPIC.generate(rng, "easy", 42, 0)
    # Check that clue and rule contain Italian words
    assert "verbo" in item_pps.steps[0].latex.lower() or "indicatore" in item_pps.steps[0].latex.lower()
    assert "verbi" in item_pps.steps[1].latex.lower() or "forma" in item_pps.steps[1].latex.lower()
    assert "verbo" in item_pps.answer.payload["explanation"][0].lower() or "forma" in item_pps.answer.payload["explanation"][0].lower()

    rng = make_rng(42, RCK_TOPIC.id, "easy", 0)
    item_rc = RCK_TOPIC.generate(rng, "easy", 42, 0)
    assert "persona" in item_rc.steps[0].latex.lower() or "antecedente" in item_rc.steps[0].latex.lower()
    assert "relative" in item_rc.steps[1].latex.lower() or "persone" in item_rc.steps[1].latex.lower()


def test_sequential_question_order() -> None:
    """Questions are generated in stable sequential order without random jumps."""
    rng = make_rng(1, PPS_TOPIC.id, "easy", 0)
    for i in range(20):
        item = PPS_TOPIC.generate(rng, "easy", 1, i)
        assert item.statement_key == PPS_EASY[i].sentence

    for i in range(20):
        item = RCK_TOPIC.generate(rng, "easy", 1, i)
        assert item.statement_key == RCK_QUESTIONS[i].sentence


def test_the_comma_is_the_only_thing_that_changes_the_answer() -> None:
    """The same pronoun is the right answer on both sides of the comma.

    When 'which' is correct in a defining card and in a non-defining one, the pronoun
    cannot be what decides: the commas are. Those are the cards that teach the rule
    instead of rewarding a guess. The labelled twin ("which (defining)") used to carry
    that contrast, and it was the label the operator rejected — here the same contrast is
    carried by the picker, and the pool must still hold it.
    """
    by_kind: dict[str, set[str]] = {"defining": set(), "non-defining": set()}
    for spec in RCK_QUESTIONS:
        by_kind[sentence_classification(spec.sentence)].add(spec.correct)
    assert by_kind["defining"] & by_kind["non-defining"], (
        "no pronoun is correct under both kinds: the comma would have nothing to decide"
    )


def test_a_that_answer_between_commas_is_refused_by_verify() -> None:
    """The grammar truth is enforced, not merely respected by the data."""
    index = next(
        i for i, spec in enumerate(RCK_QUESTIONS)
        if sentence_classification(spec.sentence) == "non-defining"
        and "that" in spec.options
    )
    item = RCK_TOPIC.generate(make_rng(7, RCK_TOPIC.id, "easy", index), "easy", 7, index)
    forged = type(item)(**{**item.__dict__, "answer": type(item.answer)(
        latex=item.answer.latex,
        kind=item.answer.kind,
        payload={**item.answer.payload, "correct": ["that"]},
    )})
    result = RCK_TOPIC.verify(forged)
    assert not result.ok
    assert result.reason == "that_in_non_defining"


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


# --- Present Perfect, the medium level -------------------------------------
# The page `english-present-perfect` publishes the easy level. These tests guard the
# second exercise: it must be a distinct topic with its own pool, never the easy pool
# under a medium label, and its questions must carry the sibling's depth.


def test_present_perfect_medium_pool_is_rich_and_well_formed() -> None:
    """Twenty questions, twenty statements, and four options of which one is right."""
    assert len(PPM_MEDIUM) >= 20, "a batch of 20 needs at least 20 questions"
    assert len({spec.sentence for spec in PPM_MEDIUM}) == len(PPM_MEDIUM), "duplicate sentence"
    for spec in PPM_MEDIUM:
        assert len(spec.options) == 4, spec.sentence
        assert len(set(spec.options)) == 4, spec.sentence
        assert spec.correct in spec.options, spec.sentence
        assert "______" in spec.sentence, spec.sentence

        for text in (spec.explanation, spec.clue, spec.rule):
            assert text.strip(), spec.sentence
            # the text is wrapped in \text{...}: a LaTeX special would break the render
            assert not set(text) & set("%&$#_\\{}"), (spec.sentence, text)

        # the clue carries the diagnostic signal, not the answer
        assert spec.correct.lower() not in spec.clue.lower(), spec.sentence
        # the explanation is the WHY: it names the form and at least one tempting twin
        assert "present perfect" in spec.explanation.lower(), spec.sentence
        assert any(option != spec.correct and option in spec.explanation for option in spec.options), (
            "the explanation must say why the tempting option fails", spec.sentence
        )


def test_present_perfect_medium_weighs_the_two_aspects_against_each_other() -> None:
    """The level exists to make Simple and Continuous argue on the same sentence.

    Most questions offer both aspects of the same verb, and neither aspect may win the
    whole pool: a level that is all Simple (or all Continuous) would not be a choice.
    """
    both = [spec for spec in PPM_MEDIUM if {aspect(o) for o in spec.options} >= {"simple", "continuous"}]
    assert len(both) >= 15, "the twin form must be on the table, or there is nothing to choose"
    simple = [spec for spec in PPM_MEDIUM if aspect(spec.correct) == "simple"]
    continuous = [spec for spec in PPM_MEDIUM if aspect(spec.correct) == "continuous"]
    assert len(simple) >= 8, "too few Simple answers: the Continuous would win by habit"
    assert len(continuous) >= 8, "too few Continuous answers: the Simple would win by habit"


def test_present_perfect_medium_for_and_since_are_both_on_the_table() -> None:
    """`for` and `since` are the two signals the level is built on: each must appear."""
    assert any(" since " in spec.sentence for spec in PPM_MEDIUM), "no question with 'since'"
    assert any(" for " in spec.sentence for spec in PPM_MEDIUM), "no question with 'for'"


def test_verbs_of_state_never_take_the_continuous_form() -> None:
    """know, own, believe, possessive have: the -ing twin is offered, and it is wrong."""
    statives = [spec for spec in PPM_MEDIUM if asks_for_a_continuous_form(spec.sentence)]
    assert len(statives) >= 3, "the level must exercise verbs of state"
    for spec in statives:
        assert aspect(spec.correct) == "simple", spec.sentence
        assert any(aspect(option) == "continuous" for option in spec.options), spec.sentence


def test_a_continuous_answer_for_a_verb_of_state_is_refused_by_verify() -> None:
    """The grammar truth is enforced, not merely respected by the data."""
    index = next(
        i for i, spec in enumerate(PPM_MEDIUM) if verb_hint(spec.sentence) == "know"
    )
    rng = make_rng(7, PPM_TOPIC.id, "medium", index)
    item = PPM_TOPIC.generate(rng, "medium", 7, index)
    forged = type(item.answer)(
        latex=item.answer.latex,
        kind=item.answer.kind,
        payload={**item.answer.payload, "correct": ["has been knowing"]},
    )
    result = PPM_TOPIC.verify(type(item)(**{**item.__dict__, "answer": forged}))
    assert not result.ok
    assert result.reason == "stative_in_continuous"


def test_a_statement_without_a_blank_is_refused_by_verify() -> None:
    rng = make_rng(7, PPM_TOPIC.id, "medium", 0)
    item = PPM_TOPIC.generate(rng, "medium", 7, 0)
    broken = type(item)(**{**item.__dict__, "statement_key": "She has known the answer since Monday."})
    result = PPM_TOPIC.verify(broken)
    assert not result.ok
    assert result.reason == "missing_blank"


def test_present_perfect_medium_is_the_second_level_of_the_topic() -> None:
    """Two pages over the same grammar: one easy, one medium, each backed by its own topic."""
    easy_page = find_page("english-present-perfect")
    medium_page = find_page("english-present-perfect-medium")
    assert easy_page is not None and medium_page is not None

    assert medium_page.macro == "english"
    assert medium_page.sub == "grammatica"
    assert medium_page.kind == "multiple_choice"
    assert medium_page.count == 20
    assert medium_page.topic == PPM_TOPIC.id
    assert PPM_TOPIC.id in TOPICS

    # the two pages are different levels of the same grammar, not the same page twice
    assert (easy_page.difficulty, medium_page.difficulty) == ("easy", "medium")
    assert easy_page.topic != medium_page.topic
    assert PPM_TOPIC.difficulties == ("medium",), (
        "no easy level under a medium label: a level this pool does not have must be refused"
    )

    strings = load_strings("it")
    assert strings[medium_page.label_key].strip()
    assert strings[PPM_TOPIC.label_key].strip()
    # the two entries must be tellable apart in the menu
    assert strings[medium_page.label_key] != strings[easy_page.label_key]


def test_present_perfect_medium_serves_twenty_distinct_questions_and_one_level() -> None:
    base = "/api/generate?topic=english.grammar.present_perfect_medium&seed=12345&count=20"

    response = client.get(f"{base}&difficulty=medium")
    assert response.status_code == 200, response.text
    statements = [item["statement"]["key"] for item in response.json()["items"]]
    assert len(statements) == 20
    assert len(set(statements)) == 20, "a batch of 20 must be 20 distinct questions"

    refused = client.get(f"{base}&difficulty=easy")
    assert refused.status_code == 400, "a level this topic does not have must be refused"
    assert refused.json()["error"]["code"] == "invalid_difficulty"

    pages = client.get("/api/pages").json()["pages"]
    served = next(page for page in pages if page["id"] == "english-present-perfect-medium")
    assert served["difficulty"] == "medium"
    assert served["difficulties"] == ["medium"]


def test_the_correct_answer_is_not_always_the_first_option() -> None:
    """A batch of 20 must spread the answer over the four positions.

    The shuffling is deterministic (a reload shows the same card), so a pool whose data
    happen to land the answer first every time would teach the student to press A. The
    spread is checked on a full batch, which is what a page asks for.
    """
    response = client.get(
        "/api/generate?topic=english.grammar.present_perfect_medium&difficulty=medium"
        "&seed=12345&count=20"
    )
    assert response.status_code == 200, response.text
    positions = [
        item["answer"]["payload"]["options"].index(item["answer"]["payload"]["correct"][0])
        for item in response.json()["items"]
    ]
    assert len(positions) == 20
    for position in range(4):
        assert 2 <= positions.count(position) <= 8, (
            f"the correct answer sits in position {position} {positions.count(position)} "
            f"times out of 20: the position is a habit, not a coincidence"
        )


# --- Relative clauses: one page, the kind chosen before the pronoun ---------
# The operator rejected the previous page for a reason that is a design rule: an option
# written as "who (defining)" repeats the correct classification across the four options,
# so the answer is readable off the pattern instead of the commas. The page
# `english-relative-classification` therefore asks the kind separately, with a selector
# (frontend: `web/src/pages.js`, kind `classification_choice`) and grades both answers.
# On 2026-11-11 the operator held this page up as the model and asked for the other two
# relative pages to become this one, so these tests now hold the merged pool: one page,
# every card answerable only by reading the punctuation, and the absorbed grammar points
# (`which` for a whole clause, a preposition before `which`, `who` as object, `where`
# between commas) really on the page.


def test_the_relative_pool_is_the_batch_and_holds_the_absorbed_grammar() -> None:
    # MAX_COUNT is 20, so a pool longer than the batch would leave cards the page can
    # never serve: the merged pool is exactly the batch.
    assert len(RCK_QUESTIONS) == 20, "the pool must be the batch the page asks for"
    sentences = [spec.sentence for spec in RCK_QUESTIONS]
    assert len(set(sentences)) == len(sentences), "duplicate sentence in the pool"

    # No sentence of this pool is already elsewhere in the English macro: the page has one
    # subject, and a sentence shared with another page would be the same exercise twice.
    existing = {
        spec.sentence
        for pool in (PPS_EASY, PPM_MEDIUM, PPSC_QUESTIONS)
        for spec in pool
    }
    assert set(sentences) & existing == set(), "a sentence was copied from another page"

    # The four cards absorbed from the fused pages carry grammar this pool did not have.
    absorbed = {
        "He arrived twenty minutes late, ______ annoyed the teacher greatly.": (
            "which", "non-defining"),
        "The village in ______ my grandparents lived had no paved roads.": (
            "which", "defining"),
        "The woman ______ you were talking to at the reception is the CEO.": (
            "who", "defining"),
        "The villa, ______ we spent the summer, has a view of the lake.": (
            "where", "non-defining"),
    }
    by_sentence = {spec.sentence: spec for spec in RCK_QUESTIONS}
    for sentence, (pronoun, kind) in absorbed.items():
        assert sentence in by_sentence, f"absorbed card missing: {sentence}"
        spec = by_sentence[sentence]
        assert spec.correct == pronoun, sentence
        assert sentence_classification(sentence) == kind, sentence
    # and the trap the operator asked never to lose is still on the page: 'that' offered
    # between commas, where it can only be wrong
    assert any(
        "that" in spec.options and sentence_classification(spec.sentence) == "non-defining"
        for spec in RCK_QUESTIONS
    ), "'that' after a comma: the rule is not taught"

    for spec in RCK_QUESTIONS:
        assert len(spec.options) == 4, spec.sentence
        assert len(set(spec.options)) == 4, spec.sentence
        assert spec.correct in spec.options, spec.sentence

        # an option is a pronoun and nothing else: no classification rides along with it
        assert all(option in RCK_PRONOUNS for option in spec.options), spec.sentence
        # and no label anywhere in the sentence, in either spelling
        assert "(" not in spec.sentence and ")" not in spec.sentence, spec.sentence
        assert "defining" not in spec.sentence.lower(), spec.sentence

        kind = sentence_classification(spec.sentence)
        assert kind in RCK_CLASSIFICATIONS, spec.sentence

        # 'that' never introduces a clause between commas ...
        assert not (spec.correct == "that" and kind == "non-defining"), spec.sentence
        # ... and is never offered in a defining card, where 'who' or 'which' would be
        # equally right and the card would carry two correct answers
        assert not (kind == "defining" and "that" in spec.options), spec.sentence

        for text in (spec.explanation, spec.clue, spec.rule):
            assert text.strip(), spec.sentence
            # the text is wrapped in \text{...}: a LaTeX special would break the render
            assert not set(text) & set("%&$#_\\{}"), (spec.sentence, text)

        # the explanation is the WHY: it names the kind first, and one tempting twin after
        explanation = spec.explanation.lower()
        assert explanation.startswith(f"{kind}:"), spec.sentence
        assert "virgol" in explanation, spec.sentence
        assert any(option != spec.correct and option in spec.explanation
                   for option in spec.options), (
            "the explanation must say why a tempting option fails", spec.sentence
        )
        # the clue carries the diagnostic signal and never the answer: it names no pronoun
        for pronoun in RCK_PRONOUNS:
            assert not re.search(rf"\b{pronoun}\b", spec.clue, re.I), (spec.sentence, pronoun)


def test_relative_classification_serves_twenty_distinct_questions_in_pool_order() -> None:
    rng = make_rng(1, RCK_TOPIC.id, "easy", 0)
    for i in range(20):
        item = RCK_TOPIC.generate(rng, "easy", 1, i)
        assert item.statement_key == RCK_QUESTIONS[i].sentence
        assert RCK_TOPIC.verify(item).ok

    base = "/api/generate?topic=english.grammar.relative_classification&seed=12345&count=20"
    response = client.get(f"{base}&difficulty=easy")
    assert response.status_code == 200, response.text
    items = response.json()["items"]
    assert len(items) == 20
    statements = [item["statement"]["key"] for item in items]
    assert len(set(statements)) == 20, "a batch of 20 must be 20 distinct questions"
    assert not any("defining" in statement.lower() for statement in statements), (
        "the sentence must not carry the label: the kind is a question, not a printed hint"
    )

    kinds = set()
    for item in items:
        payload = item["answer"]["payload"]
        assert payload["classification"][0] in RCK_CLASSIFICATIONS, item["statement"]["key"]
        kinds.add(payload["classification"][0])
        for option in payload["options"]:
            assert option in RCK_PRONOUNS, item["statement"]["key"]
            assert "(" not in option, item["statement"]["key"]
    # both kinds are on the page, with a selector showing two options only
    assert kinds == set(RCK_CLASSIFICATIONS), "one kind only: the selector would have one answer"

    refused = client.get(f"{base}&difficulty=medium")
    assert refused.status_code == 400, "a level this topic does not have must be refused"
    assert refused.json()["error"]["code"] == "invalid_difficulty"


def test_the_chosen_kind_must_be_the_one_the_commas_show() -> None:
    """The grammar truth is enforced by verify, not merely respected by the data."""
    seed = 7
    non_defining = next(
        i for i, spec in enumerate(RCK_QUESTIONS)
        if sentence_classification(spec.sentence) == "non-defining"
    )
    item = RCK_TOPIC.generate(make_rng(seed, RCK_TOPIC.id, "easy", non_defining),
                              "easy", seed, non_defining)
    forged = type(item)(
        **{**item.__dict__, "answer": type(item.answer)(
            latex=item.answer.latex,
            kind=item.answer.kind,
            payload={**item.answer.payload, "classification": ["defining"]},
        )}
    )
    result = RCK_TOPIC.verify(forged)
    assert not result.ok
    assert result.reason == "classification_mismatch"

    # a pronoun with the classification written beside it is the label the operator
    # rejected: a card like that cannot be answered, only decoded
    branded = type(item)(
        **{**item.__dict__, "answer": type(item.answer)(
            latex=item.answer.latex,
            kind=item.answer.kind,
            payload={**item.answer.payload,
                     "options": [f"{item.answer.payload['correct'][0]} (defining)",
                                 "which", "whose", "where"]},
        )}
    )
    assert RCK_TOPIC.verify(branded).reason == "option_is_not_a_bare_pronoun"

    # and a sentence that prints its own classification is refused the same way
    labelled = type(item)(**{
        **item.__dict__,
        "statement_key": "The nurse ______ looked after my father works here (non-defining).",
    })
    assert RCK_TOPIC.verify(labelled).reason == "statement_carries_the_label"

    # a card with no blank is a broken question, not a hard one
    blankless = type(item)(**{**item.__dict__, "statement_key": "The nurse looked after my father."})
    assert RCK_TOPIC.verify(blankless).reason == "missing_blank"


def test_the_classification_page_is_the_only_relative_page() -> None:
    page = find_page("english-relative-classification")
    assert page is not None, "the surviving page is not in the catalogue"
    assert page.macro == "english"
    assert page.sub == "grammatica"
    assert page.kind == "classification_choice"
    assert page.kind in KINDS
    assert page.count == 20
    assert page.topic == RCK_TOPIC.id
    assert RCK_TOPIC.id in TOPICS
    assert RCK_TOPIC.difficulties == ("easy",), (
        "one level only: a level this pool does not have must be refused, not served under "
        "another name"
    )

    # The catalogue changed on the operator's request (task-281711): the page that wrote
    # the classification inside every option is gone, so no option on the site carries a
    # label any more, and the two removed ids are not served.
    assert all("(" not in option for spec in RCK_QUESTIONS for option in spec.options)
    served_pages = client.get("/api/pages").json()["pages"]
    served_ids = {p["id"] for p in served_pages}
    assert "english-relative-classification" in served_ids
    for removed in ("english-relative-clauses", "english-relative-defining-non-defining"):
        assert removed not in served_ids, f"{removed} is still served"

    strings = load_strings("it")
    assert strings[page.label_key].strip()
    assert strings[RCK_TOPIC.label_key].strip()
    english_labels = [strings[p.label_key] for p in PAGES if p.macro == "english"]
    assert len(set(english_labels)) == len(english_labels), "two pages share a label"

    served = next(p for p in client.get("/api/pages").json()["pages"] if p["id"] == page.id)
    assert served["kind"] == "classification_choice"
    assert served["count"] == 20
    assert served["difficulties"] == ["easy"]


# --- Present Perfect Simple vs Continuous, and the pronoun: one page, two moves ---
# The operator asked for an online page, not a PDF, and for the interaction the site
# already had: the kind of the sentence is chosen first and the check is born disabled
# (`classification_choice`). This pool is what backs it — three groups of statements in
# the order the schema lists them, and two facts graded per card.


def test_present_perfect_simple_continuous_pool_is_new_and_well_formed() -> None:
    assert len(PPSC_QUESTIONS) >= 20, "a batch of 20 needs at least 20 questions"
    sentences = [spec.sentence for spec in PPSC_QUESTIONS]
    assert len(set(sentences)) == len(sentences), "duplicate sentence in the pool"

    # A new page, not the same questions with a new label: no sentence of this pool
    # appears in any pool already on the site (the intersection is empty).
    existing = {
        spec.sentence
        for pool in (PPS_EASY, PPM_MEDIUM, RCK_QUESTIONS)
        for spec in pool
    }
    assert set(sentences) & existing == set(), "a sentence was copied from an existing pool"

    for spec in PPSC_QUESTIONS:
        assert len(spec.options) == 4, spec.sentence
        assert len(set(spec.options)) == 4, spec.sentence
        assert spec.correct in spec.options, spec.sentence
        assert "______" in spec.sentence, spec.sentence

        for text in (spec.explanation, spec.clue, spec.rule):
            assert text.strip(), spec.sentence
            # the text is wrapped in \text{...}: a LaTeX special would break the render
            assert not set(text) & set("%&$#_\\{}"), (spec.sentence, text)

        # the family is one of the two the picker knows, and the claimed kind is one of the
        # two values that picker shows
        assert spec.family in PPSC_CLASSIFICATIONS, spec.sentence
        assert spec.classification in [value for value, _ in PPSC_CLASSIFICATIONS[spec.family]]

        # the hint names the diagnostic signal, never the answer
        assert spec.correct.lower() not in spec.clue.lower(), spec.sentence

        if spec.family == "verb":
            # the explanation is the WHY of the aspect, and it names the tempting twin
            assert "present perfect" in spec.explanation.lower(), spec.sentence
            # quoted in the running text, a sentence-initial option loses its capital
            explanation = spec.explanation.lower()
            assert any(option != spec.correct and option.lower() in explanation
                       for option in spec.options), (
                "the explanation must say why a tempting option fails", spec.sentence
            )


def test_the_page_keeps_the_progression_the_schema_asks_for() -> None:
    """10 by indicator, 5 that only the Simple can answer, 6 on the pronoun."""
    verb_cards = [spec for spec in PPSC_QUESTIONS if spec.family == "verb"]
    clause_cards = [spec for spec in PPSC_QUESTIONS if spec.family == "clause"]
    by_indicator = [spec for spec in verb_cards if spec.classification == "action"]
    stative = [spec for spec in verb_cards if spec.classification == "state"]

    assert 8 <= len(by_indicator) <= 10, "8-10 statements decide by the indicator"
    assert len(stative) >= 4, "4-5 cards where the Continuous is impossible"
    assert 4 <= len(clause_cards) <= 6, "4-6 statements on the relative pronouns"

    # neither aspect wins the first group by habit, and the twin is always on the table
    assert {aspect_of(spec.correct) for spec in by_indicator} == {"simple", "continuous"}
    for spec in by_indicator:
        assert aspect_of(spec.correct) in ("simple", "continuous"), spec.sentence
        assert any(aspect_of(option) != aspect_of(spec.correct) for option in spec.options), (
            "the other aspect must be offered, or there is nothing to choose", spec.sentence
        )

    # a verb of state: the Simple is right and the -ing twin is offered and wrong
    for spec in stative:
        assert aspect_of(spec.correct) == "simple", spec.sentence
        assert any(aspect_of(option) == "continuous" for option in spec.options), spec.sentence

    # the indicators of the schema are really in the sentences
    def has(word: str) -> bool:
        return any(word in spec.sentence.lower() for spec in by_indicator)

    for marker in ("already", "just", "yet", "ever", "so far", "recently", "lately",
                   "all morning", "for two hours", "since"):
        assert has(marker), f"no statement carries {marker}"

    # the relative cards claim the class their commas show, and the forbidden `that` after
    # a comma is on the page, offered where it can only be wrong
    for spec in clause_cards:
        assert spec.classification == sentence_classification(spec.sentence), spec.sentence
        assert all(option in RCK_PRONOUNS for option in spec.options), spec.sentence
        assert not (spec.correct == "that" and spec.classification == "non-defining"), spec.sentence
        assert not ("that" in spec.options and spec.classification == "defining"), spec.sentence
    comma_that = [spec for spec in clause_cards if "that" in spec.options]
    assert comma_that, "'that' is never offered after a comma: the rule is not taught"
    for spec in comma_that:
        assert spec.classification == "non-defining", spec.sentence
        assert spec.correct != "that", spec.sentence


def test_the_picker_travels_in_the_payload_not_in_the_client() -> None:
    """Which question is asked, and with which two values, is data the server sends."""
    strings = load_strings("it")
    seen_families = set()
    for index in range(len(PPSC_QUESTIONS)):
        item = PPSC_TOPIC.generate(make_rng(4242, PPSC_TOPIC.id, "medium", index),
                                   "medium", 4242, index)
        assert PPSC_TOPIC.verify(item).ok, PPSC_TOPIC.verify(item).reason
        payload = item.answer.payload
        family = PPSC_QUESTIONS[index].family
        seen_families.add(family)

        values = payload["classification_values"]
        labels = payload["classification_labels"]
        assert values == [value for value, _ in PPSC_CLASSIFICATIONS[family]]
        assert len(labels) == len(values)
        assert all(label in strings and strings[label].strip() for label in labels), labels

        # the two lines that explain the lock and the mistake follow the same grammar, and
        # so does the line that names what was answered wrong
        for key in ("classification_prompt_key", "classification_locked_key",
                    "classification_wrong_key", "option_wrong_key"):
            assert len(payload[key]) == 1, (family, key)
            assert payload[key][0] in strings and strings[payload[key][0]].strip(), key

        # and the kind the card asks for is the one the sentence itself shows
        assert payload["classification"][0] == expected_classification(
            item.statement_key, tuple(payload["options"])), item.statement_key
    assert seen_families == {"verb", "clause"}, "one picker only: a group lost its question"


def test_verify_refuses_the_continuous_on_a_verb_of_state() -> None:
    """The grammar truth is enforced, not merely respected by the data."""
    index = next(i for i, spec in enumerate(PPSC_QUESTIONS) if spec.classification == "state")
    spec = PPSC_QUESTIONS[index]
    continuous = next(option for option in spec.options if aspect_of(option) == "continuous")
    item = PPSC_TOPIC.generate(make_rng(3, PPSC_TOPIC.id, "medium", index), "medium", 3, index)
    forged = type(item)(**{**item.__dict__, "answer": type(item.answer)(
        latex=item.answer.latex,
        kind=item.answer.kind,
        payload={**item.answer.payload, "correct": [continuous]},
    )})
    result = PPSC_TOPIC.verify(forged)
    assert not result.ok
    assert result.reason == "stative_in_continuous"


def test_verify_refuses_that_between_commas() -> None:
    index = next(i for i, spec in enumerate(PPSC_QUESTIONS)
                 if "that" in spec.options and spec.classification == "non-defining")
    item = PPSC_TOPIC.generate(make_rng(3, PPSC_TOPIC.id, "medium", index), "medium", 3, index)
    forged = type(item)(**{**item.__dict__, "answer": type(item.answer)(
        latex=item.answer.latex,
        kind=item.answer.kind,
        payload={**item.answer.payload, "correct": ["that"]},
    )})
    assert PPSC_TOPIC.verify(forged).reason == "that_in_non_defining"


def test_verify_refuses_a_label_a_missing_blank_and_a_foreign_picker() -> None:
    item = PPSC_TOPIC.generate(make_rng(3, PPSC_TOPIC.id, "medium", 0), "medium", 3, 0)

    labelled = type(item)(**{
        **item.__dict__,
        "statement_key": "I ______ (already / send) it, so she has it (azione).",
    })
    assert PPSC_TOPIC.verify(labelled).reason == "statement_carries_the_label"

    blankless = type(item)(**{**item.__dict__, "statement_key": "I have already sent it."})
    assert PPSC_TOPIC.verify(blankless).reason == "missing_blank"

    # a picker that asks about the relative clause on a card about a verb of state is the
    # opposite page: the values are checked against the card, not trusted
    foreign = type(item)(**{**item.__dict__, "answer": type(item.answer)(
        latex=item.answer.latex,
        kind=item.answer.kind,
        payload={**item.answer.payload,
                 "classification_values": ["defining", "non-defining"],
                 "classification_labels": ["ui.classification_defining",
                                           "ui.classification_non_defining"]},
    )})
    assert PPSC_TOPIC.verify(foreign).reason == "picker_does_not_match_the_card"

    # a kind that contradicts the sentence is a broken question, not a hard one
    wrong_kind = type(item)(**{**item.__dict__, "answer": type(item.answer)(
        latex=item.answer.latex,
        kind=item.answer.kind,
        payload={**item.answer.payload, "classification": ["state"]},
    )})
    assert PPSC_TOPIC.verify(wrong_kind).reason == "classification_mismatch"


def test_the_choice_page_is_a_new_catalogue_entry() -> None:
    page = find_page("english-present-perfect-simple-continuous")
    assert page is not None, "the new page is not in the catalogue"
    assert page.macro == "english"
    assert page.sub == "grammatica"
    assert page.kind == "classification_choice"
    assert page.kind in KINDS
    assert page.count == 20, "a batch of 20: MAX_COUNT is 20, so the count cannot be raised"
    assert page.topic == PPSC_TOPIC.id
    assert PPSC_TOPIC.id in TOPICS
    assert PPSC_TOPIC.difficulties == ("medium",), (
        "one level only: a level this pool does not have is refused, not served under "
        "another name"
    )

    # the page it borrows the interaction from stays exactly as it was
    sibling = find_page("english-relative-classification")
    assert sibling is not None and sibling.id != page.id
    assert sibling.topic != page.topic
    assert sibling.kind == page.kind

    strings = load_strings("it")
    assert strings[page.label_key].strip()
    assert strings[PPSC_TOPIC.label_key].strip()
    english_pages = [p for p in PAGES if p.macro == "english"]
    labels = [strings[p.label_key] for p in english_pages]
    assert len(set(labels)) == len(labels), "two pages share a label in the menu"

    served = next(p for p in client.get("/api/pages").json()["pages"] if p["id"] == page.id)
    assert served["kind"] == "classification_choice"
    assert served["count"] == 20
    assert served["difficulties"] == ["medium"]


def test_the_choice_page_serves_twenty_distinct_questions_in_pool_order() -> None:
    rng = make_rng(1, PPSC_TOPIC.id, "medium", 0)
    for i in range(20):
        item = PPSC_TOPIC.generate(rng, "medium", 1, i)
        assert item.statement_key == PPSC_QUESTIONS[i].sentence
        assert PPSC_TOPIC.verify(item).ok, PPSC_TOPIC.verify(item).reason

    base = f"/api/generate?topic={PPSC_TOPIC.id}&seed=12345&count=20"
    response = client.get(f"{base}&difficulty=medium")
    assert response.status_code == 200, response.text
    items = response.json()["items"]
    assert len(items) == 20
    statements = [item["statement"]["key"] for item in items]
    assert len(set(statements)) == 20, "a batch of 20 must be 20 distinct questions"

    # the answer position is a coincidence, not a habit
    positions = [
        item["answer"]["payload"]["options"].index(item["answer"]["payload"]["correct"][0])
        for item in items
    ]
    for position in range(4):
        assert 2 <= positions.count(position) <= 8, (
            f"the correct answer sits in position {position} {positions.count(position)} "
            "times out of 20"
        )

    # both pickers are on the page, and every card carries its own question
    prompts = {
        item["answer"]["payload"]["classification_prompt_key"][0] for item in items
    }
    assert prompts == {"ui.classification_prompt_verb", "ui.classification_prompt"}

    refused = client.get(f"{base}&difficulty=easy")
    assert refused.status_code == 400, "a level this topic does not have must be refused"
    assert refused.json()["error"]["code"] == "invalid_difficulty"


def test_the_choice_page_prints_its_worksheet() -> None:
    """The same batch must still export: the statements carry the blank and the answers key."""
    strings = load_strings("it")
    items = [PPSC_TOPIC.generate(make_rng(42, PPSC_TOPIC.id, "medium", i), "medium", 42, i)
             for i in range(3)]
    html = worksheet_html(items, answers=False, strings=strings)
    assert '<ol class="options"' in html
    assert items[0].statement_key in html
    html_answers = worksheet_html(items, answers=True, strings=strings)
    assert '<section class="key">' in html_answers
