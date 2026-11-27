"""La scheda dei polinomi: UNA pagina, due sezioni, le otto formule del suo PDF.

PERCHÉ QUESTO FILE ESISTE. La scheda dei radicali ha una storia di difetti che
hanno tutti la stessa forma — una formula che c'era e non c'è più, e un
controllo che non se ne accorgeva — e la lezione è scritta in
``tests/test_schede_radicali.py``: si confronta col **PDF dell'operatore**,
formula per formula, e si misura il **contenuto**, non l'inchiostro. Questo
file fa lo stesso per la seconda scheda, e ci aggiunge la cosa nuova che
l'operatore ha chiesto il 27/11/2026: **le frecce curve**, che devono stare
nella libreria e devono VEDERSI.

Le prove, in ordine:

1. **Il termine di confronto è SUO**: ``tests/golden/schede/polinomi-operatore.pdf``,
   115964 byte, Chromium — non una nostra compilazione.
2. **Il contenuto, cella per cella** (``FORMULE``): per ognuna delle otto
   righe, gli atomi che la cella «schema» e la cella «regola» devono portare,
   letti dal PDF compilato DAL SORGENTE.
3. **Il disegno**: le forme sono TikZ e nel testo non ci sono; per ogni cella
   di schema si contano i pixel disegnati a 200 dpi.
4. **Il confronto col suo PDF**: le sue otto righe ci sono tutte, nello stesso
   ordine, con gli atomi dichiarati, e con il disegno.
5. **Le regole in parole sono le sue**, parola per parola.
6. **Le frecce curve**: ``\\frecciaCurva`` esiste in ``schede.sty``, la scheda
   la usa otto volte, e togliendole dal sorgente l'inchiostro delle due righe
   che le portano scende — cioè si vedono, e la prova sa fallire.
7. **La mappatura delle forme**: le tre forme della palette, il rombo grigio e
   il rombo grigio piccolo; nessun colore nuovo, nessuna forma inventata.

Gli strumenti di misura sono quelli di ``tests/test_schede_radicali.py``,
copiati qui: la scheda dei radicali non si tocca (ordine dell'operatore), e un
secondo foglio che misura la stessa pagina deve poter cambiare senza
rischiare di rompere il primo.
"""

from __future__ import annotations

import collections
import hashlib
import re
import shutil
import subprocess
from pathlib import Path

import pytest

RADICE = Path(__file__).resolve().parents[1]
SCHEDE = RADICE / "schede"
SORGENTE = SCHEDE / "polinomi" / "polinomi.tex"
COMMITTATO = SCHEDE / "polinomi" / "polinomi.pdf"
LIBRERIA = SCHEDE / "schede.sty"

# IL PDF DELL'OPERATORE: «Operazioni con i Polinomi — Schema Visivo», 115964
# byte, Chromium/Skia, una pagina, consegnato il 27/11/2026. È il metro, non
# un'ispirazione: lo sha256 è qui perché un golden che nessuno identifica è un
# golden che può diventare una copia di noi stessi.
SUO_PDF = RADICE / "tests" / "golden" / "schede" / "polinomi-operatore.pdf"
SUO_BYTE = 115964
SUO_SHA256 = "b641a63ad1a56928e97a9c522cebdf8a6b2c8896ea2c0dee87879c069743a3f7"

PAGINE = 1

# Le due sezioni, con le sue parole e nell'ordine del suo foglio.
SEZIONI = (
    "1. Operazioni con i Polinomi",
    "2. Prodotti Notevoli",
)

# Le parole d'intestazione che aprono la seconda e la terza colonna: da lì si
# trovano i confini delle celle, uguali per il nostro PDF e per il suo
# (l'intestazione della terza colonna cambia fra le due sezioni — «Regola a
# parole» e «Sviluppo a parole» — ma la parola «parole» sta nella stessa
# colonna in tutte e due).
COLONNE = ("schema", ("regola", "sviluppo"))
# Il suo foglio ha DUE colonne: il nome dell'operazione e una cella sola che
# porta lo schema E la regola in parole.
SUE_COLONNE = ("schema",)

