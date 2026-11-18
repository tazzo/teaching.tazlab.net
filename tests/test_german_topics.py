"""The German section: the content gate the operator asked for, page by page.

The five pages of «Tedesco» are data — pools of cards in ``app/generators/german/`` — and
this file is what keeps the data honest, because a worksheet for a ten-year-old cannot be
reviewed card by card at every change. What it measures, and why each one is here:

* **every exercise has a solution** — a card without one is not an exercise; a completion
  must carry its accepted spellings (the solution first), a multiple choice must have its
  correct form among the four options and four *distinct* options;
* **the section is in the index** — ``/api/pages`` must serve the macro, its four
  sub-topics and its five pages, with labels that exist and are distinct, because a page
  nobody can reach is a page nobody has;
* **no repetition between pages** — the same sentence on two pages is the duplicate the
  operator refused for the relative clauses, and it is refused here too, across all five
  German pools and against the English ones already on the site;
* **each page explains itself** — an intro of three to six lines in Italian with the
  examples in German, and a page count inside the 15-20 the operator asked for;
* **Italian explains, German speaks** — the explanations are Italian, and the German
  spelling survives the wire with its umlauts and its ß;
* **the verifier can fail** — five deliberately broken cards are refused with a reason,
  because a verifier that cannot say no is not a verifier.

The served path is measured too (``/api/generate``), not only the objects: the site is
what the server answers.
"""

from __future__ import annotations

import re

import pytest
from fastapi.testclient import TestClient

from app.core.rng import make_rng
from app.core.strings import load_strings
from app.generators.german.practice import GAP
from app.generators.registry import TOPICS
from app.main import app
from app.pages import KINDS, PAGES, find_page
from app.render.pdf import worksheet_html

client = TestClient(app)

GERMAN_PAGES = [page for page in PAGES if page.macro == "tedesco"]
GERMAN_TOPICS = [TOPICS[page.topic] for page in GERMAN_PAGES]

#: Italian words that explanations and intros are made of. The German content is full of
#: German words, so the check is "contains Italian glue", not "contains no German".
ITALIAN = (" il ", " la ", " di ", " che ", " non ", " si ", " un ", " una ", " con ", " in ",
           " per ", " del ", " della ", " è ", " sono ", " anche ", " come ", " dice ",
           " vale ", " dopo ", " prima ")


def italian(text: str) -> bool:
    padded = f" {text.lower()} "
    return any(word in padded for word in ITALIAN)


def items_of(topic, count: int | None = None):
    total = count if count is not None else len(topic.cards)
    return [topic.generate(make_rng(1, topic.id, "easy", index), "easy", 1, index)
            for index in range(total)]


# ------------------------------------------------------------------ the catalogue


def test_the_section_is_in_the_index_the_client_reads() -> None:
    """`Tedesco` must be a voice of the menu, not an orphan page with a URL."""
    served = client.get("/api/pages").json()
    assert "tedesco" in served["macros"], "the section is not in the macro list"
    assert served["subs"]["tedesco"] == ["1a", "1b", "1c", "zahlen"], (
        "the four topics of Einheit 1, in the order of the book"
    )

    ids = [page["id"] for page in served["pages"] if page["macro"] == "tedesco"]
    assert ids == [
        "tedesco-1a-laender-kommen",
        "tedesco-1b-artikel",
        "tedesco-1b-possessivi",
        "tedesco-1c-familie",
        "tedesco-zahlen",
    ], "five pages: 1A, 1B articles, 1B possessives, 1C, Zahlen"

    strings = load_strings("it")
    assert strings["macro.tedesco"] == "Tedesco"
    labels = [strings[page["label_key"]] for page in served["pages"]
              if page["macro"] == "tedesco"]
    assert all(label.strip() for label in labels), "a page without a label has no name"
    assert len(set(labels)) == len(labels), "two pages share a label in the menu"
    topic_labels = [strings[TOPICS[page.topic].label_key] for page in GERMAN_PAGES]
    assert all(label.strip() for label in topic_labels)


def test_every_page_pins_one_level_eighteen_cards_and_its_own_kind() -> None:
    for page in GERMAN_PAGES:
        assert page.kind in KINDS
        assert page.kind == "completion_choice"
        assert page.difficulty == "easy", "one level: the order of the pool is the difficulty"
        assert page.count == 18, "fifteen to twenty per page, and MAX_COUNT is 20"
        assert TOPICS[page.topic].difficulties == ("easy",), (
            "a level this pool does not have must be refused, not served under another name"
        )


def test_each_page_opens_with_an_intro_in_italian_and_its_german_examples() -> None:
    strings = load_strings("it")
    for page in GERMAN_PAGES:
        assert page.intro_key, f"{page.id} has no intro"
        intro = strings.get(page.intro_key, "")
        lines = [line for line in intro.split("\n") if line.strip()]
        assert 3 <= len(lines) <= 6, f"{page.id}: intro of {len(lines)} lines"
        assert italian(intro), f"{page.id}: the intro is not in Italian"
        assert any(word in intro for word in ("der ", "die ", "das ", "ich ", "du ",
                                              "mein ", "dein ", "heiße ", "zwei ", "drei ",
                                              "sieben ", "zwanzig ")), (
            f"{page.id}: the intro carries no German example"
        )


