"""Le potenze: UNA pagina, due sezioni, otto proprietà — e il confronto col PDF dell'operatore.

PERCHÉ QUESTO FILE ESISTE (27/11/2026). L'operatore ha chiesto la scheda delle
potenze con la stessa regola delle due precedenti: «stesso lavoro su questo PDF:
le proprietà delle potenze, stessa coerenza e stessa pubblicazione». La scheda dei
radicali aveva già pagato il difetto che questi test prevengono — una formula che
c'era e non c'è più, e un controllo che non se ne accorgeva — quindi qui la misura
è la stessa, sul contenuto:

1. **L'ELENCO DELLE PROPRIETÀ** (``PROPRIETA``): le otto righe della sua scheda,
   ognuna con gli atomi che la cella «schema visivo» e la cella «esempio numerico»
   DEVONO portare. Si controlla cella per cella: un atomo mancante dice QUALE
   proprietà è monca, non fa leggere un diff di caratteri.
2. **IL DISEGNO**: le forme, le frecce e le frazioni sono TikZ o disegno, e nel
   testo non ci sono. Per ogni cella di formula si contano i pixel a 200 dpi: una
   cella piena ne ha centinaia, una svuotata zero.
3. **L'ORDINE DELLE FORME**: il quadrato (base *a*, blu) e il triangolo (base *b*,
   rosso) portano un significato, quindi la loro SEQUENZA è una misura — la base 2
   deve stare a destra della base 1, e la freccia in mezzo.
4. **IL SUO PDF**: le stesse misure sul PDF dell'operatore (110034 byte, Chromium,
   «Le Potenze: Schema Visivo»), riga per riga: le sue otto proprietà ci sono
   tutte, nello stesso ordine, con gli stessi atomi, e l'inchiostro delle nostre
   celle sta in una banda dichiarata rispetto al suo. È il confronto che conta:
   col suo documento, non con una nostra versione.
5. **LE DUE PROVE CHE SANNO FALLIRE**: tolta una riga dal sorgente, il confronto
   col suo PDF la nomina; girate le due basi, la firma dei colori se ne accorge.

I test costruiscono la scheda DAL SORGENTE e non guardano il PDF committato: un
artefatto vecchio non deve poter far passare un sorgente rotto — e c'è un test
apposta che il PDF committato sia quello che il sorgente produce.

Il file si può eseguire anche senza pytest (``python3 tests/test_schede_potenze.py``):
ogni prova è una funzione senza argomenti e il ``main`` le chiama tutte, così la
prova si può fare dove pytest non c'è (la casa, 27/11/2026) e resta una prova
della suite dove pytest c'è (la CI del teaching).
"""

from __future__ import annotations

import collections
import hashlib
import os
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

RADICE = Path(__file__).resolve().parents[1]
SCHEDE = RADICE / "schede"
SORGENTE = SCHEDE / "potenze" / "potenze.tex"
COMMITTATO = SCHEDE / "potenze" / "potenze.pdf"
SUO_PDF = RADICE / "tests" / "golden" / "schede" / "potenze-operatore.pdf"

# Il PDF dell'operatore, identificato: 110034 byte, Chromium/Skia, «Le Potenze:
# Schema Visivo», caricato il 27/11/2026. Un golden che nessuno identifica può
# diventare una copia di noi stessi senza che nessuno se ne accorga.
SUO_BYTE = 110034
SUO_SHA256 = "16076888b8e56c46f1e6835108c9bef2e321e638e20863248ee6d777a0592186"

PAGINE = 1

# Le due sezioni del suo PDF, nell'ordine in cui stanno.
SEZIONI = (
    "1. Operazioni con la Stessa Base",
    "2. Stesso Esponente & Casi Particolari",
)

