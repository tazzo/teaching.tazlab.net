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

Every explanation says *why* the classification is what it is before it says which pronoun
goes in the blank, and names why the tempting option fails — in particular the twin that
has the right pronoun and the wrong classification. The clue carries the diagnostic signal
and never the answer: it names no pronoun. Several questions turn on the comma alone.
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
#: The relative pronouns the exercise can offer.
PRONOUNS = ("who", "which", "that", "whose", "where")


EASY_QUESTIONS: tuple[QuestionSpec, ...] = (
    QuestionSpec(
        sentence="The girl ______ won the science competition is in my class.",
        options=("who (defining)", "who (non-defining)", "which (defining)", "that (non-defining)"),
        correct="who (defining)",
        explanation=(
            "Defining: non ci sono virgole e la relativa serve a dire di quale ragazza si parla — "
            "senza di essa la frase non identifica nessuno. Il pronome è 'who' perché l'antecedente "
            "è una persona e il pronome è il soggetto di 'won'. 'who (non-defining)' ha il pronome "
            "giusto e la classificazione sbagliata: senza virgole l'informazione non può essere "
            "accessoria. 'which (defining)' sbaglia il pronome, perché 'the girl' non è una cosa, e "
            "'that (non-defining)' sbaglia entrambe le cose, perché 'that' non può introdurre una "
            "relativa tra virgole."
        ),
        clue="Nessuna virgola; l'antecedente è una persona e il verbo della relativa ('won') non ha ancora il suo soggetto.",
        rule="Defining clause, senza virgole: la relativa identifica il referente. Per le persone soggetto si usa 'who' (oppure 'that', ammesso solo qui).",
    ),
    QuestionSpec(
        sentence="This is the book ______ inspired me to become an engineer.",
        options=("which (defining)", "which (non-defining)", "that (non-defining)", "who (defining)"),
        correct="which (defining)",
        explanation=(
            "Defining: nessuna virgola e la relativa restringe il riferimento a un libro preciso. "
            "'which' perché 'the book' è una cosa e il pronome è il soggetto di 'inspired'. "
            "'which (non-defining)' ha il pronome giusto e la classificazione sbagliata: "
            "un'informazione accessoria starebbe fra virgole. 'who (defining)' sbaglia l'antecedente, "
            "perché un libro non è una persona, e 'that (non-defining)' è impossibile perché 'that' "
            "non regge una relativa tra virgole."
        ),
        clue="Nessuna virgola; antecedente inanimato e il verbo 'inspired' è ancora senza soggetto.",
        rule="Defining clause: per le cose, come soggetto o oggetto, si usa 'which' oppure 'that'.",
    ),
    QuestionSpec(
        sentence="My uncle, ______ is a pilot, flies planes all over the world.",
        options=("who (non-defining)", "who (defining)", "that (non-defining)", "which (non-defining)"),
        correct="who (non-defining)",
        explanation=(
            "Non-defining: la relativa è chiusa fra due virgole e aggiunge un dettaglio su uno zio "
            "già identificato — togliendola la frase resta completa. Il pronome è 'who' perché "
            "l'antecedente è una persona e il pronome è il soggetto di 'is'. 'who (defining)' ha il "
            "pronome giusto e la classificazione sbagliata: le virgole dicono che l'informazione è "
            "accessoria. 'that (non-defining)' è sempre scorretto, perché 'that' non può stare in una "
            "non-defining, e 'which (non-defining)' sbaglia l'antecedente personale."
        ),
        clue="Due virgole attorno alla relativa; l'antecedente è una persona e il verbo 'is' non ha ancora il soggetto.",
        rule="Non-defining clause, tra virgole: informazione accessoria. Per le persone si usa 'who'; 'that' è vietato.",
    ),
    QuestionSpec(
        sentence="The restaurant ______ we had dinner last night was excellent.",
        options=("where (defining)", "which (defining)", "where (non-defining)", "that (defining)"),
        correct="where (defining)",
        explanation=(
            "Defining: nessuna virgola e la relativa identifica il ristorante. Qui il pronome non è "
            "un oggetto ma un avverbio di luogo: 'we had dinner last night' ha già soggetto e "
            "oggetto, quindi manca il complemento di luogo e serve 'where'. 'which (defining)' e "
            "'that (defining)' sarebbero corretti solo se il verbo della relativa cercasse un "
            "oggetto, ma 'had' ne ha già uno ('dinner'); 'where (non-defining)' ha il pronome giusto "
            "e la classificazione sbagliata, perché senza virgole l'informazione è essenziale."
        ),
        clue="'we had dinner last night' è una frase già completa: il verbo 'had' ha il suo oggetto, quindi manca il luogo.",
        rule="Nelle defining clauses, se la subordinata è completa si usa 'where' (in cui / nel quale); 'which' e 'that' servono solo come soggetto o oggetto.",
    ),
    QuestionSpec(
        sentence="A mechanic is someone ______ repairs broken cars.",
        options=("who (defining)", "which (defining)", "who (non-defining)", "whose (defining)"),
        correct="who (defining)",
        explanation=(
            "Defining: nessuna virgola e la relativa definisce che cosa è un meccanico. 'who' perché "
            "'someone' è una persona e il pronome è il soggetto di 'repairs'. 'which (defining)' "
            "sbaglia l'antecedente, perché 'someone' non è una cosa. 'who (non-defining)' ha il "
            "pronome giusto e la classificazione sbagliata: senza virgole l'informazione è necessaria "
            "a definire il mestiere. 'whose (defining)' introduce un possesso che qui non c'è."
        ),
        clue="Nessuna virgola; 'someone' è una persona e il verbo 'repairs' non ha ancora il soggetto.",
        rule="Defining clause: con i pronomi indefiniti che indicano persone si usa 'who' (o 'that') come soggetto.",
    ),
    QuestionSpec(
        sentence="The computer ______ I bought last week has already crashed twice.",
        options=("which (defining)", "who (defining)", "which (non-defining)", "that (non-defining)"),
        correct="which (defining)",
        explanation=(
            "Defining: nessuna virgola e la relativa dice di quale computer si tratta. 'which' perché "
            "'the computer' è una cosa e il pronome è l'oggetto di 'bought'. 'who (defining)' sbaglia "
            "l'antecedente; 'which (non-defining)' ha il pronome giusto e la classificazione "
            "sbagliata; 'that (non-defining)' è impossibile perché 'that' non entra in una relativa "
            "tra virgole."
        ),
        clue="Nessuna virgola; cosa inanimata e il verbo 'bought' cerca il suo oggetto.",
        rule="Defining clause: per le cose oggetto si usa 'which' oppure 'that'.",
    ),
    QuestionSpec(
        sentence="My grandmother, ______ is 85, walks three miles every morning.",
        options=("who (non-defining)", "that (non-defining)", "who (defining)", "whose (non-defining)"),
        correct="who (non-defining)",
        explanation=(
            "Non-defining: le virgole racchiudono un commento su una nonna già identificata, e la "
            "frase regge anche senza. 'who' perché è una persona e il pronome è il soggetto di 'is'. "
            "'who (defining)' ha il pronome giusto e la classificazione sbagliata; 'that "
            "(non-defining)' è sempre vietato; 'whose (non-defining)' esprimerebbe un possesso che "
            "qui non c'è."
        ),
        clue="Due virgole; antecedente personale e il verbo 'is' senza soggetto.",
        rule="Non-defining clause: 'who' per le persone, mai 'that'.",
    ),
    QuestionSpec(
        sentence="A widow is a woman ______ husband has died.",
        options=("whose (defining)", "who (defining)", "whose (non-defining)", "which (defining)"),
        correct="whose (defining)",
        explanation=(
            "Defining: nessuna virgola e la relativa serve a spiegare che cosa è una vedova. 'whose' "
            "perché 'husband' appartiene alla donna: è l'unico pronome che regge direttamente un "
            "sostantivo. 'who (defining)' non può introdurre 'husband'; 'whose (non-defining)' ha il "
            "pronome giusto e la classificazione sbagliata; 'which (defining)' sbaglia l'antecedente "
            "personale."
        ),
        clue="Nessuna virgola; rapporto di possesso tra 'woman' e 'husband'.",
        rule="Si usa 'whose' quando il pronome esprime possesso e regge un sostantivo: vale sia in defining sia in non-defining.",
    ),
    QuestionSpec(
        sentence="The town ______ I grew up has changed completely.",
        options=("where (defining)", "which (defining)", "where (non-defining)", "that (defining)"),
        correct="where (defining)",
        explanation=(
            "Defining: nessuna virgola e la relativa identifica la città. 'I grew up' è completa e "
            "non ha oggetto, quindi manca il complemento di luogo: 'where'. 'which (defining)' e "
            "'that (defining)' funzionerebbero solo come soggetto o oggetto di un verbo che ne ha "
            "bisogno; 'where (non-defining)' ha il pronome giusto e la classificazione sbagliata."
        ),
        clue="Nessuna virgola; 'grew up' è intransitivo, quindi la relativa non cerca un oggetto.",
        rule="Con i luoghi si usa 'where' quando la relativa è completa; 'which' e 'that' solo se servono da soggetto o oggetto.",
    ),
    QuestionSpec(
        sentence="The students ______ failed the test must take it again next Friday.",
        options=("who (defining)", "who (non-defining)", "which (defining)", "whose (defining)"),
        correct="who (defining)",
        explanation=(
            "Defining: non ci sono virgole e la relativa identifica quali studenti devono rifare il "
            "test — è informazione essenziale, non un commento. Il pronome è 'who' perché sono "
            "persone e il pronome è il soggetto di 'failed'. 'who (non-defining)' è la trappola: "
            "stesso pronome, classificazione sbagliata, perché la frase non ha le virgole che una "
            "non-defining richiede. 'which (defining)' sbaglia l'antecedente e 'whose (defining)' un "
            "possesso che non c'è."
        ),
        clue="Nessuna virgola e antecedente personale; la relativa restringe il gruppo a chi ha fallito.",
        rule="La classificazione la decidono le virgole, non il pronome: senza virgole la relativa è defining.",
    ),
    QuestionSpec(
        sentence="Paris, ______ is known as the City of Light, attracts millions of visitors.",
        options=("which (non-defining)", "that (non-defining)", "which (defining)", "where (non-defining)"),
        correct="which (non-defining)",
        explanation=(
            "Non-defining: le virgole aggiungono un soprannome a una città già identificata. 'which' "
            "perché Parigi è il soggetto del passivo 'is known' — non è il luogo in cui avviene "
            "un'azione, quindi 'where' sarebbe sbagliato. 'that (non-defining)' è vietato; 'which "
            "(defining)' ha il pronome giusto e la classificazione sbagliata."
        ),
        clue="Due virgole; la città è il soggetto del verbo passivo 'is known'.",
        rule="Nelle non-defining, per una cosa o una città soggetto si usa 'which'; 'where' solo se la relativa descrive un'azione che avviene nel luogo.",
    ),
    QuestionSpec(
        sentence="The boy ______ dog ran away was crying in the park.",
        options=("whose (defining)", "whose (non-defining)", "who (defining)", "which (defining)"),
        correct="whose (defining)",
        explanation=(
            "Defining: nessuna virgola e la relativa identifica il ragazzo. 'whose' perché 'dog' "
            "appartiene a lui. 'whose (non-defining)' ha il pronome giusto e la classificazione "
            "sbagliata; 'who (defining)' non può reggere il sostantivo 'dog'; 'which (defining)' "
            "sbaglia l'antecedente personale."
        ),
        clue="Nessuna virgola; il cane è del ragazzo.",
        rule="'Whose' sostituisce 'his', 'her', 'their' e regge il sostantivo che segue, in entrambe le classificazioni.",
    ),
    QuestionSpec(
        sentence="The phone ______ was on the kitchen table started ringing.",
        options=("which (defining)", "who (defining)", "which (non-defining)", "that (non-defining)"),
        correct="which (defining)",
        explanation=(
            "Defining: nessuna virgola e la relativa dice di quale telefono si parla. 'which' perché "
            "è una cosa e il pronome è il soggetto di 'was'. 'who (defining)' sbaglia l'antecedente; "
            "'which (non-defining)' ha il pronome giusto e la classificazione sbagliata; 'that "
            "(non-defining)' è impossibile tra virgole."
        ),
        clue="Nessuna virgola; oggetto inanimato e il verbo 'was' senza soggetto.",
        rule="Defining clause con una cosa soggetto: 'which' oppure 'that'.",
    ),
    QuestionSpec(
        sentence="Dr Adams, ______ examined me at the clinic, was very reassuring.",
        options=("who (non-defining)", "that (non-defining)", "which (non-defining)", "who (defining)"),
        correct="who (non-defining)",
        explanation=(
            "Non-defining: nome e cognome identificano già la persona, quindi la relativa fra "
            "virgole aggiunge un dettaglio. 'who' perché è una persona e il pronome è il soggetto di "
            "'examined'. 'who (defining)' ha il pronome giusto e la classificazione sbagliata; 'that "
            "(non-defining)' è sempre vietato; 'which (non-defining)' sbaglia l'antecedente."
        ),
        clue="Due virgole; il referente è già identificato dal nome proprio.",
        rule="Dopo un nome proprio la relativa è di norma accessoria: virgole e 'who', mai 'that'.",
    ),
    QuestionSpec(
        sentence="This is the café ______ we usually have coffee.",
        options=("where (defining)", "which (defining)", "where (non-defining)", "whose (defining)"),
        correct="where (defining)",
        explanation=(
            "Defining: nessuna virgola e la relativa identifica il bar. 'we usually have coffee' è "
            "completa: 'have' ha già il suo oggetto, quindi manca il luogo e serve 'where'. 'which "
            "(defining)' non può essere l'oggetto di 'have', che ne ha già uno; 'where "
            "(non-defining)' ha il pronome giusto e la classificazione sbagliata; 'whose "
            "(defining)' esprime possesso e qui non c'è."
        ),
        clue="Nessuna virgola; 'have coffee' ha già l'oggetto, quindi la relativa non cerca un oggetto.",
        rule="Con i luoghi si usa 'where' quando la relativa non ha bisogno di soggetto o oggetto.",
    ),
    QuestionSpec(
        sentence="She has a friend ______ father is an ambassador.",
        options=("whose (defining)", "who (defining)", "whose (non-defining)", "which (defining)"),
        correct="whose (defining)",
        explanation=(
            "Defining: nessuna virgola e la relativa identifica di quale amica si parla. 'whose' "
            "perché 'father' appartiene a lei. 'who (defining)' non regge il sostantivo 'father'; "
            "'whose (non-defining)' ha il pronome giusto e la classificazione sbagliata; 'which "
            "(defining)' sbaglia l'antecedente."
        ),
        clue="Nessuna virgola; il padre è dell'amica.",
        rule="'Whose' introduce ciò che appartiene all'antecedente, in defining e in non-defining.",
    ),
    QuestionSpec(
        sentence="The umbrella ______ you lent me kept me completely dry.",
        options=("which (defining)", "who (defining)", "which (non-defining)", "whose (defining)"),
        correct="which (defining)",
        explanation=(
            "Defining: nessuna virgola e la relativa identifica l'ombrello. 'which' perché è una "
            "cosa e il pronome è l'oggetto di 'lent'. 'who (defining)' sbaglia l'antecedente; 'which "
            "(non-defining)' ha il pronome giusto e la classificazione sbagliata; 'whose "
            "(defining)' esprime possesso e non può essere l'oggetto di 'lent'."
        ),
        clue="Nessuna virgola; cosa inanimata e 'lent' cerca il suo oggetto.",
        rule="Defining clause: per le cose oggetto si usa 'which' oppure 'that'.",
    ),
    QuestionSpec(
        sentence="The hotel, ______ had a rooftop swimming pool, was right by the sea.",
        options=("which (non-defining)", "that (non-defining)", "where (non-defining)", "which (defining)"),
        correct="which (non-defining)",
        explanation=(
            "Non-defining: le virgole aggiungono un dettaglio a un albergo già identificato. 'which' "
            "perché l'albergo è il soggetto di 'had' — non è il luogo di un'azione altrui, quindi "
            "'where' non va. 'that (non-defining)' è vietato; 'which (defining)' ha il pronome "
            "giusto e la classificazione sbagliata."
        ),
        clue="Due virgole; l'albergo è il soggetto del verbo 'had'.",
        rule="Nelle non-defining un edificio soggetto richiede 'which'; 'that' è sempre escluso.",
    ),
    QuestionSpec(
        sentence="The woman ______ lives next door is an architect.",
        options=("who (defining)", "who (non-defining)", "which (defining)", "where (defining)"),
        correct="who (defining)",
        explanation=(
            "Defining: nessuna virgola e la relativa identifica la donna. 'who' perché è una persona "
            "e il pronome è il soggetto di 'lives'. 'who (non-defining)' è la trappola della "
            "virgola: stesso pronome, classificazione sbagliata, perché senza virgole l'informazione "
            "è essenziale. 'which (defining)' sbaglia l'antecedente e 'where (defining)' non può "
            "fare da soggetto a un verbo."
        ),
        clue="Nessuna virgola; una persona e il verbo 'lives' senza soggetto.",
        rule="Senza virgole la relativa è defining: 'who' (o 'that') per le persone soggetto.",
    ),
    QuestionSpec(
        sentence="Rome, ______ was founded in 753 BC, is the capital of Italy.",
        options=("which (non-defining)", "where (non-defining)", "that (non-defining)", "which (defining)"),
        correct="which (non-defining)",
        explanation=(
            "Non-defining: le virgole aggiungono una data a una città già identificata. 'which' "
            "perché Roma è il soggetto del passivo 'was founded'; 'where' vorrebbe dire che l'azione "
            "avviene a Roma, ma chi fonda non è la città. 'that (non-defining)' è vietato; 'which "
            "(defining)' ha il pronome giusto e la classificazione sbagliata."
        ),
        clue="Due virgole; la città è il soggetto del verbo passivo.",
        rule="Una città soggetto richiede 'which'; 'where' si usa solo per un'azione che avviene nel luogo.",
    ),
)


