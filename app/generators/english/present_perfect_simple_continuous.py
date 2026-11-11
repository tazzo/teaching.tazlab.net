"""Present Perfect Simple vs Continuous — and the pronoun that goes with it.

The operator asked for **a page, not a PDF**: the same online exercise the site already
serves for relative clauses (``english-relative-classification``), fed by this pool. The
interaction is the one the operator chose and it is reused untouched:
``CLASSIFICATION_CHOICE`` — two moves per card, the kind is chosen first and the check
button is born disabled, with one line under it saying why. What changes is only the
content the picker asks about, which travels in the payload instead of being hardcoded
in the client.

Three groups of statements, in the order the schema lists them:

* **1-10 — Simple or Continuous?** the decision is carried by the indicator in the
  sentence: ``already, just, yet, ever, three times, so far, recently`` point at a
  completed result, ``all morning, for two hours, since yesterday evening, lately`` at an
  activity still going on. Six answers are Simple, four Continuous, so neither aspect wins
  by habit. Every card offers the twin of the correct form among its four options.
* **11-15 — the Continuous is impossible.** ``know, belong, believe, understand, have``
  (possession): verbs of state describe a condition, not an activity, so ``-ing`` is
  agrammatical however long the duration is. These are the cards where a student who
  applies "duration means continuous" gets it wrong, which is the whole point.
* **16-21 — relative pronouns.** ``who`` (person), ``which`` (thing), ``where`` (place),
  ``whose`` (possession), and two cards where ``that`` stands among the options inside a
  pair of commas, where it is always wrong: a non-defining clause never takes ``that``.

There is no label anywhere on the card: the signal is in the sentence (the indicator, the
verb, the commas), never in a parenthesis next to an option. The explanation opens with
the *reason*, not with the form, and names the tempting twin that fails.

The picker asks two different questions because the pool contains two different grammars,
and a single question would be false for one of them:

* ``azione`` / ``stato`` for the verb cards — the schema's own precondition for the
  Continuous ("solo verbi d'azione"). It does **not** hand over the form: an action verb
  takes the Simple with a result (``I have sent it``) and the Continuous with a duration
  (``I have been sending it``), so the form is still read off the indicator;
* ``defining`` / ``non-defining`` for the clause cards — the comma decides, and with it
  whether ``that`` is allowed at all.

``verify`` derives both truths from the sentence rather than trusting the data: the verb
class from the hint in parentheses against the same ``STATIVES`` set the medium topic uses,
the clause class from the punctuation (``sentence_classification``). A card that claims a
class its own sentence contradicts is a broken question, not a wrong student.
"""

from __future__ import annotations

import random
import re
from typing import NamedTuple

from app.core.verify import VerificationResult
from app.generators.base import Answer, Item, Step
from app.generators.english.present_perfect_medium import (
    STATIVES,
    VERB_HINT,
    WORD,
    aspect,
)
from app.generators.english.relative_grammar import sentence_classification


class QuestionSpec(NamedTuple):
    sentence: str
    options: tuple[str, str, str, str]
    correct: str
    explanation: str
    clue: str
    rule: str
    #: The value the picker must land on. Whatever grammar the card teaches, the second
    #: fact is asked separately and stored here — never written inside the sentence.
    classification: str
    #: Which picker this card shows: ``verb`` (azione/stato) or ``clause``
    #: (defining/non-defining). The two grammars in one pool need two questions.
    family: str = "verb"


#: The blank the student fills; the exercise text uses six underscores.
BLANK = re.compile(r"_{3,}")
#: The pronouns an option can be, taken from the sibling page so the two cannot drift.
PRONOUNS = ("who", "which", "that", "whose", "where")

#: The two values of each picker, with the label key the client prints. Order is the
#: order of the buttons: the first one is not privileged by anything but the layout.
CLASSIFICATIONS: dict[str, tuple[tuple[str, str], ...]] = {
    "verb": (
        ("action", "ui.classification_verb_action"),
        ("state", "ui.classification_verb_state"),
    ),
    "clause": (
        ("defining", "ui.classification_defining"),
        ("non-defining", "ui.classification_non_defining"),
    ),
}

