"""1A — *Ich komme aus Italien*: the countries, saying who you are, and where you come from.

The book's first Einheit pairs three things that belong together: the names of the
countries, the greetings that open a conversation, and the two verbs that carry it —
``kommen`` for the origin, ``sein`` for the person. The question word ``Woher`` and the
yes/no question (verb first) are the grammar of the page, and the last cards bring the
countries that take an article (``aus der Schweiz``, ``aus den Niederlanden``), which is
where a ten-year-old stops guessing and starts noticing.

Cards run easiest first: the verb form with ``ich``, then ``du``/``wir``/``ihr``, then the
two question shapes, then the articles. Nothing on this page is reused from another page
of the site — the test in ``tests/test_german_topics.py`` holds that line for all five
pools together.
"""

from __future__ import annotations

from app.generators.german.practice import (
    Card,
    GermanPractice,
    choice,
    completion,
)

CARDS: tuple[Card, ...] = (
    # --- completion: the verb with the subject that is written -----------------------
    completion(
        "Hallo, ich ______ Anna.",
        "heiße",
        "«heißen» al presente fa ich heiße: la desinenza di «ich» è -e. Non si dice "
        "«ich heißen».",
        "Il soggetto è ich: il verbo prende la desinenza -e.",
        "heißen: ich heiße, du heißt, er/sie/es heißt, wir heißen, ihr heißt, sie heißen.",
        accept=("heisse",),
    ),
    completion(
        "Ich ______ aus Italien.",
        "komme",
        "«kommen» dice da dove vieni: ich komme aus Italien. Con ich la desinenza è -e.",
        "Soggetto ich, verbo kommen: desinenza -e.",
        "kommen: ich komme, du kommst, er/sie/es kommt, wir kommen, ihr kommt, sie kommen.",
    ),
    completion(
        "Das ______ mein Freund Luca.",
        "ist",
        "«sein» è il verbo essere: ich bin, du bist, er/sie/es ist. Con «das» serve ist.",
        "Il soggetto è das, cioè er: sein diventa ist.",
        "sein: ich bin, du bist, er/sie/es ist, wir sind, ihr seid, sie sind.",
    ),
    completion(
        "Woher ______ du?",
        "kommst",
        "Con du il verbo prende -st: du kommst. «Woher?» chiede «da dove?».",
        "Soggetto du: la desinenza è -st.",
        "La domanda con Woher chiede la provenienza: Woher kommst du? — Ich komme aus Italien.",
    ),
    completion(
        "Wir ______ aus Italien.",
        "kommen",
        "Con wir la desinenza è -en: wir kommen. La forma è la stessa di sie/Sie kommen.",
        "Soggetto wir: la desinenza è -en.",
        "kommen: wir kommen, sie kommen, Sie kommen.",
    ),
    completion(
        "______ du Maria?",
        "Bist",
        "Domanda sì/no: il verbo va davanti al soggetto. Con du, sein fa bist: Bist du "
        "Maria?",
        "Il verbo è in prima posizione e il soggetto è du.",
        "Domanda sì/no: verbo + soggetto + resto: Bist du …? Kommst du …?",
    ),
    completion(
        "______ ihr aus Frankreich?",
        "Kommt",
        "Con ihr la desinenza è -t: ihr kommt. Nella domanda il verbo va davanti.",
        "Soggetto ihr: desinenza -t, verbo in prima posizione.",
        "kommen: ihr kommt. La domanda sì/no mette il verbo davanti al soggetto.",
    ),
    completion(
        "Guten ______, Frau Müller!",
        "Tag",
        "«Guten Tag» è il saluto della giornata; al mattino «Guten Morgen», la sera «Guten "
        "Abend».",
        "È un saluto che comincia con Guten … e vale per tutto il giorno.",
        "Saluti: Guten Morgen, Guten Tag, Guten Abend; tra amici anche Hallo.",
    ),
    completion(
        "Auf ______, bis morgen!",
        "Wiedersehen",
        "«Auf Wiedersehen» è l'arrivederci formale; tra amici si dice «Tschüs».",
        "Con Auf … si saluta quando si va via.",
        "Saluto d'addio: Auf Wiedersehen (formale), Tschüs (informale).",
    ),

    # --- choice: the same grammar, read off four forms ------------------------------
    choice(
        "Ich komme ______ Italien.",
        "aus",
        ("aus", "in", "von", "bei"),
        "La provenienza si dice con aus: aus Italien, aus Deutschland. «in» direbbe dove "
        "sei, «von» da una persona, «bei» vicino a qualcuno.",
        "La frase dice da dove vieni, non dove abiti.",
        "aus + paese: Ich komme aus Italien.",
    ),
    choice(
        "Meine Eltern ______ aus Spanien.",
        "kommen",
        ("kommen", "kommt", "komme", "kommst"),
        "«Meine Eltern» sono due persone, quindi il verbo va al plurale: sie kommen. "
        "«kommt» è per er/sie/es e per ihr.",
        "Il soggetto è plurale: meine Eltern = sie.",
        "kommen: sie kommen (come wir kommen).",
    ),
    choice(
        "Er ______ aus Deutschland.",
        "kommt",
        ("kommt", "komme", "kommst", "kommen"),
        "Con er la desinenza è -t: er kommt. «komme» è la forma di ich, «kommst» quella di "
        "du.",
        "Soggetto er: desinenza -t.",
        "kommen: er/sie/es kommt.",
    ),
    choice(
        "Anna und Petra ______ aus Österreich.",
        "kommen",
        ("kommen", "kommt", "komme", "kommst"),
        "Due nomi insieme valgono «sie» (loro): Anna und Petra kommen. Il verbo resta al "
        "plurale anche se i nomi sono femminili.",
        "Due persone: il soggetto è plurale.",
        "Plurale: die Mädchen kommen, Anna und Petra kommen.",
    ),
    choice(
        "Wie ______ du?",
        "heißt",
        ("heißt", "heiße", "heißen", "heißst"),
        "Con du, heißen fa heißt: la radice è heiß- e la desinenza di du è -t. «heißst» non "
        "esiste.",
        "Domanda sul nome, soggetto du.",
        "heißen: ich heiße, du heißt, er heißt.",
    ),
    choice(
        "______ kommst du?",
        "Woher",
        ("Woher", "Wo", "Was", "Wer"),
        "«Woher» chiede la provenienza (da dove?). «Wo» chiede dove sei, «was» che cosa, "
        "«wer» chi.",
        "La risposta comincia con «aus»: la domanda chiede la provenienza.",
        "Woher kommst du? — Ich komme aus …",
    ),
    choice(
        "Ich komme aus ______ Schweiz.",
        "der",
        ("der", "die", "das", "den"),
        "La Svizzera è femminile (die Schweiz). Dopo «aus» il femminile diventa der: aus "
        "der Schweiz. È uno dei pochi paesi con l'articolo.",
        "die Schweiz + la preposizione aus.",
        "Paesi con articolo: aus der Schweiz, aus der Türkei, aus dem Iran, aus den USA.",
    ),
    choice(
        "Ich komme aus ______ Niederlanden.",
        "den",
        ("den", "der", "die", "dem"),
        "I Paesi Bassi sono plurali (die Niederlande). Dopo «aus» il plurale diventa den: "
        "aus den Niederlanden.",
        "die Niederlande è plurale, e aus vuole il dativo.",
        "aus + plurale = den: aus den Niederlanden, aus den USA.",
    ),
    choice(
        "Es ist 8 Uhr morgens. Du sagst: «______»",
        "Guten Morgen",
        ("Guten Morgen", "Guten Abend", "Gute Nacht", "Auf Wiedersehen"),
        "Alle otto del mattino si saluta con Guten Morgen. «Guten Abend» è la sera, «Gute "
        "Nacht» si dice prima di dormire, «Auf Wiedersehen» quando si va via.",
        "Guarda l'ora: sono le otto di mattina.",
        "Guten Morgen (mattina), Guten Tag (giorno), Guten Abend (sera).",
    ),
)


class Unit1A(GermanPractice):
    id = "german.unit1a.laender"
    label_key = "topic.german_unit1a"
    cards = CARDS


TOPIC = Unit1A()
