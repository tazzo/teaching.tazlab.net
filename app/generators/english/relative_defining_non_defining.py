"""Relative clauses: choose the pronoun AND the classification together.

The existing ``relative_clauses`` topic asks the student for the pronoun only. This one
asks a harder question: the blank can be filled by more than one pronoun in some
sentences (``which`` and ``that`` are both defining), so the real skill is deciding
*whether* the clause is defining at all. Each option therefore carries two pieces of
information — the pronoun and the classification — and exactly one of the four is fully
correct:

    who (defining)        who (non-defining)
    which (defining)      that (non-defining)

The grammar the exercise enforces (and that ``verify`` re-checks on every generated item):

* **defining** — no commas; ``who/which/that/whose/where`` are all available, so ``that``
  is possible;
* **non-defining** — the clause sits between commas; ``who/which/whose/where`` are
  available and ``that`` is *forbidden*. ``that (non-defining)`` is therefore a plausible
  distractor that is always wrong.

Every wrong option is wrong for one precise reason: either the pronoun does not fit the
antecedent, or the classification contradicts the commas (or both). Several questions
turn on the comma alone — the same pronoun is offered twice, once per classification,
and only the punctuation decides.
"""

from __future__ import annotations

import random
import re
from typing import NamedTuple

from app.core.verify import VerificationResult
from app.generators.base import Answer, Item, Step


class QuestionSpec(NamedTuple):
    sentence: str
    options: tuple[str, str, str, str]
    correct: str
    explanation: str
    clue: str
    rule: str


#: ``who (defining)``, ``which (non-defining)``, … — the shape every option must have.
OPTION_SHAPE = re.compile(r"^(who|which|that|whose|where) \((non-defining|defining)\)$")
#: The blank the student fills; the exercise text uses six underscores.
BLANK = re.compile(r"_{3,}")