# ---------------------------------------------------------------------------
# LE OTTO FORMULE, una per una — le sue otto.
#
# `schema`: gli atomi di TESTO che la cella dello schema deve portare. Le
# forme sono disegnate e non compaiono nel testo estratto: quello che si può
# pretendere sono le parentesi, i segni, gli esponenti.
# `regola`: le parole della regola che stanno accanto alla formula.
# `sua`: la regola come l'ha scritta lui, parola per parola.
# ---------------------------------------------------------------------------
FORMULE = (
    # --- 1. Operazioni con i polinomi ---------------------------------------
    {
        "voce": "Somma di polinomi",
        "sezione": 1,
        "schema": ("(", ")", "+", "="),
        "regola": ("stesso", "segno"),
        "sua": "Con il + davanti alla parentesi si tolgono parentesi e + e si "
               "copiano i monomi con lo stesso segno.",
        "perche": "con il + davanti alla parentesi i segni non cambiano",
    },
    {
        "voce": "Sottrazione di polinomi",
        "sezione": 1,
        "schema": ("(", ")", "+", "−", "="),
        "regola": ("cambiando", "segno"),
        "sua": "Con il − davanti alla parentesi si tolgono parentesi e − e si "
               "copiano i monomi cambiando segno.",
        "perche": "con il − davanti alla parentesi i segni si cambiano",
    },
    {
        "voce": "Monomio per polinomio",
        "sezione": 1,
        "schema": ("(", ")", "+", "="),
        "regola": ("esponenti", "lettere"),
        "sua": "Si moltiplicano i numeri e si sommano gli esponenti delle "
               "lettere uguali; le lettere sole si copiano.",
        "perche": "il monomio moltiplica ogni termine del polinomio",
    },
    {
        "voce": "Polinomio per polinomio",
        "sezione": 1,
        "schema": ("(", ")", "+", "="),
        "regola": ("moltiplica", "termini"),
        "sua": "Ogni termine del 1° polinomio moltiplica tutti i termini del 2° "
               "(sommando gli esponenti delle lettere uguali).",
        "perche": "ogni termine del primo moltiplica tutti i termini del secondo",
    },
    # --- 2. Prodotti notevoli ----------------------------------------------
    {
        "voce": "Quadrato di binomio",
        "sezione": 2,
        "schema": ("(", ")", "+", "=", "2"),
        "regola": ("doppio", "prodotto", "quadrato"),
        "sua": "Quadrato del 1°, doppio prodotto del 1° per il 2°, quadrato del 2°.",
        "perche": "quadrato del primo, doppio prodotto, quadrato del secondo",
    },
    {
        "voce": "Differenza di quadrati",
        "sezione": 2,
        "schema": ("(", ")", "+", "−", "=", "2"),
        "regola": ("cambia", "segno", "meno"),
        "sua": "Quadrato del termine che non cambia segno meno quadrato del "
               "termine che cambia segno.",
        "perche": "somma per differenza: il quadrato del termine che cambia segno "
                  "si toglie",
    },
    {
        "voce": "Cubo di binomio",
        "sezione": 2,
        "schema": ("(", ")", "+", "=", "2", "3"),
        "regola": ("triplo", "cubo"),
        "sua": "Cubo del 1°, triplo prodotto del quadrato del 1° per il 2°, "
               "triplo prodotto del 1° per il quadrato del 2°, cubo del 2°.",
        "perche": "cubo del primo, triplo prodotto, triplo prodotto, cubo del secondo",
    },
    {
        "voce": "Quadrato di trinomio",
        "sezione": 2,
        "schema": ("(", ")", "+", "=", "2"),
        "regola": ("tre", "quadrati", "doppi", "prodotti"),
        "sua": "Somma dei tre quadrati più i tre doppi prodotti delle possibili coppie.",
        "perche": "tre quadrati più i tre doppi prodotti delle coppie",
    },
)

# Le righe che portano le frecce curve, e quante ne porta ognuna come nel suo
# foglio: due archi dal monomio (uno per ogni termine del polinomio) e sei dal
# prodotto di due polinomi (tre per ciascuno dei due termini, sopra e sotto).
FRECCE = {
    "Monomio per polinomio": 2,
    "Polinomio per polinomio": 6,
}

# Il minimo di pixel disegnati (a 200 dpi) sotto il quale una cella di schema è
# VUOTA.
MINIMO_CELLA = 600

# Quanto può valere l'inchiostro della nostra cella rispetto a quella del suo
# PDF. NON è una misura del contenuto (quello lo fanno gli atomi): la sua cella
# porta anche la regola in parole, quindi il confronto è di ordine di grandezza
# e serve a vedere una formula che sparisce, non a pesare l'inchiostro.
RAPPORTO_MIN, RAPPORTO_MAX = 0.15, 5.0


# ------------------------------------------------------------------ strumenti


def _serve(*programmi: str) -> None:
    mancanti = [p for p in programmi if shutil.which(p) is None]
    if mancanti:
        pytest.skip(f"manca {', '.join(mancanti)} (TeX Live / poppler): la prova non è eseguibile qui")


def os_environ() -> dict[str, str]:
    import os

    return dict(os.environ)