# ---------------------------------------------------------------------------
# LE OTTO PROPRIETÀ, una per una — il contenuto del suo PDF.
#
# `atomi`: i caratteri che il testo estratto DEVE portare in quella cella. Le
# forme (quadrato, triangolo), le frecce e le frazioni sono disegnate: le misura
# il test dell'inchiostro e dell'ordine, non questo.
#
# `firma`: l'ordine in cui le FORME si incontrano da sinistra nella cella dello
# schema, letto dai colori della palette — blu = quadrato (base *a*), rosso =
# triangolo (base *b*), grigio = la freccia. È la misura che né il testo né
# l'inchiostro sanno fare: le stesse forme in ordine diverso hanno gli stessi
# atomi e lo stesso inchiostro.
# ---------------------------------------------------------------------------
PROPRIETA = (
    {
        "voce": "Prodotto stesse basi",
        "sezione": 1,
        "schema": ("n", "m", "+"),
        "esempio": ("3", "2", "4", "6", "=", "+"),
        "firma": ("blu", "grigio", "blu"),
        "perche": "prodotto con la stessa base: gli esponenti si sommano",
    },
    {
        "voce": "Quoziente stesse basi",
        "sezione": 1,
        "schema": ("n", "m", "−"),
        "esempio": ("5", "7", "3", "4", "=", "−"),
        "firma": ("blu", "grigio", "blu"),
        "perche": "quoziente con la stessa base: gli esponenti si sottraggono",
    },
    {
        "voce": "Potenza di potenza",
        "sezione": 1,
        "schema": ("(", ")", "n", "m", "·"),
        "esempio": ("(", ")", "2", "3", "6", "=", "·"),
        "firma": ("blu", "grigio", "blu"),
        "perche": "potenza di potenza: gli esponenti si moltiplicano",
    },
    {
        "voce": "Prodotto stessi esponenti",
        "sezione": 2,
        "schema": ("n", "·"),
        "esempio": ("4", "3", "2", "=", "·", "("),
        "firma": ("blu", "rosso", "grigio", "blu", "rosso"),
        "perche": "prodotto con lo stesso esponente: le basi si moltiplicano",
    },
    {
        "voce": "Quoziente stessi esponenti",
        "sezione": 2,
        "schema": ("n", ":"),
        "esempio": ("1", "0", "3", "5", "=", ":"),
        "firma": ("blu", "rosso", "grigio", "blu", "rosso"),
        "perche": "quoziente con lo stesso esponente: le basi si dividono",
    },
    {
        "voce": "Esponente zero",
        "sezione": 2,
        "schema": ("0",),
        "esempio": ("1", "5", "0", "="),
        "firma": ("blu", "grigio"),
        "perche": "esponente zero: qualunque base (diversa da zero) dà 1",
    },
    {
        "voce": "Esponente uno",
        "sezione": 2,
        "schema": ("1",),
        "esempio": ("8", "="),
        "firma": ("blu", "grigio", "blu"),
        "perche": "esponente uno: la base resta quella",
    },
    {
        "voce": "Esponente negativo",
        "sezione": 2,
        "schema": ("−", "n"),
        "esempio": ("2", "3", "8", "=", "−"),
        "firma": ("blu", "grigio", "blu"),
        "perche": "esponente negativo: si inverte la base (1/∎ⁿ)",
    },
)

# Il minimo di pixel disegnati (a 200 dpi) sotto il quale una cella di formula è
# VUOTA: una formula vera ne ha centinaia, una cella svuotata zero.
MINIMO_CELLA = 600

# La cella dell'ESEMPIO è testo (numeri e segni), non forme: la sua soglia è più
# bassa, e serve solo a dire che qualcosa è stampato (una cella svuotata ne ha 0).
MINIMO_ESEMPIO = 120

# Quanto può valere il nostro inchiostro rispetto al suo: la nostra scheda è un
# RIFACIMENTO (font, spaziature, forme al posto delle lettere) e il suo è un
# render Chromium con un corpo più grande — il rapporto misurato il 27/11 va da
# 0,12 a 4,6. La banda non chiede la stessa tipografia: chiede che una cella non
# sia VUOTA (zero) né disegnata d'altro (un ordine di grandezza).
RAPPORTO_MIN, RAPPORTO_MAX = 0.08, 6.0

# I COLORI DELLA PALETTE (schede.sty §1), come pixel RGB.
PALETTE = {
    "blu": (0x25, 0x63, 0xEB),    # quadrato — base a
    "rosso": (0xDC, 0x26, 0x26),  # triangolo — base b
    "verde": (0x16, 0xA3, 0x4A),  # cerchio
    "grigio": (0x47, 0x55, 0x69), # frecce, rombo, note
}
ESATTO = {(r << 16) | (g << 8) | b: nome for nome, (r, g, b) in PALETTE.items()}


# ------------------------------------------------------------------ strumenti


def _serve(*programmi: str) -> None:
    mancanti = [p for p in programmi if shutil.which(p) is None]
    if mancanti:
        _salta(f"manca {', '.join(mancanti)} (TeX Live / poppler): la prova non è eseguibile qui")