MEDIUM_QUESTIONS: tuple[QuestionSpec, ...] = (
    QuestionSpec(
        sentence="He arrived twenty minutes late, ______ annoyed the teacher greatly.",
        options=("which (non-defining)", "that (non-defining)", "which (defining)", "who (non-defining)"),
        correct="which (non-defining)",
        explanation=(
            "Non-defining: la virgola segnala un commento che riguarda tutta la frase precedente, non "
            "un sostantivo. 'which' è l'unico pronome che può riferirsi a un'intera proposizione. "
            "'that (non-defining)' è vietato; 'which (defining)' ha il pronome giusto ma non può "
            "introdurre un commento separato da virgola; 'who (non-defining)' si riferisce a persone, "
            "non a una frase."
        ),
        clue="Una sola virgola, e il pronome non ha un sostantivo a cui appoggiarsi: guarda che cosa c'è prima.",
        rule="Per commentare un'intera frase si usa ', which': non-defining e mai 'that'.",
    ),
    QuestionSpec(
        sentence="The company, ______ headquarters are in Zurich, announced record profits.",
        options=("whose (non-defining)", "which (non-defining)", "whose (defining)", "that (non-defining)"),
        correct="whose (non-defining)",
        explanation=(
            "Non-defining: le virgole presentano la sede come dettaglio di un'azienda già "
            "identificata. 'whose' perché 'headquarters' appartiene alla compagnia, e regge "
            "direttamente il sostantivo. 'which (non-defining)' non può reggere 'headquarters'; "
            "'whose (defining)' ha il pronome giusto e la classificazione sbagliata; 'that "
            "(non-defining)' è vietato."
        ),
        clue="Due virgole; la sede è dell'azienda, e 'headquarters' non ha articolo: dipende dal pronome.",
        rule="'Whose' esprime possesso anche con aziende e istituzioni, in entrambe le classificazioni.",
    ),
    QuestionSpec(
        sentence="Mount Everest, ______ peak is the highest in the world, attracts thousands of climbers.",
        options=("whose (non-defining)", "which (non-defining)", "that (non-defining)", "whose (defining)"),
        correct="whose (non-defining)",
        explanation=(
            "Non-defining: le virgole aggiungono un primato a una montagna già identificata. 'whose' "
            "perché 'peak' appartiene alla montagna. 'which (non-defining)' non regge 'peak'; 'that "
            "(non-defining)' è vietato; 'whose (defining)' ha il pronome giusto e la classificazione "
            "sbagliata."
        ),
        clue="Due virgole; la vetta è della montagna, e 'peak' dipende dal pronome.",
        rule="'Whose' si usa anche per elementi geografici e cose inanimate, al posto di 'of which'.",
    ),
    QuestionSpec(
        sentence="Children ______ parents are both working often attend after-school clubs.",
        options=("whose (defining)", "who (defining)", "whose (non-defining)", "which (defining)"),
        correct="whose (defining)",
        explanation=(
            "Defining: nessuna virgola e la relativa restringe il gruppo ai bambini con genitori "
            "lavoratori. 'whose' perché 'parents' appartiene ai bambini. 'who (defining)' non può "
            "reggere 'parents'; 'whose (non-defining)' ha il pronome giusto e la classificazione "
            "sbagliata; 'which (defining)' sbaglia l'antecedente personale."
        ),
        clue="Nessuna virgola; i genitori sono dei bambini, e 'parents' non ha articolo.",
        rule="Nelle defining 'whose' indica legami familiari o di possesso.",
    ),
    QuestionSpec(
        sentence="The politician, ______ was accused of corruption, resigned from parliament.",
        options=("who (non-defining)", "that (non-defining)", "which (non-defining)", "who (defining)"),
        correct="who (non-defining)",
        explanation=(
            "Non-defining: le virgole aggiungono un'accusa su un politico già identificato. 'who' "
            "perché è una persona e il pronome è il soggetto di 'was accused'. 'that "
            "(non-defining)' è vietato; 'which (non-defining)' sbaglia l'antecedente; 'who "
            "(defining)' ha il pronome giusto e la classificazione sbagliata."
        ),
        clue="Due virgole; una persona e il passivo 'was accused' senza soggetto.",
        rule="Nelle non-defining con una persona soggetto si usa 'who', mai 'that'.",
    ),
    QuestionSpec(
        sentence="Venice, ______ canals are famous across the world, is threatened by rising sea levels.",
        options=("whose (non-defining)", "whose (defining)", "which (non-defining)", "where (non-defining)"),
        correct="whose (non-defining)",
        explanation=(
            "Non-defining: le virgole aggiungono un dettaglio su una città già identificata. 'whose' "
            "perché i canali appartengono a Venezia. 'whose (defining)' ha il pronome giusto e la "
            "classificazione sbagliata; 'which (non-defining)' non regge 'canals'; 'where "
            "(non-defining)' indica un luogo, non un possesso."
        ),
        clue="Due virgole; i canali sono di Venezia.",
        rule="'Whose' esprime appartenenza anche per entità geografiche.",
    ),
    QuestionSpec(
        sentence="The historic castle, ______ was constructed in the twelfth century, was damaged by fire.",
        options=("which (non-defining)", "that (non-defining)", "where (non-defining)", "which (defining)"),
        correct="which (non-defining)",
        explanation=(
            "Non-defining: le virgole aggiungono una data a un castello già identificato. 'which' "
            "perché il castello è il soggetto del passivo 'was constructed'; 'where' indicherebbe un "
            "luogo in cui avviene un'azione, non il soggetto che la subisce. 'that (non-defining)' è "
            "vietato; 'which (defining)' ha il pronome giusto e la classificazione sbagliata."
        ),
        clue="Due virgole; il castello è il soggetto del passivo.",
        rule="Nelle non-defining un edificio soggetto richiede 'which'; 'that' non è mai ammesso.",
    ),
    QuestionSpec(
        sentence="The candidate ______ we interviewed yesterday had an impressive CV.",
        options=("who (defining)", "which (defining)", "who (non-defining)", "whose (defining)"),
        correct="who (defining)",
        explanation=(
            "Defining: nessuna virgola e la relativa identifica il candidato. 'who' perché è una "
            "persona e il pronome è l'oggetto di 'interviewed'. 'which (defining)' sbaglia "
            "l'antecedente; 'who (non-defining)' ha il pronome giusto e la classificazione "
            "sbagliata; 'whose (defining)' esprimerebbe un possesso che non c'è."
        ),
        clue="Nessuna virgola; una persona e 'interviewed' cerca il suo oggetto.",
        rule="Per le persone oggetto nelle defining si usa 'who' (oppure 'that').",
    ),
    QuestionSpec(
        sentence="The car ______ engine broke down on the motorway was towed away.",
        options=("whose (defining)", "which (defining)", "whose (non-defining)", "who (defining)"),
        correct="whose (defining)",
        explanation=(
            "Defining: nessuna virgola e la relativa identifica l'auto. 'whose' perché 'engine' è "
            "parte dell'auto. 'which (defining)' non può reggere 'engine'; 'whose (non-defining)' "
            "ha il pronome giusto e la classificazione sbagliata; 'who (defining)' è riservato alle "
            "persone."
        ),
        clue="Nessuna virgola; il motore è parte dell'auto.",
        rule="'Whose' si usa anche per le parti di un oggetto, in entrambe le classificazioni.",
    ),
    QuestionSpec(
        sentence="My sister, ______ works in Milan, is coming home for Christmas.",
        options=("who (non-defining)", "who (defining)", "that (non-defining)", "whose (non-defining)"),
        correct="who (non-defining)",
        explanation=(
            "Non-defining: il possessivo 'my' identifica già la persona, quindi le virgole "
            "aggiungono solo un dettaglio. 'who' perché è una persona e il pronome è il soggetto di "
            "'works'. 'who (defining)' ha il pronome giusto e la classificazione sbagliata; 'that "
            "(non-defining)' è vietato; 'whose (non-defining)' esprime possesso e qui non serve."
        ),
        clue="Due virgole; 'my' identifica già la persona e 'works' aspetta il soggetto.",
        rule="Con un antecedente già identificato la relativa è accessoria: virgole e 'who'.",
    ),
    QuestionSpec(
        sentence="The film ______ we watched last night was absolutely terrifying.",
        options=("which (defining)", "whose (defining)", "which (non-defining)", "where (defining)"),
        correct="which (defining)",
        explanation=(
            "Defining: nessuna virgola e la relativa identifica il film. 'which' perché è una cosa e "
            "il pronome è l'oggetto di 'watched'. 'whose (defining)' non può reggere 'watched'; "
            "'which (non-defining)' ha il pronome giusto e la classificazione sbagliata; 'where "
            "(defining)' non può essere oggetto di un verbo."
        ),
        clue="Nessuna virgola; cosa inanimata e 'watched' cerca il suo oggetto.",
        rule="Defining clause: per le cose oggetto si usa 'which' oppure 'that'.",
    ),
    QuestionSpec(
        sentence="The house ______ we rented in Cornwall had a beautiful garden.",
        options=("which (defining)", "where (defining)", "which (non-defining)", "that (non-defining)"),
        correct="which (defining)",
        explanation=(
            "Defining: nessuna virgola e la relativa identifica la casa. 'rented' è transitivo e il "
            "suo oggetto è la casa, quindi serve 'which'. 'where (defining)' è la trappola più "
            "insidiosa: sostituirebbe un complemento di luogo, ma il luogo è già detto ('in "
            "Cornwall'). 'which (non-defining)' ha il pronome giusto e la classificazione "
            "sbagliata; 'that (non-defining)' è vietato."
        ),
        clue="Nessuna virgola; 'we rented' è transitivo e il luogo è già 'in Cornwall'.",
        rule="Se il verbo della relativa è transitivo serve 'which' o 'that'; 'where' sostituisce solo un complemento di luogo mancante.",
    ),
    QuestionSpec(
        sentence="The teacher, ______ patience is legendary, never raises her voice.",
        options=("whose (non-defining)", "who (non-defining)", "which (non-defining)", "whose (defining)"),
        correct="whose (non-defining)",
        explanation=(
            "Non-defining: le virgole aggiungono un dettaglio su un'insegnante già identificata. "
            "'whose' perché la pazienza è sua e regge direttamente il sostantivo. 'who "
            "(non-defining)' non può reggere 'patience'; 'which (non-defining)' sbaglia "
            "l'antecedente; 'whose (defining)' ha il pronome giusto e la classificazione sbagliata."
        ),
        clue="Due virgole; la pazienza è dell'insegnante.",
        rule="'Whose' è l'unico pronome relativo che regge direttamente un sostantivo, in entrambe le classificazioni.",
    ),
    QuestionSpec(
        sentence="This is the best pizza ______ I have ever eaten.",
        options=("that (defining)", "that (non-defining)", "which (non-defining)", "who (defining)"),
        correct="that (defining)",
        explanation=(
            "Defining: nessuna virgola, e il superlativo restringe già il riferimento alla pizza "
            "migliore, quindi la relativa è essenziale. Qui 'that' è la scelta naturale dopo un "
            "superlativo. 'that (non-defining)' è impossibile; 'which (non-defining)' ha il pronome "
            "giusto e la classificazione sbagliata; 'who (defining)' sbaglia l'antecedente."
        ),
        clue="Nessuna virgola e un superlativo ('the best'): il riferimento è già ristretto.",
        rule="Dopo un superlativo si preferisce 'that' nelle relative defining riferite a cose.",
    ),
    QuestionSpec(
        sentence="Everything ______ he told us turned out to be true.",
        options=("that (defining)", "that (non-defining)", "which (non-defining)", "whose (defining)"),
        correct="that (defining)",
        explanation=(
            "Defining: nessuna virgola e la relativa restringe 'everything' a ciò che lui ha "
            "raccontato. Con antecedenti come 'everything', 'all' o 'nothing' la forma naturale è "
            "'that'. 'that (non-defining)' è impossibile; 'which (non-defining)' ha il pronome "
            "giusto e la classificazione sbagliata; 'whose (defining)' esprime possesso e non può "
            "reggere 'told'."
        ),
        clue="Nessuna virgola; antecedente indefinito ('everything').",
        rule="Dopo 'everything', 'all', 'nothing' e simili si usa 'that' nella relativa defining.",
    ),
    QuestionSpec(
        sentence="She is the only person ______ knows the truth.",
        options=("who (defining)", "who (non-defining)", "which (defining)", "that (non-defining)"),
        correct="who (defining)",
        explanation=(
            "Defining: con 'the only' l'informazione è essenziale — non ci sono altre persone — e "
            "non ci sono virgole. 'who' perché è una persona e il pronome è il soggetto di 'knows'. "
            "'who (non-defining)' è la trappola della virgola: stesso pronome, classificazione "
            "sbagliata, perché un'informazione essenziale non può stare fra virgole. 'which "
            "(defining)' sbaglia l'antecedente e 'that (non-defining)' è vietato."
        ),
        clue="Nessuna virgola; 'the only' rende l'informazione necessaria, e 'knows' aspetta il soggetto.",
        rule="Con 'the only' la relativa è sempre defining: niente virgole, e 'who' per le persone soggetto.",
    ),
    QuestionSpec(
        sentence="The lab ______ they carried out the experiment was closed for renovation.",
        options=("where (defining)", "which (defining)", "where (non-defining)", "that (defining)"),
        correct="where (defining)",
        explanation=(
            "Defining: nessuna virgola e la relativa identifica il laboratorio. 'they carried out "
            "the experiment' è completa e ha già l'oggetto, quindi manca il luogo: 'where'. 'which "
            "(defining)' e 'that (defining)' non possono essere l'oggetto di 'carried out', che ne "
            "ha già uno; 'where (non-defining)' ha il pronome giusto e la classificazione "
            "sbagliata."
        ),
        clue="Nessuna virgola; soggetto e oggetto ci sono già, manca il luogo.",
        rule="Se la relativa è completa si usa 'where'; 'which' e 'that' servono come soggetto o oggetto.",
    ),
    QuestionSpec(
        sentence="Her new novel, ______ has already sold a million copies, is set in Naples.",
        options=("which (non-defining)", "that (non-defining)", "which (defining)", "where (non-defining)"),
        correct="which (non-defining)",
        explanation=(
            "Non-defining: le virgole aggiungono un dato su un romanzo già identificato ('her new "
            "novel'). 'which' perché il romanzo è il soggetto di 'has sold'; 'where' non può essere "
            "soggetto. 'that (non-defining)' è vietato; 'which (defining)' ha il pronome giusto e "
            "la classificazione sbagliata."
        ),
        clue="Due virgole; il romanzo è il soggetto del verbo 'has sold'.",
        rule="Nelle non-defining, una cosa soggetto richiede 'which' e mai 'that'.",
    ),
    QuestionSpec(
        sentence="The students, ______ had finished the exam early, were allowed to leave.",
        options=("who (non-defining)", "who (defining)", "that (non-defining)", "which (non-defining)"),
        correct="who (non-defining)",
        explanation=(
            "Non-defining: le virgole presentano l'informazione come aggiuntiva su studenti già "
            "individuati. 'who' perché sono persone e il pronome è il soggetto di 'had finished'. "
            "'who (defining)' ha il pronome giusto e la classificazione sbagliata; 'that "
            "(non-defining)' è vietato; 'which (non-defining)' sbaglia l'antecedente."
        ),
        clue="Due virgole; persone e il verbo 'had finished' senza soggetto.",
        rule="La virgola cambia la classificazione, non il pronome: per le persone soggetto resta 'who'.",
    ),
    QuestionSpec(
        sentence="The villa, ______ we spent the summer, has a view of the lake.",
        options=("where (non-defining)", "which (non-defining)", "where (defining)", "that (non-defining)"),
        correct="where (non-defining)",
        explanation=(
            "Non-defining: le virgole rendono accessorio il soggiorno in villa. 'we spent the "
            "summer' è completa ('the summer' è già l'oggetto) e descrive un'azione dentro la villa, "
            "quindi serve 'where'. 'which (non-defining)' non può essere l'oggetto di 'spent', che "
            "ne ha già uno; 'where (defining)' ha il pronome giusto e la classificazione sbagliata; "
            "'that (non-defining)' è vietato."
        ),
        clue="Due virgole; 'spent' ha già il suo oggetto ('the summer'), manca il luogo.",
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