def costruisci(destinazione: Path, testo: str | None = None) -> Path:
    """Compila la scheda in ``destinazione``; ``testo`` sostituisce il sorgente."""
    _serve("pdflatex")
    destinazione.mkdir(parents=True, exist_ok=True)
    sorgente = testo if testo is not None else SORGENTE.read_text(encoding="utf-8")
    (destinazione / "polinomi.tex").write_text(sorgente, encoding="utf-8")
    ambiente = {**os_environ(), "TEXINPUTS": f".:{SCHEDE}:"}
    for _ in range(2):  # due passate: la seconda serve al «Pagina n di N» del piede
        esito = subprocess.run(
            ["pdflatex", "-interaction=nonstopmode", "-halt-on-error", "polinomi.tex"],
            cwd=destinazione,
            env=ambiente,
            capture_output=True,
            text=True,
        )
        if esito.returncode != 0:
            coda = "\n".join(esito.stdout.splitlines()[-15:])
            pytest.fail(f"pdflatex è uscito {esito.returncode}:\n{coda}")
    return destinazione / "polinomi.pdf"


def estrai_testo(pdf: Path) -> str:
    _serve("pdftotext")
    esito = subprocess.run(["pdftotext", str(pdf), "-"], capture_output=True, text=True)
    assert esito.returncode == 0, esito.stderr
    return esito.stdout


def normale(contenuto: str) -> str:
    """Il testo con gli spazi ridotti a uno: le andate a capo non contano."""
    return " ".join(contenuto.split())


def segni(contenuto: str) -> str:
    """Il testo con i segni staccati dalle lettere: «=(» diventa «= ( ».

    Nella formula le parentesi e i segni stanno attaccati alle forme, e
    pdftotext li lega in un token solo («=(», «)(», «)+(»): così un atomo come
    «=» non si troverebbe, pur essendo stampato. Qui ogni segno è una parola.
    """
    return " ".join(re.sub(r"([()=+−])", r" \1 ", contenuto).split())


def caratteri(contenuto: str) -> collections.Counter[str]:
    """Il contenuto come multinsieme di caratteri: gli spazi (e gli a-capo) fuori."""
    return collections.Counter(c for c in contenuto.replace("\u00a0", " ") if not c.isspace())


def pagine(pdf: Path) -> int:
    _serve("pdfinfo")
    esito = subprocess.run(["pdfinfo", str(pdf)], capture_output=True, text=True)
    trovato = re.search(r"^Pages:\s+(\d+)$", esito.stdout, re.MULTILINE)
    assert trovato, "pdfinfo non ha detto quante pagine ha il PDF"
    return int(trovato.group(1))


def pagine_e_parole(pdf: Path) -> tuple[float, float, list[tuple[str, float, float, float, float]]]:
    """Il lato della pagina e le parole con la loro posizione (pdftotext -bbox)."""
    _serve("pdftotext")
    esito = subprocess.run(["pdftotext", "-bbox", str(pdf), "-"], capture_output=True, text=True)
    assert esito.returncode == 0, esito.stderr
    pagina = re.search(r'<page width="([\d.]+)" height="([\d.]+)">', esito.stdout)
    assert pagina, "pdftotext -bbox non ha dichiarato la pagina"
    larghezza, altezza = float(pagina.group(1)), float(pagina.group(2))
    parole = [
        (m.group(5), float(m.group(1)), float(m.group(2)), float(m.group(3)), float(m.group(4)))
        for m in re.finditer(
            r'<word xMin="([\d.]+)" yMin="([\d.]+)" xMax="([\d.]+)" yMax="([\d.]+)">(.*?)</word>',
            esito.stdout,
        )
    ]
    return larghezza, altezza, parole


def _ppm(pdf: Path, cartella: Path, dpi: int) -> tuple[int, int, bytes]:
    """La pagina resa in un PPM grezzo (P6): larghezza, altezza e i pixel RGB."""
    _serve("pdftoppm")
    cartella.mkdir(parents=True, exist_ok=True)
    base = cartella / f"scheda-{dpi}"
    esito = subprocess.run(
        ["pdftoppm", "-r", str(dpi), "-singlefile", str(pdf), str(base)],
        capture_output=True,
        text=True,
    )
    assert esito.returncode == 0, esito.stderr
    dati = base.with_suffix(".ppm").read_bytes()
    assert dati[:2] == b"P6", f"pdftoppm ha scritto {dati[:2]!r}, non un PPM grezzo (P6)"
    campi: list[int] = []
    posizione = 2
    while len(campi) < 3:
        while posizione < len(dati) and dati[posizione : posizione + 1].isspace():
            posizione += 1
        if dati[posizione : posizione + 1] == b"#":  # un commento fino a fine riga
            while dati[posizione : posizione + 1] not in (b"\n", b""):
                posizione += 1
            continue
        inizio = posizione
        while dati[posizione : posizione + 1].isdigit():
            posizione += 1
        campi.append(int(dati[inizio:posizione]))
    posizione += 1  # un solo spazio dopo il massimo
    larghezza, altezza, massimo = campi
    assert massimo < 256, f"PPM a {massimo} livelli: atteso 8 bit per canale"
    pixel = dati[posizione : posizione + larghezza * altezza * 3]
    assert len(pixel) == larghezza * altezza * 3, "PPM troncato: i pixel non tornano"
    return larghezza, altezza, pixel


