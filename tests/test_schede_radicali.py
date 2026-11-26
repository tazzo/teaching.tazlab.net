"""La scheda dei radicali: una pagina, e dentro TUTTO quello che c'era.

Perchè questo file esiste (26/11/2026). La scheda è stata compattata per farla
stare in una pagina A4 e l'operatore ha detto: «adesso il PDF è una pagina sola
ma mancano le formule che erano scritte nella seconda pagina». Il controllo che
allora ha lasciato passare il difetto era un CONTEGGIO — le ``\\riga`` del
``.tex`` (8) e le righe di ``pdftotext`` (50 prima, 50 dopo) — e un conteggio è
cieco proprio ai due guasti che contano:

* una formula tolta DENTRO una riga: le righe restano 8 e le righe di testo
  restano 50;
* una formula che nel sorgente c'è e non viene DISEGNATA (colonna troppo
  stretta, pagina che trabocca): il conteggio del sorgente non la vede, e nel
  testo estratto non c'era mai stata.

Qui il confronto è sul CONTENUTO, in due strati, perchè questa scheda è metà
testo e metà disegno:

1. **il testo**: le lettere, le cifre e i simboli che ``pdftotext`` legge dal
   PDF costruito devono essere ESATTAMENTE quelli della versione originale
   (``tests/golden/schede/radicali-1-originale.txt``, presa dal PDF da 140290
   byte del commit 7702236). Confronto come multinsieme di caratteri: uno
   spostamento di una formula dentro la cella non fa fallire il test, una
   formula che sparisce sì. Zero mancanti, zero in più.
2. **l'inchiostro**: il segno di radice, le frecce e le forme sono TikZ —
   nel testo non ci sono e non ci saranno mai. Per quelle il test misura i
   pixel disegnati, colonna per colonna, e li confronta con l'originale
   (``tests/golden/schede/radicali-1-originale.json``, che dice anche come
   sono state misurate). La tolleranza è stretta apposta: cambiare la
   spaziatura costa lo 0,1%, togliere una riga il 7,4%.

Il test costruisce la scheda DAL SORGENTE, non guarda il PDF committato: un
artefatto vecchio in repository non deve poter far passare un sorgente rotto —
e c'è un test apposta che il PDF committato sia quello che il sorgente
produce.

Il terzo test è il più importante e si chiama "il controllo sa fallire": prende
il ``.tex``, cancella la riga «Radice di radice» e verifica che il confronto
del contenuto la veda. Un test che non può fallire non è una prova.
"""

from __future__ import annotations

import collections
import json
import os
import re
import shutil
import subprocess
from pathlib import Path

import pytest

RADICE = Path(__file__).resolve().parents[1]
SCHEDE = RADICE / "schede"
SORGENTE = SCHEDE / "radicali" / "radicali-1.tex"
COMMITTATO = SCHEDE / "radicali" / "radicali-1.pdf"
ORIGINALE_TXT = RADICE / "tests" / "golden" / "schede" / "radicali-1-originale.txt"
ORIGINALE_JSON = RADICE / "tests" / "golden" / "schede" / "radicali-1-originale.json"

TOT_TESTO = 0.02      # 2% sul totale: una riga tolta pesa il 7,4%
TOT_COLONNA = 0.04    # 4% per colonna: la colonna stretta pesa il 5,8%

# Le colonne della tabella, in millimetri, come le fissa schede.sty
# (\\schedaColonne{0.225}{0.40}{0.375} su una giustezza di 180 mm da 15 a 195).
COLONNE_MM = ((15.0, 55.5), (55.5, 127.5), (127.5, 195.0))

