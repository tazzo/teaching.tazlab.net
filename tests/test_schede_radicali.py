"""La scheda dei radicali: UNA pagina, tre sezioni, e le formule di entrambe.

PERCHÉ QUESTO FILE ESISTE (26/11/2026, rifatto). La scheda dei radicali ha una
storia di difetti che hanno tutti la stessa forma: una formula che c'era e non
c'è più, e un controllo che non se ne accorgeva.

* il primo controllo contava le righe del ``.tex`` e le righe di
  ``pdftotext``: una formula tolta DENTRO una riga non cambia nessuno dei due;
* il secondo confrontava il testo con una NOSTRA versione precedente: se la
  formula era già sparita prima, il confronto era verde — e la giornata è
  andata persa a rifare la scheda sul PDF dell'operatore per scoprirlo;
* il terzo misurava l'inchiostro per colonna: una formula tolta sposta i pixel
  dell'1%, che sta dentro ogni tolleranza.

Qui il confronto è col **PDF originale dell'operatore** — il Chromium «Schema
sui Radicali: Campo di Esistenza e Operazioni», 124364 byte, che sta in
``tests/golden/schede/radicali-operatore.pdf`` e il cui sha256 è scritto qui
sotto: se qualcuno lo scambia con una nostra compilazione, il test lo dice — e
la misura è il **contenuto**, formula per formula:

1. **L'ELENCO DELLE FORMULE** (``FORMULE``): undici righe, ognuna con le due
   celle di formula (schema ed esempio) e gli atomi di testo che quella
   formula DEVE portare. Si controlla cella per cella, sulla scheda compilata
   dal sorgente: un atomo mancante dice QUALE formula è monca.
2. **IL DISEGNO**: le forme, il segno di radice e le frecce sono TikZ e nel
   testo non ci sono. Per ognuna delle ventidue celle di formula si contano i
   pixel disegnati a **200 dpi**: una cella piena ne ha centinaia, una cella
   svuotata (o una formula che non viene disegnata perché non c'è spazio) ne
   ha zero.
3. **IL SUO PDF**: per le otto righe che vengono dalla sua scheda (campo di
   esistenza e operazioni) le stesse misure si fanno sul PDF dell'operatore, e
   si confrontano: le sue righe ci sono tutte, nello stesso ordine, gli atomi
   che l'elenco dichiara ci sono anche nel suo, e l'inchiostro della nostra
   cella sta dentro una banda dichiarata rispetto al suo. È il confronto che
   mancava: col PDF SUO, non con una nostra versione.

Le ultime due prove sono le più importanti: **il controllo sa fallire**. Si
toglie una riga dal sorgente e si svuota una cella, e si verifica che ENTRAMBI
gli strati se ne accorgano. Un test che non può fallire non è una prova.

Il test costruisce la scheda DAL SORGENTE e non guarda il PDF committato: un
artefatto vecchio in repository non deve poter far passare un sorgente rotto —
e c'è un test apposta che il PDF committato sia quello che il sorgente produce.
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
SORGENTE = SCHEDE / "radicali" / "radicali.tex"
COMMITTATO = SCHEDE / "radicali" / "radicali.pdf"

# IL PDF DELL'OPERATORE. Non è una nostra compilazione e non si tocca: è il
# documento che la scheda deve riprodurre (campo di esistenza e operazioni).
# 124364 byte, Chromium/Skia, «Schema sui Radicali: Campo di Esistenza e
# Operazioni», caricato il 26/11/2026. Lo sha256 è qui perché un golden che
# nessuno identifica è un golden che può diventare una copia di noi stessi.
SUO_PDF = RADICE / "tests" / "golden" / "schede" / "radicali-operatore.pdf"
SUO_SHA256 = "1f8c5cdf76061f82fc6831f9cca965868de577919a5bc6a6aac1c8b6874fe544"

# Il numero di pagine: la richiesta dell'operatore, e il vincolo della scheda.
PAGINE = 1

# Le tre sezioni, nell'ordine in cui si studiano.
SEZIONI = (
    "1. Campo di Esistenza (CE)",
    "2. Operazioni con i Radicali (Casi Semplici)",
    "3. Semplificazione: la Proprietà Invariantiva",
)

# ---------------------------------------------------------------------------
# L'ELENCO DELLE FORMULE, una per una.
#
# Per ogni riga: il titolo della cella «voce» (il testo che si legge a
# sinistra), la sezione, e — per le due celle di formula — gli atomi che il
# testo estratto DEVE portare. Gli atomi sono quelli che nel PDF sono CARATTERI:
# le forme, il segno di radice e le frecce sono disegnati (li misura il test
# dell'inchiostro), quindi non si possono pretendere nel testo.
#
# `dal_suo`: la formula viene dal PDF dell'operatore (sezioni 1 e 2) e va
# confrontata con lui. Senza il segno, viene dalla seconda scheda (la
# semplificazione), che l'operatore ci ha chiesto di fondere qui.
# ---------------------------------------------------------------------------
FORMULE = (
    # --- 1. Campo di esistenza ---------------------------------------------
    {
        "voce": "Indice pari",
        "sezione": 1,
        "dal_suo": True,
        "schema": ("≥", "0"),
        "esempio": ("≥", "0", "4"),
        "perche": "radice di indice pari: il radicando deve essere ≥ 0",
    },
    {
        "voce": "Indice dispari",
        "sezione": 1,
        "dal_suo": True,
        "schema": ("∀", "∈", "x"),
        "esempio": ("∀", "∈", "x", "5"),
        "perche": "indice dispari: nessuna condizione, vale per ogni x",
    },
    {
        "voce": "Più radici pari",
        "sezione": 1,
        "dal_suo": True,
        "schema": ("≥", "0"),
        "esempio": ("≥", "0", "4"),
        "perche": "due radici pari: un sistema di condizioni, una per radice",
    },
    # --- 2. Operazioni ------------------------------------------------------
    {
        "voce": "Somma e sottrazione",
        "sezione": 2,
        "dal_suo": True,
        "schema": ("±", "(", ")", "a", "b", "n"),
        "esempio": ("+", "=", "−", "3", "5", "8"),
        "perche": "radicali simili: i coefficienti si sommano",
    },
    {
        "voce": "Prodotto",
        "sezione": 2,
        "dal_suo": True,
        "schema": ("n",),
        "esempio": ("=", "3"),
        "perche": "prodotto di radici con lo stesso indice",
    },
    {
        "voce": "Divisione",
        "sezione": 2,
        "dal_suo": True,
        "schema": ("n", ":", "0", "≠"),
        "esempio": (":", "=", "4"),
        "perche": "quoziente di radici, con la condizione ▲ ≠ 0",
    },
    {
        "voce": "Potenza di radice",
        "sezione": 2,
        "dal_suo": True,
        "schema": ("(", ")", "k", "n"),
        "esempio": ("(", ")", "=", "2", "4"),
        "perche": "potenza di una radice e potenza del coefficiente",
    },
    {
        "voce": "Radice di radice",
        "sezione": 2,
        "dal_suo": True,
        "schema": ("m", "n"),
        "esempio": ("=", "3", "2", "6"),
        "perche": "radice di radice: gli indici si moltiplicano",
    },
    # --- 3. Semplificazione -------------------------------------------------
    {
        "voce": "Semplificare l'indice",
        "sezione": 3,
        "dal_suo": False,
        "schema": ("n", "k"),
        "esempio": ("=", "6", "3", "2"),
        "perche": "proprietà invariantiva: indice ed esponente divisi per k",
    },
    {
        "voce": "Portar fuori",
        "sezione": 3,
        "dal_suo": False,
        "schema": ("n",),
        "esempio": ("=", "3"),
        "perche": "il fattore che ha esponente uguale all'indice esce",
    },
    {
        "voce": "Portar dentro",
        "sezione": 3,
        "dal_suo": False,
        "schema": ("n",),
        "esempio": ("=", "2"),
        "perche": "il fattore davanti rientra elevato all'indice",
    },
)

# Il minimo di pixel disegnati (a 200 dpi) sotto il quale una cella di formula
# è VUOTA: una formula vera ne ha centinaia (la più magra, il «Prodotto», ne ha
# 2900), una cella svuotata ne tiene zero — i filetti della tabella stanno
# fuori dalla banda della riga, e non contano.
MINIMO_CELLA = 600

# Quanto può valere l'inchiostro della nostra cella rispetto a quella del suo
# PDF: la nostra scheda è un RIFACIMENTO (font, spaziature, indici disegnati a
# mano) e non sarà mai identica. Una formula che sparisce scende a zero, che è
# sotto la banda; una che cambia forma resta dentro.
RAPPORTO_MIN, RAPPORTO_MAX = 0.25, 4.0


# ------------------------------------------------------------------ strumenti


def _serve(*programmi: str) -> None:
    mancanti = [p for p in programmi if shutil.which(p) is None]
    if mancanti:
        pytest.skip(f"manca {', '.join(mancanti)} (TeX Live / poppler): la prova non è eseguibile qui")


def costruisci(destinazione: Path, testo: str | None = None) -> Path:
    """Compila la scheda in ``destinazione``; ``testo`` sostituisce il sorgente."""
    _serve("pdflatex")
    destinazione.mkdir(parents=True, exist_ok=True)
    sorgente = testo if testo is not None else SORGENTE.read_text(encoding="utf-8")
    (destinazione / "radicali.tex").write_text(sorgente, encoding="utf-8")
    ambiente = {**os_environ(), "TEXINPUTS": f".:{SCHEDE}:"}
    for _ in range(2):  # due passate: la seconda serve al «Pagina n di N» del piede
        esito = subprocess.run(
            ["pdflatex", "-interaction=nonstopmode", "-halt-on-error", "radicali.tex"],
            cwd=destinazione,
            env=ambiente,
            capture_output=True,
            text=True,
        )
        if esito.returncode != 0:
            coda = "\n".join(esito.stdout.splitlines()[-15:])
            pytest.fail(f"pdflatex è uscito {esito.returncode}:\n{coda}")
    return destinazione / "radicali.pdf"


def os_environ() -> dict[str, str]:
    import os

    return dict(os.environ)


def estrai_testo(pdf: Path) -> str:
    _serve("pdftotext")
    esito = subprocess.run(["pdftotext", str(pdf), "-"], capture_output=True, text=True)
    assert esito.returncode == 0, esito.stderr
    return esito.stdout


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

    Servono a due cose, e tutte e due contano: delimitano le RIGHE (una banda per
    riga, trovata dal disegno e non da un numero scritto a mano) e non vanno
    contate come inchiostro di una formula.
    """
    soglia = 0.93 * (x1 - x0)
    marche = [
        y
        for y in range(altezza)
        if sum(1 for k in range(x0 * 3, x1 * 3, 3) if pixel[y * larghezza * 3 + k] < 250) > soglia
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
    dpi: int = 200,
    tollera_mancanti: bool = False,
) -> dict[str, dict[str, object]]:
    """Per ogni riga dell'elenco: il testo delle tre celle e l'inchiostro delle due formule.

    La riga si trova DAL PDF — la posizione della parola che apre la cella
    «voce» — dentro la banda delimitata dai filetti della tabella: se una riga
    si sposta o si allunga, la misura la segue invece di misurare il vuoto o la
    riga di sotto. Le colonne si trovano dalle intestazioni («Schema…» ed
    «Esempio»), così la stessa misura vale per il nostro PDF e per quello
    dell'operatore, che hanno margini diversi.
    """
    larghezza_pt, _altezza_pt, parole = pagine_e_parole(pdf)
    larghezza, altezza, pixel = _ppm(pdf, cartella, dpi)
    per_pt = larghezza / larghezza_pt  # pixel per punto tipografico

    # Il bordo della tabella: le colonne che hanno inchiostro per almeno il 2%
    # dell'altezza. Fuori da lì c'è il margine della pagina.
    colonne = [
        sum(1 for y in range(altezza) if pixel[(y * larghezza + x) * 3] < 200)
        for x in range(larghezza)
    ]
    x0 = min(x for x, quante in enumerate(colonne) if quante > altezza * 0.02)
    x1 = max(x for x, quante in enumerate(colonne) if quante > altezza * 0.02)
    filetti = _filetti(pixel, larghezza, altezza, x0, x1)
    bande = [(filetti[i][1], filetti[i + 1][0]) for i in range(len(filetti) - 1)]

    def intestazione(parola: str) -> float:
        for testo, x, _y0, _x1, _y1 in parole:
            if testo.lower().startswith(parola):
                return x * per_pt
        raise AssertionError(f"manca l'intestazione «{parola}»: le colonne non si possono misurare")

    c1, c2 = intestazione("schema"), intestazione("esempio")
    limiti = (x0, c1, c2, x1)

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
            # «≠» nel PDF è «=» con la barra sovrapposta (U+0338), e il testo
            # estratto porta la barra da sola: qui le due grafie diventano una,
            # così la stessa dichiarazione vale per il nostro PDF e per il suo.
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
            "celle": tuple(testo_cella(limiti[i], limiti[i + 1]) for i in range(3)),
            "inchiostro": tuple(inchiostro(limiti[i], limiti[i + 1]) for i in (1, 2)),
            "caratteri": tuple(
                caratteri(testo_cella(limiti[i], limiti[i + 1])) for i in (1, 2)
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
        SUO_PDF, tmp_path_factory.mktemp("suo"), tuple(f for f in FORMULE if f["dal_suo"])
    )