def _filetti(pixel: bytes, larghezza: int, altezza: int, x0: int, x1: int) -> list[tuple[int, int]]:
    """Le righe di separazione della tabella: scure da bordo a bordo, non testo.

    La soglia è 230 e non 250 perché il foglio dell'operatore ha le righe
    colorate: il fondo azzurro (239) e quello crema (251) coprono tutta la
    larghezza della riga, e con una soglia alta sarebbero presi per filetti —
    le righe sparirebbero. I filetti veri sono più scuri: 203-213 nel suo
    foglio, 212 nel nostro.
    """
    soglia = 0.93 * (x1 - x0)
    marche = [
        y
        for y in range(altezza)
        if sum(1 for k in range(x0 * 3, x1 * 3, 3) if pixel[y * larghezza * 3 + k] < 230) > soglia
    ]
    gruppi: list[list[int]] = []
    for y in marche:
        if gruppi and y - gruppi[-1][-1] <= 3:
            gruppi[-1].append(y)
        else:
            gruppi.append([y])
    return [(gruppo[0], gruppo[-1]) for gruppo in gruppi]


def _misura(
    pdf: Path,
    cartella: Path,
    formule: tuple[dict[str, object], ...] = FORMULE,
    colonne: tuple = COLONNE,
    dpi: int = 200,
    tollera_mancanti: bool = False,
) -> dict[str, dict[str, object]]:
    """Per ogni riga dell'elenco: il testo delle celle e l'inchiostro della formula.

    La riga si trova DAL PDF — la posizione della parola che apre la cella
    «voce» — dentro la banda delimitata dai filetti della tabella; le colonne
    si trovano dalle intestazioni. Così la stessa misura vale per il nostro PDF
    (tre colonne) e per quello dell'operatore (due).
    """
    larghezza_pt, _altezza_pt, parole = pagine_e_parole(pdf)
    larghezza, altezza, pixel = _ppm(pdf, cartella, dpi)
    per_pt = larghezza / larghezza_pt  # pixel per punto tipografico

    colonne_ink = [
        sum(1 for y in range(altezza) if pixel[(y * larghezza + x) * 3] < 200)
        for x in range(larghezza)
    ]
    x0 = min(x for x, quante in enumerate(colonne_ink) if quante > altezza * 0.02)
    x1 = max(x for x, quante in enumerate(colonne_ink) if quante > altezza * 0.02)
    filetti = _filetti(pixel, larghezza, altezza, x0, x1)
    bande = [(filetti[i][1], filetti[i + 1][0]) for i in range(len(filetti) - 1)]

    def intestazione(parola) -> float:
        """La x della parola d'intestazione che apre la colonna.

        Può essere più d'una («Regola a parole» nella prima sezione,
        «Sviluppo a parole» nella seconda: la colonna è la stessa, la parola
        cambia) e si prende la prima che si trova.
        """
        alternative = parola if isinstance(parola, tuple) else (parola,)
        # Solo le parole DENTRO la tabella: la stessa parola sta anche nel
        # titolo («I Polinomi: Schema Visivo») e nel piede («Schema di
        # Matematica»), e quelle non dicono dove comincia una colonna.
        inizio, fine = bande[0][0], bande[-1][1]
        dentro = [
            (x, y)
            for testo, x, y, _x1, _y1 in parole
            if any(testo.lower().startswith(a) for a in alternative)
            and inizio < (y + _y1) / 2 * per_pt < fine
        ]
        if not dentro:
            raise AssertionError(
                f"manca l'intestazione «{parola}»: le colonne non si possono misurare"
            )
        return min(x for x, _y in dentro) * per_pt

    limiti = (x0, *[intestazione(c) for c in colonne], x1)

    precedente = -1.0
    misure: dict[str, dict[str, object]] = {}
    for formula in formule:
        prima = str(formula["voce"]).split()[0]
        candidate = sorted(
            y for testo, _x, y, _x1, _y1 in parole if testo == prima and y > precedente
        )
        if not candidate:
            assert tollera_mancanti, f"manca la riga «{formula['voce']}» nel testo estratto"
            continue
        y = candidate[0]
        precedente = y
        banda = [(a, b) for a, b in bande if a < y * per_pt < b]
        assert banda, f"la riga «{formula['voce']}» non sta in nessuna banda della tabella"
        a, b = banda[0]

        def testo_cella(xa: float, xb: float) -> str:
            # «≠» nel PDF è «=» con la barra sovrapposta (U+0338): qui le due
            # grafie diventano una, così la stessa dichiarazione vale per tutti
            # e due i PDF.
            return " ".join(
                testo
                for testo, px0, py0, px1, py1 in parole
                if xa <= (px0 + px1) / 2 * per_pt < xb and a < (py0 + py1) / 2 * per_pt < b
            ).replace("\u0338", "≠")

        def inchiostro(xa: float, xb: float) -> int:
            return sum(
                1
                for riga in range(a + 1, b)
                for k in range(int(xa) * 3, int(xb) * 3, 3)
                if pixel[riga * larghezza * 3 + k] < 200
            )

        misure[formula["voce"]] = {
            "celle": tuple(testo_cella(limiti[i], limiti[i + 1]) for i in range(len(limiti) - 1)),
            "inchiostro": tuple(inchiostro(limiti[i], limiti[i + 1]) for i in range(1, len(limiti) - 1)),
            "caratteri": tuple(
                caratteri(testo_cella(limiti[i], limiti[i + 1])) for i in range(len(limiti) - 1)
            ),
        }
    return misure


