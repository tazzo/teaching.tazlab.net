"""The grammar the relative-clause pages share, independent of how a page asks for it.

Two pages question the same sentences from different sides: the classification page asks
the *kind* first and the pronoun after, the present-perfect/relative page reuses the same
picker for its own clause cards. Both need the same two facts, so they live here rather
than in one generator that the other imports sideways:

* the shape of a blank (six underscores in the exercise text),
* the relative pronouns a card may offer,
* the classification, which is **read from the punctuation** and never stored in a spec.

The last point is the contract: ``sentence_classification`` says that a comma right before
the blank makes the clause non-defining, so a card cannot claim a kind its own commas
contradict.
"""

from __future__ import annotations

import re

#: The blank the student fills; the exercise text uses six underscores.
BLANK = re.compile(r"_{3,}")
#: The relative pronouns a card may offer. Deliberately the five the picker can grade:
#: ``whom``/``when``/``why`` are formal or adverbial relatives and belong to another
#: exercise, one that would need its own vocabulary.
PRONOUNS = ("who", "which", "that", "whose", "where")
#: The two kinds the selector offers, spelled as the grammar spells them.
CLASSIFICATIONS = ("defining", "non-defining")


def sentence_classification(sentence: str) -> str | None:
    """Read the classification off the punctuation: a comma before the blank means non-defining."""
    match = BLANK.search(sentence)
    if match is None:
        return None
    return "non-defining" if sentence[: match.start()].rstrip().endswith(",") else "defining"