# --------------------------------------------------------------------- le prove


def test_il_golden_e_il_pdf_dell_operatore() -> None:
    """Il termine di confronto è SUO, e si sa quale: 124364 byte, Chromium."""
    assert SUO_PDF.exists(), "manca il PDF dell'operatore in tests/golden/schede/"
    byte = SUO_PDF.read_bytes()
    assert len(byte) == 124364, f"il PDF dell'operatore sono {len(byte)} byte, non 124364"
    assert hashlib.sha256(byte).hexdigest() == SUO_SHA256, (
        "questo non è il PDF dell'operatore: è stato sostituito (con una nostra "
        "compilazione?). Il confronto deve essere col suo, non con una versione nostra"
    )
    assert b"/Skia" in byte or b"Chromium" in byte, "il PDF dell'operatore è uscito da Chromium"


def test_la_scheda_sta_in_una_pagina(scheda: Path) -> None:
    """Una pagina A4: è la richiesta dell'operatore, e il vincolo della scheda."""
    assert pagine(scheda) == PAGINE, "la scheda non sta in una pagina"


def test_le_tre_sezioni_ci_sono_e_in_ordine(scheda: Path) -> None:
    """Campo di esistenza, operazioni, semplificazione: le tre, nell'ordine."""
    contenuto = estrai_testo(scheda)
    posizioni = []
    for sezione in SEZIONI:
        assert sezione in contenuto, f"manca la sezione «{sezione}»"
        posizioni.append(contenuto.index(sezione))
    assert posizioni == sorted(posizioni), "le tre sezioni non sono nell'ordine in cui si studiano"