@pytest.fixture(scope="module")
def scheda(tmp_path_factory: pytest.TempPathFactory) -> Path:
    return costruisci(tmp_path_factory.mktemp("scheda"))


@pytest.fixture(scope="module")
def nostro(scheda: Path, tmp_path_factory: pytest.TempPathFactory) -> dict[str, dict[str, object]]:
    return _misura(scheda, tmp_path_factory.mktemp("misura"))


@pytest.fixture(scope="module")
def suo(tmp_path_factory: pytest.TempPathFactory) -> dict[str, dict[str, object]]:
    """Le stesse misure sul PDF dell'operatore: è il termine di confronto."""
    return _misura(
        SUO_PDF,
        tmp_path_factory.mktemp("suo"),
        FORMULE,
        colonne=SUE_COLONNE,
    )


# --------------------------------------------------------------------- le prove


def test_il_golden_e_il_pdf_dell_operatore() -> None:
    """Il termine di confronto è SUO, e si sa quale: 115964 byte, Chromium."""
    assert SUO_PDF.exists(), "manca il PDF dell'operatore in tests/golden/schede/"
    byte = SUO_PDF.read_bytes()
    assert len(byte) == SUO_BYTE, f"il PDF dell'operatore sono {len(byte)} byte, non {SUO_BYTE}"
    assert hashlib.sha256(byte).hexdigest() == SUO_SHA256, (
        "questo non è il PDF dell'operatore: è stato sostituito (con una nostra "
        "compilazione?). Il confronto deve essere col suo, non con una versione nostra"
    )
    assert b"/Skia" in byte or b"Chromium" in byte, "il PDF dell'operatore è uscito da Chromium"


def test_la_scheda_sta_in_una_pagina(scheda: Path) -> None:
    """Una pagina A4: è la richiesta dell'operatore, e il vincolo della scheda."""
    assert pagine(scheda) == PAGINE, "la scheda non sta in una pagina"


def test_le_due_sezioni_ci_sono_e_in_ordine(scheda: Path) -> None:
    """Operazioni con i polinomi, poi prodotti notevoli: le sue due sezioni."""
    contenuto = estrai_testo(scheda)
    posizioni = []
    for sezione in SEZIONI:
        assert sezione in contenuto, f"manca la sezione «{sezione}»"
        posizioni.append(contenuto.index(sezione))
    assert posizioni == sorted(posizioni), "le due sezioni non sono nell'ordine del suo foglio"


def test_ogni_formula_porta_i_suoi_atomi(nostro: dict[str, dict[str, object]]) -> None:
    """L'elenco, formula per una: ogni cella porta gli atomi che quella formula è.

    Un errore qui dice QUALE formula è monca e che cosa le manca.
    """
    guasti = []
    for formula in FORMULE:
        celle = nostro[formula["voce"]]["celle"]
        for indice, chiave in ((1, "schema"), (2, "regola")):
            for atomo in formula[chiave]:
                if atomo not in segni(celle[indice]):
                    guasti.append(
                        f"riga «{formula['voce']}» ({formula['perche']}), cella «{chiave}»: "
                        f"manca «{atomo}» — la cella dice {celle[indice]!r}"
                    )
    assert not guasti, "formule monche:\n" + "\n".join(guasti)