def _salta(motivo: str) -> None:
    """Salta come farebbe pytest — e senza pytest si ferma dicendo perché."""
    try:
        import pytest  # noqa: F401
    except ImportError:
        raise SystemExit(f"SKIP: {motivo}")
    import pytest

    pytest.skip(motivo)


def costruisci(destinazione: Path, testo: str | None = None) -> Path:
    """Compila la scheda in ``destinazione``; ``testo`` sostituisce il sorgente."""
    _serve("pdflatex")
    destinazione.mkdir(parents=True, exist_ok=True)
    sorgente = testo if testo is not None else SORGENTE.read_text(encoding="utf-8")
    (destinazione / "potenze.tex").write_text(sorgente, encoding="utf-8")
    ambiente = {**dict(os.environ), "TEXINPUTS": f".:{SCHEDE}:"}
    for _ in range(2):  # due passate: la seconda serve al «Pagina n di N» del piede
        esito = subprocess.run(
            ["pdflatex", "-interaction=nonstopmode", "-halt-on-error", "potenze.tex"],
            cwd=destinazione,
            env=ambiente,
            capture_output=True,
            text=True,
        )
        if esito.returncode != 0:
            coda = "\n".join(esito.stdout.splitlines()[-15:])
            raise AssertionError(f"pdflatex è uscito {esito.returncode}:\n{coda}")
    return destinazione / "potenze.pdf"


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


