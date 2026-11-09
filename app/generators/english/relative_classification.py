"""Relative clauses: the student names the *kind* of clause before answering.

The sibling topic ``relative_defining_non_defining`` writes the classification inside every
option — ``who (defining)``, ``that (non-defining)`` — and the operator rejected it for a
reason that is a lesson in test design, not a matter of taste: the correct classification
is the *only one that repeats* across the four options, so it can be read off the pattern
without looking at the commas at all. The label hands the answer over.

Here the sentence carries no label anywhere. Under it there is a selector with the two
kinds, and the pronoun is asked separately:

    sentence:  The nurse ______ looked after my father works at the city hospital.
    type:      [ defining ] [ non-defining ]      <- must be chosen
    pronoun:   who   which   whose   where
    [ Verifica ]                                  <- disabled until a type is chosen

Two facts are graded, not one, and the client will not let the second be guessed: the
check button starts disabled and only a chosen type enables it. The type is read from the
punctuation (``sentence_classification``), never stored in the spec, so the data cannot
drift from the grammar the exercise claims to teach.

Two consequences the teacher will notice, both deliberate:

* **no step prints the answer.** The sibling topic closes its steps with the correct form;
  here the steps are the diagnostic clue and the rule only, because a page whose lock says
  "choose first" cannot put the answer in a drawer three centimetres below it.
* **``that`` is never the right answer, and never offered in a defining card.** ``who`` and
  ``that`` are both correct in a defining clause about a person, so offering them together
  would be two right answers; ``that`` therefore appears only between commas, where it is
  always wrong, and the explanation says why.
"""

from __future__ import annotations

import random
import re
from typing import NamedTuple

from app.core.verify import VerificationResult
from app.generators.base import Answer, Item, Step
from app.generators.english.relative_defining_non_defining import sentence_classification


class QuestionSpec(NamedTuple):
    sentence: str
    options: tuple[str, str, str, str]
    correct: str
    explanation: str
    clue: str
    rule: str


#: The relative pronouns the exercise can offer, always bare: an option that carries the
#: classification would be the label the operator asked to remove.
PRONOUNS = ("who", "which", "that", "whose", "where")
#: The two kinds the selector offers, spelled as the grammar spells them.
CLASSIFICATIONS = ("defining", "non-defining")
#: A classification written into the sentence itself — the label the operator removed. It
#: matches inside 'non-defining' too, so one pattern covers both spellings.
LABEL_IN_SENTENCE = re.compile(r"\bdefining\b", re.IGNORECASE)