def test_le_regole_sono_le_sue_parola_per_parola(scheda: Path) -> None:
    """Le otto regole in parole sono quelle del suo foglio, non una nostra parafrasi.

    Il testo è confrontato sugli spazi ridotti a uno (le andate a capo della
    colonna non sono contenuto), ma le parole sono sue: se qualcuno riscrive una
    regola «meglio», questo test lo dice.
    """
    contenuto = normale(estrai_testo(scheda))
    mancanti = [
        f"la regola di «{f['voce']}» non è la sua: manca «{f['sua']}»"
        for f in FORMULE
        if normale(str(f["sua"])) not in contenuto
    ]
    assert not mancanti, "regole non sue:\n" + "\n".join(mancanti)


def test_ogni_formula_e_disegnata(nostro: dict[str, dict[str, object]]) -> None:
    """Le otto celle di schema hanno il loro disegno, a 200 dpi.

    È lo strato che il testo non può vedere: le forme e le frecce sono TikZ.
    Una formula che c'è nel sorgente ma non viene disegnata (colonna troppo
    stretta, pagina che trabocca) qui si vede.
    """
    vuote = [
        f"riga «{formula['voce']}»: {nostro[formula['voce']]['inchiostro'][0]} pixel disegnati"
        for formula in FORMULE
        if nostro[formula["voce"]]["inchiostro"][0] < MINIMO_CELLA
    ]
    assert not vuote, "celle di schema senza disegno:\n" + "\n".join(vuote)


def test_le_formule_del_suo_pdf_ci_sono_tutte(
    nostro: dict[str, dict[str, object]], suo: dict[str, dict[str, object]]
) -> None:
    """Confronto col PDF DELL'OPERATORE, riga per riga: le sue otto righe.

    Non è un confronto con una nostra versione precedente — è il difetto che ha
    fatto perdere la giornata del 26/11. Ogni riga della sua scheda deve esserci,
    portare gli stessi atomi di testo (la sua cella tiene schema e regola
    assieme) e avere il disegno: una formula che nella copiatura si è persa si
    vede qui, con il suo nome.
    """
    assert len(suo) == len(FORMULE), (
        f"nel suo PDF si sono trovate {len(suo)} righe su {len(FORMULE)}: "
        "la misura non sa leggere il suo foglio"
    )
    guasti = []
    for formula in FORMULE:
        nome = formula["voce"]
        suo_testo = segni(" ".join(suo[nome]["celle"]))
        for chiave in ("schema", "regola"):
            for atomo in formula[chiave]:
                if atomo not in suo_testo:
                    guasti.append(
                        f"l'elenco dichiara «{atomo}» per «{nome}»/{chiave}, "
                        "ma nel PDF dell'operatore non c'è: l'elenco non descrive il suo documento"
                    )
        suo_inchiostro = suo[nome]["inchiostro"][0]
        nostro_inchiostro = nostro[nome]["inchiostro"][0]
        if suo_inchiostro <= 0:
            guasti.append(f"riga «{nome}»: nel suo PDF la cella non ha disegno")
            continue
        rapporto = nostro_inchiostro / suo_inchiostro
        if not RAPPORTO_MIN <= rapporto <= RAPPORTO_MAX:
            guasti.append(
                f"riga «{nome}»: la nostra cella disegna {nostro_inchiostro} pixel "
                f"contro i {suo_inchiostro} del suo PDF (rapporto {rapporto:.2f}, "
                f"la banda è {RAPPORTO_MIN}–{RAPPORTO_MAX})"
            )
    assert not guasti, "il confronto col PDF dell'operatore non torna:\n" + "\n".join(guasti)


def test_il_pdf_committato_e_quello_che_il_sorgente_produce(scheda: Path) -> None:
    """Il PDF in repository non deve essere un artefatto vecchio."""
    assert COMMITTATO.exists(), "manca schede/polinomi/polinomi.pdf (make in schede/polinomi)"
    committato = caratteri(estrai_testo(COMMITTATO))
    dal_sorgente = caratteri(estrai_testo(scheda))
    assert committato == dal_sorgente, (
        "il PDF committato non è quello che il .tex produce — ricompila con "
        "`make -C schede/polinomi`"
    )


# ------------------------------------------------------ le frecce curve, nuove


def test_la_libreria_ha_il_comando_delle_frecce_curve() -> None:
    """`\\frecciaCurva` esiste nella LIBRERIA, e prende due ancore.

    L'operatore l'ha chiesto perché la prossima scheda le riusa senza
    ridisegnarle (27/11/2026): se il comando vivesse dentro la scheda dei
    polinomi, la richiesta sarebbe tradita.
    """
    libreria = LIBRERIA.read_text(encoding="utf-8")
    assert "\\newcommand{\\frecciaCurva}[3][]" in libreria, (
        "schede.sty non definisce \\frecciaCurva[opzioni]{partenza}{arrivo}"
    )
    assert "\\newenvironment{schedaFrecce}" in libreria, "manca l'ambiente schedaFrecce"
    assert "\\newcommand{\\termine}[3][0pt]" in libreria, "manca \\termine[spazio]{nome}{pezzo}"