# ------------------------------------------------------------------- the content


def test_every_exercise_has_a_solution_and_a_reason() -> None:
    for topic in GERMAN_TOPICS:
        for item in items_of(topic):
            assert topic.verify(item).ok, (topic.id, item.index, topic.verify(item).reason)
            payload = item.answer.payload
            assert payload["correct"] and payload["correct"][0].strip(), (
                f"{topic.id} #{item.index + 1}: no solution"
            )
            assert payload["explanation"][0].strip(), (
                f"{topic.id} #{item.index + 1}: no reason after the answer"
            )
            assert italian(payload["explanation"][0]), (
                f"{topic.id} #{item.index + 1}: the explanation is not in Italian"
            )


def test_every_multiple_choice_solution_is_one_of_its_options() -> None:
    choices = 0
    for topic in GERMAN_TOPICS:
        for item in items_of(topic):
            payload = item.answer.payload
            if payload["format"][0] != "choice":
                continue
            choices += 1
            options = payload["options"]
            assert len(options) == 4, (topic.id, item.index)
            assert len(set(options)) == 4, "two identical options are a broken card"
            assert payload["correct"][0] in options, (
                f"{topic.id} #{item.index + 1}: the solution is not among the options"
            )
            # the answer is never written beside the option: bare forms only, no label
            for option in options:
                assert "(" not in option, (topic.id, item.index, option)
    assert choices >= 25, "both formats must be on the pages, and the choice is well used"


def test_every_completion_carries_its_spellings_and_the_solution_comes_first() -> None:
    completions = 0
    for topic in GERMAN_TOPICS:
        for item in items_of(topic):
            payload = item.answer.payload
            if payload["format"][0] != "completion":
                continue
            completions += 1
            assert payload["accept"], (topic.id, item.index)
            assert payload["accept"][0] == payload["correct"][0]
            assert len(set(payload["accept"])) == len(payload["accept"])
    assert completions >= 25, "both formats must be on the pages, and the completion is used"


def test_each_page_holds_both_formats() -> None:
    for page in GERMAN_PAGES:
        topic = TOPICS[page.topic]
        formats = [item.answer.payload["format"][0] for item in items_of(topic)]
        assert formats.count("completion") >= 6, f"{page.id}: too few completions"
        assert formats.count("choice") >= 6, f"{page.id}: too few multiple choices"
        assert len(formats) == 18


def test_no_exercise_is_repeated_between_pages() -> None:
    """One exercise, not two doubles — the rule of the relative pages, for all five pools."""
    seen: dict[str, str] = {}
    for page in GERMAN_PAGES:
        topic = TOPICS[page.topic]
        for item in items_of(topic):
            sentence = item.statement_key
            assert sentence not in seen, (
                f"«{sentence}» is on both {seen.get(sentence)} and {page.id}"
            )
            seen[sentence] = page.id
    assert len(seen) == 5 * 18

    # and a German card does not repeat an English one: the English pools are already there
    english = {item.statement_key for topic_id, topic in TOPICS.items()
               if topic.family == "english"
               for item in items_of(topic, len(getattr(topic, "cards", ())) or 20)}
    assert not (set(seen) & english), "a German card repeats an English one"


def test_a_batch_serves_both_formats_whatever_its_count() -> None:
    """«restino entrambe le tipologie» must hold for the batch, not only for the pool.

    A pool of nine completions and nine choices served in pool order gives a batch of two
    that is two completions: the kind the girl never meets is the kind the page does not
    have. The served order alternates the two (`serving_order`), so a batch of any size
    holds both — and a batch of eighteen opens with a completion and a choice inside its
    first three cards.
    """
    for page in GERMAN_PAGES:
        for count in (2, 3, 18):
            response = client.get(f"/api/generate?topic={page.topic}&difficulty=easy"
                                  f"&seed=7&count={count}")
            assert response.status_code == 200, response.text
            items = response.json()["items"]
            formats = [item["answer"]["payload"]["format"][0] for item in items]
            assert set(formats) == {"completion", "choice"}, (
                f"{page.id}: a batch of {count} holds only {set(formats)}"
            )
            if count == 18:
                assert set(formats[:3]) == {"completion", "choice"}, (
                    f"{page.id}: the first three cards are all {formats[0]} — on a 360 px "
                    "phone the other format is several screens down"
                )
                # difficulty is still order *inside* a format: the pool is easiest first
                topic = TOPICS[page.topic]
                for kind in ("completion", "choice"):
                    served = [item["statement"]["key"] for item in items
                              if item["answer"]["payload"]["format"][0] == kind]
                    pool = [card.sentence for card in topic.cards if card.format == kind]
                    assert served == pool, f"{page.id}: the {kind} cards left their order"