def test_ogni_formula_porta_i_suoi_atomi(nostro: dict[str, dict[str, object]]) -> None:
    """L'elenco, formula per formula: ogni cella porta gli atomi che quella formula è.

    Un errore qui dice QUALE formula è monca e che cosa le manca, invece di far
    leggere un diff di caratteri.
    """
    guasti = []
    for formula in FORMULE:
        misura = nostro[formula["voce"]]
        celle = misura["celle"]
        for indice, chiave in ((1, "schema"), (2, "esempio")):
            for atomo in formula[chiave]:
                if atomo not in celle[indice]:
                    guasti.append(
                        f"riga «{formula['voce']}» ({formula['perche']}), cella «{chiave}»: "
                        f"manca «{atomo}» — la cella dice {celle[indice]!r}"
                    )
    assert not guasti, "formule monche:\n" + "\n".join(guasti)


def test_ogni_formula_e_disegnata(nostro: dict[str, dict[str, object]]) -> None:
    """Le ventidue celle di formula hanno il loro disegno, a 200 dpi.

    È lo strato che il testo non può vedere: il segno di radice, le frecce e le
    forme sono TikZ. Una formula che c'è nel sorgente ma non viene disegnata
    (colonna troppo stretta, pagina che trabocca) qui si vede.
    """
    vuote = [
        f"riga «{formula['voce']}», cella {'schema' if i == 1 else 'esempio'}: "
        f"{nostro[formula['voce']]['inchiostro'][i - 1]} pixel disegnati"
        for formula in FORMULE
        for i in (1, 2)
        if nostro[formula["voce"]]["inchiostro"][i - 1] < MINIMO_CELLA
    ]
    assert not vuote, "celle di formula senza disegno (una formula non è stata disegnata):\n" + "\n".join(vuote)