#: The prompt, the lock line and the wrong-kind line, one set per picker: a sentence about
#: the kind of a relative clause has nothing to say about a verb of state.
TEXTS: dict[str, dict[str, str]] = {
    "verb": {
        "prompt": "ui.classification_prompt_verb",
        "locked": "ui.classification_locked_verb",
        "wrong": "ui.classification_wrong_verb",
        "option_wrong": "ui.form_wrong",
    },
    "clause": {
        "prompt": "ui.classification_prompt",
        "locked": "ui.classification_locked",
        "wrong": "ui.classification_wrong",
        "option_wrong": "ui.pronoun_wrong",
    },
}

#: A classification written into the sentence — the label that would hand the answer over.
#: Both spellings are covered: the card is read in Italian, the grammar terms are English.
LABEL_IN_SENTENCE = re.compile(r"\b(?:defining|action|state|azione|stato)\b", re.IGNORECASE)


QUESTIONS: tuple[QuestionSpec, ...] = (
    # --- 1-10: Simple or Continuous, decided by the indicator ------------------
    QuestionSpec(
        sentence="I ______ (already / send) the report, so the manager has it on her desk.",
        options=("have already sent", "have already been sending",
                 "already sent", "am already sending"),
        correct="have already sent",
        explanation=(
            "Il risultato è compiuto e il suo effetto è ancora presente ('has it on her "
            "desk'): 'already' segna il punto raggiunto, quindi Present Perfect Simple. "
            "'have already been sending' mette al centro l'attività di invio ancora in "
            "corso, e un'attività in corso non lascia il rapporto sul tavolo. 'already "
            "sent' (past simple) chiude l'invio nel passato e taglia il legame con il "
            "presente. 'am already sending' descrive solo l'istante in cui si parla."
        ),
        clue="L'invio è concluso e il risultato è ancora sul tavolo ('has it on her desk'); "
             "'already' segna un punto raggiunto.",
        rule="'Already' e 'just' vanno con il Present Perfect Simple quando il risultato "
             "dell'azione è compiuto e conta ancora adesso.",
        classification="action",
    ),
    QuestionSpec(
        sentence="She ______ (just / finish) her homework, so she can go out with us.",
        options=("has just been finishing", "was just finishing",
                 "is just finishing", "has just finished"),
        correct="has just finished",
        explanation=(
            "Il permesso di uscire è la conseguenza di un compito concluso un attimo prima: "
            "'just' segna il risultato appena raggiunto e vuole il Present Perfect Simple. "
            "'has just been finishing' presenterebbe il compito come attività ancora aperta, "
            "e un compito aperto non fa uscire nessuno. 'was just finishing' (past "
            "continuous) chiude la scena nel passato. 'is just finishing' dice che sta "
            "finendo proprio ora, senza il risultato già acquisito."
        ),
        clue="Il compito è concluso e il permesso di uscire è la sua conseguenza ('she can go "
             "out'); 'just' segna un risultato appena raggiunto.",
        rule="'Just' con un risultato compiuto vuole il Present Perfect Simple.",
        classification="action",
    ),
    QuestionSpec(
        sentence="We ______ (not / decide) yet where to spend the summer holidays.",
        options=("didn't decide", "don't decide", "haven't decided", "haven't been deciding"),
        correct="haven't decided",
        explanation=(
            "'yet' dice che la decisione è attesa e non è ancora arrivata: il tempo non è "
            "concluso e si guarda al risultato mancante, quindi Present Perfect Simple alla "
            "forma negativa. 'haven't been deciding' descrive un'attività di decisione in "
            "corso, che 'yet' non chiede. 'didn't decide' (past simple) chiuderebbe la "
            "questione nel passato, come se non ci fosse più niente da decidere. 'don't "
            "decide' è un Present Simple: descrive un'abitudine."
        ),
        clue="'yet' segna un risultato atteso e non ancora raggiunto.",
        rule="Con 'yet' il Present Perfect Simple dice che il risultato non è ancora arrivato.",
        classification="action",
    ),
    QuestionSpec(
        sentence="______ (you / ever / eat) sushi in your life?",
        options=("Do you ever eat", "Have you ever eaten",
                 "Have you ever been eating", "Did you ever eat"),
        correct="Have you ever eaten",
        explanation=(
            "'ever' chiede se l'esperienza esiste nel corso della vita fino a ora: il tempo "
            "non è definito e non è concluso, quindi Present Perfect Simple. 'have you ever "
            "been eating' mette in primo piano lo svolgersi dell'attività e non "
            "l'esperienza. 'did you ever eat' chiude l'esperienza in un passato concluso che "
            "la frase non nomina. 'do you ever eat' è un'abitudine, non un bilancio di "
            "esperienze."
        ),
        clue="'ever' chiede un'esperienza dentro un tempo che arriva fino a ora, senza un "
             "momento definito.",
        rule="'Ever' e 'never' con il Present Perfect Simple parlano di esperienze, senza "
             "dire quando.",
        classification="action",
    ),
    QuestionSpec(
        sentence="He ______ (call) me three times so far this morning.",
        options=("has called", "has been calling", "called", "is calling"),
        correct="has called",
        explanation=(
            "'three times so far' conta i risultati raggiunti dentro un tempo ancora aperto "
            "('this morning'): un numero di azioni concluse, quindi Present Perfect Simple. "
            "'has been calling' descrive l'attività continua e non il conto delle chiamate. "
            "'called' (past simple) metterebbe le chiamate in un tempo chiuso, mentre la "
            "mattina non è finita. 'is calling' dice soltanto che sta chiamando adesso."
        ),
        clue="'three times so far' conta azioni concluse dentro un tempo che non è ancora "
             "finito.",
        rule="Con un conteggio ('once', 'three times', 'so far') il Present Perfect Simple "
             "somma risultati.",
        classification="action",
    ),
    QuestionSpec(
        sentence="He ______ (call) me all morning, and I still haven't picked up.",
        options=("has called", "calls", "is calling", "has been calling"),
        correct="has been calling",
        explanation=(
            "'all morning' misura la durata di un'attività che arriva fino a ora e non è "
            "finita, e 'I still haven't picked up' dice che continua: Present Perfect "
            "Continuous. 'has called' conterebbe le chiamate concluse invece di descrivere "
            "l'attività. 'calls' è un'abitudine, senza il tratto di tempo che arriva ad "
            "adesso. 'is calling' descrive l'istante presente e perde la mattinata intera."
        ),
        clue="'all morning' misura quanto dura un'attività che continua ancora adesso.",
        rule="'All day' e 'all morning' misurano la durata di un'attività: Present Perfect "
             "Continuous.",
        classification="action",
    ),
    QuestionSpec(
        sentence="They ______ (play) football for two hours and nobody has scored yet.",
        options=("play", "are playing", "have been playing", "have played"),
        correct="have been playing",
        explanation=(
            "'for two hours' dice quanto dura un'attività ancora in corso, e 'nobody has "
            "scored yet' conferma che la partita continua: Present Perfect Continuous. "
            "'have played' presenterebbe il gioco come concluso o come un computo di "
            "partite. 'play' è un'abitudine e 'are playing' solo il momento presente, senza "
            "le due ore già trascorse."
        ),
        clue="'for two hours' più una partita che non è finita ('nobody has scored yet').",
        rule="'For' con una durata misura l'attività: Present Perfect Continuous se l'attività "
             "non è conclusa.",
        classification="action",
    ),
    QuestionSpec(
        sentence="It ______ (rain) since yesterday evening, and the garden is flooded.",
        options=("rained", "has been raining", "has rained", "rains"),
        correct="has been raining",
        explanation=(
            "'since yesterday evening' dà il punto di partenza e il giardino allagato mostra "
            "l'effetto di un'attività che non si è fermata: Present Perfect Continuous. "
            "'has rained' suonerebbe come un bilancio di piogge concluse. 'rains' descrive il "
            "clima in generale e 'rained' chiude la pioggia nel passato, mentre "
            "l'allagamento è di adesso."
        ),
        clue="'since' con un punto di partenza e un effetto visibile adesso.",
        rule="'Since' più un'attività che continua vuole il Present Perfect Continuous.",
        classification="action",
    ),
    QuestionSpec(
        sentence="My brother ______ (recently / start) a new job at the hospital.",
        options=("has recently started", "has recently been starting",
                 "recently started", "is recently starting"),
        correct="has recently started",
        explanation=(
            "'recently' colloca il fatto in un passato vicino che tocca il presente, e "
            "'start' è un'azione puntuale che si compie una volta: Present Perfect Simple. "
            "'has recently been starting' proporrebbe un inizio ripetuto e in corso, che "
            "'start' non ammette. 'recently started' (past simple) rinuncia al legame con "
            "ora che 'recently' senza momento definito richiede. 'is recently starting' non "
            "esiste in inglese."
        ),
        clue="'recently' con un'azione puntuale, che si compie una volta sola.",
        rule="Le azioni puntuali ('start', 'finish', 'send') con 'recently' prendono il "
             "Present Perfect Simple.",
        classification="action",
    ),
    QuestionSpec(
        sentence="I ______ (sleep) badly lately, because the neighbours' dog barks all night.",
        options=("have slept", "sleep", "slept", "have been sleeping"),
        correct="have been sleeping",
        explanation=(
            "'lately' descrive un periodo aperto che arriva a oggi e 'badly' riguarda il "
            "modo di dormire, non un conteggio di notti: Present Perfect Continuous. 'have "
            "slept' conterebbe le notti concluse invece di descrivere come vanno le cose "
            "ultimamente. 'sleep' è un'abitudine senza limite di tempo e 'slept' chiude il "
            "disturbo nel passato."
        ),
        clue="'lately' descrive un periodo aperto fino a oggi, e 'badly' riguarda il modo, "
             "non un conteggio.",
        rule="'Lately' con un'attività che continua prende il Present Perfect Continuous.",
        classification="action",
    ),
    # --- 11-15: the Continuous is impossible — verbs of state -------------------
    QuestionSpec(
        sentence="He ______ (know) my sister since primary school.",
        options=("knows", "knew", "has known", "has been knowing"),
        correct="has known",
        explanation=(
            "'know' è un verbo di stato: descrive una condizione della mente, non "
            "un'attività, e non ha la forma in -ing. La durata 'since primary school' va "
            "quindi con il Present Perfect Simple. 'has been knowing' è impossibile, come "
            "'is knowing'. 'knows' dichiara la conoscenza di oggi ma perde il punto di "
            "partenza. 'knew' farebbe pensare che non la conosce più."
        ),
        clue="Un verbo di cognizione con un punto di partenza ('since primary school').",
        rule="I verbi di stato non hanno la forma continua: con 'for' e 'since' prendono il "
             "Present Perfect Simple.",
        classification="state",
    ),
    QuestionSpec(
        sentence="That painting ______ (belong) to my grandmother since 1962.",
        options=("belonged", "has belonged", "has been belonging", "belongs"),
        correct="has belonged",
        explanation=(
            "'belong' esprime appartenenza ed è un verbo di stato, quindi la forma continua "
            "è esclusa e la durata 'since 1962' va con il Present Perfect Simple. 'has been "
            "belonging' è scorretto per la stessa ragione per cui non si dice 'is "
            "belonging'. 'belongs' direbbe a chi appartiene oggi, perdendo la data di "
            "partenza. 'belonged' chiuderebbe l'appartenenza nel passato."
        ),
        clue="Un verbo di appartenenza con una data di inizio ('since 1962').",
        rule="Appartenenza e possesso si dicono con il Present Perfect Simple anche con "
             "'since'.",
        classification="state",
    ),
    QuestionSpec(
        sentence="I ______ (believe) her story from the very first minute.",
        options=("have believed", "have been believing", "believe", "believed"),
        correct="have believed",
        explanation=(
            "'believe' è un verbo di stato e non ammette la forma in -ing: l'intervallo "
            "'from the very first minute' vuole quindi il Present Perfect Simple. 'have "
            "been believing' è agrammaticale. 'believe' al presente direbbe che ci credo "
            "adesso, senza il percorso cominciato al primo minuto. 'believed' chiuderebbe la "
            "fiducia nel passato, come se fosse finita."
        ),
        clue="Un verbo di opinione con un intervallo che parte dal primo minuto.",
        rule="Le opinioni (believe, think) restano al Present Perfect Simple anche quando la "
             "durata è espressa.",
        classification="state",
    ),
    QuestionSpec(
        sentence="Nobody ______ (understand) the instructions so far, so the teacher will "
                 "explain them again.",
        options=("has been understanding", "understood", "is understanding", "has understood"),
        correct="has understood",
        explanation=(
            "'understand' è un verbo di stato: la forma in -ing è esclusa, e con 'so far' il "
            "risultato mancante si dice con il Present Perfect Simple. 'has been "
            "understanding' è agrammaticale. 'understood' (past simple) metterebbe la "
            "comprensione in un tempo chiuso, mentre 'so far' guarda fino a questo momento. "
            "'is understanding' descrive una comprensione in divenire che il verbo non "
            "ammette."
        ),
        clue="Un verbo di comprensione più 'so far', che guarda fino a questo momento.",
        rule="Con 'so far' un verbo di stato prende il Present Perfect Simple: la forma "
             "continua non esiste.",
        classification="state",
    ),
    QuestionSpec(
        sentence="He ______ (have) my dictionary for two weeks, and I need it back.",
        options=("had", "is having", "has had", "has been having"),
        correct="has had",
        explanation=(
            "'have' qui significa possedere, non svolgere: è un verbo di stato e non ha la "
            "forma continua, quindi la durata 'for two weeks' va con il Present Perfect "
            "Simple. 'has been having' sarebbe possibile solo con un altro senso di 'have', "
            "per esempio 'have a shower'. 'had' chiuderebbe il prestito nel passato e 'is "
            "having' descrive il possesso nel solo istante presente."
        ),
        clue="'Have' nel senso di possedere, con una durata misurata ('for two weeks').",
        rule="'Have' che significa possedere è un verbo di stato: Present Perfect Simple, mai "
             "la forma continua.",
        classification="state",
    ),
    # --- 16-21: relative pronouns, and the `that` a comma forbids --------------
    QuestionSpec(
        sentence="The electrician ______ fixed our boiler last week has just sent the invoice.",
        options=("where", "who", "which", "whose"),
        correct="who",
        explanation=(
            "Defining: non ci sono virgole e la relativa dice quale elettricista ha mandato "
            "la fattura, quindi serve a identificarlo. Il pronome è 'who' perché "
            "l'antecedente è una persona e il pronome è il soggetto di 'fixed'. 'which' "
            "sbaglia l'antecedente, 'whose' chiederebbe un sostantivo posseduto e 'where' "
            "non può fare da soggetto."
        ),
        clue="Nessuna virgola; l'antecedente è una persona e il verbo 'fixed' non ha ancora il "
             "suo soggetto.",
        rule="Defining clause per le persone soggetto: si usa 'who'; 'that' è ammesso solo "
             "qui, mai tra virgole.",
        classification="defining",
        family="clause",
    ),
    QuestionSpec(
        sentence="The film ______ we watched last night was much better than the reviews said.",
        options=("which", "who", "whose", "where"),
        correct="which",
        explanation=(
            "Defining: nessuna virgola e la relativa identifica il film di cui parla la "
            "frase. Il pronome è 'which' perché l'antecedente è una cosa e il pronome è "
            "l'oggetto di 'watched'. 'who' sbaglia l'antecedente, 'whose' esigerebbe un "
            "sostantivo posseduto e 'where' non può essere l'oggetto di un verbo."
        ),
        clue="Nessuna virgola, antecedente inanimato, e 'watched' cerca ancora il suo oggetto.",
        rule="Defining clause per le cose oggetto: si usa 'which' oppure 'that'.",
        classification="defining",
        family="clause",
    ),
    QuestionSpec(
        sentence="My uncle Giorgio, ______ has lived in Canada since 1990, is coming home "
                 "for Christmas.",
        options=("that", "which", "whose", "who"),
        correct="who",
        explanation=(
            "Non-defining: la relativa è chiusa fra due virgole e aggiunge un dettaglio su "
            "una persona già identificata dal nome. Il pronome è 'who' perché l'antecedente "
            "è una persona e il pronome è il soggetto di 'has lived'. 'that' è sempre "
            "vietato dopo la virgola, in qualunque frase. 'which' sbaglia l'antecedente e "
            "'whose' chiederebbe un sostantivo posseduto."
        ),
        clue="Due virgole e un nome proprio che identifica già la persona; il verbo 'has "
             "lived' aspetta il soggetto.",
        rule="Tra virgole 'that' non si usa mai: per le persone si sceglie 'who'.",
        classification="non-defining",
        family="clause",
    ),
    QuestionSpec(
        sentence="The village ______ my grandparents met has become a tourist attraction.",
        options=("who", "whose", "where", "which"),
        correct="where",
        explanation=(
            "Defining: nessuna virgola e la relativa dice di quale paese si parla. Il "
            "pronome è 'where' perché nel buco della frase manca un complemento di luogo: "
            "'my grandparents met' ha già soggetto e oggetto. 'which' non può fare da "
            "complemento di luogo senza preposizione, 'who' sbaglia l'antecedente e 'whose' "
            "chiederebbe un sostantivo posseduto."
        ),
        clue="Nessuna virgola e 'met' ha già soggetto e oggetto: manca il luogo.",
        rule="Per i luoghi, quando il verbo è già completo, si usa 'where'.",
        classification="defining",
        family="clause",
    ),
    QuestionSpec(
        sentence="The student ______ essay won the prize is only sixteen.",
        options=("where", "whose", "who", "which"),
        correct="whose",
        explanation=(
            "Defining: nessuna virgola e la relativa identifica lo studente. 'essay' è un "
            "sostantivo senza articolo che dipende dal pronome, quindi il tema appartiene "
            "allo studente e serve 'whose'. 'who' non può reggere un sostantivo, 'which' "
            "sbaglia l'antecedente e 'where' non esprime possesso."
        ),
        clue="Nessuna virgola e un sostantivo senza articolo ('essay') che appartiene a "
             "qualcuno.",
        rule="'Whose' esprime possesso e regge un sostantivo, per le persone come per le cose.",
        classification="defining",
        family="clause",
    ),
    QuestionSpec(
        sentence="This laptop, ______ I bought only in March, already needs a new battery.",
        options=("which", "that", "who", "whose"),
        correct="which",
        explanation=(
            "Non-defining: le virgole aggiungono un'informazione su un portatile già "
            "identificato da 'this'. Il pronome è 'which' perché l'antecedente è una cosa e "
            "il pronome è l'oggetto di 'bought'. 'that' è vietato dopo la virgola, 'who' "
            "sbaglia l'antecedente e 'whose' chiederebbe un sostantivo posseduto."
        ),
        clue="Due virgole; l'antecedente è una cosa e 'bought' cerca il suo oggetto.",
        rule="Non-defining clause: si usa 'which' e mai 'that' fra le virgole.",
        classification="non-defining",
        family="clause",
    ),
)