def test_the_batch_the_server_serves_is_eighteen_distinct_cards() -> None:
    for page in GERMAN_PAGES:
        response = client.get(f"/api/generate?topic={page.topic}&difficulty=easy"
                              "&seed=12345&count=18")
        assert response.status_code == 200, response.text
        items = response.json()["items"]
        assert len(items) == 18
        statements = [item["statement"]["key"] for item in items]
        assert len(set(statements)) == 18, f"{page.id}: a repeated card in one batch"
        for item in items:
            assert GAP in item["statement"]["key"], "every card carries the gap"
            assert item["answer"]["payload"]["correct"], "every card carries its solution"

        # the answer is not always in the same place: a coincidence would be a habit
        positions = [item["answer"]["payload"]["options"].index(
            item["answer"]["payload"]["correct"][0])
            for item in items if item["answer"]["payload"]["format"][0] == "choice"]
        assert len(positions) == 9
        assert len(set(positions)) >= 3, "the right option clusters in one place"


def test_the_level_a_page_does_not_have_is_refused() -> None:
    response = client.get("/api/generate?topic=german.zahlen&difficulty=medium"
                          "&seed=1&count=1")
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "invalid_difficulty"


# ------------------------------------------------------------------- the spelling

def test_german_survives_the_wire_with_its_umlauts_and_its_sz() -> None:
    strings = load_strings("it")
    assert "ä" in strings["intro.tedesco.unit1b_artikel"]
    assert "ß" in strings["intro.tedesco.zahlen"]

    words = set()
    for topic in GERMAN_TOPICS:
        for item in items_of(topic):
            words.add(item.statement_key)
            payload = item.answer.payload
            words.update(payload.get("options") or [])
            words.update(payload["accept"] if "accept" in payload else [])
    joined = " ".join(words)
    for expected in ("zwölf", "dreißig", "heiße", "fünfzehn", "Kaninchen", "Österreich"):
        assert expected in joined, f"«{expected}» is missing: an umlaut did not survive"

    # the ASCII transliteration is a spelling the field accepts, never the only spelling
    assert "dreissig" in joined and "dreißig" in joined


# ------------------------------------------------------------------ the verifier


def test_the_verifier_refuses_a_broken_card() -> None:
    topic = TOPICS["german.unit1a.laender"]
    base = items_of(topic, 1)[0]

    def corrupt(**payload_changes):
        payload = {**base.answer.payload, **payload_changes}
        answer = type(base.answer)(latex=base.answer.latex, kind=base.answer.kind,
                                   payload=payload)
        return type(base)(**{**base.__dict__, "answer": answer})

    # a solution that is not among the options
    choice_index = next(i for i, card in enumerate(topic.cards) if card.options)
    card_item = items_of(topic, choice_index + 1)[choice_index]
    options = card_item.answer.payload["options"]
    forged = type(card_item)(**{**card_item.__dict__, "answer": type(card_item.answer)(
        latex=card_item.answer.latex, kind=card_item.answer.kind,
        payload={**card_item.answer.payload, "correct": ["nicht_in_den_optionen"],
                 "options": options})})
    assert topic.verify(forged).reason == "correct_answer_does_not_match_the_card"

    # a completion with no accepted spelling
    assert topic.verify(corrupt(accept=[])).reason == "missing_accepted_spellings"

    # an accepted list that does not start with the solution
    assert topic.verify(corrupt(accept=["falsch", base.answer.payload["correct"][0]])).reason \
        == "accepted_spellings_do_not_start_with_the_solution"

    # a statement whose gap was filled in: the answer is printed, so there is nothing to ask
    filled = next(card for card in topic.cards
                  if card.correct.lower() not in card.sentence.lower())
    printed = type(base)(**{**base.__dict__,
                            "statement_key": filled.sentence.replace(GAP, filled.correct)})
    assert topic.verify(printed).reason == "missing_blank"

    # a sentence that is not a card of the pool: nothing to verify against
    unknown = type(base)(**{**base.__dict__, "statement_key": "Ich ______ aus Japan."})
    assert unknown.topic == topic.id
    assert topic.verify(unknown).reason == "unknown_statement"


def test_the_worksheet_still_prints() -> None:
    """The same cards must export: the statement carries the gap, the key carries the answers."""
    strings = load_strings("it")
    topic = TOPICS["german.zahlen"]
    items = items_of(topic, 3)
    html = worksheet_html(items, answers=False, strings=strings)
    for item in items:
        assert item.statement_key in html
    key = worksheet_html(items, answers=True, strings=strings)
    assert '<section class="key">' in key
    # one bold answer per card. The umlaut is not asserted as contiguous text: KaTeX draws
    # the diaeresis in its own span, so «zwölf» is not one string in the rendered HTML —
    # the card with no umlaut is the one read verbatim.
    assert key.count('class="mord textbf"') >= len(items)
    assert "sechzehn" in key
