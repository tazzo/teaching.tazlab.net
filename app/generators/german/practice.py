"""German for the first year of middle school: complete the gap, or choose, then read why.

The English pages are the model (``app/generators/english/``): a static pool of cards, a
``TOPIC`` object with ``generate``/``verify``, and the page in ``app/pages.py`` pointing at
it. What the operator asked for on the German section adds one thing the English pages do
not have: **each page carries both a completion and a multiple choice**, and both must
explain themselves *after* the answer. So the card says its own format in the payload
(``format`` = ``completion`` | ``choice``) and the page kind is one — ``completion_choice``
— because the layout is one: a sentence with a gap, a field or four options under it, and
the reason that appears once the student has answered.

The house rules that shaped this file:

* **the answer is never written beside the option** (the relative-clause lesson): the four
  options are bare forms, no ``der (maschile)`` label riding along, and the sentence never
  contains the word it asks for — ``verify`` refuses both.
* **one exercise, not two doubles**: the five pools are disjoint, and a test asserts it
  (``tests/test_german_topics.py``); a sentence may appear on exactly one page.
* **difficulty is order, not a label**: one level per page, and the pool is written from
  the easiest card to the hardest, because the girl meets them in that order.
* **Italian explains, German speaks**: clue, rule and explanation are Italian; the
  sentence, the options and the answers are German, umlauts included.
* **the keyboard is the only tool**: nothing here needs a mouse — the renderer gives every
  card a field (or four buttons) and a check button, and Enter in the field checks.
"""

from __future__ import annotations

import random
import re
from dataclasses import dataclass, field

from app.core.verify import VerificationResult
from app.generators.base import Answer, Item, Step

#: The gap every card carries. Six underscores: the same mark the English pages print, so
#: one renderer, one PDF template and one test read the same convention.
GAP = "______"

#: A word, for the "the answer is not printed in the sentence" check.
_WORD = re.compile(r"[A-Za-zÄÖÜäöüß]+")


@dataclass(frozen=True)
class Card:
    """One exercise: the sentence, how it is answered, the answer, and why.

    ``options`` empty means *completion*: the student types the missing word and the
    accepted spellings live in ``accept`` (the first one is the solution shown on screen).
    Four options mean *choice*: the student picks one, and the solution is ``correct``.
    ``clue`` and ``rule`` are the two steps a card carries — the diagnostic hint and the
    grammar rule — and never the answer (a step that printed it would hand over what the
    field is asking for).
    """

    sentence: str
    correct: str
    explanation: str
    clue: str
    rule: str
    options: tuple[str, ...] = ()
    accept: tuple[str, ...] = ()

    @property
    def format(self) -> str:
        return "choice" if self.options else "completion"

    def accepted(self) -> tuple[str, ...]:
        """The solution first, then the spellings the field also takes (``ss`` for ``ß``)."""
        spellings = [self.correct]
        for spelling in self.accept:
            if spelling not in spellings:
                spellings.append(spelling)
        return tuple(spellings)


def completion(sentence: str, correct: str, explanation: str, clue: str, rule: str,
               accept: tuple[str, ...] = ()) -> Card:
    return Card(sentence=sentence, correct=correct, explanation=explanation, clue=clue,
                rule=rule, accept=accept)


def choice(sentence: str, correct: str, options: tuple[str, str, str, str],
           explanation: str, clue: str, rule: str) -> Card:
    return Card(sentence=sentence, correct=correct, options=options, explanation=explanation,
                clue=clue, rule=rule)


class GermanPractice:
    """The shared topic: a pool, one level, and a verifier that refuses a broken card.

    Subclasses set ``id``, ``label_key`` and ``cards``. Everything else is here, so the
    five pages differ in content and not in machinery — the same reason the English topics
    share ``relative_grammar``.
    """

    id = ""
    family = "german"
    difficulties = ("easy",)
    label_key = ""
    scenarios: tuple[str, ...] = ()
    cards: tuple[Card, ...] = ()

    def card_for(self, sentence: str) -> Card | None:
        return next((card for card in self.cards if card.sentence == sentence), None)

    def generate(self, rng: random.Random, difficulty: str, seed: int, index: int,
                 options: dict | None = None) -> Item:
        card = self.cards[index % len(self.cards)]

        payload: dict[str, list[str]] = {
            "format": [card.format],
            "correct": [card.correct],
            "explanation": [card.explanation],
        }
        latex = f"\\textbf{{{card.correct}}}"
        kind = "completion"
        if card.format == "choice":
            # Deterministic shuffle: a reload shows the same card, and the right answer is
            # not always in the same place (the English topics do the same).
            opt_rng = random.Random(f"{card.sentence}:{index}")
            shuffled = list(card.options)
            opt_rng.shuffle(shuffled)
            payload["options"] = shuffled
            kind = "multiple_choice"
        else:
            payload["accept"] = list(card.accepted())

        steps = (
            Step("step.grammar_analysis", f"\\text{{{card.clue}}}"),
            Step("step.rule_application", f"\\text{{{card.rule}}}"),
        )
        return Item(
            topic=self.id,
            difficulty=difficulty,
            seed=seed,
            index=index,
            params={},
            statement_key=card.sentence,
            steps=steps,
            answer=Answer(latex=latex, kind=kind, payload=payload),
        )

    def verify(self, item: Item) -> VerificationResult:
        if item.topic != self.id:
            return VerificationResult(False, "topic_mismatch")
        if item.difficulty not in self.difficulties:
            return VerificationResult(False, "invalid_difficulty")
        if GAP not in item.statement_key:
            return VerificationResult(False, "missing_blank")

        card = self.card_for(item.statement_key)
        if card is None:
            return VerificationResult(False, "unknown_statement")

        payload = item.answer.payload
        claimed_format = (payload.get("format") or [""])[0]
        if claimed_format != card.format:
            return VerificationResult(False, "format_mismatch")
        expected_kind = "multiple_choice" if card.format == "choice" else "completion"
        if item.answer.kind != expected_kind:
            return VerificationResult(False, "kind_mismatch")

        correct = (payload.get("correct") or [""])[0]
        if not correct:
            return VerificationResult(False, "missing_correct_answer")
        if correct != card.correct:
            return VerificationResult(False, "correct_answer_does_not_match_the_card")

        if not (payload.get("explanation") or [""])[0].strip():
            return VerificationResult(False, "missing_explanation")

        # The word the card asks for must not be printed in the sentence: that is the
        # relative-clause lesson applied to a gap.
        if card.correct.lower() in {word.lower() for word in _WORD.findall(card.sentence)}:
            return VerificationResult(False, "answer_printed_in_the_statement")

        if card.format == "choice":
            options = payload.get("options") or []
            if len(options) != 4:
                return VerificationResult(False, "expected_four_options")
            if len(set(options)) != 4:
                return VerificationResult(False, "duplicate_options")
            if correct not in options:
                return VerificationResult(False, "correct_not_among_the_options")
            if set(options) != set(card.options):
                return VerificationResult(False, "options_do_not_match_the_card")
        else:
            accept = payload.get("accept") or []
            if not accept:
                return VerificationResult(False, "missing_accepted_spellings")
            if accept[0] != correct:
                return VerificationResult(
                    False, "accepted_spellings_do_not_start_with_the_solution")
            if "options" in payload:
                return VerificationResult(False, "completion_carries_options")

        return VerificationResult(True, "ok")