QUESTIONS: tuple[QuestionSpec, ...] = (
    QuestionSpec(
        sentence="The nurse ______ looked after my father works at the city hospital.",
        options=("who", "which", "whose", "where"),
        correct="who",
        explanation=(
            "Defining: non ci sono virgole e la relativa dice di quale infermiera si parla — "
            "senza di essa la frase non identifica una persona precisa. Il pronome è 'who' "
            "perché l'antecedente è una persona e il pronome è il soggetto di 'looked after'. "
            "'which' sbaglia l'antecedente, 'whose' esigerebbe un sostantivo posseduto al "
            "posto di un verbo, e 'where' non può fare da soggetto."
        ),
        clue="Nessuna virgola; l'antecedente è una persona e il verbo 'looked after' non ha ancora il suo soggetto.",
        rule="Defining clause, senza virgole: la relativa identifica il referente. Per le persone soggetto si usa 'who' ('that' è ammesso solo qui, mai tra virgole).",
    ),
    QuestionSpec(
        sentence="My cousin Anna, ______ studied in Vienna, now works for a bank.",
        options=("who", "that", "which", "where"),
        correct="who",
        explanation=(
            "Non-defining: la relativa è chiusa fra due virgole e aggiunge un dettaglio su una "
            "persona già identificata dal nome, quindi la frase regge anche senza. Il pronome "
            "è 'who' perché l'antecedente è una persona e il pronome è il soggetto di "
            "'studied'. 'that' è sempre vietato tra virgole, 'which' sbaglia l'antecedente "
            "personale e 'where' non può fare da soggetto."
        ),
        clue="Due virgole e un nome proprio che identifica già la persona; il verbo 'studied' aspetta il soggetto.",
        rule="Non-defining clause, tra virgole: informazione accessoria. Per le persone si usa 'who'; 'that' è escluso.",
    ),
    QuestionSpec(
        sentence="This is the recipe ______ my grandmother wrote on a postcard.",
        options=("which", "who", "whose", "where"),
        correct="which",
        explanation=(
            "Defining: nessuna virgola e la relativa dice di quale ricetta si tratta. Il "
            "pronome è 'which' perché l'antecedente è una cosa e il pronome è l'oggetto di "
            "'wrote'. 'who' sbaglia l'antecedente, 'whose' chiederebbe un sostantivo "
            "posseduto e 'where' non può essere l'oggetto di un verbo."
        ),
        clue="Nessuna virgola, antecedente inanimato, e 'wrote' cerca ancora il suo oggetto.",
        rule="Defining clause: per le cose oggetto si usa 'which' (oppure 'that').",
    ),
    QuestionSpec(
        sentence="The old bridge, ______ was built by the Romans, is still in use.",
        options=("which", "that", "who", "whose"),
        correct="which",
        explanation=(
            "Non-defining: le virgole aggiungono un'informazione su un ponte già identificato. "
            "Il pronome è 'which' perché l'antecedente è una cosa e il pronome è il soggetto "
            "del passivo 'was built'. 'that' è vietato tra virgole, 'who' sbaglia "
            "l'antecedente e 'whose' esigerebbe un sostantivo posseduto."
        ),
        clue="Due virgole; l'antecedente è una cosa e il verbo passivo 'was built' non ha soggetto.",
        rule="Non-defining clause: per le cose soggetto si usa 'which'; 'that' non entra mai fra virgole.",
    ),
    QuestionSpec(
        sentence="The woman ______ car was stolen called the police immediately.",
        options=("whose", "who", "which", "where"),
        correct="whose",
        explanation=(
            "Defining: nessuna virgola e la relativa identifica la donna. Il pronome è 'whose' "
            "perché 'car' appartiene a lei: è l'unico relativo che regge direttamente un "
            "sostantivo. 'who' non può introdurre 'car', 'which' sbaglia l'antecedente "
            "personale e 'where' indica un luogo."
        ),
        clue="Nessuna virgola; rapporto di possesso fra la donna e l'auto, e 'car' non ha articolo.",
        rule="'Whose' esprime possesso e regge il sostantivo che segue, sia in defining sia in non-defining.",
    ),
    QuestionSpec(
        sentence="Our neighbours, ______ son plays in the national team, moved to Spain.",
        options=("whose", "who", "that", "which"),
        correct="whose",
        explanation=(
            "Non-defining: le virgole presentano il figlio come dettaglio di vicini già "
            "identificati. Il pronome è 'whose' perché 'son' appartiene a loro. 'who' non può "
            "reggere 'son', 'that' è vietato tra virgole e 'which' sbaglia l'antecedente "
            "personale."
        ),
        clue="Due virgole; il figlio è dei vicini, e 'son' non ha articolo.",
        rule="'Whose' vale anche per i legami di famiglia: prende il posto di 'their' e regge il sostantivo.",
    ),
    QuestionSpec(
        sentence="The bicycle ______ belongs to my neighbour has a broken chain.",
        options=("which", "who", "whose", "where"),
        correct="which",
        explanation=(
            "Defining: nessuna virgola e la relativa dice di quale bicicletta si parla. Il "
            "pronome è 'which' perché l'antecedente è una cosa e il pronome è il soggetto di "
            "'belongs to'. 'who' sbaglia l'antecedente, 'whose' chiederebbe un sostantivo "
            "posseduto e 'where' non può fare da soggetto."
        ),
        clue="Nessuna virgola; antecedente inanimato e il verbo 'belongs to' senza soggetto.",
        rule="Defining clause con una cosa soggetto: 'which' (oppure 'that').",
    ),
    QuestionSpec(
        sentence="Alberto, ______ works in my office, speaks four languages fluently.",
        options=("who", "that", "which", "whose"),
        correct="who",
        explanation=(
            "Non-defining: il nome proprio identifica già la persona e le virgole aggiungono "
            "un dettaglio. Il pronome è 'who' perché l'antecedente è una persona e il pronome "
            "è il soggetto di 'works'. 'that' è vietato tra virgole, 'which' sbaglia "
            "l'antecedente e 'whose' esigerebbe un sostantivo posseduto."
        ),
        clue="Due virgole; nome proprio e il verbo 'works' che aspetta il soggetto.",
        rule="Dopo un nome proprio la relativa è di norma accessoria: virgole e 'who', mai 'that'.",
    ),
    QuestionSpec(
        sentence="The library ______ I borrowed this atlas is on the second floor.",
        options=("where", "which", "whose", "who"),
        correct="where",
        explanation=(
            "Defining: nessuna virgola e la relativa identifica la biblioteca. 'I borrowed "
            "this atlas' ha già soggetto e oggetto, quindi manca il complemento di luogo e "
            "serve 'where'. 'which' sarebbe corretto solo con una preposizione davanti ('from "
            "which'), 'whose' esprime possesso e 'who' è riservato alle persone."
        ),
        clue="Nessuna virgola; 'I borrowed this atlas' ha già soggetto e oggetto, quindi non cerca un oggetto ma un luogo.",
        rule="Se la relativa è completa si usa 'where' (in cui / nel quale); 'which' e 'that' servono solo come soggetto o oggetto.",
    ),
    QuestionSpec(
        sentence="The conference, ______ took place in Lisbon, was attended by two hundred people.",
        options=("which", "that", "where", "who"),
        correct="which",
        explanation=(
            "Non-defining: le virgole aggiungono il luogo a una conferenza già identificata. Il "
            "pronome è 'which' perché la conferenza è il soggetto di 'took place'; 'where' "
            "sarebbe sbagliato, perché il luogo è già detto ('in Lisbon') e 'took place' non "
            "cerca un complemento. 'that' è vietato tra virgole e 'who' sbaglia l'antecedente."
        ),
        clue="Due virgole; il luogo è già nella relativa ('in Lisbon'), quindi manca il soggetto, non il luogo.",
        rule="Nelle non-defining una cosa soggetto richiede 'which'; 'where' sostituisce solo un complemento di luogo mancante.",
    ),
    QuestionSpec(
        sentence="Children ______ eat too much sugar often have problems at school.",
        options=("who", "which", "whose", "where"),
        correct="who",
        explanation=(
            "Defining: nessuna virgola e la relativa restringe il gruppo ai bambini che mangiano "
            "troppo zucchero — è informazione essenziale. Il pronome è 'who' perché sono "
            "persone e il pronome è il soggetto di 'eat'. 'which' sbaglia l'antecedente, "
            "'whose' chiederebbe un sostantivo posseduto e 'where' non può fare da soggetto."
        ),
        clue="Nessuna virgola; antecedente personale e il verbo 'eat' senza soggetto.",
        rule="Defining clause: per le persone soggetto si usa 'who' ('that' è ammesso solo qui).",
    ),
    QuestionSpec(
        sentence="Her grandfather, ______ health is sadly failing, lives with them now.",
        options=("whose", "who", "that", "which"),
        correct="whose",
        explanation=(
            "Non-defining: il possessivo 'her' e le virgole rendono accessoria l'informazione. "
            "Il pronome è 'whose' perché la salute è del nonno e 'health' è un sostantivo che "
            "dipende dal relativo. 'who' non può reggere 'health', 'that' è vietato tra "
            "virgole e 'which' sbaglia l'antecedente personale."
        ),
        clue="Due virgole; la salute è del nonno, e 'health' non ha articolo.",
        rule="'Whose' è l'unico relativo che regge direttamente un sostantivo: vale in entrambe le classificazioni.",
    ),
    QuestionSpec(
        sentence="The keys ______ I left on the table this morning have disappeared.",
        options=("which", "who", "whose", "where"),
        correct="which",
        explanation=(
            "Defining: nessuna virgola e la relativa dice di quali chiavi si parla. Il pronome "
            "è 'which' perché l'antecedente è una cosa e il pronome è l'oggetto di 'left'. "
            "'who' sbaglia l'antecedente, 'whose' chiederebbe un sostantivo posseduto e "
            "'where' non può essere l'oggetto di un verbo."
        ),
        clue="Nessuna virgola; antecedente inanimato e 'left' cerca il suo oggetto.",
        rule="Defining clause: per le cose oggetto si usa 'which' (oppure 'that').",
    ),
    QuestionSpec(
        sentence="The photograph, ______ was taken in 1963, hangs in the hallway.",
        options=("which", "that", "who", "where"),
        correct="which",
        explanation=(
            "Non-defining: le virgole aggiungono una data a una fotografia già identificata. Il "
            "pronome è 'which' perché la fotografia è il soggetto del passivo 'was taken'; "
            "'where' indicherebbe il luogo di un'azione, non il soggetto che la subisce. 'that' "
            "è vietato tra virgole e 'who' sbaglia l'antecedente."
        ),
        clue="Due virgole; la fotografia è il soggetto del verbo passivo.",
        rule="Nelle non-defining un oggetto soggetto richiede 'which'; 'that' non è mai ammesso.",
    ),
    QuestionSpec(
        sentence="A carpenter is a person ______ makes wooden furniture.",
        options=("who", "which", "whose", "where"),
        correct="who",
        explanation=(
            "Defining: nessuna virgola e la relativa definisce che cosa è un falegname. Il "
            "pronome è 'who' perché l'antecedente è una persona e il pronome è il soggetto di "
            "'makes'. 'which' sbaglia l'antecedente, 'whose' esigerebbe un sostantivo "
            "posseduto e 'where' non può fare da soggetto."
        ),
        clue="Nessuna virgola; 'a person' è una persona e 'makes' non ha ancora il soggetto.",
        rule="Defining clause: con i nomi di mestiere si usa 'who' (o 'that') come soggetto.",
    ),
    QuestionSpec(
        sentence="Our guide, ______ had never been to the castle before, got lost twice.",
        options=("who", "that", "which", "where"),
        correct="who",
        explanation=(
            "Non-defining: le virgole aggiungono un dettaglio su una guida già identificata. Il "
            "pronome è 'who' perché l'antecedente è una persona e il pronome è il soggetto di "
            "'had been'. 'that' è vietato tra virgole, 'which' sbaglia l'antecedente e 'where' "
            "non può fare da soggetto."
        ),
        clue="Due virgole; una persona e il verbo 'had been' senza soggetto.",
        rule="La virgola cambia la classificazione, non il pronome: per le persone soggetto resta 'who'.",
    ),
    QuestionSpec(
        sentence="The village ______ my parents got married has a famous bridge.",
        options=("where", "which", "whose", "who"),
        correct="where",
        explanation=(
            "Defining: nessuna virgola e la relativa identifica il paese. 'my parents got "
            "married' è completa e non ha oggetto, quindi manca il complemento di luogo: "
            "'where'. 'which' avrebbe bisogno di una preposizione ('in which'), 'whose' "
            "esprime possesso e 'who' è riservato alle persone."
        ),
        clue="Nessuna virgola; 'got married' è intransitivo, quindi la relativa non cerca un oggetto.",
        rule="Con i luoghi si usa 'where' quando la relativa è completa; 'which' e 'that' solo se servono da soggetto o oggetto.",
    ),
    QuestionSpec(
        sentence="The little restaurant, ______ tables overlook the harbour, serves fresh fish.",
        options=("whose", "which", "that", "who"),
        correct="whose",
        explanation=(
            "Non-defining: le virgole aggiungono un dettaglio su un ristorante già identificato. "
            "Il pronome è 'whose' perché i tavoli sono del ristorante e 'tables' è il "
            "sostantivo che dipende dal relativo. 'which' non può reggere 'tables', 'that' è "
            "vietato tra virgole e 'who' sbaglia l'antecedente."
        ),
        clue="Due virgole; i tavoli sono del ristorante, e 'tables' non ha articolo.",
        rule="'Whose' si usa anche per gli oggetti e i locali, al posto di 'of which'.",
    ),
    QuestionSpec(
        sentence="The athlete ______ ankle was injured during the race withdrew immediately.",
        options=("whose", "who", "which", "where"),
        correct="whose",
        explanation=(
            "Defining: nessuna virgola e la relativa identifica l'atleta. Il pronome è 'whose' "
            "perché 'ankle' è parte di lui. 'who' non può reggere 'ankle', 'which' sbaglia "
            "l'antecedente personale e 'where' indica un luogo."
        ),
        clue="Nessuna virgola; la caviglia è dell'atleta, e 'ankle' non ha articolo.",
        rule="'Whose' si usa anche per le parti del corpo, in entrambe le classificazioni.",
    ),
    QuestionSpec(
        sentence="The exam, ______ I had prepared for all winter, turned out to be easy.",
        options=("which", "that", "who", "whose"),
        correct="which",
        explanation=(
            "Non-defining: le virgole aggiungono un dettaglio su un esame già identificato. Il "
            "pronome è 'which' perché l'esame è ciò per cui ci si è preparati: è l'oggetto "
            "della preposizione finale 'for'. 'that' è vietato tra virgole, 'who' sbaglia "
            "l'antecedente e 'whose' esigerebbe un sostantivo posseduto."
        ),
        clue="Due virgole; la preposizione 'for' è rimasta in fondo e cerca il suo oggetto.",
        rule="Nelle non-defining il pronome oggetto resta necessario: la preposizione in fondo regge 'which', mai 'that'.",
    ),
    QuestionSpec(
        sentence="The mechanic ______ repaired our brakes did not charge for the parts.",
        options=("who", "which", "whose", "where"),
        correct="who",
        explanation=(
            "Defining: nessuna virgola e la relativa identifica il meccanico. Il pronome è "
            "'who' perché è una persona e il pronome è il soggetto di 'repaired'. 'which' "
            "sbaglia l'antecedente, 'whose' chiederebbe un sostantivo posseduto e 'where' non "
            "può fare da soggetto."
        ),
        clue="Nessuna virgola; antecedente personale e 'repaired' senza soggetto.",
        rule="Defining clause: per le persone soggetto si usa 'who' (oppure 'that').",
    ),
    QuestionSpec(
        sentence="The school concert, ______ was held in the gym, raised five hundred euros.",
        options=("which", "that", "who", "whose"),
        correct="which",
        explanation=(
            "Non-defining: le virgole aggiungono un dettaglio su un concerto già identificato. "
            "Il pronome è 'which' perché il concerto è il soggetto del passivo 'was held'. "
            "'that' è vietato tra virgole, 'who' sbaglia l'antecedente e 'whose' esigerebbe un "
            "sostantivo posseduto."
        ),
        clue="Due virgole; l'evento è il soggetto del verbo passivo.",
        rule="Nelle non-defining una cosa soggetto richiede 'which'; 'that' non entra mai fra virgole.",
    ),
    QuestionSpec(
        sentence="The mountain ______ we climbed last summer is covered in snow.",
        options=("which", "who", "whose", "where"),
        correct="which",
        explanation=(
            "Defining: nessuna virgola e la relativa identifica la montagna. 'climbed' è "
            "transitivo e il suo oggetto è la montagna, quindi serve 'which'. 'where' è la "
            "trappola: sostituirebbe un complemento di luogo, ma qui manca l'oggetto di "
            "'climbed'. 'who' sbaglia l'antecedente e 'whose' esigerebbe un sostantivo "
            "posseduto."
        ),
        clue="Nessuna virgola; 'we climbed' è transitivo e non ha ancora il suo oggetto.",
        rule="Se il verbo della relativa è transitivo serve 'which' o 'that'; 'where' sostituisce solo un complemento di luogo mancante.",
    ),
    QuestionSpec(
        sentence="The novel, ______ plot twists surprised every reader, has become a bestseller.",
        options=("whose", "which", "that", "who"),
        correct="whose",
        explanation=(
            "Non-defining: le virgole aggiungono un dettaglio su un romanzo già identificato. Il "
            "pronome è 'whose' perché i colpi di scena sono del romanzo: 'plot twists' è il "
            "sostantivo che dipende dal relativo. 'which' non può reggere 'plot twists', 'that' "
            "è vietato tra virgole e 'who' sbaglia l'antecedente."
        ),
        clue="Due virgole; i colpi di scena appartengono al romanzo, e 'plot twists' non ha articolo.",
        rule="'Whose' regge un sostantivo anche quando il possessore è una cosa, in entrambe le classificazioni.",
    ),
)