def misure_pagina(pdf: Path) -> tuple[float, float]:
    _serve("pdfinfo")
    esito = subprocess.run(["pdfinfo", str(pdf)], capture_output=True, text=True)
    trovato = re.search(r"^Page size:\s+([\d.]+) x ([\d.]+)", esito.stdout, re.MULTILINE)
    assert trovato, "pdfinfo non ha detto la dimensione della pagina"
    return float(trovato.group(1)), float(trovato.group(2))


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

    Delimitano le RIGHE (una banda per riga, trovata dal disegno e non da un
    numero scritto a mano) e non vanno contate come inchiostro di una formula.
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
    proprieta: tuple[dict[str, object], ...] = PROPRIETA,
    dpi: int = 200,
    tollera_mancanti: bool = False,
) -> dict[str, dict[str, object]]:
    """Per ogni riga dell'elenco: il testo delle tre celle, l'inchiostro e l'ordine delle forme.

    La riga si trova DAL PDF — la posizione della parola che apre la cella «voce»
    — dentro la banda delimitata dai filetti: se una riga si sposta o si allunga,
    la misura la segue. Le colonne si trovano dalle intestazioni («Schema…» ed
    «Esempio»), così la stessa misura vale per il nostro PDF e per il suo.
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

    def intestazione(parola: str) -> float:
        for testo, x, _y0, _x1, _y1 in parole:
            if testo.lower().startswith(parola):
                return x * per_pt
        raise AssertionError(f"manca l'intestazione «{parola}»: le colonne non si possono misurare")

    c1, c2 = intestazione("schema"), intestazione("esempio")
    limiti = (x0, c1, c2, x1)

    # LE BANDE DELLE RIGHE, dagli ancoraggi delle voci: la riga comincia dove
    # comincia il suo titolo e finisce dove comincia il titolo della riga dopo.
    # (Le righe di separazione non servono a questo: nel PDF dell'operatore le
    # intestazioni sono fasce SCURE a tutta larghezza, e una banda misurata sui
    # filetti scambierebbe l'intestazione per una riga — misurato il 27/11.)
    ancoraggi: list[float] = []
    precedente = -1.0
    for formula in proprieta:
        prima = str(formula["voce"]).split()[0]
        candidate = sorted(
            y for testo, _x, y, _x1, _y1 in parole if testo == prima and y > precedente
        )
        if not candidate:
            assert tollera_mancanti, f"manca la riga «{formula['voce']}» nel testo estratto"
            continue
        precedente = candidate[0]
        ancoraggi.append(candidate[0])
    assert ancoraggi, "nessuna riga dell'elenco è stata trovata nel testo estratto"

    misure: dict[str, dict[str, object]] = {}
    for indice_riga, formula in enumerate(proprieta):
        if indice_riga >= len(ancoraggi):
            break  # la riga manca e `tollera_mancanti` l'ha già ammesso
        y = ancoraggi[indice_riga]
        a = max(0, int((y - 3) * per_pt))
        fine = ancoraggi[indice_riga + 1] if indice_riga + 1 < len(ancoraggi) else y + 34
        b = min(altezza, int((fine - 1) * per_pt))

        def testo_cella(xa: float, xb: float) -> str:
            return " ".join(
                testo
                for testo, px0, py0, px1, py1 in parole
                if xa <= (px0 + px1) / 2 * per_pt < xb and a < (py0 + py1) / 2 * per_pt < b
            )

        def inchiostro(xa: float, xb: float) -> int:
            return sum(
                1
                for riga in range(a + 1, b)
                for k in range(int(xa) * 3, int(xb) * 3, 3)
                if pixel[riga * larghezza * 3 + k] < 200
            )

        def firma(xa: float, xb: float) -> tuple[str, ...]:
            """L'ORDINE delle forme lungo la riga: la sequenza dei colori, da sinistra.

            Ogni colonna di pixel appartiene al colore che vi ha più pixel (le
            colonne vuote non contano) e le colonne uguali di fila diventano una
            voce sola: ne esce la parola che la riga scrive — per esempio
            «blu, rosso, grigio, blu, rosso».
            """
            etichette: list[str] = []
            for x in range(int(xa), int(xb)):
                conta = {nome: 0 for nome in PALETTE}
                for riga in range(a + 1, b):
                    base = riga * larghezza * 3 + x * 3
                    rgb = (pixel[base] << 16) | (pixel[base + 1] << 8) | pixel[base + 2]
                    nome = ESATTO.get(rgb)
                    if nome is not None:
                        conta[nome] += 1
                migliore = max(conta, key=lambda chiave: conta[chiave])
                if conta[migliore] >= 2:  # una forma, non un pixel di antialiasing
                    etichette.append(migliore)
            ordine: list[str] = []
            for nome in etichette:
                if not ordine or ordine[-1] != nome:
                    ordine.append(nome)
            return tuple(ordine)

        misure[formula["voce"]] = {
            "celle": tuple(testo_cella(limiti[i], limiti[i + 1]) for i in range(3)),
            "inchiostro": tuple(inchiostro(limiti[i], limiti[i + 1]) for i in (1, 2)),
            "caratteri": tuple(caratteri(testo_cella(limiti[i], limiti[i + 1])) for i in (1, 2)),
            "firma": firma(limiti[1], limiti[2]),
        }
    return misure


# I prodotti una volta sola: compilare e misurare costa qualche secondo, e ogni
# prova li vuole uguali. (Senza pytest non ci sono fixture: la cache è qui.)
_CACHE: dict[str, object] = {}


def _cartella() -> Path:
    if "cartella" not in _CACHE:
        _CACHE["cartella"] = Path(tempfile.mkdtemp(prefix="scheda-potenze-"))
    return _CACHE["cartella"]  # type: ignore[return-value]


def _scheda() -> Path:
    if "pdf" not in _CACHE:
        _CACHE["pdf"] = costruisci(_cartella() / "scheda")
    return _CACHE["pdf"]  # type: ignore[return-value]


def _nostro() -> dict[str, dict[str, object]]:
    if "nostro" not in _CACHE:
        _CACHE["nostro"] = _misura(_scheda(), _cartella() / "misura")
    return _CACHE["nostro"]  # type: ignore[return-value]


def _suo() -> dict[str, dict[str, object]]:
    if "suo" not in _CACHE:
        _CACHE["suo"] = _misura(SUO_PDF, _cartella() / "suo")
    return _CACHE["suo"]  # type: ignore[return-value]


# --------------------------------------------------------------------- le prove


def test_il_golden_e_il_pdf_dell_operatore() -> None:
    """Il termine di confronto è SUO, e si sa quale: 110034 byte, Chromium."""
    assert SUO_PDF.exists(), "manca il PDF dell'operatore in tests/golden/schede/"
    byte = SUO_PDF.read_bytes()
    assert len(byte) == SUO_BYTE, f"il PDF dell'operatore sono {len(byte)} byte, non {SUO_BYTE}"
    assert hashlib.sha256(byte).hexdigest() == SUO_SHA256, (
        "questo non è il PDF dell'operatore: è stato sostituito (con una nostra "
        "compilazione?). Il confronto deve essere col suo, non con una versione nostra"
    )
    assert b"Chromium" in byte or b"Skia" in byte, "il PDF dell'operatore è uscito da Chromium"


def test_la_scheda_sta_in_una_pagina() -> None:
    """Una pagina A4: la richiesta dell'operatore, e il vincolo della scheda."""
    pdf = _scheda()
    assert pagine(pdf) == PAGINE, f"la scheda ha {pagine(pdf)} pagine, non {PAGINE}"
    larghezza, altezza = misure_pagina(pdf)
    assert abs(larghezza - 595.276) < 1 and abs(altezza - 841.89) < 1, (
        f"la pagina è {larghezza} × {altezza} punti: non è A4"
    )


