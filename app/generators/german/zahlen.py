"""Die Zahlen 1–100: the numbers the book asks for, including how they are built.

The page the operator asked for by name. Three things are drillled, in the order a
first-year class meets them: 1–12 by heart and 13–19 with ``-zehn``; the tens in ``-zig``
with the two irregular ones (``sechzig``, ``siebzig``, and ``dreißig`` with the ß); and the
composition from 21 up, where German says the unit **first** — ``einundzwanzig``, not
“twenty-one”.

Cards run easiest first: the small numbers, then the two spellings children get wrong
(``sechzehn``/``sechzig``, ``siebzehn``/``siebzig``), then the tens, then the composition.
The completion cards take the ASCII spelling as well (``zwoelf``, ``dreissig``): an Italian
keyboard has no ß, and refusing ``ss`` would test the keyboard, not the number.
"""

from __future__ import annotations

from app.generators.german.practice import (
    Card,
    GermanPractice,
    choice,
    completion,
)

CARDS: tuple[Card, ...] = (
    # --- completion: write the number in words ---------------------------------------
    completion(
        "In Worten: 12 = ______",
        "zwölf",
        "12 è zwölf, una forma irregolare: non si dice «zweizehn». Fino a 12 i numeri si "
        "imparano a memoria.",
        "Dodici non segue la regola di «due + zehn».",
        "1–12: eins, zwei, drei, vier, fünf, sechs, sieben, acht, neun, zehn, elf, zwölf.",
        accept=("zwoelf",),
    ),
    completion(
        "In Worten: 17 = ______",
        "siebzehn",
        "17 è siebzehn: da sieben si toglie la -en e si aggiunge -zehn.",
        "sieben + zehn, ma senza la -en di sieben.",
        "13–19: dreizehn, vierzehn, fünfzehn, sechzehn, siebzehn, achtzehn, neunzehn.",
        accept=("siebzehn",),
    ),
    completion(
        "In Worten: 16 = ______",
        "sechzehn",
        "16 è sechzehn: da sechs si toglie la -s e si aggiunge -zehn.",
        "sechs + zehn, ma senza la -s di sechs.",
        "sechs → sechzehn (e sechzig): la -s cade davanti alla desinenza.",
        accept=("sechzehn",),
    ),
    completion(
        "In Worten: 60 = ______",
        "sechzig",
        "60 è sechzig, senza la -s di sechs, con la desinenza -zig delle decine.",
        "sechs + zig, ma senza la -s.",
        "Le decine: zwanzig, dreißig, vierzig, fünfzig, sechzig, siebzig, achtzig, neunzig.",
        accept=("sechzig",),
    ),
    completion(
        "In Worten: 30 = ______",
        "dreißig",
        "30 è dreißig: è l'unica decina con la ß, e finisce in -ig come le altre.",
        "Trenta: attenzione alla lettera ß.",
        "dreißig (30) non «dreizig»; 13 è dreizehn.",
        accept=("dreissig",),
    ),
    completion(
        "In Worten: 44 = ______",
        "vierundvierzig",
        "44 = vier + und + vierzig: prima l'unità, poi la decina. In tedesco si dice «quattro "
        "e quaranta».",
        "Da 21 in poi si comincia dall'unità.",
        "21–99: unità + und + decina: einundzwanzig, vierundvierzig.",
    ),
    completion(
        "In Worten: 21 = ______",
        "einundzwanzig",
        "21 è einundzwanzig: ein + und + zwanzig. L'unità viene prima della decina e le due "
        "parole si scrivono attaccate.",
        "Ventuno: in tedesco «uno e venti».",
        "21 = einundzwanzig, scritto tutto attaccato.",
    ),
    completion(
        "In Worten: 99 = ______",
        "neunundneunzig",
        "99 = neun + und + neunzig: unità, und, decina. Due volte neun, ma solo la decina "
        "prende -zig.",
        "Novantanove: «nove e novanta».",
        "99 = neunundneunzig.",
    ),
    completion(
        "In Worten: 100 = ______",
        "hundert",
        "100 è hundert (oppure einhundert). «einhundert» è la forma più lunga, entrambe sono "
        "corrette.",
        "Cento: una parola sola.",
        "100 = hundert / einhundert.",
        accept=("einhundert",),
    ),

    # --- choice ----------------------------------------------------------------------
    choice(
        "In Worten: 14 = ______",
        "vierzehn",
        ("vierzehn", "vierzig", "vierzeht", "vierzen"),
        "14 è vier + zehn = vierzehn. «vierzig» è 40, e la desinenza dei numeri 13–19 è "
        "sempre -zehn.",
        "Quattordici: vier + zehn.",
        "13–19 finiscono in -zehn; le decine in -zig.",
    ),
    choice(
        "In Worten: 40 = ______",
        "vierzig",
        ("vierzig", "vierzehn", "vierzich", "fierzig"),
        "Le decine finiscono in -zig, con la z: vierzig. «vierzehn» è 14.",
        "Quaranta è una decina: -zig.",
        "40 = vierzig, 14 = vierzehn.",
    ),
    choice(
        "In Worten: 32 = ______",
        "zweiunddreißig",
        ("zweiunddreißig", "dreißigundzwei", "zweizigunddrei", "zweiunddreizig"),
        "32 = zwei + und + dreißig: unità, und, decina. La decina tiene la sua ß: dreißig.",
        "Trentadue: in tedesco «due e trenta».",
        "32 = zweiunddreißig.",
    ),
    choice(
        "7 + 8 = ______",
        "fünfzehn",
        ("fünfzehn", "sechzehn", "fünfzig", "vierzehn"),
        "7 + 8 = 15, cioè fünfzehn (fünf + zehn). «fünfzig» è 50.",
        "Sette più otto fa quindici.",
        "15 = fünfzehn; 50 = fünfzig.",
    ),
    choice(
        "Die Zahl zwischen 29 und 31 ist ______.",
        "dreißig",
        ("dreißig", "dreizig", "dreisig", "dreißich"),
        "30 è dreißig: la ß sta dopo la vocale lunga e la desinenza è -ig. «dreizehn» è 13.",
        "Trenta: la lettera ß.",
        "dreißig (30), dreizehn (13).",
    ),
    choice(
        "In Worten: 66 = ______",
        "sechsundsechzig",
        ("sechsundsechzig", "sechzigundsechs", "sechsundsechszig", "sechzigsechs"),
        "66 = sechs + und + sechzig. Il primo sechs tiene la -s, la decina no: sechzig.",
        "Sessantasei: unità sechs, decina sechzig.",
        "sechs (6) → sechzig (60) → sechsundsechzig (66).",
    ),
    choice(
        "In Worten: 80 = ______",
        "achtzig",
        ("achtzig", "achtzehn", "achtzich", "achtzg"),
        "80 è achtzig; 18 è achtzehn. La -zehn è per i numeri da 13 a 19, la -zig per le "
        "decine.",
        "Ottanta è una decina.",
        "80 = achtzig, 18 = achtzehn.",
    ),
    choice(
        "In Worten: 70 = ______",
        "siebzig",
        ("siebzig", "siebenzig", "siebzehn", "siebzich"),
        "70 è siebzig: come 17 (siebzehn), anche 70 perde la -en di sieben.",
        "Settanta, come 17: sieben perde la -en.",
        "sieben (7) → siebzehn (17), siebzig (70).",
    ),
    choice(
        "Die Zahl nach 99 ist ______.",
        "hundert",
        ("hundert", "neunzig", "neunundneunzig", "einhundertundeins"),
        "Dopo 99 viene 100 = hundert. «neunzig» è 90 e «neunundneunzig» è 99.",
        "Dopo novantanove viene cento.",
        "99 = neunundneunzig, 100 = hundert.",
    ),
)


class Zahlen(GermanPractice):
    id = "german.zahlen"
    label_key = "topic.german_zahlen"
    cards = CARDS


TOPIC = Zahlen()