# L'inventario, per NOME: se una riga sparisce, il test dice quale. I frammenti
# sono quelli che il testo estratto contiene davvero (le forme e le frecce sono
# disegnate, e le vede l'altro test).
RIGHE = (
    "Indice pari",
    "Indice dispari",
    "Più radici pari",
    "Somma e sottrazione",
    "Prodotto",
    "Divisione",
    "Potenza di radice",
    "Radice di radice",
)
SEZIONI = (
    "1. Campo di Esistenza (CE)",
    "2. Operazioni con i Radicali (Casi Semplici)",
)
INTESTAZIONI = (
    "Tipo di radice",
    "Schema visivo",
    "Esempio",
    "Operazione",
    "Schema visivo (stesso indice n)",
)
# Gli atomi di formula che il testo estratto porta: le disuguaglianze e i
# quantificatori di OGNI riga. Contati, non solo cercati: due «∀x ∈ R» sono
# l'indice dispari e il suo esempio, e se ne resta uno il test lo dice.
ATOMI = {"≥": 6, "∀": 2, "∈": 2}
# Il «≠» della divisione non è un carattere: nel PDF è U+0338 (la barra
# sovrapposta) accanto a «=», e nel testo estratto è una barra da sola.
SBARRATO = "\u0338"


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
    (destinazione / "radicali-1.tex").write_text(sorgente, encoding="utf-8")
    ambiente = {**os.environ, "TEXINPUTS": f".:{SCHEDE}:"}
    for _ in range(2):  # due passate: la seconda serve al «Pagina n di N»
        esito = subprocess.run(
            ["pdflatex", "-interaction=nonstopmode", "-halt-on-error", "radicali-1.tex"],
            cwd=destinazione,
            env=ambiente,
            capture_output=True,
            text=True,
        )
        if esito.returncode != 0:
            coda = "\n".join(esito.stdout.splitlines()[-15:])
            pytest.fail(f"pdflatex è uscito {esito.returncode}:\n{coda}")
    return destinazione / "radicali-1.pdf"


def estrai_testo(pdf: Path) -> str:
    _serve("pdftotext")
    esito = subprocess.run(["pdftotext", str(pdf), "-"], capture_output=True, text=True)
    assert esito.returncode == 0, esito.stderr
    return esito.stdout


def caratteri(contenuto: str) -> collections.Counter[str]:
    """Il contenuto come multinsieme di caratteri: gli spazi (e gli a-capo) fuori.

    Il riempimento delle celle, l'interruzione di una formula su due righe e il
    margine spostato cambiano gli spazi e non il contenuto: devono passare. Una
    formula tolta cambia questo conteggio, sempre.
    """
    return collections.Counter(c for c in contenuto.replace("\u00a0", " ") if not c.isspace())


def pagine(pdf: Path) -> int:
    _serve("pdfinfo")
    esito = subprocess.run(["pdfinfo", str(pdf)], capture_output=True, text=True)
    trovato = re.search(r"^Pages:\s+(\d+)$", esito.stdout, re.MULTILINE)
    assert trovato, "pdfinfo non ha detto quante pagine ha il PDF"
    return int(trovato.group(1))


def _pgm(percorso: Path) -> tuple[int, int, bytes]:
    """Legge un PGM grezzo (P5): larghezza, altezza, i pixel, uno per byte."""
    dati = percorso.read_bytes()
    assert dati[:2] == b"P5", f"pdftoppm ha scritto {dati[:2]!r}, non un PGM grezzo (P5)"
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
    assert massimo < 256, f"PGM a {massimo} livelli: atteso 8 bit per pixel"
    pixel = dati[posizione : posizione + larghezza * altezza]
    assert len(pixel) == larghezza * altezza, "PGM troncato: i pixel non tornano"
    return larghezza, altezza, pixel


def inchiostro(pdf: Path, cartella: Path) -> dict[str, object]:
    """I pixel disegnati, per colonna della tabella (grigio, 60 dpi)."""
    _serve("pdftoppm")
    cartella.mkdir(parents=True, exist_ok=True)
    base = cartella / "scheda"
    esito = subprocess.run(
        ["pdftoppm", "-r", "60", "-singlefile", "-gray", str(pdf), str(base)],
        capture_output=True,
        text=True,
    )
    assert esito.returncode == 0, esito.stderr
    larghezza, altezza, pixel = _pgm(base.with_suffix(".pgm"))
    per_mm = larghezza / 210.0  # A4 in orizzontale: 210 mm

    def conta(x0: float, x1: float) -> int:
        a, b = int(x0 * per_mm), int(x1 * per_mm)
        return sum(
            1
            for y in range(altezza)
            for i in range(a, b)
            if pixel[y * larghezza + i] < 200
        )

    colonne = [conta(*colonna) for colonna in COLONNE_MM]
    return {"colonne": colonne, "totale": sum(colonne), "righe": altezza, "larghezza": larghezza}