def test_la_scheda_usa_le_frecce_curve() -> None:
    """Le due righe che le portano, con il numero di archi del suo foglio."""
    sorgente = SORGENTE.read_text(encoding="utf-8")
    for voce, quante in FRECCE.items():
        # la riga della scheda: dalla sua voce fino alla riga dopo
        dove = sorgente.index(f"\\voce{{{voce}}}")
        fine = sorgente.index("\\riga{", dove + 1)
        pezzo = sorgente[dove:fine]
        quante_qui = pezzo.count("\\frecciaCurva[")
        assert quante_qui == quante, (
            f"la riga «{voce}» porta {quante_qui} frecce curve, "
            f"il suo foglio ne ha {quante}"
        )
        assert "\\begin{schedaFrecce}" in pezzo, (
            f"la riga «{voce}» porta frecce curve fuori dall'ambiente schedaFrecce: "
            "senza i pezzi con un nome non hanno due ancore"
        )
    assert SORGENTE.read_text(encoding="utf-8").count("\\frecciaCurva[") == sum(FRECCE.values()), (
        "il numero di frecce curve della scheda non è quello dichiarato"
    )


def test_le_frecce_curve_si_vedono(tmp_path: Path, nostro: dict[str, dict[str, object]]) -> None:
    """Tolte le frecce dal sorgente, l'inchiostro delle due righe cala: si vedono.

    Non basta che il comando sia chiamato: deve DISEGNARE. Si ricompila la
    scheda senza le righe `\\frecciaCurva` e si misurano le stesse celle: le due
    che le portavano perdono inchiostro, le altre sei non cambiano di un pixel.
    """
    sorgente = SORGENTE.read_text(encoding="utf-8")
    senza = "\n".join(
        riga for riga in sorgente.splitlines() if "\\frecciaCurva[" not in riga
    )
    assert "\\frecciaCurva[" not in senza

    pdf = costruisci(tmp_path / "senza_frecce", senza)
    assert pagine(pdf) == PAGINE
    misure = _misura(pdf, tmp_path / "misura-senza-frecce")

    for voce in FRECCE:
        con = int(nostro[voce]["inchiostro"][0])
        senza_frecce = int(misure[voce]["inchiostro"][0])
        # Le frecce pesano l'8-20% dell'inchiostro della cella (misurato il
        # 27/11: 12,2% e 18,3%): sotto l'8% non stanno disegnando.
        assert senza_frecce < con * 0.92, (
            f"riga «{voce}»: senza le frecce la cella disegna {senza_frecce} pixel "
            f"contro {con} con le frecce — le frecce non si vedono"
        )
    for formula in FORMULE:
        voce = str(formula["voce"])
        if voce in FRECCE:
            continue
        con = int(nostro[voce]["inchiostro"][0])
        senza_frecce = int(misure[voce]["inchiostro"][0])
        # Le altre righe non hanno frecce: togliendole dalla scheda la loro
        # misura può solo ballare di qualche pixel (la tabella si accorcia e i
        # pixel si spostano sotto il retino), non cambiare di sostanza.
        assert abs(con - senza_frecce) <= 0.04 * con, (
            f"riga «{voce}»: togliere le frecce da un'altra riga ne ha cambiato "
            f"l'inchiostro ({con} -> {senza_frecce})"
        )


def test_le_frecce_curve_hanno_la_punta_e_il_colore_della_casa() -> None:
    """La punta è quella di `\\freccia` (Stealth 2.8×2.4) e i colori sono i nostri.

    Le frecce della casa sono grigie; l'arco prende un colore della PALETTE solo
    quando deve dire da quale termine parte (blu il quadrato, rosso il
    triangolo) — un colore nuovo non si inventa.
    """
    libreria = LIBRERIA.read_text(encoding="utf-8")
    assert "Stealth[length=2.8pt,width=2.4pt]" in libreria
    scheda = SORGENTE.read_text(encoding="utf-8")
    assert "colore=schedeBlu" in scheda, "gli archi del primo termine non sono blu come il quadrato"
    assert "colore=schedeRosso" in scheda, "gli archi del secondo termine non sono rossi come il triangolo"
    assert "colore=schedeGrigio" not in scheda
    assert "\\definecolor" not in scheda, "la scheda si definisce un colore: la palette sta nella libreria"


