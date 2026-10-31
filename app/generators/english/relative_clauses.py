"""Relative Clauses (Defining & Non-defining) exercise generator.

Provides multiple-choice fill-in-the-blank questions focusing on:
- Defining vs Non-defining relative clauses (commas, essential vs extra information)
- Pronoun choice: who (people), which (things), that (defining only, never after a comma)
- Possession with 'whose' (for both people and things)
- Relative adverbs: where (places of action), when (time), why (reasons)
- Formal register and prepositions: 'to whom', 'with whom', 'in which'
- Sentential relative clauses: 'which' commenting on a whole preceding clause
"""

from __future__ import annotations

import random
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


EASY_QUESTIONS: tuple[QuestionSpec, ...] = (
    QuestionSpec(
        sentence="The girl ______ won the science competition is in my class.",
        options=("who", "which", "whose", "where"),
        correct="who",
        explanation="'The girl' è una persona in una defining clause (senza virgole); si usa 'who'.",
        clue="L'antecedente è una persona ('The girl') in una defining relative clause.",
        rule="Si usa 'who' per le persone nelle relative restrittive (defining clauses).",
    ),
    QuestionSpec(
        sentence="This is the book ______ inspired me to become an engineer.",
        options=("which", "who", "whom", "whose"),
        correct="which",
        explanation="'The book' è un oggetto; si usa 'which' (o 'that') in una proposizione relativa restrittiva.",
        clue="L'antecedente è una cosa inanimata ('the book').",
        rule="Si usa 'which' o 'that' per cose e oggetti nelle relative restrittive.",
    ),
    QuestionSpec(
        sentence="My uncle, ______ is a pilot, flies planes all over the world.",
        options=("who", "that", "which", "whom"),
        correct="who",
        explanation="Proposizione non-defining (tra virgole) riferita a una persona. 'That' non si usa MAI tra virgole.",
        clue="Proposizione non-defining separata da virgole riferita a una persona.",
        rule="Nelle non-defining relative clauses si usa 'who' per le persone; l'uso di 'that' è vietato.",
    ),
    QuestionSpec(
        sentence="The restaurant ______ we had dinner last night was excellent.",
        options=("where", "which", "that", "whose"),
        correct="where",
        explanation="'Where' si riferisce al luogo in cui si svolge l'azione ('nel ristorante').",
        clue="L'antecedente è un luogo in cui avviene un'azione ('we had dinner').",
        rule="Si usa 'where' come avverbio relativo per indicare il luogo in cui si verifica un'attività.",
    ),
    QuestionSpec(
        sentence="A mechanic is someone ______ repairs broken cars and engines.",
        options=("who", "which", "whose", "where"),
        correct="who",
        explanation="'Someone' si riferisce a una persona che funge da soggetto; si usa 'who'.",
        clue="Il pronome si riferisce a una persona ('someone') come soggetto della subordinata.",
        rule="Si usa 'who' quando il pronome relativo sostituisce una persona come soggetto della frase relativa.",
    ),
    QuestionSpec(
        sentence="The computer ______ I bought last week has already crashed twice.",
        options=("which", "who", "whose", "where"),
        correct="which",
        explanation="'The computer' è un dispositivo inanimato in una defining clause; si usa 'which' (oppure 'that').",
        clue="L'antecedente è un oggetto ('the computer').",
        rule="Si usa 'which' (o 'that') per oggetti inanimati nelle frasi relative defining.",
    ),
    QuestionSpec(
        sentence="My grandmother, ______ is 85, walks three miles every morning.",
        options=("who", "that", "which", "whom"),
        correct="who",
        explanation="Proposizione non-defining (tra virgole) su una persona specifica; 'that' non è consentito.",
        clue="Proposizione non-defining racchiusa da virgole su una persona specifica.",
        rule="'That' non si usa mai nelle proposizioni non-defining; per le persone si usa sempre 'who'.",
    ),
    QuestionSpec(
        sentence="A widow is a woman ______ husband has died.",
        options=("whose", "who", "which", "whom"),
        correct="whose",
        explanation="'Whose' esprime possesso o legame di parentela ('il marito di lei').",
        clue="Relazione di possesso/parentela tra 'woman' e 'husband'.",
        rule="Si usa 'whose' come pronome possessivo sia nelle defining sia nelle non-defining clauses.",
    ),
    QuestionSpec(
        sentence="The town ______ I grew up has changed completely.",
        options=("where", "which", "that", "whose"),
        correct="where",
        explanation="'Where' si riferisce al luogo geografico in cui si è svolta l'azione ('nella città').",
        clue="Luogo in cui si è svolta una vicenda personale ('I grew up').",
        rule="Si usa l'avverbio relativo 'where' con significato di 'in cui' / 'nel quale' per i luoghi.",
    ),
    QuestionSpec(
        sentence="The students ______ failed the test must take it again next Friday.",
        options=("who", "which", "whose", "where"),
        correct="who",
        explanation="Defining clause che individua le specifiche persone che hanno fallito il test; si usa 'who'.",
        clue="Proposizione restrittiva che identifica un gruppo di persone ('The students').",
        rule="'Who' identifica e restringe il gruppo di persone di cui si parla.",
    ),
    QuestionSpec(
        sentence="Paris, ______ is known as the City of Light, attracts millions of visitors.",
        options=("which", "that", "where", "what"),
        correct="which",
        explanation="Non-defining clause (tra virgole) in cui la città è il soggetto del verbo 'is'; 'that' è vietato.",
        clue="Frase non-defining con virgole in cui la città è il soggetto grammaticale del verbo.",
        rule="Nelle non-defining clauses riferite a cose o città con ruolo di soggetto si usa 'which', mai 'that'.",
    ),
    QuestionSpec(
        sentence="The boy ______ dog ran away was crying in the park.",
        options=("whose", "who", "which", "whom"),
        correct="whose",
        explanation="'Whose' indica il legame di possesso ('il cane del ragazzo').",
        clue="Legame possessivo tra 'boy' e 'dog'.",
        rule="Si usa 'whose' come pronome relativo possessivo per sostituire 'his', 'her' o 'their'.",
    ),
    QuestionSpec(
        sentence="The phone ______ was on the kitchen table started ringing.",
        options=("which", "who", "whom", "whose"),
        correct="which",
        explanation="'The phone' è un oggetto inanimato; si usa 'which' (oppure 'that') come soggetto della relativa.",
        clue="Pronome soggetto per un oggetto inanimato ('The phone').",
        rule="Si usa 'which' o 'that' per gli oggetti quando fungono da soggetto della proposizione relativa.",
    ),
    QuestionSpec(
        sentence="Dr. Adams, ______ examined me at the clinic, was very reassuring.",
        options=("who", "that", "which", "whose"),
        correct="who",
        explanation="Non-defining clause su una persona indicata con nome e cognome; 'that' non è ammesso dopo una virgola.",
        clue="Proposizione non-defining riferita a un individuo specifico ('Dr. Adams').",
        rule="Non usare mai 'that' nelle frasi non-defining tra virgole; per le persone si usa sempre 'who'.",
    ),
    QuestionSpec(
        sentence="I will never forget the day ______ we graduated from university.",
        options=("when", "where", "which", "whose"),
        correct="when",
        explanation="'When' si riferisce a un sostantivo che indica tempo ('the day').",
        clue="L'antecedente è un'espressione temporale ('the day').",
        rule="Si usa l'avverbio relativo 'when' per riferirsi a giorni, date, orari ed epoche.",
    ),
    QuestionSpec(
        sentence="The umbrella ______ you lent me kept me completely dry.",
        options=("that", "who", "whose", "where"),
        correct="that",
        explanation="Defining clause che specifica un oggetto; 'that' (o 'which') è la forma corretta.",
        clue="Defining relative clause che specifica un particolare oggetto.",
        rule="'That' è comunemente usato nelle frasi relative restrittive per riferirsi a cose e oggetti.",
    ),
    QuestionSpec(
        sentence="The hotel, ______ had a rooftop swimming pool, was right by the sea.",
        options=("which", "that", "where", "what"),
        correct="which",
        explanation="Non-defining clause (tra virgole) che descrive un edificio con funzione di soggetto; 'that' è vietato.",
        clue="Proposizione non-defining con l'hotel come soggetto grammaticale di 'had'.",
        rule="Si usa 'which' per frasi non-defining relative a cose; 'that' non si usa mai tra virgole.",
    ),
    QuestionSpec(
        sentence="She has a friend ______ father is an ambassador.",
        options=("whose", "who", "which", "whom"),
        correct="whose",
        explanation="'Whose' esprime la relazione di parentela/possesso ('il padre della sua amica').",
        clue="Relazione possessiva/parentale tra 'friend' e 'father'.",
        rule="'Whose' indica che qualcosa appartiene o è legato all'antecedente.",
    ),
    QuestionSpec(
        sentence="The café ______ we usually have coffee is closed today.",
        options=("where", "which", "that", "whose"),
        correct="where",
        explanation="'Where' si riferisce al luogo fisico in cui si compie l'azione ('nel bar').",
        clue="L'antecedente è un luogo in cui si svolge un'azione abituale ('we have coffee').",
        rule="Si usa 'where' quando la subordinata descrive ciò che accade all'interno del luogo indicato.",
    ),
    QuestionSpec(
        sentence="The woman ______ lives next door is an architect.",
        options=("who", "which", "whose", "where"),
        correct="who",
        explanation="Defining relative clause che identifica la persona; si usa 'who'.",
        clue="Proposizione restrittiva che individua di quale donna si sta parlando.",
        rule="Si usa 'who' per identificare le persone nelle relative restrittive.",
    ),
)