def differenza(originale: collections.Counter[str], nuovo: collections.Counter[str]) -> str:
    mancanti = {c: n for c, n in (originale - nuovo).items()}
    in_piu = {c: n for c, n in (nuovo - originale).items()}
    righe = []
    if mancanti:
        righe.append(f"NON c'è più (carattere × quante volte manca): {mancanti}")
    if in_piu:
        righe.append(f"c'è in più: {in_piu}")
    return "\n".join(righe)


@pytest.fixture(scope="module")
def scheda(tmp_path_factory: pytest.TempPathFactory) -> Path:
    return costruisci(tmp_path_factory.mktemp("scheda"))


@pytest.fixture(scope="module")
def originale() -> collections.Counter[str]:
    return caratteri(ORIGINALE_TXT.read_text(encoding="utf-8"))


# --------------------------------------------------------------------- le prove


def test_la_scheda_sta_in_una_pagina(scheda: Path) -> None:
    """Una pagina A4: è la richiesta dell'operatore, e il vincolo della scheda."""
    assert pagine(scheda) == 1, "la scheda è tornata su più fogli"


# Il 26/11/2026 la formula «Potenza di radice» è stata ridisegnata come quella
# dell'esempio dell'operatore: le parentesi sono a corpo testo, non più
# `\left( \right)` — che nel PDF diventavano due delimitatori alti quanto la
# radice, con l'esponente staccato in cima e due glifi privati (U+0012, U+0013)
# e due «!» nel testo estratto. La differenza è tutta qui, ed è dichiarata:
# tre coppie di tonde in più, quei quattro caratteri in meno. Tutto il resto
# deve restare identico all'originale: se cambia, il test lo dice.
DELTA_VOLUTO = collections.Counter({"(": 3, ")": 3})
DELTA_TOLTO = collections.Counter({"\x12": 1, "\x13": 1, "!": 2})


def test_il_testo_e_quello_dell_originale(scheda: Path, originale: collections.Counter[str]) -> None:
    """Zero caratteri mancanti e zero in più rispetto alla versione originale."""
    nuovo = caratteri(estrai_testo(scheda))
    assert nuovo + DELTA_TOLTO == originale + DELTA_VOLUTO, (
        "il contenuto della scheda è cambiato rispetto all'originale (140290 B, commit 7702236):\n"
        + differenza(originale, nuovo)
        + "\nSe il cambio è voluto: SCHEDE_UPDATE_GOLDEN=1 pytest tests/test_schede_radicali.py"
    )


def test_ogni_riga_e_ogni_formula_ha_il_suo_nome(scheda: Path) -> None:
    """Le due sezioni, le otto righe, le intestazioni e gli atomi di formula.

    Un errore qui dice QUALE riga o QUALE formula manca, invece di far leggere
    un diff di caratteri.
    """
    contenuto = estrai_testo(scheda)
    for sezione in SEZIONI:
        assert sezione in contenuto, f"manca la sezione «{sezione}»"
    for intestazione in INTESTAZIONI:
        assert intestazione in contenuto, f"manca l'intestazione «{intestazione}»"
    for riga in RIGHE:
        assert riga in contenuto, f"manca la riga «{riga}»"
    for atomo, quante in ATOMI.items():
        assert contenuto.count(atomo) == quante, (
            f"«{atomo}» compare {contenuto.count(atomo)} volte invece di {quante}: "
            "una formula che lo conteneva non c'è più"
        )
    assert contenuto.count(SBARRATO) == 1, (
        "manca la condizione della divisione «▲ ≠ 0»: la barra sovrapposta non c'è "
        f"({contenuto.count(SBARRATO)} volte invece di 1)"
    )