def aspect_of(option: str) -> str:
    """``continuous``, ``simple`` or ``other`` for an option, case taken out of the way.

    The medium topic's detector matches lowercase auxiliaries, and its own pool never starts
    an option with a capital. This pool does — a question opens with ``Have you ever eaten``
    — so the case is normalised here rather than loosening the sibling's pattern.
    """
    return aspect(option.lower())


def verb_of(sentence: str) -> str | None:
    """The verb named in the hint — ``(already / send)`` gives ``send``.

    Same rule as the medium topic: the verb is the last word of the hint, so a hint that
    also carries a subject or an adverb can be read without guessing its shape.
    """
    match = VERB_HINT.search(sentence)
    if match is None:
        return None
    words = WORD.findall(match.group(1))
    return words[-1].lower() if words else None


def expected_classification(sentence: str, options: tuple[str, ...]) -> str | None:
    """What the picker must land on, derived from the sentence — never from the data.

    A card whose options are all pronouns is a clause card: the commas decide, exactly as
    on the sibling page. Any other card asks about the verb: a verb of state cannot have
    a continuous form, so the class follows the hint.
    """
    if options and all(option in PRONOUNS for option in options):
        return sentence_classification(sentence)
    verb = verb_of(sentence)
    if verb is None:
        return None
    return "state" if verb in STATIVES else "action"


