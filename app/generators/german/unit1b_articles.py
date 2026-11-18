"""1B — *Mein Hund, meine Liebe*: the animals, and the three articles that name them.

The page is about gender: German gives every noun one of three articles and there is no
rule that can be guessed from the Italian word, so the animals are the vocabulary and the
article is the exercise. The plural takes ``die`` for all three genders, and the personal
pronouns (``er``/``sie``/``es``/``sie``) follow the noun's gender and not the animal's sex
— which is why the trap card is ``das Mädchen``: a diminutive in ``-chen`` is neuter even
when it names a girl.

Cards run easiest first: one article per gender, then the pronoun that replaces each noun,
then the plurals, then the nouns whose ending decides the gender.
"""

from __future__ import annotations

from app.generators.german.practice import (
    Card,
    GermanPractice,
    choice,
    completion,
)

CARDS: tuple[Card, ...] = (
    # --- completion: the article the sentence has to carry ---------------------------
    completion(
        "______ Hund heißt Rex.",
        "Der",
        "Hund è maschile: der Hund. A inizio frase l'articolo si scrive con la "
        "maiuscola.",
        "Pensa al genere di Hund: maschile, femminile o neutro?",
        "der = maschile, die = femminile, das = neutro.",
    ),
    completion(
        "______ Katze ist klein.",
        "Die",
        "Katze è femminile: die Katze. L'articolo non dipende dall'animale, ma dal nome.",
        "Katze: quale dei tre articoli?",
        "die Katze, die Maus, die Schlange.",
    ),
    completion(
        "______ Pferd läuft schnell.",
        "Das",
        "Pferd è neutro: das Pferd. Anche Kaninchen e Mädchen sono neutri.",
        "Pferd: maschile, femminile o neutro?",
        "das Pferd, das Kaninchen, das Mädchen.",
    ),
    completion(
        "Das ist ein Hund. ______ heißt Rex.",
        "Er",
        "Per riprendere un nome maschile si usa er, come «lui» in italiano.",
        "Sostituisci «der Hund» con un pronome.",
        "Pronomi: er (maschile), sie (femminile), es (neutro), sie (plurale).",
    ),
    completion(
        "Das ist eine Katze. ______ ist klein.",
        "Sie",
        "Per un nome femminile il pronome è sie. In tedesco il pronome segue il genere del "
        "nome, non il sesso dell'animale.",
        "Katze è femminile: quale pronome?",
        "die Katze → sie.",
    ),
    completion(
        "Das ist ein Pferd. ______ ist groß.",
        "Es",
        "Per un nome neutro il pronome è es.",
        "Pferd è neutro: quale pronome?",
        "das Pferd → es.",
    ),
    completion(
        "Der Hund und die Katze: ______ sind Freunde.",
        "Sie",
        "Due animali insieme sono un plurale: il pronome è sie, che vale anche per «loro».",
        "Il soggetto è «der Hund und die Katze»: due esseri.",
        "Plurale: sie sind (come wir sind, ihr seid).",
    ),
    completion(
        "______ Mädchen hat einen Hund.",
        "Das",
        "Mädchen finisce in -chen: tutti i nomi in -chen sono neutri, anche se indicano "
        "una ragazza. Quindi das Mädchen.",
        "Guarda la desinenza del nome: -chen.",
        "I diminutivi in -chen e -lein sono neutri: das Mädchen, das Kaninchen.",
    ),
    completion(
        "Ich habe zwei ______ (die Katze).",
        "Katzen",
        "Il plurale di Katze è Katzen: si aggiunge -n. Tra parentesi c'è il nome da mettere "
        "al plurale.",
        "Plurale femminile: spesso si aggiunge -n o -en.",
        "Plurali: die Katze → die Katzen, der Hund → die Hunde, das Pferd → die Pferde.",
    ),

    # --- choice --------------------------------------------------------------------
    choice(
        "______ Maus ist klein.",
        "Die",
        ("Die", "Der", "Das", "Den"),
        "Maus è femminile: die Maus. «Den» è l'accusativo maschile e qui non serve.",
        "Maus: quale articolo?",
        "die Maus (femminile).",
    ),
    choice(
        "______ Vogel singt.",
        "Der",
        ("Der", "Die", "Das", "Dem"),
        "Vogel è maschile: der Vogel. «Dem» è il dativo e non serve al soggetto.",
        "Vogel: maschile, femminile o neutro?",
        "der Vogel (maschile).",
    ),
    choice(
        "______ Kaninchen frisst Gras.",
        "Das",
        ("Das", "Der", "Die", "Den"),
        "Kaninchen finisce in -chen, quindi è neutro: das Kaninchen.",
        "La desinenza -chen decide il genere.",
        "das Kaninchen (neutro, come das Mädchen).",
    ),
    choice(
        "Das ist mein Hund. ______ ist braun.",
        "Er",
        ("Er", "Sie", "Es", "Ihr"),
        "Hund è maschile, quindi il pronome è er. «Ihr» è «voi», non un pronome per l'animale.",
        "Hund è maschile.",
        "der Hund → er.",
    ),
    choice(
        "Meine Katze heißt Mimi. ______ schläft viel.",
        "Sie",
        ("Sie", "Er", "Es", "Ihr"),
        "Katze è femminile: sie. Attenzione: «sie» con la minuscola è «lei» o «loro».",
        "Katze è femminile.",
        "die Katze → sie.",
    ),
    choice(
        "Das Kaninchen ist weiß. ______ frisst Gras.",
        "Es",
        ("Es", "Er", "Sie", "Ihr"),
        "Kaninchen è neutro: il pronome è es.",
        "Kaninchen è neutro.",
        "das Kaninchen → es.",
    ),
    choice(
        "Die ______ (der Fisch) schwimmen im Wasser.",
        "Fische",
        ("Fische", "Fischen", "Fisch", "Fisches"),
        "Il plurale di Fisch è Fische: die Fische. «schwimmen» è già al plurale e lo dice.",
        "Il verbo è al plurale: schwimmen.",
        "der Fisch → die Fische.",
    ),
    choice(
        "______ Schlange ist gefährlich.",
        "Die",
        ("Die", "Der", "Das", "Den"),
        "Schlange è femminile: die Schlange.",
        "Schlange: quale articolo?",
        "die Schlange (femminile).",
    ),
    choice(
        "______ Pferde laufen auf der Wiese.",
        "Die",
        ("Die", "Der", "Das", "Den"),
        "Al plurale l'articolo è sempre die, per tutti e tre i generi: die Pferde.",
        "Pferde è plurale: l'articolo del plurale è uno solo.",
        "Plurale: die Hunde, die Katzen, die Pferde.",
    ),
)


class Unit1BArticles(GermanPractice):
    id = "german.unit1b.artikel"
    label_key = "topic.german_unit1b_artikel"
    cards = CARDS


TOPIC = Unit1BArticles()