def test_la_scheda_disegna_quanto_l_originale(scheda: Path, tmp_path: Path) -> None:
    """Le formule disegnate (radice, frecce, forme) non sono testo: si contano i pixel."""
    atteso = json.loads(ORIGINALE_JSON.read_text(encoding="utf-8"))
    misurato = inchiostro(scheda, tmp_path)
    assert misurato["righe"] == atteso["righe"] and misurato["larghezza"] == atteso["larghezza"], (
        "la pagina non è più A4 a 60 dpi come quando è stato misurato l'originale: "
        f"{misurato['larghezza']}x{misurato['righe']} invece di "
        f"{atteso['larghezza']}x{atteso['righe']}"
    )
    for numero, (avuto, voluto) in enumerate(zip(misurato["colonne"], atteso["colonne"]), start=1):
        scarto = abs(avuto - voluto) / voluto
        assert scarto <= TOT_COLONNA, (
            f"colonna {numero}: {avuto} pixel disegnati invece di {voluto} "
            f"({scarto:.1%} di scarto, il tetto è {TOT_COLONNA:.0%}) — una formula disegnata non c'è più"
        )
    scarto = abs(misurato["totale"] - atteso["totale"]) / atteso["totale"]
    assert scarto <= TOT_TESTO, (
        f"inchiostro totale {misurato['totale']} invece di {atteso['totale']} ({scarto:.1%})"
    )


def test_il_pdf_committato_e_quello_che_il_sorgente_produce(scheda: Path) -> None:
    """Il PDF in repository non deve essere un artefatto vecchio.

    Il difetto del 26/11 è passato anche perché si guardava un PDF che non era
    quello del sorgente: qui i due contenuti devono coincidere.
    """
    assert COMMITTATO.exists(), "manca schede/radicali/radicali-1.pdf (make in schede/radicali)"
    committato = caratteri(estrai_testo(COMMITTATO))
    dal_sorgente = caratteri(estrai_testo(scheda))
    assert committato == dal_sorgente, (
        "il PDF committato non è quello che il .tex produce — ricompila con "
        "`make -C schede/radicali`:\n" + differenza(dal_sorgente, committato)
    )


def test_il_controllo_sa_fallire(tmp_path: Path) -> None:
    """Il controllo che ha lasciato passare il difetto non sapeva fallire: questo sì.

    Si toglie una riga intera («Radice di radice», la formula più annidata) dal
    sorgente, si ricompila, e si verifica che ENTRAMBI gli strati la vedano: il
    testo e l'inchiostro. Se questo test passasse, il confronto sarebbe cieco.
    """
    sorgente = SORGENTE.read_text(encoding="utf-8")
    inizio = sorgente.index("\\riga{\\voce{Radice di radice}")
    fine = sorgente.index("\\end{schedaTabella}", inizio)
    mutilato = sorgente[:inizio] + sorgente[fine:]
    assert "Radice di radice" not in mutilato  # la riga è davvero andata

    pdf = costruisci(tmp_path / "mutilato", mutilato)
    assert pagine(pdf) == 1, "togliendo una riga la scheda deve stare in una pagina comunque"

    originale = caratteri(ORIGINALE_TXT.read_text(encoding="utf-8"))
    nuovo = caratteri(estrai_testo(pdf))
    assert nuovo != originale, (
        "tolta la riga «Radice di radice» il confronto del testo non se n'è accorto: "
        "è lo stesso controllo cieco del 26/11 (contava le righe, non il contenuto)"
    )

    atteso = json.loads(ORIGINALE_JSON.read_text(encoding="utf-8"))
    misurato = inchiostro(pdf, tmp_path / "mutilato")
    scarto = (atteso["totale"] - misurato["totale"]) / atteso["totale"]
    assert scarto > TOT_TESTO, (
        f"tolta la riga «Radice di radice» l'inchiostro è calato solo del {scarto:.1%}: "
        "la misura dei pixel non se ne accorgerebbe"
    )


