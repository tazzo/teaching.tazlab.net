"""Present Perfect Simple vs Present Perfect Continuous exercise generator.

Provides multiple-choice fill-in-the-blank questions focusing on:
- Ongoing duration vs completed quantity (how long vs how many)
- Recent activity with visible present evidence vs finished result
- Stative verbs (know, believe, have, understand, own) which do not take continuous
- Time markers: already, yet, just, ever, since, for, all day, lately
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
        sentence="I ______ (know) Sarah for more than ten years.",
        options=("have known", "have been knowing", "know", "am knowing"),
        correct="have known",
        explanation="Il verbo 'know' è uno stative verb (verbo di stato) che esprime cognizione/relazione e non ammette la forma continua (-ing); si usa il Present Perfect Simple.",
        clue="Stative verb 'know' con indicatore di durata ('for more than ten years').",
        rule="I verbi di stato (know, like, believe, understand) prendono il Present Perfect Simple, mai il continuous.",
    ),
    QuestionSpec(
        sentence="She ______ (already / do) her homework, so she can relax now.",
        options=("has already done", "has already been doing", "already does", "is already doing"),
        correct="has already done",
        explanation="'Already' indica un'azione completata prima del previsto o prima del momento presente; si usa il Present Perfect Simple.",
        clue="Avverbio 'already' + risultato presente completato ('she can relax now').",
        rule="Si usa il Present Perfect Simple con 'already' per indicare un'azione completata prima del momento attuale.",
    ),
    QuestionSpec(
        sentence="He ______ (play) video games for three hours without stopping.",
        options=("has been playing", "has played", "plays", "was playing"),
        correct="has been playing",
        explanation="'For three hours without stopping' pone l'enfasi sulla durata continua e ininterrotta dell'attività fino ad ora.",
        clue="Attività continua con indicatore di durata 'for three hours without stopping'.",
        rule="Si usa il Present Perfect Continuous per sottolineare per quanto tempo un'azione si è protratta fino al presente.",
    ),
    QuestionSpec(
        sentence="We ______ (not see) that new film yet.",
        options=("haven't seen", "haven't been seeing", "don't see", "didn't see"),
        correct="haven't seen",
        explanation="'Yet' nelle frasi negative indica che l'azione non è ancora avvenuta fino a questo momento; richiede il Present Perfect Simple.",
        clue="Avverbio di tempo 'yet' in frase negativa.",
        rule="Il Present Perfect Simple si usa con 'yet' per esprimere che un evento atteso non si è ancora verificato.",
    ),
    QuestionSpec(
        sentence="It ______ (rain) all day and the garden is soaked.",
        options=("has been raining", "has rained", "rains", "is raining"),
        correct="has been raining",
        explanation="'All day' evidenzia la durata continua e ininterrotta dell'evento atmosferico con effetto visibile nel presente (il giardino è allagato).",
        clue="Espressione di durata 'all day' con verbo d'azione ('rain').",
        rule="Si usa il Present Perfect Continuous con eventi atmosferici o azioni continuative prolungate nel tempo.",
    ),
    QuestionSpec(
        sentence="How many cups of coffee ______ (you / drink) this morning?",
        options=("have you drunk", "have you been drinking", "did you drink", "do you drink"),
        correct="have you drunk",
        explanation="Quando si chiede o si indica una quantità o un numero completato ('how many cups'), si usa sempre il Present Perfect Simple.",
        clue="Domanda con 'how many' incentrata sulla quantità completata.",
        rule="Con 'How many' o 'how much' si usa il Present Perfect Simple per focalizzarsi sulla quantità o sul risultato finale.",
    ),
    QuestionSpec(
        sentence="They ______ (live) in Rome since 2015.",
        options=("have lived", "are living", "lived", "were living"),
        correct="have lived",
        explanation="Una residenza stabile e duratura iniziata nel passato ('since 2015') e tuttora in corso richiede il Present Perfect Simple.",
        clue="Punto di partenza 'since 2015' per descrivere una situazione abitativa duratura.",
        rule="Il Present Perfect Simple si preferisce per situazioni stabili o permanenti che proseguono fino al presente.",
    ),
    QuestionSpec(
        sentence="I ______ (read) fifty pages of the novel so far.",
        options=("have read", "have been reading", "read", "am reading"),
        correct="have read",
        explanation="'So far' unito a un conteggio preciso ('fifty pages') richiede il Present Perfect Simple per indicare la porzione completata.",
        clue="'So far' associato a una quantità numerica completata ('fifty pages').",
        rule="Si usa il Present Perfect Simple per indicare quante parti o unità di un'attività sono state completate.",
    ),
    QuestionSpec(
        sentence="Listen! The baby ______ (cry) for twenty minutes.",
        options=("has been crying", "has cried", "cries", "is crying"),
        correct="has been crying",
        explanation="L'attenzione è focalizzata sulla durata continua ('for twenty minutes') di un'azione che prosegue nel momento presente.",
        clue="Osservazione diretta ('Listen!') unita alla durata ('for twenty minutes').",
        rule="Il Present Perfect Continuous descrive un'azione in corso che si prolunga nel tempo fino al presente.",
    ),
    QuestionSpec(
        sentence="______ (you / ever / visit) London?",
        options=("Have you ever visited", "Have you ever been visiting", "Did you ever visit", "Do you ever visit"),
        correct="Have you ever visited",
        explanation="'Ever' nelle domande si riferisce a un'esperienza di vita generale in qualsiasi momento fino ad oggi; si usa il Present Perfect Simple.",
        clue="Avverbio 'ever' in una domanda sulle esperienze di vita.",
        rule="Si usa il Present Perfect Simple con 'ever' e 'never' per parlare di esperienze personali nel corso della vita.",
    ),
    QuestionSpec(
        sentence="He ______ (have) that bicycle since his tenth birthday.",
        options=("has had", "has been having", "has", "had"),
        correct="has had",
        explanation="'Have' nel senso di possesso è uno stative verb e non può avere la forma in -ing; si usa il Present Perfect Simple.",
        clue="Stative verb di possesso 'have' + durata da 'since his tenth birthday'.",
        rule="I verbi di stato che esprimono possesso (have, own, belong) non si usano alla forma progressiva.",
    ),
    QuestionSpec(
        sentence="They ______ (wait) at the bus stop for forty minutes.",
        options=("have been waiting", "have waited", "are waiting", "waited"),
        correct="have been waiting",
        explanation="L'atto di aspettare per una durata prolungata ('for forty minutes') richiede il Present Perfect Continuous per evidenziare l'attesa.",
        clue="Durata prolungata di un processo in corso ('for forty minutes').",
        rule="Il Present Perfect Continuous sottolinea il trascorrere del tempo e lo svolgimento dell'azione.",
    ),
    QuestionSpec(
        sentence="I ______ (lose) my house keys; can you help me look for them?",
        options=("have lost", "have been losing", "lost", "am losing"),
        correct="have lost",
        explanation="'Lose' è un'azione puntuale e istantanea con conseguenza immediata nel presente (non posso entrare in casa); la forma continua è impossibile.",
        clue="Evento istantaneo con forte conseguenza nel presente.",
        rule="Le azioni momentanee con risultato immediato nel presente richiedono il Present Perfect Simple.",
    ),
    QuestionSpec(
        sentence="She ______ (study) for her exam since 8 o'clock this morning.",
        options=("has been studying", "has studied", "studies", "is studying"),
        correct="has been studying",
        explanation="Sottolinea l'impegno continuativo e la durata dell'attività di studio iniziata alle 8:00 e ancora in corso.",
        clue="Verbo di attività 'study' + punto di inizio 'since 8 o'clock'.",
        rule="Le attività prolungate iniziate nel passato e ancora in corso con enfasi sullo sforzo richiedono il Present Perfect Continuous.",
    ),
    QuestionSpec(
        sentence="We ______ (buy) a new television for the living room.",
        options=("have bought", "have been buying", "are buying", "bought"),
        correct="have bought",
        explanation="Il focus è sull'acquisto completato come singola novità con effetto nel soggiorno (Present Perfect Simple).",
        clue="Azione completata con risultato concreto nel presente.",
        rule="Si usa il Present Perfect Simple per annunciare un acquisto o un evento completato di recente.",
    ),
    QuestionSpec(
        sentence="Tom ______ (sleep) for ten hours — you should wake him up!",
        options=("has been sleeping", "has slept", "sleeps", "is sleeping"),
        correct="has been sleeping",
        explanation="L'enfasi è sulla durata ininterrotta del sonno ('for ten hours') che sta proseguendo proprio adesso.",
        clue="Durata 'for ten hours' + invito a svegliarlo nel presente.",
        rule="Il Present Perfect Continuous enfatizza la durata ininterrotta di un'azione ancora in svolgimento.",
    ),
    QuestionSpec(
        sentence="How many emails ______ (she / send) today?",
        options=("has she sent", "has she been sending", "did she send", "does she send"),
        correct="has she sent",
        explanation="'How many' chiede il numero totale di elementi completati (email inviate); richiede il Present Perfect Simple.",
        clue="'How many' riferito a elementi numerabili ('emails').",
        rule="Si usa sempre il Present Perfect Simple quando si specifica o si chiede il numero di unità completate.",
    ),
    QuestionSpec(
        sentence="I ______ (learn) English for three years and I really enjoy it.",
        options=("have been learning", "have learned", "learn", "am learning"),
        correct="have been learning",
        explanation="Un percorso di apprendimento che si sviluppa lungo un arco di tempo ('for three years') richiede il Present Perfect Continuous.",
        clue="Processo di apprendimento nel tempo ('for three years').",
        rule="Il Present Perfect Continuous si usa per abilità, studi o attività in corso di sviluppo nel tempo.",
    ),
    QuestionSpec(
        sentence="The train ______ (just / arrive) at platform 4.",
        options=("has just arrived", "has just been arriving", "just arrived", "is just arriving"),
        correct="has just arrived",
        explanation="'Just' indica un evento completato pochissimi istanti fa (Present Perfect Simple).",
        clue="'Just' indica un completamento appena avvenuto.",
        rule="Si usa il Present Perfect Simple con 'just' per azioni completate poco prima del momento in cui si parla.",
    ),
    QuestionSpec(
        sentence="They ______ (work) in the garden all morning.",
        options=("have been working", "have worked", "work", "are working"),
        correct="have been working",
        explanation="'All morning' con un verbo di attività fisica evidenzia l'impegno e la durata prolungata dell'azione.",
        clue="Espressione temporale 'all morning' con verbo d'azione 'work'.",
        rule="Si usa il Present Perfect Continuous con espressioni come 'all day' o 'all morning' per dare risalto alla durata.",
    ),
)


MEDIUM_QUESTIONS: tuple[QuestionSpec, ...] = (
    QuestionSpec(
        sentence="Look at your hands, they are covered in mud! What ______ (you / do)?",
        options=("have you been doing", "have you done", "did you do", "were you doing"),
        correct="have you been doing",
        explanation="Si usa il Present Perfect Continuous quando c'è un'evidenza fisica presente (fango sulle mani) derivante da un'attività recente.",
        clue="Evidenza fisica visibile nel presente ('covered in mud') di un'attività appena svolta.",
        rule="Il Present Perfect Continuous spiega uno stato presente derivante da un'attività continuativa recente.",
    ),
    QuestionSpec(
        sentence="The kitchen walls look wonderful! I ______ (paint) them light blue.",
        options=("have painted", "have been painting", "painted", "am painting"),
        correct="have painted",
        explanation="Il focus è sul risultato finale completato con successo ('look wonderful'); si usa il Present Perfect Simple.",
        clue="Focus sul risultato finale completato ('walls look wonderful').",
        rule="Si usa il Present Perfect Simple quando il centro dell'attenzione è il risultato compiuto e non il processo.",
    ),
    QuestionSpec(
        sentence="I ______ (paint) the kitchen all afternoon, which is why my shirt is stained.",
        options=("have been painting", "have painted", "painted", "was painting"),
        correct="have been painting",
        explanation="Il focus è sull'attività svolta e sul tempo impiegato ('all afternoon'), spiegando la conseguenza presente (maglietta macchiata).",
        clue="Processo e durata ('all afternoon') che spiegano un effetto presente ('shirt is stained').",
        rule="Il Present Perfect Continuous collega un'attività prolungata direttamente a una conseguenza visibile presente.",
    ),
    QuestionSpec(
        sentence="Somebody ______ (eat) my chocolates — the box is half empty!",
        options=("has been eating", "has eaten", "ate", "is eating"),
        correct="has been eating",
        explanation="L'azione non è terminata (la scatola è mezza piena), focalizzandosi sull'attività recente che ha intaccato i cioccolatini.",
        clue="Azione incompiuta: la scatola è solo mezza vuota, restano dei cioccolatini.",
        rule="Il Present Perfect Continuous si usa quando un'azione è parziale o non completamente conclusa.",
    ),
    QuestionSpec(
        sentence="The children ______ (eat) all the biscuits; there is nothing left in the jar.",
        options=("have eaten", "have been eating", "ate", "were eating"),
        correct="have eaten",
        explanation="L'azione è del tutto conclusa con un risultato totale (non è rimasto nulla); richiede il Present Perfect Simple.",
        clue="Completamento totale senza residui ('nothing left in the jar').",
        rule="Si usa il Present Perfect Simple quando l'intera quantità di qualcosa è stata consumata o completata.",
    ),
    QuestionSpec(
        sentence="Why are you breathing so heavily? — I ______ (run).",
        options=("have been running", "have run", "ran", "was running"),
        correct="have been running",
        explanation="Il Present Perfect Continuous spiega una condizione fisica visibile nel presente (respiro affannoso) dovuta a uno sforzo recente.",
        clue="Sintomo fisico presente ('breathing so heavily') causato da attività recente.",
        rule="Si usa il Present Perfect Continuous per spiegare come qualcuno appare o si sente nel presente a causa di un'attività appena conclusa.",
    ),
    QuestionSpec(
        sentence="I ______ (write) report drafts all morning, but I ______ (only / finish) one.",
        options=("have been writing / have only finished", "have written / have only been finishing", "wrote / only finished", "am writing / only finish"),
        correct="have been writing / have only finished",
        explanation="L'attività in corso ('all morning') richiede il continuous, mentre la quantità completata ('only one') richiede il simple.",
        clue="Contrasto: durata del processo ('all morning') vs quantità completata ('only one').",
        rule="Si abbina il Present Perfect Continuous per la durata del processo e il Present Perfect Simple per il numero di elementi completati.",
    ),
    QuestionSpec(
        sentence="He ______ (believe) in that theory his entire life.",
        options=("has believed", "has been believing", "believes", "is believing"),
        correct="has believed",
        explanation="'Believe' è un verbo di stato mentale (stative verb) e non può essere usato nei tempi continui.",
        clue="Stative verb mentale 'believe' + durata 'his entire life'.",
        rule="I verbi di opinione e cognizione (believe, know, think that, understand) non ammettono forme progressive.",
    ),
    QuestionSpec(
        sentence="She is exhausted because she ______ (not sleep) well lately.",
        options=("has not been sleeping", "has not slept", "didn't sleep", "is not sleeping"),
        correct="has not been sleeping",
        explanation="'Lately' descrive una condizione che si è ripetuta o protratta nei giorni recenti; si usa il Present Perfect Continuous.",
        clue="'Lately' indica una condizione continuativa o ripetuta che causa stanchezza.",
        rule="Il Present Perfect Continuous con 'lately' o 'recently' esprime abitudini o stati che si protraggono nel periodo recente.",
    ),
    QuestionSpec(
        sentence="We ______ (travel) through South America for the past two months.",
        options=("have been travelling", "have travelled", "are travelling", "travelled"),
        correct="have been travelling",
        explanation="'For the past two months' sottolinea un viaggio continuativo e temporaneo che prosegue nel presente.",
        clue="Viaggio prolungato temporaneo nel corso de 'the past two months'.",
        rule="Il Present Perfect Continuous descrive situazioni temporanee prolungate che continuano nel presente.",
    ),
    QuestionSpec(
        sentence="He ______ (break) his watch, so he doesn't know what time it is.",
        options=("has broken", "has been breaking", "broke", "was breaking"),
        correct="has broken",
        explanation="'Break' è un'azione istantanea con effetto presente; la forma continua non ha senso in questo contesto.",
        clue="Evento istantaneo con diretta conseguenza presente ('doesn't know what time it is').",
        rule="I verbi che descrivono eventi istantanei (break, lose, drop) richiedono la forma Simple.",
    ),
    QuestionSpec(
        sentence="They ______ (negotiate) the new contract for three weeks, but they haven't signed it yet.",
        options=("have been negotiating", "have negotiated", "negotiate", "are negotiating"),
        correct="have been negotiating",
        explanation="Il processo di negoziazione è ancora in corso e non concluso ('haven't signed it yet').",
        clue="Processo prolungato non ancora concluso con durata 'for three weeks'.",
        rule="Si usa il Present Perfect Continuous per processi prolungati ancora aperti che non sono giunti a conclusione.",
    ),
    QuestionSpec(
        sentence="I ______ (call) him four times this afternoon, but his phone is switched off.",
        options=("have called", "have been calling", "called", "am calling"),
        correct="have called",
        explanation="Azioni ripetute e completate con un numero esatto di volte ('four times') richiedono il Present Perfect Simple.",
        clue="Numero specifico di azioni ripetute completate ('four times').",
        rule="Quando si specifica il numero esatto di volte in cui un'azione è avvenuta, si usa il Present Perfect Simple.",
    ),
    QuestionSpec(
        sentence="She ______ (teach) at this university since she graduated.",
        options=("has been teaching", "is teaching", "taught", "was teaching"),
        correct="has been teaching",
        explanation="Attività professionale attiva che prosegue dalla laurea fino al presente.",
        clue="Carriera attiva continuativa dal momento 'since she graduated'.",
        rule="Il Present Perfect Continuous valorizza l'attività continuativa di una carriera o occupazione.",
    ),
    QuestionSpec(
        sentence="I ______ (own) this vintage record player for over twenty years.",
        options=("have owned", "have been owning", "own", "am owning"),
        correct="have owned",
        explanation="'Own' esprime possesso ed è uno stative verb; le forme in -ing sono grammaticalmente errate.",
        clue="Stative verb di possesso 'own' + durata 'for over twenty years'.",
        rule="I verbi di possesso (own, possess, belong to) prendono sempre il Present Perfect Simple.",
    ),
    QuestionSpec(
        sentence="How long ______ (you / learn) Japanese?",
        options=("have you been learning", "have you learned", "do you learn", "did you learn"),
        correct="have you been learning",
        explanation="'How long' applicato a un'attività di studio in corso richiede il Present Perfect Continuous.",
        clue="Domanda con 'How long' su un'attività in pieno svolgimento.",
        rule="Si chiede 'How long' con il Present Perfect Continuous per indagare la durata di un'azione in corso.",
    ),
    QuestionSpec(
        sentence="The company ______ (develop) this new software since last year and it is almost ready.",
        options=("has been developing", "has developed", "develops", "developed"),
        correct="has been developing",
        explanation="Sviluppo in corso ('almost ready') su un arco temporale iniziato l'anno scorso.",
        clue="Lavoro in corso non ancora terminato ('almost ready') iniziato l'anno scorso.",
        rule="Lo sviluppo continuativo di un progetto in corso richiede il Present Perfect Continuous.",
    ),
    QuestionSpec(
        sentence="Scientists ______ (discover) a new species of frog in the Amazon rainforest.",
        options=("have discovered", "have been discovering", "discover", "were discovering"),
        correct="have discovered",
        explanation="Una notizia singola e una scoperta completata richiedono il Present Perfect Simple.",
        clue="Annuncio di una singola scoperta completata di recente.",
        rule="Si usa il Present Perfect Simple per dare notizie recenti e annunciare eventi o scoperte puntuali.",
    ),
    QuestionSpec(
        sentence="You look exhausted! ______ (you / work) on the computer all night?",
        options=("Have you been working", "Have you worked", "Did you work", "Do you work"),
        correct="Have you been working",
        explanation="Si chiede conto dell'attività continuativa che spiega l'aspetto esausto di qualcuno nel presente.",
        clue="Aspetto esteriore visibile ('look exhausted') dovuto a un'attività durata 'all night'.",
        rule="Il Present Perfect Continuous si usa per interrogare l'attività recente che ha prodotto una condizione attuale evidente.",
    ),
    QuestionSpec(
        sentence="I ______ (never / understand) why people enjoy horror movies so much.",
        options=("have never understood", "have never been understanding", "never understood", "am never understanding"),
        correct="have never understood",
        explanation="'Understand' è uno stative verb di cognizione; si usa con il Present Perfect Simple unito a 'never'.",
        clue="Stative verb cognitivo 'understand' con indicatore di esperienza 'never'.",
        rule="I verbi di percezione mentale non ammettono l'aspetto continuativo.",
    ),
)


class PresentPerfectTopic:
    id = "english.grammar.present_perfect"
    family = "english"
    difficulties = ("easy", "medium", "hard")
    label_key = "topic.english_present_perfect"
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


TOPIC = PresentPerfectTopic()
