"""Present Perfect Simple vs Continuous — the medium level: the cases that deceive.

``present_perfect`` publishes the *easy* level of the topic and keeps its own harder
pool inside the same file. This module is the second exercise the site was missing: the
same grammar, one level up, with its own question pool so that a teacher can hand out a
batch that is *not* the easy one.

Where the easy level separates "azione in corso" from "azione conclusa" with one clean
signal per sentence, the medium level puts the two forms side by side on the same verb
and makes the student read *why* the sentence chooses one:

* **duration vs result on the same verb** — ``I've been reading it`` (unfinished) against
  ``I've read it`` (you can borrow it); ``I've been writing`` (since nine) against
  ``I've only finished two pages``;
* **stative verbs** — know, own, believe, and ``have`` in the sense of possession, which
  never take ``-ing``, so ``for`` and ``since`` go with the Simple;
* **for and since** — a starting point (``since the war``, ``since she graduated``), a
  measured duration (``for thirty years``), and the trap where ``since`` is followed by a
  *count* (``three different schools``), which pulls the answer back to the Simple;
* **been / gone**, ``think about`` vs ``think that``, ``this is the third time``,
  repeated attempts with and without a number, a temporary arrangement that continues.

Every question carries the sibling's five pieces of information: the sentence, four
options, the correct one, an explanation that says *why* that form and why each tempting
twin fails, the clue that names the diagnostic signal without giving the answer, and the
general rule. All of it is in Italian except the English sentence.

``verify`` enforces two truths that the data must never break: a stative verb is never
given as a continuous answer, and every statement really contains a blank to fill.

The order of the options *in the data* is arranged so that the deterministic shuffle in
``generate`` spreads the correct answer evenly over the four positions: with the answer
first in every tuple, twelve questions out of twenty would print it as option A — a
student learns that, not the grammar. Reorder the tuples freely; keep the spread.
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


#: The blank the student fills; the exercise text uses six underscores.
BLANK = re.compile(r"_{3,}")
#: What the exercise prints next to the blank: the lexical verb, sometimes with a subject
#: or an adverb — ``(know)``, ``(you / ever / visit)``, ``(not sleep)``. The verb itself is
#: the last word, so the hint can be read without guessing how the prompt was phrased.
VERB_HINT = re.compile(r"\(([^)]*)\)")
WORD = re.compile(r"[A-Za-z']+")
#: A continuous form: the auxiliary ``been`` plus the -ing participle.
CONTINUOUS = re.compile(r"\bbeen\s+\w+ing\b")
#: A simple form: ``have``/``has`` and a participle, with no ``been`` in front of it.
SIMPLE = re.compile(r"\b(?:have|has|haven't|hasn't)\b")
#: Verbs of state: they describe a condition, not an activity, so they take no -ing form.
#: ``have`` is here in its possessive sense, which is the only one the exercise prompts.
STATIVES = frozenset({
    "know", "believe", "own", "belong", "possess", "seem", "understand", "want", "need",
    "prefer", "mean", "contain", "remember", "like", "hate", "love", "have",
})


MEDIUM_QUESTIONS: tuple[QuestionSpec, ...] = (
    QuestionSpec(
        sentence="I ______ (read) that novel at the moment — I'm on the last chapter.",
        options=("have read", "read", "have been reading", "am reading"),
        correct="have been reading",
        explanation=(
            "Il romanzo non è finito: 'I'm on the last chapter' dice che la lettura è ancora "
            "aperta, quindi si guarda all'attività nel suo svolgersi e serve il Present Perfect "
            "Continuous. 'have read' presenterebbe la lettura come conclusa, e la frase appena "
            "dopo lo smentisce. 'read' (past simple) spezzerebbe il legame con il presente e "
            "suonerebbe come un fatto chiuso nel passato. 'am reading' descrive solo l'istante "
            "presente, senza il tratto di tempo che comincia prima e arriva fino a ora."
        ),
        clue="Il libro non è finito ('I'm on the last chapter'): la lettura è un'attività ancora aperta.",
        rule="Il Present Perfect Continuous presenta un'attività iniziata nel passato e non ancora conclusa, con l'accento sul suo svolgersi.",
    ),
    QuestionSpec(
        sentence="I ______ (read) that novel — you can borrow it now.",
        options=("have been reading", "read", "have read", "am reading"),
        correct="have read",
        explanation=(
            "'you can borrow it now' è la conseguenza di un'azione conclusa: il libro è finito e "
            "passa di mano. Un risultato compiuto, di cui il presente raccoglie gli effetti, vuole "
            "il Present Perfect Simple. 'have been reading' metterebbe al centro l'attività ancora "
            "in corso, e allora il libro non sarebbe disponibile. 'read' (past simple) chiuderebbe "
            "il fatto nel passato, mentre qui conta la conseguenza di adesso. 'am reading' direbbe "
            "che la lettura è in corso proprio ora, non che è terminata."
        ),
        clue="Il risultato è compiuto e disponibile ('you can borrow it now'): la lettura è conclusa.",
        rule="Il Present Perfect Simple presenta un risultato compiuto, di cui il presente raccoglie le conseguenze.",
    ),
    QuestionSpec(
        sentence="She ______ (know) the answer since the first lesson.",
        options=("has been knowing", "knows", "has known", "knew"),
        correct="has known",
        explanation=(
            "'know' è un verbo di stato (cognizione): descrive una condizione, non un'attività, e "
            "non ha la forma in -ing. Con 'since the first lesson' serve quindi il Present Perfect "
            "Simple. 'has been knowing' è grammaticalmente impossibile, perché i verbi di stato "
            "non ammettono il continuous. 'knows' direbbe che lo sa in generale, ma perderebbe il "
            "punto di partenza 'since' e la durata fino a ora. 'knew' (past simple) lascerebbe "
            "intendere che non lo sa più."
        ),
        clue="Verbo di cognizione ('know') più il punto di partenza 'since the first lesson'.",
        rule="I verbi di stato (know, believe, understand) non hanno la forma continua: con 'since' e 'for' prendono il Present Perfect Simple.",
    ),
    QuestionSpec(
        sentence="My parents ______ (own) that house for thirty years.",
        options=("have been owning", "own", "have owned", "owned"),
        correct="have owned",
        explanation=(
            "'own' esprime possesso ed è un verbo di stato: la forma continua è esclusa, quindi la "
            "durata 'for thirty years' va con il Present Perfect Simple. 'have been owning' è "
            "scorretto per la stessa ragione per cui non si dice 'am owning'. 'own' al presente "
            "semplice dichiara il possesso di oggi ma cancella i trent'anni già trascorsi, che sono "
            "l'informazione della frase. 'owned' chiuderebbe il possesso nel passato: la casa non "
            "sarebbe più loro."
        ),
        clue="Verbo di possesso con una durata misurata ('for thirty years').",
        rule="Possesso e appartenenza (own, belong, possess) si dicono con il Present Perfect Simple anche quando la durata è lunga.",
    ),
    QuestionSpec(
        sentence="How long ______ (you / wait) for the bus?",
        options=("have you been waiting", "have you waited", "do you wait", "are you waiting"),
        correct="have you been waiting",
        explanation=(
            "'How long' chiede la durata di un'attività che si sta ancora svolgendo: l'attesa è in "
            "corso adesso e viene da prima, quindi Present Perfect Continuous. 'have you waited' "
            "sposterebbe la domanda su un risultato o un computo concluso, che 'how long' con "
            "un'attesa aperta non chiede. 'do you wait' è un'abitudine e 'are you waiting' solo "
            "l'istante presente: nessuno dei due collega il passato al momento in cui si parla."
        ),
        clue="Domanda sulla durata di un'attesa che sta ancora avvenendo.",
        rule="'How long' con un'attività ancora in corso vuole il Present Perfect Continuous.",
    ),
    QuestionSpec(
        sentence="How many letters ______ (you / write) this morning?",
        options=("have you been writing", "did you write", "have you written", "do you write"),
        correct="have you written",
        explanation=(
            "'How many' chiede un numero di cose completate: le lettere finite questa mattina. Un "
            "conteggio concluso richiede il Present Perfect Simple. 'have you been writing' "
            "descriverebbe l'attività in sé, non quante lettere sono state portate a termine. "
            "'did you write' (past simple) staccherebbe le lettere dal 'this morning', che non è "
            "ancora finito. 'do you write' è un'abitudine e non dice quante ne sono state scritte."
        ),
        clue="Domanda con 'how many' su un insieme di cose portate a termine questa mattina.",
        rule="Con 'how many' e 'how much' si conta ciò che è completato: Present Perfect Simple.",
    ),
    QuestionSpec(
        sentence="I ______ (think) about your proposal all week, and I still haven't decided.",
        options=("have thought", "have been thinking", "think", "was thinking"),
        correct="have been thinking",
        explanation=(
            "Qui 'think about' significa valutare, rimuginare: è un'attività mentale, non uno "
            "stato, e ammette quindi la forma continua. 'all week' insieme a 'I still haven't "
            "decided' dice che il processo è aperto, e il Present Perfect Continuous mette al "
            "centro proprio il suo svolgersi. 'have thought' suonerebbe come un'opinione già "
            "formata, mentre la frase dice il contrario: la decisione non c'è ancora. 'think' è "
            "l'opinione del momento e 'was thinking' chiude il ragionamento nel passato."
        ),
        clue="'think about' nel senso di valutare, con 'all week' e una decisione ancora da prendere.",
        rule="'Think about' nel senso di valutare è un'attività e ammette il continuous; 'think that' nel senso di credere è uno stato e non lo ammette.",
    ),
    QuestionSpec(
        sentence="Ever since I was a child, I ______ (always / believe) that honesty is the best policy.",
        options=("have always been believing", "have always believed", "always believe", "am always believing"),
        correct="have always believed",
        explanation=(
            "'believe' è un verbo di stato (opinione) e non si usa al continuous: 'have always "
            "been believing' è quindi impossibile. Con 'ever since I was a child' il Present "
            "Perfect Simple dice che l'opinione vale da allora fino a ora, che è esattamente ciò "
            "che la frase vuole. 'always believe' al presente semplice enuncerebbe l'opinione di "
            "oggi senza il tratto che parte dall'infanzia. 'am always believing' sbaglia due volte: "
            "il tempo e l'aspetto continuo su un verbo di stato."
        ),
        clue="Verbo di opinione più 'ever since I was a child': l'opinione vale da allora a oggi.",
        rule="Con 'ever since' un'opinione che dura da sempre si dice con il Present Perfect Simple, mai con il continuous.",
    ),
    QuestionSpec(
        sentence="He ______ (be) to Japan three times, but he doesn't speak a word of Japanese.",
        options=("has gone", "is", "has been", "was"),
        correct="has been",
        explanation=(
            "'have been to' un luogo significa esserci stati e essere tornati: è l'espressione "
            "dell'esperienza, e il numero di volte ('three times') la rende un conteggio concluso, "
            "da Present Perfect Simple. 'has gone' direbbe che è partito e non è ancora tornato, il "
            "che contraddice 'three times' e il fatto che la frase lo descrive qui. 'is' e 'was' "
            "perdono il legame tra le esperienze passate e il presente, che è tutto il punto."
        ),
        clue="Conteggio di esperienze ('three times') su una persona che la frase descrive qui adesso.",
        rule="'Have been to' un luogo significa esserci stati e essere tornati: è l'espressione dell'esperienza e va con il Present Perfect Simple.",
    ),
    QuestionSpec(
        sentence="Marta isn't at her desk — she ______ (go) to the dentist.",
        options=("has been", "has gone", "is going", "went"),
        correct="has gone",
        explanation=(
            "Il Present Perfect Simple con 'gone to' dice che è andata e non è ancora tornata: è "
            "esattamente la ragione per cui adesso non è alla scrivania. 'has been' direbbe che "
            "c'è stata e che è già "
            "rientrata, e allora sarebbe di nuovo al suo posto. 'is going' descrive il movimento in "
            "corso, non l'assenza che dura da prima; 'went' chiude la partita nel passato e non "
            "spiega il presente."
        ),
        clue="Assenza attuale di Marta e partenza non ancora rientrata.",
        rule="'Have gone to' un luogo significa esserci andati e non essere ancora tornati: spiega un'assenza presente.",
    ),
    QuestionSpec(
        sentence="This is the third time I ______ (see) that advert today.",
        options=("have been seeing", "saw", "have seen", "am seeing"),
        correct="have seen",
        explanation=(
            "La formula 'this is the first, second, third time' vuole il Present Perfect Simple: "
            "conta le volte in cui il fatto si è già compiuto. 'have been seeing' metterebbe in "
            "scena un'attività ripetuta e ancora in corso, mentre qui si contano episodi conclusi. "
            "'saw' (past simple) romperebbe il collegamento con 'this is' e con 'today', che non è "
            "finito. 'am seeing' descrive l'istante in cui guardo, non quante volte è successo."
        ),
        clue="La formula 'this is the third time' conta episodi già compiuti.",
        rule="'This is the first, second, third time' si costruisce con il Present Perfect Simple.",
    ),
    QuestionSpec(
        sentence="It ______ (rain) all afternoon and it is still pouring.",
        options=("has rained", "rains", "rained", "has been raining"),
        correct="has been raining",
        explanation=(
            "'and it is still pouring' dice che la pioggia continua: il Present Perfect Continuous "
            "è la forma che copre un'attività iniziata nel passato e ancora in corso. 'has rained' "
            "presenterebbe la pioggia come un episodio concluso, contraddetto da 'still pouring'. "
            "'rains' è una constatazione generale sul clima e 'rained' chiude tutto nel passato: "
            "nessuna delle due arriva fino a ora."
        ),
        clue="'all afternoon' più 'it is still pouring': la pioggia non è finita.",
        rule="'Still' insieme a un'espressione di durata ('all afternoon') segnala un'attività non finita: Present Perfect Continuous.",
    ),
    QuestionSpec(
        sentence="She ______ (teach) in three different schools since she graduated.",
        options=("has taught", "has been teaching", "taught", "is teaching"),
        correct="has taught",
        explanation=(
            "'three different schools' conta episodi già conclusi: si è insegnato in tre scuole, e "
            "un numero di cose compiute vuole il Present Perfect Simple. 'has been teaching' "
            "metterebbe al centro un'unica attività continua e ininterrotta, che tre sedi diverse "
            "non raccontano. 'taught' (past simple) spegnerebbe il 'since she graduated', che è il "
            "punto di partenza della carriera fino a oggi. 'is teaching' direbbe soltanto che cosa "
            "fa in questo momento."
        ),
        clue="'since she graduated' con un numero di sedi già attraversate ('three different schools').",
        rule="Con 'since' ma con un numero di episodi conclusi ('three different schools') si usa il Present Perfect Simple: si conta ciò che è finito, non l'attività.",
    ),
    QuestionSpec(
        sentence="I ______ (work) in that shop for six months, while my brother is abroad.",
        options=("have worked", "work", "have been working", "worked"),
        correct="have been working",
        explanation=(
            "La situazione è temporanea e aperta: dura sei mesi e finirà quando il fratello torna. "
            "Le situazioni temporanee prolungate che arrivano fino a ora vogliono il Present "
            "Perfect Continuous. 'have worked' presenterebbe i sei mesi come un'esperienza "
            "conclusa e computabile, ma il lavoro continua. 'work' è il presente abituale e "
            "'worked' chiude il periodo nel passato: nessuno dei due dice 'da sei mesi fino a ora'."
        ),
        clue="Accordo temporaneo ('while my brother is abroad') che dura da sei mesi.",
        rule="Le situazioni temporanee prolungate vogliono il Present Perfect Continuous; quelle stabili e permanenti preferiscono il Simple.",
    ),
    QuestionSpec(
        sentence="My grandfather ______ (have) that watch since the war.",
        options=("has been having", "has", "has had", "had"),
        correct="has had",
        explanation=(
            "Qui 'have' significa possedere ed è un verbo di stato: la forma continua è esclusa. "
            "Resta il Present Perfect Simple, che con 'since the war' copre il possesso da allora a "
            "oggi. 'has been having' è scorretto, perché il possesso non si svolge nel tempo come "
            "un'attività. 'has' al presente semplice direbbe che ce l'ha oggi ma non da allora; "
            "'had' lascerebbe intendere che non ce l'ha più."
        ),
        clue="Possesso di un oggetto con il punto di partenza 'since the war'.",
        rule="'Have' nel senso di possedere è un verbo di stato: Present Perfect Simple con 'since' e 'for'.",
    ),
    QuestionSpec(
        sentence="I ______ (call) the office all morning, but nobody picks up.",
        options=("have been calling", "have called", "call", "called"),
        correct="have been calling",
        explanation=(
            "Le telefonate si ripetono senza sosta e l'attesa è ancora aperta ('nobody picks up'): "
            "è il caso del Present Perfect Continuous, che descrive l'attività ripetuta e "
            "prolungata fino a ora. 'have called' conterebbe le chiamate concluse, e allora "
            "servirebbe un numero, come 'four times'. 'call' è l'abitudine e 'called' un fatto "
            "chiuso nel passato, che non spiega il telefono che squilla ancora."
        ),
        clue="Tentativi ripetuti e ancora senza risposta ('nobody picks up').",
        rule="Tentativi ripetuti e ancora in corso si dicono con il Present Perfect Continuous; con un numero esatto ('four times') si passa al Simple.",
    ),
    QuestionSpec(
        sentence="The students ______ (prepare) for the exam since September, and they sit it tomorrow.",
        options=("have been preparing", "have prepared", "prepare", "prepared"),
        correct="have been preparing",
        explanation=(
            "La preparazione è cominciata a settembre e non è finita: l'esame è domani. Un lavoro "
            "in corso, misurato dalla durata ('since September'), vuole il Present Perfect "
            "Continuous. 'have prepared' direbbe che è già tutto pronto, e 'they sit it tomorrow' "
            "lo smentisce. 'prepare' è il presente abituale e 'prepared' chiude il lavoro nel "
            "passato, lasciando il domani senza preparazione."
        ),
        clue="'since September' e un esame che è ancora da sostenere domani.",
        rule="Un lavoro iniziato e non concluso, misurato dalla durata, vuole il Present Perfect Continuous.",
    ),
    QuestionSpec(
        sentence="I ______ (write) this report since nine o'clock, but I ______ (only / finish) two pages.",
        options=(
            "have written / have only been finishing",
            "have been writing / have only finished",
            "wrote / only finished",
            "am writing / only finish",
        ),
        correct="have been writing / have only finished",
        explanation=(
            "La frase chiede due cose diverse: la durata del lavoro ('since nine o'clock') e la "
            "quantità già completata ('two pages'). La durata di un'attività ancora aperta vuole il "
            "Present Perfect Continuous, il conteggio di ciò che è finito vuole il Present Perfect "
            "Simple. 'have written / have only been finishing' rovescia i due: presenterebbe la "
            "scrittura come conclusa e il completamento come attività in corso. 'wrote / only "
            "finished' chiude tutto nel passato, mentre 'am writing / only finish' perde il 'since' "
            "e il conteggio."
        ),
        clue="Due informazioni nella stessa frase: la durata del lavoro e le pagine già terminate.",
        rule="Nella stessa frase la durata aperta prende il Continuous e il conteggio delle parti completate prende il Simple.",
    ),
    QuestionSpec(
        sentence="The price of coffee ______ (go) up twice this year.",
        options=("has gone", "has been going", "went", "goes"),
        correct="has gone",
        explanation=(
            "'Twice this year' conta due aumenti già avvenuti in un anno non ancora finito: un "
            "numero di episodi conclusi richiede il Present Perfect Simple. 'has been going' "
            "descriverebbe un aumento continuo e in atto, non due salti distinti. 'went' (past "
            "simple) spezzerebbe il legame con 'this year', mentre 'goes' direbbe che sale sempre, "
            "senza contare le due volte."
        ),
        clue="Un numero di episodi ('twice') dentro un anno non ancora concluso.",
        rule="Un numero di episodi conclusi dentro un periodo non finito ('twice this year') vuole il Present Perfect Simple.",
    ),
    QuestionSpec(
        sentence="My eyes are red because I ______ (stare) at the screen all morning.",
        options=("have stared", "stare", "have been staring", "stared"),
        correct="have been staring",
        explanation=(
            "Il nesso è tra un'attività prolungata ('all morning') e una conseguenza visibile "
            "adesso (gli occhi rossi): è il terreno del Present Perfect Continuous, che spiega lo "
            "stato presente con il processo che lo ha prodotto. 'have stared' metterebbe l'accento "
            "sull'azione conclusa e non renderebbe conto degli occhi rossi di questo momento. "
            "'stare' è il presente puntuale e 'stared' il passato chiuso: nessuno dei due spiega "
            "perché sono rosso adesso."
        ),
        clue="Effetto visibile adesso (gli occhi rossi) prodotto da un'attività durata tutta la mattina.",
        rule="Il Present Perfect Continuous spiega uno stato presente come conseguenza di un'attività prolungata.",
    ),
)


def verb_hint(sentence: str) -> str | None:
    """The lexical verb the sentence prompts for, read off the parenthesised hint."""
    match = VERB_HINT.search(sentence)
    if match is None:
        return None
    words = WORD.findall(match.group(1))
    return words[-1].lower() if words else None


def aspect(option: str) -> str:
    """``continuous``, ``simple`` or ``other`` — the form an option is written in."""
    if CONTINUOUS.search(option):
        return "continuous"
    if SIMPLE.search(option):
        return "simple"
    return "other"


def asks_for_a_continuous_form(sentence: str) -> bool:
    """True when the sentence prompts for a verb of state, which has no continuous form."""
    hint = verb_hint(sentence)
    return hint is not None and hint in STATIVES


class PresentPerfectMediumTopic:
    id = "english.grammar.present_perfect_medium"
    family = "english"
    #: One level only: the easy level is ``english.grammar.present_perfect``. Declaring
    #: 'easy' here would let a caller ask for a level this pool does not have and receive
    #: a medium question under a false label — a 400 is the honest answer.
    difficulties = ("medium",)
    label_key = "topic.english_present_perfect_medium"
    scenarios: tuple[str, ...] = ()

    def generate(
        self,
        rng: random.Random,
        difficulty: str,
        seed: int,
        index: int,
        options: dict | None = None,
    ) -> Item:
        chosen_spec = MEDIUM_QUESTIONS[index % len(MEDIUM_QUESTIONS)]

        # Same convention as the other grammar topics: the order is shuffled so the correct
        # option is not always A, but deterministically, so a reload shows the same card.
        opt_rng = random.Random(f"{chosen_spec.sentence}:{index}")
        shuffled_options = list(chosen_spec.options)
        opt_rng.shuffle(shuffled_options)

        steps = (
            Step("step.grammar_analysis", f"\\text{{{chosen_spec.clue}}}"),
            Step("step.rule_application", f"\\text{{{chosen_spec.rule}}}"),
            Step("step.correct_form", f"\\textbf{{{chosen_spec.correct}}}"),
        )
        answer = Answer(
            latex=f"\\textbf{{{chosen_spec.correct}}}",
            kind="multiple_choice",
            payload={
                "options": shuffled_options,
                "correct": [chosen_spec.correct],
                "explanation": [chosen_spec.explanation],
            },
        )
        return Item(
            topic=self.id,
            difficulty=difficulty,
            seed=seed,
            index=index,
            params={},
            statement_key=chosen_spec.sentence,
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

        # The grammar is part of the contract: a question with no blank cannot be answered,
        # and a verb of state handed a continuous answer teaches something false — that is a
        # broken question, not a wrong student.
        if BLANK.search(item.statement_key) is None:
            return VerificationResult(False, "missing_blank")
        if asks_for_a_continuous_form(item.statement_key) and aspect(correct[0]) == "continuous":
            return VerificationResult(False, "stative_in_continuous")

        return VerificationResult(True, "ok")


TOPIC = PresentPerfectMediumTopic()