EASY_QUESTIONS: tuple[QuestionSpec, ...] = (
    QuestionSpec(
        sentence="The girl ______ won the science competition is in my class.",
        options=("who (defining)", "who (non-defining)", "which (defining)", "that (non-defining)"),
        correct="who (defining)",
        explanation=(
            "La frase non ha virgole: la relativa serve a identificare 'the girl' e per questo è "
            "defining. L'antecedente è una persona e il pronome è il soggetto di 'won', quindi si "
            "usa 'who'. 'who (non-defining)' sbaglia la classificazione, 'which (defining)' sbaglia "
            "il pronome, 'that (non-defining)' è doppiamente sbagliato perché 'that' non si usa mai "
            "in una relativa tra virgole."
        ),
        clue="Nessuna virgola e antecedente personale: la relativa identifica la ragazza e il pronome è il soggetto di 'won'.",
        rule="Defining clause, senza virgole: per le persone soggetto si usa 'who' oppure 'that'.",
    ),
    QuestionSpec(
        sentence="This is the book ______ inspired me to become an engineer.",
        options=("which (defining)", "which (non-defining)", "that (non-defining)", "who (defining)"),
        correct="which (defining)",
        explanation=(
            "'The book' è una cosa e il pronome è il soggetto di 'inspired'. Senza virgole la "
            "relativa è defining e il pronome per le cose è 'which'. 'which (non-defining)' sbaglia "
            "la classificazione, 'who (defining)' sbaglia l'antecedente, 'that (non-defining)' è "
            "impossibile perché 'that' non regge una relativa tra virgole."
        ),
        clue="Antecedente inanimato e nessuna virgola: la relativa restringe il riferimento a quel libro.",
        rule="Defining clause: per le cose si usa 'which' oppure 'that'.",
    ),
    QuestionSpec(
        sentence="My uncle, ______ is a pilot, flies planes all over the world.",
        options=("who (non-defining)", "who (defining)", "that (non-defining)", "which (non-defining)"),
        correct="who (non-defining)",
        explanation=(
            "Le due virgole racchiudono un'informazione aggiuntiva su uno zio già identificato: è "
            "una non-defining. Per una persona soggetto si usa 'who'. 'who (defining)' sbaglia la "
            "classificazione, 'that (non-defining)' sbaglia il pronome perché 'that' è vietato tra "
            "virgole, 'which (non-defining)' sbaglia l'antecedente personale."
        ),
        clue="Le virgole isolano la relativa: l'informazione è accessoria e il pronome è il soggetto di 'is'.",
        rule="Non-defining clause, tra virgole: 'who' per le persone e mai 'that'.",
    ),
    QuestionSpec(
        sentence="The restaurant ______ we had dinner last night was excellent.",
        options=("where (defining)", "which (defining)", "where (non-defining)", "that (defining)"),
        correct="where (defining)",
        explanation=(
            "Nessuna virgola: la relativa identifica il ristorante. La subordinata 'we had dinner "
            "last night' è già completa, quindi non manca un oggetto ma il complemento di luogo: "
            "serve 'where'. 'which (defining)' e 'that (defining)' sono errati perché il verbo "
            "'had' ha già il suo oggetto, 'where (non-defining)' sbaglia la classificazione."
        ),
        clue="'we had dinner last night' è una frase completa: manca il luogo, non l'oggetto.",
        rule="Nelle defining clauses, se la subordinata è completa si usa 'where' e non 'which' o 'that'.",
    ),
    QuestionSpec(
        sentence="A mechanic is someone ______ repairs broken cars.",
        options=("who (defining)", "which (defining)", "who (non-defining)", "whose (defining)"),
        correct="who (defining)",
        explanation=(
            "'Someone' indica una persona e il pronome è il soggetto di 'repairs', quindi 'who'. "
            "Nessuna virgola: la relativa è defining. 'which (defining)' sbaglia l'antecedente, "
            "'who (non-defining)' sbaglia la classificazione, 'whose (defining)' indica possesso e "
            "qui non c'è nulla da possedere."
        ),
        clue="Persona indeterminata come soggetto del verbo della relativa, senza virgole.",
        rule="Con i pronomi indefiniti che indicano persone si usa 'who' nelle relative defining.",
    ),
    QuestionSpec(
        sentence="The computer ______ I bought last week has already crashed twice.",
        options=("which (defining)", "who (defining)", "which (non-defining)", "that (non-defining)"),
        correct="which (defining)",
        explanation=(
            "'The computer' è una cosa e il pronome è l'oggetto di 'bought': si usa 'which'. La "
            "relativa è defining perché non ci sono virgole. 'who (defining)' sbaglia l'antecedente, "
            "'which (non-defining)' sbaglia la classificazione, 'that (non-defining)' è impossibile "
            "tra virgole."
        ),
        clue="Cosa inanimata con il pronome oggetto di 'bought'; nessuna virgola.",
        rule="Defining clause: per le cose oggetto si usa 'which' oppure 'that'.",
    ),
    QuestionSpec(
        sentence="My grandmother, ______ is 85, walks three miles every morning.",
        options=("who (non-defining)", "that (non-defining)", "who (defining)", "whose (non-defining)"),
        correct="who (non-defining)",
        explanation=(
            "Le virgole rendono l'informazione accessoria, quindi la relativa è non-defining, e "
            "l'antecedente è una persona soggetto: 'who'. 'that (non-defining)' è sempre scorretto, "
            "'who (defining)' sbaglia la classificazione, 'whose (non-defining)' esprime possesso e "
            "qui non serve."
        ),
        clue="Due virgole e una persona come soggetto di 'is': informazione aggiuntiva, non necessaria.",
        rule="Non-defining clause: 'who' per le persone e mai 'that'.",
    ),
    QuestionSpec(
        sentence="A widow is a woman ______ husband has died.",
        options=("whose (defining)", "who (defining)", "whose (non-defining)", "which (defining)"),
        correct="whose (defining)",
        explanation=(
            "'Husband' appartiene alla donna, quindi serve il possessivo 'whose'. Nessuna virgola: "
            "la relativa è defining. 'who (defining)' non può reggere un sostantivo, "
            "'whose (non-defining)' sbaglia la classificazione, 'which (defining)' sbaglia "
            "l'antecedente personale."
        ),
        clue="Rapporto di possesso tra 'woman' e 'husband', senza virgole.",
        rule="Si usa 'whose' quando il pronome esprime possesso, sia in defining sia in non-defining.",
    ),
    QuestionSpec(
        sentence="The town ______ I grew up has changed completely.",
        options=("where (defining)", "which (defining)", "where (non-defining)", "that (defining)"),
        correct="where (defining)",
        explanation=(
            "'I grew up' è una frase completa: manca il luogo, quindi 'where'. Nessuna virgola, "
            "quindi la relativa è defining. 'which (defining)' e 'that (defining)' sarebbero "
            "possibili solo se il verbo della relativa avesse bisogno di un oggetto, "
            "'where (non-defining)' sbaglia la classificazione."
        ),
        clue="Verbo intransitivo e antecedente di luogo: nessun oggetto da sostituire.",
        rule="Con i luoghi, se la relativa è completa si usa 'where'; 'which' e 'that' servono solo come soggetto o oggetto.",
    ),
    QuestionSpec(
        sentence="The students ______ failed the test must take it again next Friday.",
        options=("who (defining)", "who (non-defining)", "which (defining)", "whose (defining)"),
        correct="who (defining)",
        explanation=(
            "La relativa identifica quali studenti e non ci sono virgole: è defining, e il pronome "
            "è il soggetto di 'failed', quindi 'who'. 'who (non-defining)' è la trappola della "
            "virgola: lo stesso pronome, ma senza virgole la classificazione è sbagliata. "
            "'which (defining)' sbaglia l'antecedente, 'whose (defining)' il possesso."
        ),
        clue="Nessuna virgola e antecedente personale: la relativa restringe il gruppo degli studenti.",
        rule="La classificazione non dipende dal pronome ma dalle virgole: senza virgole la relativa è defining.",
    ),
    QuestionSpec(
        sentence="Paris, ______ is known as the City of Light, attracts millions of visitors.",
        options=("which (non-defining)", "that (non-defining)", "which (defining)", "where (non-defining)"),
        correct="which (non-defining)",
        explanation=(
            "Le virgole indicano una non-defining e la città è il soggetto del passivo 'is known', "
            "quindi serve 'which' e non 'where'. 'that (non-defining)' è vietato, 'which (defining)' "
            "sbaglia la classificazione, 'where (non-defining)' sbaglia il pronome perché non c'è "
            "un'azione che avviene nella città."
        ),
        clue="La città è il soggetto grammaticale del verbo passivo, non il luogo di un'azione altrui.",
        rule="Nelle non-defining, per una cosa o una città soggetto si usa 'which', mai 'that'.",
    ),
    QuestionSpec(
        sentence="The boy ______ dog ran away was crying in the park.",
        options=("whose (defining)", "whose (non-defining)", "who (defining)", "which (defining)"),
        correct="whose (defining)",
        explanation=(
            "'Dog' appartiene al ragazzo, quindi 'whose'. Nessuna virgola: la relativa è defining. "
            "'whose (non-defining)' sbaglia la classificazione, 'who (defining)' non può introdurre "
            "un sostantivo, 'which (defining)' sbaglia l'antecedente personale."
        ),
        clue="Possesso tra il ragazzo e il cane, senza virgole.",
        rule="'Whose' sostituisce 'his', 'her' o 'their' e si usa in entrambe le classificazioni.",
    ),
    QuestionSpec(
        sentence="The phone ______ was on the kitchen table started ringing.",
        options=("which (defining)", "who (defining)", "which (non-defining)", "that (non-defining)"),
        correct="which (defining)",
        explanation=(
            "Cosa inanimata e pronome soggetto di 'was': 'which'. Nessuna virgola, quindi defining. "
            "'who (defining)' sbaglia l'antecedente, 'which (non-defining)' sbaglia la "
            "classificazione, 'that (non-defining)' è impossibile tra virgole."
        ),
        clue="Oggetto inanimato come soggetto della relativa, senza virgole.",
        rule="Defining clause con una cosa soggetto: 'which' oppure 'that'.",
    ),
    QuestionSpec(
        sentence="Dr Adams, ______ examined me at the clinic, was very reassuring.",
        options=("who (non-defining)", "that (non-defining)", "which (non-defining)", "who (defining)"),
        correct="who (non-defining)",
        explanation=(
            "Il nome e cognome identificano già la persona: la relativa tra virgole aggiunge un "
            "dettaglio, quindi è non-defining. Persona soggetto: 'who'. 'that (non-defining)' è "
            "sempre vietato, 'which (non-defining)' sbaglia l'antecedente, 'who (defining)' sbaglia "
            "la classificazione."
        ),
        clue="Nome e cognome già identificano la persona: le virgole aggiungono un dettaglio.",
        rule="Dopo un nome proprio l'informazione della relativa è accessoria: virgole e 'who', mai 'that'.",
    ),
    QuestionSpec(
        sentence="This is the café ______ we usually have coffee.",
        options=("where (defining)", "which (defining)", "where (non-defining)", "whose (defining)"),
        correct="where (defining)",
        explanation=(
            "La subordinata 'we usually have coffee' è completa: serve l'avverbio di luogo 'where'. "
            "Nessuna virgola, quindi defining. 'which (defining)' non può essere l'oggetto di 'have', "
            "che ne ha già uno, 'where (non-defining)' sbaglia la classificazione, "
            "'whose (defining)' sbaglia il pronome."
        ),
        clue="Azione abituale dentro un luogo: la frase non manca dell'oggetto.",
        rule="Con i luoghi si usa 'where' quando la relativa non ha bisogno di soggetto o oggetto.",
    ),
    QuestionSpec(
        sentence="She has a friend ______ father is an ambassador.",
        options=("whose (defining)", "who (defining)", "whose (non-defining)", "which (defining)"),
        correct="whose (defining)",
        explanation=(
            "'Father' appartiene all'amica, quindi 'whose'. Nessuna virgola: defining. "
            "'who (defining)' non regge il sostantivo, 'whose (non-defining)' sbaglia la "
            "classificazione, 'which (defining)' sbaglia l'antecedente personale."
        ),
        clue="Il padre dell'amica: un rapporto di possesso, senza virgole.",
        rule="'Whose' introduce il nome di ciò che appartiene all'antecedente.",
    ),
    QuestionSpec(
        sentence="The umbrella ______ you lent me kept me completely dry.",
        options=("which (defining)", "who (defining)", "which (non-defining)", "whose (defining)"),
        correct="which (defining)",
        explanation=(
            "'The umbrella' è una cosa e il pronome è l'oggetto di 'lent': 'which'. Nessuna virgola, "
            "quindi defining. 'who (defining)' sbaglia l'antecedente, 'which (non-defining)' sbaglia "
            "la classificazione, 'whose (defining)' esprime possesso e qui non serve."
        ),
        clue="Cosa con il pronome oggetto di 'lent', senza virgole.",
        rule="Per le cose oggetto nelle defining clauses si usa 'which' oppure 'that'.",
    ),
    QuestionSpec(
        sentence="The hotel, ______ had a rooftop swimming pool, was right by the sea.",
        options=("which (non-defining)", "that (non-defining)", "where (non-defining)", "which (defining)"),
        correct="which (non-defining)",
        explanation=(
            "Le virgole aggiungono un dettaglio a un albergo già identificato e il pronome è il "
            "soggetto di 'had': 'which'. 'that (non-defining)' è vietato, 'where (non-defining)' "
            "sbaglia il pronome perché non c'è un'azione che avviene nell'albergo, "
            "'which (defining)' sbaglia la classificazione."
        ),
        clue="L'albergo è il soggetto di 'had': non è il luogo di un'azione altrui.",
        rule="Nelle non-defining un edificio soggetto richiede 'which'; 'that' è sempre escluso.",
    ),
    QuestionSpec(
        sentence="The woman ______ lives next door is an architect.",
        options=("who (defining)", "who (non-defining)", "which (defining)", "where (defining)"),
        correct="who (defining)",
        explanation=(
            "La relativa identifica la donna e non ci sono virgole: defining. Il pronome è il "
            "soggetto di 'lives', quindi 'who'. 'who (non-defining)' è la trappola della virgola, "
            "'which (defining)' sbaglia l'antecedente, 'where (defining)' non può essere il soggetto "
            "di un verbo."
        ),
        clue="Nessuna virgola e una persona soggetto del verbo 'lives'.",
        rule="Senza virgole la relativa è defining: 'who' oppure 'that' per le persone soggetto.",
    ),
    QuestionSpec(
        sentence="Rome, ______ was founded in 753 BC, is the capital of Italy.",
        options=("which (non-defining)", "where (non-defining)", "that (non-defining)", "which (defining)"),
        correct="which (non-defining)",
        explanation=(
            "Le virgole rendono la relativa non-defining e Roma è il soggetto del passivo 'was "
            "founded': 'which'. 'where (non-defining)' sbaglia il pronome, 'that (non-defining)' è "
            "vietato, 'which (defining)' sbaglia la classificazione."
        ),
        clue="La città è il soggetto del verbo passivo, non il luogo in cui avviene l'azione.",
        rule="Una città soggetto richiede 'which'; 'where' si usa solo se la relativa descrive un'azione che avviene nel luogo.",
    ),
)