# ------------------------------------------------- la mappatura delle forme


def test_le_forme_sono_quelle_della_palette() -> None:
    """Le cinque forme del suo foglio, mappate su tre forme e sul grigio.

    Il suo foglio usa quadrato blu, triangolo arancio-rosso, cerchio verde,
    rombo viola e un quadrato rosa arrotondato. La casa ha tre forme con il
    colore dentro e il grigio per tutto il resto: la mappatura è

        quadrato blu            -> \\formaQuadrato
        triangolo arancio-rosso -> \\formaTriangolo
        cerchio verde           -> \\formaCerchio
        rombo viola             -> \\formaRombo
        quadrato rosa           -> \\formaRombo[0.7]   (grigio, più piccolo)

    e non aggiunge né un colore né una forma: se qualcuno inventa
    `\\formaQuadratoRosa`, questo test lo dice.
    """
    scheda = SORGENTE.read_text(encoding="utf-8")
    for comando in ("\\formaQuadrato", "\\formaTriangolo", "\\formaCerchio", "\\formaRombo"):
        assert comando in scheda, f"la scheda non usa {comando}"
    assert "\\formaRombo[0.7]" in scheda, (
        "la quinta forma del suo foglio (il quadrato rosa) non è mappata sul rombo grigio piccolo"
    )
    forme_usate = set(re.findall(r"\\forma[A-Za-z]+", scheda))
    assert forme_usate == {
        "\\formaQuadrato",
        "\\formaTriangolo",
        "\\formaCerchio",
        "\\formaRombo",
    }, f"la scheda usa forme che non sono nella palette: {sorted(forme_usate)}"


# ------------------------------------------------- le due prove che sanno fallire


def test_il_confronto_col_suo_pdf_sa_fallire(
    tmp_path: Path, suo: dict[str, dict[str, object]]
) -> None:
    """Tolta una riga dal sorgente, la misura non la trova più.

    Si toglie «Quadrato di trinomio» — la formula più lunga — e si ricompila.
    Se questo test passasse, il confronto sarebbe cieco.
    """
    sorgente = SORGENTE.read_text(encoding="utf-8")
    inizio = sorgente.index("\\riga{\\voce{Quadrato di trinomio}{}}")
    fine = sorgente.index("\\end{schedaTabella}", inizio)
    mutilato = sorgente[:inizio] + sorgente[fine:]
    assert "Quadrato di trinomio" not in mutilato, "la riga non è stata tolta dal sorgente"

    pdf = costruisci(tmp_path / "mutilato", mutilato)
    assert pagine(pdf) == 1, "tolta una riga la scheda deve stare in una pagina comunque"
    misure = _misura(pdf, tmp_path / "misura-mutilata", tollera_mancanti=True)
    assert "Quadrato di trinomio" not in misure, (
        "tolta la riga «Quadrato di trinomio» la misura l'ha ancora trovata: "
        "è lo stesso controllo cieco del 26/11"
    )


def test_la_misura_del_disegno_sa_fallire(tmp_path: Path) -> None:
    """Svuotata UNA cella di schema, la misura del disegno la vede."""
    sorgente = SORGENTE.read_text(encoding="utf-8")
    inizio = sorgente.index("\\riga{\\voce{Cubo di binomio}{}}")
    fine = sorgente.index("\\riga{\\voce{Quadrato di trinomio}{}}", inizio)
    riga = sorgente[inizio:fine]
    # la SECONDA graffa della \riga è lo schema: si svuota quella, non la riga.
    gruppi: list[tuple[int, int]] = []
    posizione = 0
    while len(gruppi) < 3:
        inizio_gruppo = riga.index("{", posizione)
        livello, dove = 0, inizio_gruppo
        while True:
            if riga[dove] == "{":
                livello += 1
            elif riga[dove] == "}":
                livello -= 1
                if livello == 0:
                    break
            dove += 1
        gruppi.append((inizio_gruppo, dove + 1))
        posizione = dove + 1
    inizio_argomento, fine_argomento = gruppi[1]
    mutilata = riga[:inizio_argomento] + "{$\\;\\,$}" + riga[fine_argomento:]
    mutilato = sorgente[:inizio] + mutilata + sorgente[fine:]

    pdf = costruisci(tmp_path / "cella_vuota", mutilato)
    assert pagine(pdf) == 1
    misure = _misura(pdf, tmp_path / "misura-vuota")
    inchiostro = int(misure["Cubo di binomio"]["inchiostro"][0])
    assert inchiostro < MINIMO_CELLA, (
        f"svuotata la cella dello schema della riga «Cubo di binomio» la misura "
        f"conta ancora {inchiostro} pixel: la misura del disegno non sa fallire"
    )