MEDIUM_QUESTIONS: tuple[QuestionSpec, ...] = (
    QuestionSpec(
        sentence="He arrived twenty minutes late, ______ annoyed the teacher greatly.",
        options=("which", "that", "what", "who"),
        correct="which",
        explanation="Una sentential relative clause che commenta l'intera frase precedente richiede 'which' dopo la virgola.",
        clue="Proposizione relativa che commenta l'intera situazione precedente, non un singolo sostantivo.",
        rule="Si usa 'which' in una frase non-defining per riferirsi all'intera azione o proposizione precedente.",
    ),
    QuestionSpec(
        sentence="The scientist to ______ the award was presented gave a moving speech.",
        options=("whom", "who", "which", "that"),
        correct="whom",
        explanation="Dopo una preposizione ('to'), il pronome relativo formale per una persona è 'whom'.",
        clue="Pronome relativo preceduto direttamente dalla preposizione 'to'.",
        rule="Quando un pronome relativo riferito a una persona segue direttamente una preposizione, si usa 'whom'.",
    ),
    QuestionSpec(
        sentence="Rome, ______ we spent our honeymoon, is famous for its ancient monuments.",
        options=("where", "which", "that", "whose"),
        correct="where",
        explanation="'Where' si riferisce alla città come luogo in cui si è svolta l'azione ('a Roma').",
        clue="Non-defining clause che descrive un'azione compiuta all'interno della città ('we spent our honeymoon').",
        rule="Si usa 'where' quando la proposizione esprime un evento che si è svolto all'interno del luogo.",
    ),
    QuestionSpec(
        sentence="Rome, ______ was founded in 753 BC, is the capital of Italy.",
        options=("which", "where", "that", "what"),
        correct="which",
        explanation="'Rome' è il soggetto grammaticale del verbo passivo 'was founded'; si usa 'which', non 'where'.",
        clue="La città è il soggetto grammaticale del verbo passivo, non il luogo di un'azione altrui.",
        rule="Si usa 'which' (e non 'where') quando una città è il soggetto o il complemento oggetto della relativa.",
    ),
    QuestionSpec(
        sentence="The company, ______ headquarters are located in Zurich, announced record profits.",
        options=("whose", "which", "that", "where"),
        correct="whose",
        explanation="'Whose' esprime possesso anche per enti e aziende ('la sede dell'azienda').",
        clue="Relazione di appartenenza tra l'azienda e la sua sede centrale ('headquarters').",
        rule="'Whose' si può usare con aziende e organizzazioni per indicare possesso.",
    ),
    QuestionSpec(
        sentence="She passed all her university exams with honours, ______ pleased her parents.",
        options=("which", "that", "what", "who"),
        correct="which",
        explanation="Proposizione non-defining che commenta l'intero risultato della frase principale; si usa 'which'.",
        clue="La proposizione valuta l'intero traguardo precedente ('passed with honours').",
        rule="Una non-defining clause che modifica un'intera frase deve iniziare con 'which', mai con 'that'.",
    ),
    QuestionSpec(
        sentence="The candidate with ______ I conducted the interview seemed very capable.",
        options=("whom", "who", "which", "that"),
        correct="whom",
        explanation="Seguendo direttamente la preposizione 'with', la forma corretta per le persone nel registro formale è 'whom'.",
        clue="La preposizione 'with' precede direttamente il pronome riferito a 'The candidate'.",
        rule="Le preposizioni poste prima di pronomi relativi riferiti a persone richiedono 'whom' (es. with whom, for whom).",
    ),
    QuestionSpec(
        sentence="Mount Everest, ______ peak reaches 8,848 metres, is the highest mountain on Earth.",
        options=("whose", "which", "that", "where"),
        correct="whose",
        explanation="'Whose' si usa anche per elementi inanimati e geografici per indicare appartenenza ('la cui cima').",
        clue="Possesso tra l'elemento geografico e la sua vetta ('peak').",
        rule="'Whose' può riferirsi a montagne e oggetti inanimati per sostituire 'of which'.",
    ),
    QuestionSpec(
        sentence="The reason ______ she decided to change jobs was to have a shorter commute.",
        options=("why", "which", "where", "whose"),
        correct="why",
        explanation="'Why' è l'avverbio relativo standard usato dopo il sostantivo 'the reason'.",
        clue="L'antecedente è il sostantivo 'The reason'.",
        rule="Si usa 'why' come avverbio relativo dopo l'espressione 'the reason'.",
    ),
    QuestionSpec(
        sentence="The historic castle, ______ was constructed in the twelfth century, was damaged by fire.",
        options=("which", "that", "where", "whose"),
        correct="which",
        explanation="Proposizione non-defining racchiusa da virgole; 'that' non può essere usato tra virgole.",
        clue="Non-defining clause tra virgole che descrive il castello come soggetto.",
        rule="Le relative non-defining per oggetti devono usare 'which'; 'that' non è consentito.",
    ),
    QuestionSpec(
        sentence="Children ______ parents are both working often attend after-school clubs.",
        options=("whose", "who", "which", "whom"),
        correct="whose",
        explanation="Defining clause che indica un legame di parentela/possesso ('i cui genitori').",
        clue="Relazione possessiva tra i bambini e i loro genitori ('parents').",
        rule="Si usa 'whose' nelle relative restrittive per indicare legami familiari o di possesso.",
    ),
    QuestionSpec(
        sentence="The village in ______ my grandparents lived had no paved roads.",
        options=("which", "where", "that", "whose"),
        correct="which",
        explanation="Dopo la preposizione 'in', si usa 'which' ('in which' = 'where'). Non è possibile dire 'in where'.",
        clue="La preposizione 'in' precede il pronome relativo riferito a 'The village'.",
        rule="Si usa 'in which' (mai 'in where' o 'in that') quando una preposizione regge un sostantivo di luogo.",
    ),
    QuestionSpec(
        sentence="The woman ______ you were talking to at the reception is the CEO.",
        options=("who", "which", "whose", "where"),
        correct="who",
        explanation="Defining clause riferita a una persona ('the woman'); 'who' è normale quando la preposizione resta in fondo ('talking to').",
        clue="Persona con preposizione terminale rimasta alla fine della proposizione ('to').",
        rule="Nell'inglese quotidiano si usa 'who' quando la preposizione rimane al termine della proposizione.",
    ),
    QuestionSpec(
        sentence="His train was cancelled due to bad weather, ______ meant he missed the conference.",
        options=("which", "that", "what", "whose"),
        correct="which",
        explanation="'Which' introduce un commento relativo all'intera conseguenza del fatto precedente.",
        clue="Commento sull'intera conseguenza del treno cancellato.",
        rule="Si usa 'which' dopo la virgola per collegare una conseguenza alla proposizione principale.",
    ),
    QuestionSpec(
        sentence="The museum, ______ exhibits include Egyptian mummies, receives thousands of visitors.",
        options=("whose", "which", "that", "where"),
        correct="whose",
        explanation="Possesso riferito al museo ('i reperti del museo'); si usa 'whose'.",
        clue="Possesso tra l'istituzione museale e la sua collezione ('exhibits').",
        rule="Si usa 'whose' per musei e istituzioni per indicare l'appartenenza dei contenuti espositivi.",
    ),
    QuestionSpec(
        sentence="Is there any supermarket near here ______ stays open on Sundays?",
        options=("that", "where", "whose", "whom"),
        correct="that",
        explanation="Nelle relative restrittive rette da 'any', 'that' o 'which' è standard; 'where' non può essere soggetto di 'stays'.",
        clue="Soggetto del verbo 'stays' dopo il pronome indefinito 'any supermarket'.",
        rule="I luoghi che fungono da soggetto dell'azione richiedono 'that' o 'which', non 'where'.",
    ),
    QuestionSpec(
        sentence="The politician, ______ was accused of corruption, resigned from parliament.",
        options=("who", "that", "which", "whom"),
        correct="who",
        explanation="Soggetto di una proposizione non-defining su una persona; 'that' è scorretto dopo una virgola.",
        clue="Frase non-defining tra virgole con una persona come soggetto grammaticale.",
        rule="Scegliere sempre 'who' e non 'that' quando le virgole delimitano informazioni aggiuntive su una persona.",
    ),
    QuestionSpec(
        sentence="Venice, ______ canals are famous across the world, is threatened by rising sea levels.",
        options=("whose", "which", "that", "where"),
        correct="whose",
        explanation="Pronome relativo possessivo riferito a Venezia ('i canali di Venezia').",
        clue="Relazione possessiva tra la città di Venezia e i suoi canali.",
        rule="'Whose' si usa per esprimere attributi di appartenenza di entità geografiche.",
    ),
    QuestionSpec(
        sentence="The person from ______ I received the parcel did not leave a name.",
        options=("whom", "who", "which", "that"),
        correct="whom",
        explanation="Preposizione 'from' + pronome relativo per persona richiede la forma oggettiva 'whom'.",
        clue="La preposizione 'from' precede il pronome riferito a 'The person'.",
        rule="Usare sempre 'whom' subito dopo una preposizione (from, to, with, by, of) quando ci si riferisce a persone.",
    ),
    QuestionSpec(
        sentence="He forgot his wife's birthday, ______ caused a big argument.",
        options=("which", "that", "what", "whose"),
        correct="which",
        explanation="Proposizione non-defining che commenta l'intero avvenimento di aver dimenticato il compleanno.",
        clue="Proposizione relativa che commenta l'effetto dell'intera frase precedente.",
        rule="'Which' collega una conseguenza all'intera frase precedente attraverso una virgola.",
    ),
)


class RelativeClausesTopic:
    id = "english.grammar.relative_clauses"
    family = "english"
    difficulties = ("easy", "medium", "hard")
    label_key = "topic.english_relative_clauses"
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
        chosen_spec = pool[index % len(pool)]

        # Shuffle options deterministically based on question text and index
        # so option A is not always correct, but order remains stable across reloads
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

        return VerificationResult(True, "ok")


TOPIC = RelativeClausesTopic()