MEDIUM_QUESTIONS: tuple[QuestionSpec, ...] = (
    QuestionSpec(
        sentence="He arrived twenty minutes late, ______ annoyed the teacher greatly.",
        options=("which (non-defining)", "that (non-defining)", "which (defining)", "who (non-defining)"),
        correct="which (non-defining)",
        explanation=(
            "La relativa non si riferisce a un sostantivo ma all'intera frase precedente: è "
            "non-defining, segnalata dalla virgola, e il pronome è 'which'. 'that (non-defining)' è "
            "vietato, 'which (defining)' sbaglia la classificazione, 'who (non-defining)' non può "
            "commentare una frase."
        ),
        clue="Il pronome non sostituisce un nome ma tutto ciò che è appena stato detto.",
        rule="Per commentare un'intera frase si usa ', which': non-defining e mai 'that'.",
    ),
    QuestionSpec(
        sentence="The company, ______ headquarters are in Zurich, announced record profits.",
        options=("whose (non-defining)", "which (non-defining)", "whose (defining)", "that (non-defining)"),
        correct="whose (non-defining)",
        explanation=(
            "La sede appartiene all'azienda, quindi serve 'whose'; le virgole rendono la relativa "
            "non-defining. 'which (non-defining)' non può reggere il sostantivo 'headquarters', "
            "'whose (defining)' sbaglia la classificazione, 'that (non-defining)' è vietato."
        ),
        clue="Rapporto di appartenenza tra l'azienda e la sua sede centrale, con le virgole.",
        rule="'Whose' esprime possesso anche con aziende e istituzioni, in entrambe le classificazioni.",
    ),
    QuestionSpec(
        sentence="Mount Everest, ______ peak is the highest in the world, attracts thousands of climbers.",
        options=("whose (non-defining)", "which (non-defining)", "that (non-defining)", "whose (defining)"),
        correct="whose (non-defining)",
        explanation=(
            "La vetta appartiene alla montagna: 'whose'. Le virgole indicano una non-defining. "
            "'which (non-defining)' non può reggere 'peak', 'that (non-defining)' è vietato, "
            "'whose (defining)' sbaglia la classificazione."
        ),
        clue="La vetta della montagna: possesso tra l'antecedente e il sostantivo che segue.",
        rule="'Whose' si usa anche per elementi geografici e cose inanimate, al posto di 'of which'.",
    ),
    QuestionSpec(
        sentence="Children ______ parents are both working often attend after-school clubs.",
        options=("whose (defining)", "who (defining)", "whose (non-defining)", "which (defining)"),
        correct="whose (defining)",
        explanation=(
            "I genitori appartengono ai bambini: 'whose'. Nessuna virgola, quindi la relativa è "
            "defining e restringe il gruppo. 'who (defining)' non può reggere 'parents', "
            "'whose (non-defining)' sbaglia la classificazione, 'which (defining)' sbaglia "
            "l'antecedente personale."
        ),
        clue="Legame di parentela tra i bambini e i loro genitori, senza virgole.",
        rule="Nelle relative defining 'whose' indica legami familiari o di possesso.",
    ),
    QuestionSpec(
        sentence="The politician, ______ was accused of corruption, resigned from parliament.",
        options=("who (non-defining)", "that (non-defining)", "which (non-defining)", "who (defining)"),
        correct="who (non-defining)",
        explanation=(
            "La relativa tra virgole aggiunge un dettaglio su un politico già identificato: "
            "non-defining. Il pronome è il soggetto di 'was accused', quindi 'who'. "
            "'that (non-defining)' è vietato, 'which (non-defining)' sbaglia l'antecedente, "
            "'who (defining)' sbaglia la classificazione."
        ),
        clue="Le virgole isolano un commento su una persona che è soggetto del passivo.",
        rule="Nelle non-defining con una persona soggetto si usa sempre 'who', mai 'that'.",
    ),
    QuestionSpec(
        sentence="Venice, ______ canals are famous across the world, is threatened by rising sea levels.",
        options=("whose (non-defining)", "whose (defining)", "which (non-defining)", "where (non-defining)"),
        correct="whose (non-defining)",
        explanation=(
            "I canali appartengono a Venezia: 'whose'. Le virgole rendono la relativa non-defining. "
            "'whose (defining)' sbaglia la classificazione, 'which (non-defining)' non può reggere "
            "'canals', 'where (non-defining)' non esprime possesso."
        ),
        clue="Possesso tra la città e i suoi canali, con le virgole.",
        rule="'Whose' esprime gli attributi di appartenenza anche di entità geografiche.",
    ),
    QuestionSpec(
        sentence="The historic castle, ______ was constructed in the twelfth century, was damaged by fire.",
        options=("which (non-defining)", "that (non-defining)", "where (non-defining)", "which (defining)"),
        correct="which (non-defining)",
        explanation=(
            "Il castello è il soggetto del passivo 'was constructed', quindi 'which', e le virgole "
            "rendono la relativa non-defining. 'that (non-defining)' è vietato, "
            "'where (non-defining)' sbaglia il pronome, 'which (defining)' sbaglia la "
            "classificazione."
        ),
        clue="Il castello compie l'azione espressa dal verbo passivo: non è il luogo di un'azione.",
        rule="Nelle non-defining un edificio soggetto richiede 'which'; 'that' non è mai ammesso.",
    ),
    QuestionSpec(
        sentence="The candidate ______ we interviewed yesterday had an impressive CV.",
        options=("who (defining)", "which (defining)", "who (non-defining)", "whose (defining)"),
        correct="who (defining)",
        explanation=(
            "Il candidato è una persona e il pronome è l'oggetto di 'interviewed': 'who'. Nessuna "
            "virgola, quindi defining. 'which (defining)' sbaglia l'antecedente, "
            "'who (non-defining)' sbaglia la classificazione, 'whose (defining)' il possesso."
        ),
        clue="Persona come oggetto del verbo della relativa, senza virgole.",
        rule="Per le persone oggetto nelle defining clauses si usa 'who' oppure 'that'.",
    ),
    QuestionSpec(
        sentence="The car ______ engine broke down on the motorway was towed away.",
        options=("whose (defining)", "which (defining)", "whose (non-defining)", "who (defining)"),
        correct="whose (defining)",
        explanation=(
            "Il motore appartiene all'auto: 'whose'. Nessuna virgola, quindi defining. "
            "'which (defining)' non può reggere 'engine', 'whose (non-defining)' sbaglia la "
            "classificazione, 'who (defining)' è riservato alle persone."
        ),
        clue="Il motore dell'auto: possesso tra una cosa e una sua parte.",
        rule="'Whose' si usa anche per le parti di un oggetto, in entrambe le classificazioni.",
    ),
    QuestionSpec(
        sentence="My sister, ______ works in Milan, is coming home for Christmas.",
        options=("who (non-defining)", "who (defining)", "that (non-defining)", "whose (non-defining)"),
        correct="who (non-defining)",
        explanation=(
            "La relativa tra virgole aggiunge un dettaglio su una sorella già identificata: "
            "non-defining. Persona soggetto di 'works', quindi 'who'. 'who (defining)' sbaglia la "
            "classificazione, 'that (non-defining)' è vietato, 'whose (non-defining)' esprime "
            "possesso e qui non serve."
        ),
        clue="Il possessivo 'my' identifica già la persona: le virgole aggiungono un dettaglio.",
        rule="Con un antecedente già identificato la relativa va tra virgole e richiede 'who'.",
    ),
    QuestionSpec(
        sentence="The film ______ we watched last night was absolutely terrifying.",
        options=("which (defining)", "whose (defining)", "which (non-defining)", "where (defining)"),
        correct="which (defining)",
        explanation=(
            "Il film è una cosa e il pronome è l'oggetto di 'watched': 'which'. Nessuna virgola, "
            "quindi defining. 'whose (defining)' non può reggere 'watched', 'which (non-defining)' "
            "sbaglia la classificazione, 'where (defining)' non può essere l'oggetto di un verbo."
        ),
        clue="Cosa inanimata oggetto di 'watched', senza virgole.",
        rule="Defining clause: per le cose oggetto si usa 'which' oppure 'that'.",
    ),
    QuestionSpec(
        sentence="The house ______ we rented in Cornwall had a beautiful garden.",
        options=("which (defining)", "where (defining)", "which (non-defining)", "that (non-defining)"),
        correct="which (defining)",
        explanation=(
            "Il verbo 'rented' ha bisogno di un oggetto, e quell'oggetto è la casa: serve 'which'. "
            "'where (defining)' è la trappola più insidiosa, ma 'where' sostituisce un complemento "
            "di luogo e qui il luogo è già espresso da 'in Cornwall'. Nessuna virgola: defining. "
            "'which (non-defining)' sbaglia la classificazione, 'that (non-defining)' è vietato."
        ),
        clue="'we rented' non è completa: manca l'oggetto, non il luogo, che è già 'in Cornwall'.",
        rule="Se il verbo della relativa è transitivo serve 'which' o 'that'; 'where' sostituisce solo un complemento di luogo mancante.",
    ),
    QuestionSpec(
        sentence="The teacher, ______ patience is legendary, never raises her voice.",
        options=("whose (non-defining)", "who (non-defining)", "which (non-defining)", "whose (defining)"),
        correct="whose (non-defining)",
        explanation=(
            "La pazienza appartiene all'insegnante: 'whose'. Le virgole rendono la relativa "
            "non-defining. 'who (non-defining)' non può reggere 'patience', 'which (non-defining)' "
            "sbaglia l'antecedente, 'whose (defining)' sbaglia la classificazione."
        ),
        clue="La pazienza dell'insegnante: possesso, con le virgole.",
        rule="'Whose' è l'unico pronome relativo che regge direttamente un sostantivo, in entrambe le classificazioni.",
    ),
    QuestionSpec(
        sentence="This is the best pizza ______ I have ever eaten.",
        options=("that (defining)", "that (non-defining)", "which (non-defining)", "who (defining)"),
        correct="that (defining)",
        explanation=(
            "Dopo un superlativo la scelta naturale in inglese è 'that'. La relativa è defining "
            "perché non ci sono virgole e perché restringe il riferimento alla pizza migliore. "
            "'that (non-defining)' è impossibile, 'which (non-defining)' sbaglia la "
            "classificazione, 'who (defining)' sbaglia l'antecedente."
        ),
        clue="Un superlativo restringe già il riferimento: nessuna virgola e 'that' come pronome naturale.",
        rule="Dopo un superlativo si preferisce 'that' nelle relative defining riferite a cose.",
    ),
    QuestionSpec(
        sentence="Everything ______ he told us turned out to be true.",
        options=("that (defining)", "that (non-defining)", "which (non-defining)", "whose (defining)"),
        correct="that (defining)",
        explanation=(
            "Con antecedenti come 'everything', 'all' e 'nothing' si usa 'that'. La relativa è "
            "defining perché non ci sono virgole. 'that (non-defining)' è impossibile, "
            "'which (non-defining)' sbaglia la classificazione, 'whose (defining)' esprime possesso "
            "e non può reggere 'told'."
        ),
        clue="Antecedente indefinito ('everything'): è la forma che in inglese richiede 'that'.",
        rule="Dopo 'everything', 'all', 'nothing' e simili si usa 'that' nella relativa defining.",
    ),
    QuestionSpec(
        sentence="She is the only person ______ knows the truth.",
        options=("who (defining)", "who (non-defining)", "which (defining)", "that (non-defining)"),
        correct="who (defining)",
        explanation=(
            "La relativa identifica l'unica persona che sa la verità: è defining, senza virgole, e "
            "il pronome è il soggetto di 'knows', quindi 'who'. 'who (non-defining)' è la trappola "
            "della virgola: con 'the only' l'informazione è essenziale e non può essere tra virgole. "
            "'which (defining)' sbaglia l'antecedente, 'that (non-defining)' è vietato."
        ),
        clue="'the only' rende l'informazione essenziale: nessuna virgola e pronome soggetto.",
        rule="Con 'the only' la relativa è sempre defining: niente virgole, e 'who' per le persone soggetto.",
    ),
    QuestionSpec(
        sentence="The lab ______ they carried out the experiment was closed for renovation.",
        options=("where (defining)", "which (defining)", "where (non-defining)", "that (defining)"),
        correct="where (defining)",
        explanation=(
            "'they carried out the experiment' è completa: manca il luogo, quindi 'where'. Nessuna "
            "virgola, quindi defining. 'which (defining)' e 'that (defining)' non possono essere "
            "l'oggetto di 'carried out', che ne ha già uno, 'where (non-defining)' sbaglia la "
            "classificazione."
        ),
        clue="La subordinata ha già soggetto e oggetto: manca solo il luogo.",
        rule="Se la relativa è completa si usa 'where'; 'which' e 'that' servono come soggetto o oggetto.",
    ),
    QuestionSpec(
        sentence="Her new novel, ______ has already sold a million copies, is set in Naples.",
        options=("which (non-defining)", "that (non-defining)", "which (defining)", "where (non-defining)"),
        correct="which (non-defining)",
        explanation=(
            "Il romanzo è il soggetto di 'has sold', quindi 'which', e le virgole rendono la "
            "relativa non-defining. 'that (non-defining)' è vietato, 'which (defining)' sbaglia la "
            "classificazione, 'where (non-defining)' sbaglia il pronome."
        ),
        clue="Il romanzo compie l'azione: è soggetto, non luogo.",
        rule="Nelle non-defining, una cosa soggetto richiede 'which' e mai 'that'.",
    ),
    QuestionSpec(
        sentence="The students, ______ had finished the exam early, were allowed to leave.",
        options=("who (non-defining)", "who (defining)", "that (non-defining)", "which (non-defining)"),
        correct="who (non-defining)",
        explanation=(
            "Le virgole presentano l'informazione come aggiuntiva su studenti già individuati: "
            "non-defining. Il pronome è il soggetto di 'had finished', quindi 'who'. "
            "'who (defining)' sbaglia la classificazione, 'that (non-defining)' è vietato, "
            "'which (non-defining)' sbaglia l'antecedente."
        ),
        clue="Due virgole e una persona soggetto del verbo della relativa.",
        rule="La virgola cambia la classificazione, non il pronome: per le persone soggetto resta 'who'.",
    ),
    QuestionSpec(
        sentence="The villa, ______ we spent the summer, has a view of the lake.",
        options=("where (non-defining)", "which (non-defining)", "where (defining)", "that (non-defining)"),
        correct="where (non-defining)",
        explanation=(
            "'we spent the summer' è completa e indica un soggiorno dentro la villa: serve 'where', "
            "e le virgole rendono la relativa non-defining. 'which (non-defining)' non può essere "
            "l'oggetto di 'spent', 'where (defining)' sbaglia la classificazione, "
            "'that (non-defining)' è vietato."
        ),
        clue="La relativa è completa: manca il luogo dell'azione, e le virgole la rendono accessoria.",
        rule="'Where' si usa anche nelle non-defining quando la relativa descrive ciò che avviene nel luogo.",
    ),
)