class PresentPerfectSimpleContinuousTopic:
    id = "english.grammar.present_perfect_simple_continuous"
    family = "english"
    #: One level only: the aspect distinction is medium work (the easy level of the topic
    #: is ``english.grammar.present_perfect``). Declaring 'easy' here would serve a medium
    #: batch under a false label; a level this pool does not have must answer 400.
    difficulties = ("medium",)
    label_key = "topic.english_present_perfect_simple_continuous"
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

        # Same convention as the other grammar topics: the order is shuffled so the correct
        # option is not always A, but deterministically, so a reload shows the same card.
        opt_rng = random.Random(f"{chosen.sentence}:{index}")
        shuffled = list(chosen.options)
        opt_rng.shuffle(shuffled)

        texts = TEXTS[chosen.family]
        # Two steps, not three: the sibling classification page closes with the correct
        # form, and a card whose lock says "choose the kind first" cannot print the answer
        # in a drawer three centimetres below it.
        steps = (
            Step("step.grammar_analysis", f"\\text{{{chosen.clue}}}"),
            Step("step.rule_application", f"\\text{{{chosen.rule}}}"),
        )
        answer = Answer(
            latex=f"\\textbf{{{chosen.correct}}}, \\text{{{chosen.classification}}}",
            kind="multiple_choice",
            payload={
                "options": shuffled,
                "correct": [chosen.correct],
                "classification": [chosen.classification],
                # The picker is data, not a hardcoded pair in the client: which question is
                # asked, which two values answer it and the two lines that explain the lock
                # and the mistake all travel here. The wire payload is a map of string
                # lists (``WireAnswer.payload``), so the values and their label keys travel
                # as two parallel lists of the same length, in the order of the buttons.
                "classification_values": [value for value, _ in CLASSIFICATIONS[chosen.family]],
                "classification_labels": [key for _, key in CLASSIFICATIONS[chosen.family]],
                "classification_prompt_key": [texts["prompt"]],
                "classification_locked_key": [texts["locked"]],
                "classification_wrong_key": [texts["wrong"]],
                "option_wrong_key": [texts["option_wrong"]],
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

        if BLANK.search(item.statement_key) is None:
            return VerificationResult(False, "missing_blank")
        # The label the operator removed: the kind of the sentence is asked, never printed.
        if LABEL_IN_SENTENCE.search(item.statement_key):
            return VerificationResult(False, "statement_carries_the_label")

        clause_card = all(option in PRONOUNS for option in options)
        family = "clause" if clause_card else "verb"

        offered = payload.get("classification_values") or []
        if offered != [value for value, _ in CLASSIFICATIONS[family]]:
            return VerificationResult(False, "picker_does_not_match_the_card")
        if len(payload.get("classification_labels") or []) != len(offered):
            return VerificationResult(False, "picker_label_count")

        claimed = payload.get("classification")
        if not claimed or claimed[0] not in offered:
            return VerificationResult(False, "missing_classification")

        expected = expected_classification(item.statement_key, tuple(options))
        if expected is None:
            return VerificationResult(False, "unreadable_card")
        if claimed[0] != expected:
            return VerificationResult(False, "classification_mismatch")

        if clause_card:
            # 'that' may not introduce a clause between commas, and offering it next to
            # 'who' or 'which' in a defining clause would put two right answers on the card.
            if correct[0] == "that" and expected == "non-defining":
                return VerificationResult(False, "that_in_non_defining")
            if "that" in options and expected == "defining":
                return VerificationResult(False, "that_offered_in_defining")
            return VerificationResult(True, "ok")

        # The grammar truth the pool is built on: a verb of state has no -ing form, so a
        # continuous answer on such a card is a broken question, not a wrong student.
        if expected == "state" and aspect_of(correct[0]) == "continuous":
            return VerificationResult(False, "stative_in_continuous")
        # A card of this group is answered with a perfect form: an option that is neither
        # Simple nor Continuous would teach a tense the page does not claim to teach.
        if aspect_of(correct[0]) not in ("simple", "continuous"):
            return VerificationResult(False, "correct_answer_is_not_a_perfect_form")
        return VerificationResult(True, "ok")


TOPIC = PresentPerfectSimpleContinuousTopic()