def test_le_formule_del_suo_pdf_ci_sono_tutte(
    nostro: dict[str, dict[str, object]], suo: dict[str, dict[str, object]]
) -> None:
    """Confronto col PDF DELL'OPERATORE, riga per riga: le sue otto righe, e i suoi atomi.

    Non è un confronto con una nostra versione precedente — è il difetto che ha
    fatto perdere la giornata del 26/11. Ogni riga della sua scheda deve esserci,
    portare gli stessi atomi di testo, e avere inchiostro nella stessa banda:
    una formula che nella fusione si è persa si vede qui, con il suo nome.
    """
    sue = [f for f in FORMULE if f["dal_suo"]]
    assert len(sue) == 8, f"le righe che vengono dal suo PDF dovrebbero essere 8, sono {len(sue)}"
    guasti = []
    for formula in sue:
        nome = formula["voce"]
        assert nome in suo, f"la riga «{nome}» non si trova nel PDF dell'operatore"
        suo_testo = " ".join(suo[nome]["celle"])
        for indice, chiave in ((1, "schema"), (2, "esempio")):
            for atomo in formula[chiave]:
                if atomo not in suo_testo:
                    guasti.append(
                        f"l'elenco dichiara «{atomo}» per «{nome}»/{chiave}, "
                        "ma nel PDF dell'operatore non c'è: l'elenco non descrive il suo documento"
                    )
            suo_inchiostro = suo[nome]["inchiostro"][indice - 1]
            nostro_inchiostro = nostro[nome]["inchiostro"][indice - 1]
            if suo_inchiostro <= 0:
                continue
            rapporto = nostro_inchiostro / suo_inchiostro
            if not RAPPORTO_MIN <= rapporto <= RAPPORTO_MAX:
                guasti.append(
                    f"riga «{nome}»/{chiave}: la nostra cella disegna {nostro_inchiostro} pixel "
                    f"contro i {suo_inchiostro} del suo PDF (rapporto {rapporto:.2f}, "
                    f"la banda è {RAPPORTO_MIN}–{RAPPORTO_MAX})"
                )
    assert not guasti, "il confronto col PDF dell'operatore non torna:\n" + "\n".join(guasti)