class RelativeClassificationTopic:
    """One level: the exercise asks *which kind*, and the kind is not a difficulty."""

    id = "english.grammar.relative_classification"
    family = "english"
    difficulties = ("easy",)
    label_key = "topic.english_relative_classification"
    scenarios: tuple[str, ...] = ()

    def generate(
        self,
        rng: random.Random,
        difficulty: str,
        seed: int,
        index: int,
        options: dict | None = None,
    ) -> Item:
        chosen = QUESTIONS[index % len(QUESTIONS)]
        classification = sentence_classification(chosen.sentence) or "defining"

        # Same convention as the other grammar topics: the order is shuffled so the correct
        # option is not always A, but deterministically, so a reload shows the same card.
        opt_rng = random.Random(f"{chosen.sentence}:{index}")
        shuffled = list(chosen.options)
        opt_rng.shuffle(shuffled)

        # Two steps, not three: the sibling topic closes with the correct form, and a page
        # whose lock says "choose the kind first" cannot print the answer underneath it.
        steps = (
            Step("step.grammar_analysis", f"\\text{{{chosen.clue}}}"),
            Step("step.rule_application", f"\\text{{{chosen.rule}}}"),
        )
        answer = Answer(
            latex=f"\\textbf{{{chosen.correct}}}, \\text{{{classification}}}",
            kind="multiple_choice",
            payload={
                "options": shuffled,
                "correct": [chosen.correct],
                "classification": [classification],
                "explanation": [chosen.explanation],
            },
        )
        return Item(
            topic=self.id,
            difficulty=difficulty,
            seed=seed,
            index=index,
            params={},
            statement_key=chosen.sentence,
            steps=steps,
            answer=answer,
        )

    def verify(self, item: Item) -> VerificationResult:
        if item.topic != self.id:
            return VerificationResult(False, "topic_mismatch")
        if item.difficulty not in self.difficulties:
            return VerificationResult(False, "invalid_difficulty")
        if item.answer.kind != "multiple_choice":
            return VerificationResult(False, "kind_mismatch")

        payload = item.answer.payload
        options = payload.get("options")
        if not options or len(options) < 3:
            return VerificationResult(False, "missing_or_insufficient_options")
        if len(set(options)) != len(options):
            return VerificationResult(False, "duplicate_options")

        # An option is a pronoun and nothing else: a classification riding along with it is
        # exactly the label that gave the answer away on the previous page.
        if any(option not in PRONOUNS for option in options):
            return VerificationResult(False, "option_is_not_a_bare_pronoun")

        correct = payload.get("correct")
        if not correct or correct[0] not in options:
            return VerificationResult(False, "invalid_or_missing_correct_answer")

        sentence_class = sentence_classification(item.statement_key)
        if sentence_class is None:
            return VerificationResult(False, "missing_blank")
        if LABEL_IN_SENTENCE.search(item.statement_key):
            return VerificationResult(False, "statement_carries_the_label")

        claimed = payload.get("classification")
        if not claimed or claimed[0] not in CLASSIFICATIONS:
            return VerificationResult(False, "missing_classification")
        if claimed[0] != sentence_class:
            return VerificationResult(False, "classification_mismatch")

        # 'that' may not introduce a clause between commas, and offering it next to 'who' or
        # 'which' in a defining clause would put two right answers on the card.
        if correct[0] == "that" and sentence_class == "non-defining":
            return VerificationResult(False, "that_in_non_defining")
        if "that" in options and sentence_class == "defining":
            return VerificationResult(False, "that_offered_in_defining")

        return VerificationResult(True, "ok")


TOPIC = RelativeClassificationTopic()
