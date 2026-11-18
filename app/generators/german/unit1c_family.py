"""1C — *Meine Familie*: who the family is, how old they are, and where they live.

Three verbs carry the page: ``sein`` for who somebody is and for their age (German says
``Ich bin 11 Jahre alt``, never ``ich habe``), ``wohnen`` for the place, ``heißen`` for the
name. The vocabulary is the family — ``die Eltern`` is plural and takes a plural verb, the
relationship words are built with ``von`` (``die Mutter von meinem Vater``) so the girl can
say any of them without a list.

Cards run easiest first: one verb form per person, then the family words, then the age
trap, then the question shapes (``Wie alt bist du?``). The words of the family are the ones
of the Einheit, not a longer list: ``Oma``/``Opa`` beside ``Großmutter``/``Großvater``,
``Onkel``/``Tante`` beside the parents and the sister.
"""

from __future__ import annotations

from app.generators.german.practice import (
    Card,
    GermanPractice,
    choice,
    completion,
)

CARDS: tuple[Card, ...] = (
    # --- completion ------------------------------------------------------------------
    completion(
        "Meine Mutter ______ in Rom.",
        "wohnt",
        "wohnen: ich wohne, du wohnst, er/sie/es wohnt. «Meine Mutter» è sie, quindi "
        "wohnt.",
        "La madre è una persona sola: sie.",
        "wohnen: er/sie/es wohnt.",
    ),
    completion(
        "Ich ______ Schülerin.",
        "bin",
        "«sein» dice chi sei: ich bin Schülerin. Con ich la forma è bin.",
        "Soggetto ich: quale forma di sein?",
        "sein: ich bin, du bist, er/sie/es ist, wir sind, ihr seid, sie sind.",
    ),
    completion(
        "Wie ______ deine Schwester?",
        "heißt",
        "Per chiedere il nome si usa heißen: Wie heißt deine Schwester? Con sie la forma è "
        "heißt.",
        "La domanda chiede il nome di una persona: sie.",
        "heißen: er/sie/es heißt.",
    ),
    completion(
        "Mein Bruder ______ 15 Jahre alt.",
        "ist",
        "L'età si dice con sein: er ist 15 Jahre alt. Con er la forma è ist.",
        "Il fratello è er: quale forma di sein?",
        "sein: er ist. L'età non si dice con haben.",
    ),
    completion(
        "Wir ______ in Italien.",
        "wohnen",
        "Con wir la desinenza è -en: wir wohnen. wohnen dice dove abiti.",
        "Soggetto wir: desinenza -en.",
        "wohnen: wir wohnen, sie wohnen.",
    ),
    completion(
        "Meine Schwester ______ Emma.",
        "heißt",
        "«Meine Schwester» è sie: sie heißt Emma. La terza persona singolare di heißen "
        "finisce in -t.",
        "La sorella è sie.",
        "heißen: sie heißt.",
    ),
    completion(
        "Wo ______ ihr?",
        "wohnt",
        "Con ihr la desinenza è -t: ihr wohnt. «Wo?» chiede il luogo.",
        "Soggetto ihr: desinenza -t.",
        "wohnen: ihr wohnt.",
    ),
    completion(
        "Meine Großeltern ______ in Neapel.",
        "wohnen",
        "«Großeltern» sono i nonni, due persone: il verbo va al plurale, sie wohnen.",
        "Due nonni: il soggetto è plurale.",
        "die Großeltern → sie wohnen.",
    ),
    completion(
        "Meine Mutter ______ Lehrerin.",
        "ist",
        "Per dire che lavoro fa una persona si usa sein: sie ist Lehrerin. La madre è sie, "
        "quindi ist.",
        "sie + sein: quale forma?",
        "sein: sie ist (anche per il mestiere: sie ist Lehrerin).",
    ),

    # --- choice ----------------------------------------------------------------------
    choice(
        "Die Mutter von meinem Vater ist meine ______.",
        "Oma",
        ("Oma", "Tante", "Schwester", "Cousine"),
        "La madre di mio padre è mia nonna: die Oma (o die Großmutter). La zia è la "
        "sorella di un genitore.",
        "La madre del padre è la nonna.",
        "die Großmutter / die Oma, der Großvater / der Opa.",
    ),
    choice(
        "Der Bruder von meiner Mutter ist mein ______.",
        "Onkel",
        ("Onkel", "Opa", "Vater", "Cousin"),
        "Il fratello di mia madre è mio zio: der Onkel. «Opa» è il nonno, «Cousin» il "
        "cugino.",
        "Il fratello della madre è lo zio.",
        "der Onkel, die Tante.",
    ),
    choice(
        "Wie alt ______ du?",
        "bist",
        ("bist", "ist", "sind", "hast"),
        "La domanda sull'età usa sein: Wie alt bist du? — Ich bin 11 Jahre alt. «hast» "
        "sarebbe il verbo avere, che non si usa per l'età.",
        "Soggetto du e verbo sein.",
        "sein: du bist. L'età: Ich bin … Jahre alt.",
    ),
    choice(
        "Wie heißt deine Schwester? — «______ heißt Emma.»",
        "Sie",
        ("Sie", "Er", "Es", "Du"),
        "Schwester è femminile: il pronome è sie. In italiano diremmo «lei», e il pronome "
        "segue il genere del nome.",
        "Il nome «Schwester» è femminile.",
        "die Schwester → sie.",
    ),
    choice(
        "Ich ______ 11 Jahre alt.",
        "bin",
        ("bin", "habe", "ist", "sind"),
        "L'età si dice con sein: ich bin 11 Jahre alt. «Ich habe 11 Jahre» è l'errore che si "
        "fa dall'italiano.",
        "Soggetto ich: sein o haben?",
        "sein: ich bin … Jahre alt.",
    ),
    choice(
        "Meine Eltern ______ in Mailand.",
        "wohnen",
        ("wohnen", "wohnt", "wohne", "wohnst"),
        "«Eltern» è plurale: sie wohnen. «wohnt» è per er/sie/es e per ihr.",
        "Eltern è plurale.",
        "wohnen: sie wohnen.",
    ),
    choice(
        "Die Frau von meinem Onkel ist meine ______.",
        "Tante",
        ("Tante", "Oma", "Mutter", "Cousine"),
        "La moglie di mio zio è mia zia: die Tante, la stessa parola per la sorella di un "
        "genitore.",
        "La moglie dello zio è la zia.",
        "die Tante, der Onkel.",
    ),
    choice(
        "Ich wohne ______ Italien.",
        "in",
        ("in", "aus", "von", "bei"),
        "wohnen vuole in + paese: Ich wohne in Italien. «aus» dice la provenienza: Ich "
        "komme aus Italien.",
        "Il verbo è wohnen, non kommen.",
        "wohnen in + paese; kommen aus + paese.",
    ),
    choice(
        "Meine Schwester und ich: ______ sind Geschwister.",
        "Wir",
        ("Wir", "Ihr", "Sie", "Du"),
        "«io e mia sorella» è noi: wir. «Ihr» è «voi», «sie» è «loro».",
        "«Meine Schwester und ich» = noi.",
        "Pronomi: wir (noi), ihr (voi), sie (loro).",
    ),
)


class Unit1CFamily(GermanPractice):
    id = "german.unit1c.familie"
    label_key = "topic.german_unit1c"
    cards = CARDS


TOPIC = Unit1CFamily()