def option_classification(option: str) -> str | None:
    """The classification an option claims, or ``None`` when the option is malformed."""
    match = OPTION_SHAPE.match(option)
    return match.group(2) if match else None


def sentence_classification(sentence: str) -> str | None:
    """Read the classification off the punctuation: a comma before the blank means non-defining."""
    match = BLANK.search(sentence)
    if match is None:
        return None
    return "non-defining" if sentence[: match.start()].rstrip().endswith(",") else "defining"


class RelativeDefiningNonDefiningTopic:
    id = "english.grammar.relative_defining_non_defining"
    family = "english"
    difficulties = ("easy", "medium", "hard")
    label_key = "topic.english_relative_defining"
    scenarios: tuple[str, ...] = ()

    def generate(
        self,
        rng: random.Random,
        difficulty: str,
        seed: int,
        index: int,
        options: dict | None = None,
    ) -> Item:
        pool = EASY_QUESTIONS if difficulty == "easy" else MEDIUM_QUESTIONS
        chosen = pool[index % len(pool)]

        # Same convention as the other grammar topics: the order is shuffled so the correct
        # option is not always A, but deterministically, so a reload shows the same card.
        opt_rng = random.Random(f"{chosen.sentence}:{index}")
        shuffled = list(chosen.options)
        opt_rng.shuffle(shuffled)

        steps = (
            Step("step.grammar_analysis", f"\\text{{{chosen.clue}}}"),
            Step("step.rule_application", f"\\text{{{chosen.rule}}}"),
            Step("step.correct_form", f"\\textbf{{{chosen.correct}}}"),
        )
        answer = Answer(
            latex=f"\\textbf{{{chosen.correct}}}",
            kind="multiple_choice",
            payload={
                "options": shuffled,
                "correct": [chosen.correct],
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

        correct = payload.get("correct")
        if not correct or correct[0] not in options:
            return VerificationResult(False, "invalid_or_missing_correct_answer")

        # The grammar is part of the contract: an option that does not say both the pronoun
        # and the classification cannot be answered, and an answer whose classification
        # contradicts the commas in the sentence is a wrong question, not a wrong student.
        if any(option_classification(option) is None for option in options):
            return VerificationResult(False, "malformed_option")

        sentence_class = sentence_classification(item.statement_key)
        if sentence_class is None:
            return VerificationResult(False, "missing_blank")

        claimed = option_classification(correct[0])
        if correct[0].startswith("that ") and claimed == "non-defining":
            return VerificationResult(False, "that_in_non_defining")
        if claimed != sentence_class:
            return VerificationResult(False, "classification_mismatch")

        return VerificationResult(True, "ok")


TOPIC = RelativeDefiningNonDefiningTopic()