def test_le_due_sezioni_ci_sono_e_in_ordine() -> None:
    """Le due sezioni del suo PDF: le stesse parole, nello stesso ordine."""
    contenuto = estrai_testo(_scheda())
    posizioni = []
    for sezione in SEZIONI:
        assert sezione in contenuto, f"manca la sezione «{sezione}»"
        posizioni.append(contenuto.index(sezione))
    assert posizioni == sorted(posizioni), "le due sezioni non sono nell'ordine del suo PDF"


def test_ogni_proprieta_porta_i_suoi_atomi() -> None:
    """L'elenco, proprietà per proprietà: ogni cella porta gli atomi che quella proprietà è."""
    nostro = _nostro()
    guasti = []
    for formula in PROPRIETA:
        celle = nostro[formula["voce"]]["celle"]
        for indice, chiave in ((1, "schema"), (2, "esempio")):
            for atomo in formula[chiave]:
                if atomo not in celle[indice]:
                    guasti.append(
                        f"riga «{formula['voce']}» ({formula['perche']}), cella «{chiave}»: "
                        f"manca «{atomo}» — la cella dice {celle[indice]!r}"
                    )
    assert not guasti, "proprietà monche:\n" + "\n".join(guasti)


def test_ogni_proprieta_e_disegnata() -> None:
    """Le sedici celle di formula hanno il loro disegno, a 200 dpi.

    È lo strato che il testo non può vedere: le forme, le frecce e le frazioni.
    Una formula che c'è nel sorgente ma non viene disegnata (colonna troppo
    stretta, pagina che trabocca) qui si vede.
    """
    nostro = _nostro()
    vuote = [
        f"riga «{formula['voce']}», cella {'schema' if i == 1 else 'esempio'}: "
        f"{nostro[formula['voce']]['inchiostro'][i - 1]} pixel disegnati"
        for formula in PROPRIETA
        for i, soglia in ((1, MINIMO_CELLA), (2, MINIMO_ESEMPIO))
        if nostro[formula["voce"]]["inchiostro"][i - 1] < soglia
    ]
    assert not vuote, "celle di formula senza disegno:\n" + "\n".join(vuote)


def test_le_forme_seguono_la_legenda_della_sua_scheda() -> None:
    """L'ORDINE delle forme, misurato sul disegno: base 1 = quadrato, base 2 = triangolo.

    La legenda del suo PDF dice: base *a* = quadrato, base *b* = triangolo. Nelle
    nostre righe la sequenza dei colori dev'essere quella: il quadrato (blu) prima
    del triangolo (rosso) dove le basi sono due, e la freccia (grigia) in mezzo fra
    ciò che si ha e ciò che si ottiene. Le stesse forme in ordine diverso hanno gli
    stessi atomi e lo stesso inchiostro: lo dice solo questa misura.
    """
    nostro = _nostro()
    guasti = []
    for formula in PROPRIETA:
        firma = nostro[formula["voce"]]["firma"]
        if firma != formula["firma"]:
            guasti.append(
                f"riga «{formula['voce']}»: le forme sono «{', '.join(firma)}», "
                f"la legenda chiede «{', '.join(formula['firma'])}»"
            )
    assert not guasti, "l'ordine delle forme non segue la legenda:\n" + "\n".join(guasti)


def test_le_otto_proprieta_del_suo_pdf_ci_sono_tutte() -> None:
    """Confronto col PDF DELL'OPERATORE, riga per riga: le sue otto proprietà e i suoi atomi.

    Le sue otto righe devono esserci tutte, portare gli stessi atomi di testo, e
    avere inchiostro nella stessa banda: una proprietà che nella copia si è persa
    si vede qui, con il suo nome.
    """
    nostro, suo = _nostro(), _suo()
    assert len(suo) == len(PROPRIETA), (
        f"nel PDF dell'operatore ho misurato {len(suo)} righe, l'elenco ne dichiara {len(PROPRIETA)}"
    )
    guasti = []
    for formula in PROPRIETA:
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


