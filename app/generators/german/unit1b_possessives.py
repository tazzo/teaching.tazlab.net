"""1B — the possessive: ``mein`` and ``dein`` take the ending of the article they replace.

The rule the page teaches is one sentence long — the possessive wears the article's
ending, not the owner's gender: ``der Hund``/``das Pferd`` take ``mein``, ``die Katze`` and
every plural take ``meine`` — and the exercise is applying it to nouns whose gender is not
in the Italian word. The nouns are the animals and the family of the Einheit, so the page
does not need new vocabulary: it needs the ending.

Cards run easiest first: maschile and neutro, then femminile, then the plural, then the
same names inside a question (``Ist das dein …?``), and the last card asks the rule itself
— the answer is a sentence about German, and that is deliberate: a girl who can say *why*
«meine Katze» is not guessing any more.
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
        "Das ist ______ Hund.",
        "mein",
        "Hund è maschile (der Hund): il possessivo prende la stessa desinenza "
        "dell'articolo, quindi mein. Il nome che segue non cambia.",
        "Guarda il genere del nome che viene dopo: der Hund.",
        "mein con maschile e neutro: mein Hund, mein Pferd.",
    ),
    completion(
        "______ Katze heißt Mimi.",
        "Meine",
        "Katze è femminile (die Katze): il possessivo prende -e, quindi meine Katze.",
        "die Katze: che desinenza prende mein?",
        "meine con il femminile: meine Katze, meine Schwester.",
    ),
    completion(
        "Wo ist ______ Pferd?",
        "dein",
        "Pferd è neutro (das Pferd) e l'animale è di un'altra persona: dein Pferd. Con "
        "maschile e neutro il possessivo resta senza desinenza.",
        "das Pferd e «di te»: quale possessivo?",
        "dein con maschile e neutro: dein Hund, dein Pferd.",
    ),
    completion(
        "Sind das ______ Bücher?",
        "deine",
        "Bücher è plurale (die Bücher): al plurale il possessivo prende -e, deine.",
        "das Buch → die Bücher: è plurale.",
        "meine/deine con il plurale: meine Bücher, deine Bücher.",
    ),
    completion(
        "______ Eltern wohnen in Rom.",
        "Meine",
        "«Eltern» (i genitori) è sempre plurale: die Eltern, quindi meine Eltern.",
        "Eltern è plurale anche in italiano.",
        "die Eltern → meine Eltern, deine Eltern.",
    ),
    completion(
        "Ist das ______ Bruder?",
        "dein",
        "Bruder è maschile (der Bruder): dein Bruder. Nella domanda il possessivo non "
        "cambia.",
        "der Bruder: maschile.",
        "dein Bruder, mein Bruder.",
    ),
    completion(
        "______ Kaninchen ist weiß.",
        "Mein",
        "Kaninchen è neutro (das Kaninchen): mein Kaninchen, senza desinenza.",
        "das Kaninchen: neutro.",
        "mein Kaninchen, dein Kaninchen.",
    ),
    completion(
        "Wie heißt ______ Schwester?",
        "deine",
        "Schwester è femminile (die Schwester): deine Schwester. «Wie heißt …?» chiede il "
        "nome.",
        "die Schwester: femminile.",
        "deine Schwester, meine Schwester.",
    ),
    completion(
        "Das sind ______ Hunde.",
        "meine",
        "Hunde è plurale (die Hunde): meine Hunde. «Das sind» introduce più di uno.",
        "Hunde è plurale.",
        "meine Hunde, deine Hunde.",
    ),

    # --- choice ----------------------------------------------------------------------
    choice(
        "______ Bruder spielt Fußball.",
        "Mein",
        ("Mein", "Meine", "Meiner", "Meinen"),
        "Bruder è maschile (der Bruder): mein Bruder. «Meine» è per il femminile e il "
        "plurale.",
        "der Bruder: maschile.",
        "mein + maschile/neutro, meine + femminile/plurale.",
    ),
    choice(
        "Ist das ______ Buch?",
        "dein",
        ("dein", "deine", "deiner", "deinen"),
        "Buch è neutro (das Buch): dein Buch, senza desinenza. «deine» è per il femminile e "
        "il plurale.",
        "das Buch: neutro.",
        "dein Buch, dein Heft.",
    ),
    choice(
        "Wo sind ______ Schuhe?",
        "meine",
        ("meine", "mein", "meiner", "meinen"),
        "Schuhe è plurale (die Schuhe): meine Schuhe. «Wo sind» è già plurale.",
        "Schuhe è plurale.",
        "die Schuhe → meine Schuhe.",
    ),
    choice(
        "Das ist nicht ______ Katze!",
        "meine",
        ("meine", "mein", "meiner", "meinen"),
        "Katze è femminile (die Katze): meine Katze, anche con «nicht».",
        "die Katze: femminile.",
        "meine Katze, nicht meine Katze.",
    ),
    choice(
        "Wie alt ist ______ Hund?",
        "dein",
        ("dein", "deine", "deiner", "deinen"),
        "Hund è maschile (der Hund): dein Hund. «Wie alt ist …?» chiede l'età.",
        "der Hund: maschile.",
        "dein Hund, mein Hund.",
    ),
    choice(
        "______ Eltern sind im Urlaub.",
        "Meine",
        ("Meine", "Mein", "Meiner", "Meinen"),
        "Eltern è plurale: meine Eltern. Il verbo «sind» conferma il plurale.",
        "Eltern è plurale, e «sind» lo dice.",
        "die Eltern → meine Eltern.",
    ),
    choice(
        "Ist das ______ Pferd?",
        "dein",
        ("dein", "deine", "deiner", "deinen"),
        "Pferd è neutro (das Pferd): dein Pferd. «deine» sarebbe per un nome femminile o "
        "plurale.",
        "das Pferd: neutro.",
        "dein Pferd, mein Pferd.",
    ),
    choice(
        "Warum heißt es «mein Hund», aber «______ Katze»?",
        "meine",
        ("meine", "mein", "meiner", "meinen"),
        "Il possessivo prende la desinenza dell'articolo del nome: der Hund → mein Hund, "
        "die Katze → meine Katze. La desinenza dipende dal nome che segue, non da chi "
        "possiede.",
        "Guarda l'articolo di Katze: die.",
        "mein + der/das, meine + die (femminile e plurale).",
    ),
    choice(
        "______ Schwester ist zehn Jahre alt.",
        "Meine",
        ("Meine", "Mein", "Meiner", "Meinen"),
        "Schwester è femminile (die Schwester): meine Schwester. L'età si dice con sein: "
        "sie ist zehn Jahre alt.",
        "die Schwester: femminile.",
        "meine Schwester, meine Katze, meine Bücher.",
    ),
)


class Unit1BPossessives(GermanPractice):
    id = "german.unit1b.possessivi"
    label_key = "topic.german_unit1b_possessivi"
    cards = CARDS


TOPIC = Unit1BPossessives()