def test_il_pdf_committato_e_quello_che_il_sorgente_produce(scheda: Path) -> None:
    """Il PDF in repository non deve essere un artefatto vecchio."""
    assert COMMITTATO.exists(), "manca schede/radicali/radicali.pdf (make in schede/radicali)"
    committato = caratteri(estrai_testo(COMMITTATO))
    dal_sorgente = caratteri(estrai_testo(scheda))
    assert committato == dal_sorgente, (
        "il PDF committato non è quello che il .tex produce — ricompila con "
        "`make -C schede/radicali`"
    )


def test_il_confronto_col_suo_pdf_sa_fallire(
    tmp_path: Path, suo: dict[str, dict[str, object]]
) -> None:
    """Tolta una riga dal sorgente, il confronto col suo PDF la nomina.

    Si toglie «Radice di radice» — la formula più annidata — e si ricompila: la
    misura deve perdere la riga (il confronto riga per riga non la trova più).
    Se questo test passasse, il confronto sarebbe cieco.
    """
    sorgente = SORGENTE.read_text(encoding="utf-8")
    inizio = sorgente.index("\\riga{\\voce{Radice di radice}")
    fine = sorgente.index("\\end{schedaTabella}", inizio)
    mutilato = sorgente[:inizio] + sorgente[fine:]
    assert "Radice di radice" not in mutilato, "la riga non è stata tolta dal sorgente"

    pdf = costruisci(tmp_path / "mutilato", mutilato)
    assert pagine(pdf) == 1, "tolta una riga la scheda deve stare in una pagina comunque"
    misure = _misura(pdf, tmp_path / "misura-mutilata", tollera_mancanti=True)
    assert "Radice di radice" not in misure, (
        "tolta la riga «Radice di radice» la misura l'ha ancora trovata: "
        "è lo stesso controllo cieco del 26/11"
    )


def test_la_misura_del_disegno_sa_fallire(tmp_path: Path) -> None:
    """Svuotata UNA cella di formula, la misura del disegno la vede.

    Si toglie solo la formula della colonna «esempio» della riga «Prodotto»: la
    ``\\riga`` resta, le righe restano, il testo estratto cambia di pochissimo (le
    forme e le radici sono disegnate) — e la cella resta vuota.
    """
    sorgente = SORGENTE.read_text(encoding="utf-8")
    inizio = sorgente.index("\\riga{\\voce{Prodotto}")
    fine = sorgente.index("\\riga{\\voce{Divisione}", inizio)
    riga = sorgente[inizio:fine]
    # la TERZA graffa della \riga è l'esempio: si svuota quella, non la riga.
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
    inizio_argomento, fine_argomento = gruppi[2]
    mutilata = riga[:inizio_argomento] + "{$\\;\\,$}" + riga[fine_argomento:]
    mutilato = sorgente[:inizio] + mutilata + sorgente[fine:]

    pdf = costruisci(tmp_path / "cella_vuota", mutilato)
    assert pagine(pdf) == 1
    misure = _misura(pdf, tmp_path / "misura-vuota")
    esempio = misure["Prodotto"]["inchiostro"][1]
    assert esempio < MINIMO_CELLA, (
        f"svuotata la cella «esempio» della riga «Prodotto» la misura conta ancora "
        f"{esempio} pixel: la misura del disegno non sa fallire"
    )