def test_il_golden_si_aggiorna_solo_apposta(tmp_path: Path) -> None:
    """Il golden si riscrive con SCHEDE_UPDATE_GOLDEN=1, e lo dice.

    Serve a chi cambia la scheda apposta: senza questo, «rifai il golden» è un
    comando che nessuno sa.
    """
    if os.environ.get("SCHEDE_UPDATE_GOLDEN") != "1":
        pytest.skip("si aggiorna solo con SCHEDE_UPDATE_GOLDEN=1")
    pdf = costruisci(tmp_path)
    ORIGINALE_TXT.write_text(estrai_testo(pdf), encoding="utf-8")
    misurato = inchiostro(pdf, tmp_path / "inchiostro")
    atteso = {"colonne": misurato["colonne"], "totale": misurato["totale"],
              "righe": misurato["righe"], "larghezza": misurato["larghezza"]}
    ORIGINALE_JSON.write_text(
        json.dumps({**json.loads(ORIGINALE_JSON.read_text(encoding="utf-8")), **atteso},
                   ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


# ------------------------------------------- l'inchiostro, CELLA per CELLA
#
# Il 26/11 il difetto è passato due volte di fila, e la seconda volta con un
# test dell'inchiostro già verde: quel test misurava i pixel per COLONNA. Una
# formula tolta dentro una cella sposta l'inchiostro di una colonna dell'1%, che
# sta dentro ogni tolleranza ragionevole; e il testo non la vede mai, perché il
# segno di radice e le frecce sono disegnati e non sono caratteri. Qui la misura
# scende a una cella per volta: otto righe per due colonne di formula, sedici
# riquadri, e ognuno deve avere il suo inchiostro.

# Le righe che portano formule, nell'ordine in cui compaiono; la chiave è la
# prima parola della cella «voce», che il testo estratto porta come parola.
RIGHE_DI_FORMULA = (
    "Indice pari",
    "Indice dispari",
    "Più radici pari",
    "Somma",
    "Prodotto",
    "Divisione",
    "Potenza",
    "Radice di radice",
)
COLONNE_DI_FORMULA = (1, 2)  # «schema visivo» ed «esempio»: la colonna 0 è testo
# Il minimo di pixel (a 100 dpi) sotto il quale un riquadro è vuoto: una cella
# vera ne ha centinaia, una svuotata ne tiene solo i bordi della tabella.
MINIMO_CELLA = 120


def _parole_con_posizione(pdf: Path) -> list[tuple[str, float, float, float, float]]:
    _serve("pdftotext")
    esito = subprocess.run(["pdftotext", "-bbox", str(pdf), "-"], capture_output=True, text=True)
    assert esito.returncode == 0, esito.stderr
    return [
        (m.group(5), float(m.group(1)), float(m.group(2)), float(m.group(3)), float(m.group(4)))
        for m in re.finditer(
            r'<word xMin="([\d.]+)" yMin="([\d.]+)" xMax="([\d.]+)" yMax="([\d.]+)">(.*?)</word>',
            esito.stdout,
        )
    ]


def inchiostro_per_cella(pdf: Path, cartella: Path) -> list[list[int]]:
    """I pixel disegnati in ogni cella di formula, riga per riga, a 100 dpi.

    Le righe si trovano DAL PDF (la posizione della parola che apre la cella
    «voce»), non da un numero scritto a mano: se una riga si sposta, la misura
    la segue.
    """
    _serve("pdftoppm")
    cartella.mkdir(parents=True, exist_ok=True)
    base = cartella / "celle"
    esito = subprocess.run(
        ["pdftoppm", "-r", "100", "-singlefile", "-gray", str(pdf), str(base)],
        capture_output=True,
        text=True,
    )
    assert esito.returncode == 0, esito.stderr
    larghezza, altezza, pixel = _pgm(base.with_suffix(".pgm"))
    per_punto = 100 / 72.0  # 100 dpi: un punto tipografico vale 1,39 pixel
    per_mm = larghezza / 210.0

    # Ogni riga comincia con una parola diversa; le righe si riconoscono dalla
    # posizione di quella parola. «Indice» apre DUE righe, quindi si raccolgono
    # tutte le posizioni e si tengono le otto righe distinte, in ordine.
    prime = {etichetta.split()[0] for etichetta in RIGHE_DI_FORMULA}
    righe_trovate: list[float] = []
    for (testo, _x0, y, _x1, _y1) in _parole_con_posizione(pdf):
        if testo in prime:
            if not righe_trovate or all(abs(y - gia) > 3 for gia in righe_trovate):
                righe_trovate.append(y)
    righe_trovate.sort()
    assert len(righe_trovate) == len(RIGHE_DI_FORMULA), (
        f"il testo estratto porta {len(righe_trovate)} righe invece di {len(RIGHE_DI_FORMULA)}"
    )
    ordinate = [(etichetta, y * per_punto) for etichetta, y in zip(RIGHE_DI_FORMULA, righe_trovate)]

    # Le righe di separazione della tabella sono nere da bordo a bordo: se non
    # si tolgono, una cella vuota conta comunque i filetti e la misura non sa
    # fallire (successo il 26/11: 942 pixel su una cella svuotata). Una riga di
    # immagine è «filetto» quando più della metà della pagina è scura.
    filetti = {
        y
        for y in range(altezza)
        if sum(1 for i in range(larghezza) if pixel[y * larghezza + i] < 200) > larghezza // 2
    }

    def conta(x0: float, x1: float, y0: float, y1: float) -> int:
        a, b = int(x0 * per_mm), int(x1 * per_mm)
        c, d = int(y0), int(y1)
        return sum(
            1
            for y in range(max(c, 0), min(d, altezza))
            if y not in filetti
            for i in range(a, b)
            if pixel[y * larghezza + i] < 200
        )

    misure: list[list[int]] = []
    for indice, (_etichetta, y) in enumerate(ordinate):
        # il fondo della riga è la cima della successiva, meno qualche pixel
        fine = ordinate[indice + 1][1] - 4 if indice + 1 < len(ordinate) else y + 90
        misure.append([conta(*COLONNE_MM[c], y, fine) for c in COLONNE_DI_FORMULA])
    return misure


def test_ogni_cella_di_formula_ha_il_suo_inchiostro(scheda: Path, tmp_path: Path) -> None:
    """Sedici riquadri, sedici misure: nessuna cella di formula può essere vuota.

    È il controllo che mancava il 26/11: per colonna una formula tolta si perde
    nell'1% di tolleranza, e il testo non la vede perché è disegnata.
    """
    misure = inchiostro_per_cella(scheda, tmp_path)
    assert len(misure) == len(RIGHE_DI_FORMULA), (
        f"misurate {len(misure)} righe invece di {len(RIGHE_DI_FORMULA)}"
    )
    vuote = [
        f"riga {i + 1} «{RIGHE_DI_FORMULA[i]}», colonna {c + 1}: {valore} pixel"
        for i, riga in enumerate(misure)
        for c, valore in enumerate(riga)
        if valore < MINIMO_CELLA
    ]
    assert not vuote, "celle di formula senza disegno (una formula non è stata disegnata):\n" + "\n".join(vuote)


def test_la_misura_per_cella_sa_fallire(tmp_path: Path) -> None:
    """Tolta UNA formula dentro una riga, la misura per cella la vede.

    Si toglie solo la formula della colonna «esempio» della riga «Prodotto»: la
    ``\\riga`` resta, il numero di righe resta, il testo estratto cambia di
    pochissimo (le forme sono disegnate) — e la cella resta vuota. Se questa
    prova passasse, la misura non varrebbe niente.
    """
    sorgente = SORGENTE.read_text(encoding="utf-8")
    inizio = sorgente.index("\\riga{\\voce{Prodotto}")
    fine = sorgente.index("\\riga{\\voce{Divisione}", inizio)
    riga = sorgente[inizio:fine]
    # la TERZA graffa della \\riga è l'esempio: si svuota quella, non la riga.
    # (Si cerca a graffe contate: dentro ci sono altre graffe, quelle degli
    # argomenti di \\voce e di \\radice, e un `rindex` prenderebbe l'ultima —
    # cioè il posto sbagliato, e il LaTeX morirebbe dentro la matematica.)
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

    misure = inchiostro_per_cella(pdf, tmp_path / "cella_vuota")
    indice = RIGHE_DI_FORMULA.index("Prodotto")
    esempio = misure[indice][COLONNE_DI_FORMULA.index(2)]
    assert esempio < MINIMO_CELLA, (
        f"svuotata la cella «esempio» della riga «Prodotto» la misura conta ancora "
        f"{esempio} pixel: la misura per cella non sa fallire"
    )