def test_il_pdf_committato_e_quello_che_il_sorgente_produce() -> None:
    """Il PDF in repository non deve essere un artefatto vecchio."""
    assert COMMITTATO.exists(), "manca schede/potenze/potenze.pdf (make in schede/potenze)"
    committato = caratteri(estrai_testo(COMMITTATO))
    dal_sorgente = caratteri(estrai_testo(_scheda()))
    assert committato == dal_sorgente, (
        "il PDF committato non è quello che il .tex produce — ricompila con "
        "`make -C schede/potenze`"
    )


def test_il_confronto_col_suo_pdf_sa_fallire() -> None:
    """Tolta una riga dal sorgente, il confronto col suo PDF la nomina.

    Una prova che non può fallire non è una prova: si toglie «Esponente
    negativo» — l'ultima, quella con la frazione — e si ricompila. La misura non
    deve più trovare quella riga, e l'elenco deve dire quale manca.
    """
    sorgente = SORGENTE.read_text(encoding="utf-8")
    inizio = sorgente.index("\\riga{\\voce{Esponente negativo}")
    fine = sorgente.index("\\end{schedaTabella}", inizio)
    mutato = sorgente[:inizio] + sorgente[fine:]
    assert "Esponente negativo" not in mutato

    cartella = Path(tempfile.mkdtemp(prefix="scheda-potenze-girata-"))
    pdf = costruisci(cartella / "senza", mutato)
    misure = _misura(pdf, cartella / "misura", tollera_mancanti=True)
    mancanti = [f["voce"] for f in PROPRIETA if f["voce"] not in misure]
    assert mancanti == ["Esponente negativo"], (
        "tolto «Esponente negativo» dal sorgente, la misura dovrebbe perdere quella riga "
        f"e una sola: ha perso {mancanti}"
    )
    assert len(estrai_testo(pdf)) < len(estrai_testo(_scheda())), (
        "il testo della scheda mutata non è più corto: la riga non è stata tolta davvero"
    )


def test_l_ordine_delle_forme_sa_fallire() -> None:
    """Girate le due basi, la firma dei colori se ne accorge.

    Si ricompila la scheda col triangolo al posto del quadrato nella cella dello
    schema di «Prodotto stesse basi»: la firma diventa «rosso, …» e il test
    dell'ordine sarebbe rosso. Se questo passasse, la misura dell'ordine sarebbe
    cieca.
    """
    sorgente = SORGENTE.read_text(encoding="utf-8")
    prima = (
        "{$\\formaQuadrato^{n}\\cdot\\formaQuadrato^{m}\n"
        "         \\;\\freccia\\;\\formaQuadrato^{n+m}$}"
    )
    assert prima in sorgente, "il sorgente è cambiato di forma: la prova d'ordine non sa più girarlo"
    mutato = sorgente.replace(
        prima,
        "{$\\formaTriangolo^{n}\\cdot\\formaQuadrato^{m}\n"
        "         \\;\\freccia\\;\\formaQuadrato^{n+m}$}",
    )
    cartella = Path(tempfile.mkdtemp(prefix="scheda-potenze-colori-"))
    pdf = costruisci(cartella / "girata", mutato)
    misure = _misura(pdf, cartella / "misura")
    firma = misure["Prodotto stesse basi"]["firma"]
    assert firma[0] == "rosso", (
        "girata la prima base in triangolo, la firma dovrebbe cominciare col rosso: "
        f"comincia con «{firma[0]}» — la misura dell'ordine non se n'è accorta"
    )


# ------------------------------------------------------------ senza pytest


def main() -> int:
    """Tutte le prove, una dopo l'altra, senza pytest (dove pytest non c'è)."""
    prove = [
        (nome, oggetto)
        for nome, oggetto in sorted(globals().items())
        if nome.startswith("test_") and callable(oggetto)
    ]
    rossi = 0
    for nome, prova in prove:
        try:
            prova()
        except SystemExit as uscita:
            print(f"SKIP {nome}: {uscita}")
            continue
        except AssertionError as guasto:
            rossi += 1
            print(f"ROSSO {nome}\n{guasto}\n")
        else:
            print(f"VERDE {nome}")
    print(f"\n{len(prove) - rossi}/{len(prove)} verdi" if rossi else f"\n{len(prove)}/{len(prove)} verdi")
    return 1 if rossi else 0


if __name__ == "__main__":
    raise SystemExit(main())
