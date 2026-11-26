# Le schede — LaTeX, in locale

Schede di matematica in LaTeX, da leggere e stampare, **non pubblicate online**:
stanno qui nel repository e si compilano con una riga. La grafica sta in una
libreria sola, così la prossima scheda è un file di venti righe e non un
copia-incolla di preambolo.

```
schede/
├── schede.sty            ← LA LIBRERIA: palette, forme, radice, tabelle, testata
├── schede.json           ← QUALI schede sono pubblicate sul sito (l'elenco della pagina)
├── versions.json         ← scritto a ogni build: data, commit e sha256 (non si committa)
├── radicali/
│   ├── Makefile          ← make radicali-1.pdf
│   ├── radicali-1.tex    ← «I Radicali: Schema Visivo» (la scheda del modello)
│   ├── radicali-1.pdf    ← compilata, pubblicata su /schede/radicali/radicali-1.pdf
│   ├── radicali-2.tex    ← «I Radicali: Semplificazione» (riusa la libreria)
│   └── radicali-2.pdf    ← compilata, NON ancora pubblicata
├── prova-palette.sh      ← la prova che il blu si cambia in un punto solo
└── README.md             ← questo file
```

## 1. Le schede che ci sono

| file | che cos'è | pagine |
|---|---|---|
| `radicali/radicali-1.pdf` | **I Radicali: Schema Visivo** — campo di esistenza (indice pari, dispari, più radici pari) e operazioni (somma e sottrazione, prodotto, divisione, potenza di radice, radice di radice) | 1 |
| `radicali/radicali-2.pdf` | **I Radicali: Semplificazione** — la proprietà invariantiva, portar fuori, portar dentro | 1 |

Le due schede si assomigliano perché **non hanno grafica propria**: la prima
è il modello rifatto in LaTeX, la seconda è la prova che la libreria si riusa
(il suo preambolo sono due righe).

## 2. Come si compila

Serve TeX Live con `pdflatex` e il pacchetto `make`:

```sh
apt-get install texlive-latex-base texlive-latex-recommended \
                texlive-pictures texlive-lang-italian lmodern make
```

Poi, dalla cartella della scheda:

```sh
cd schede/radicali
make radicali-1.pdf      # oppure: make   (tutte)
```

Il `Makefile` lancia `pdflatex` **due volte** — la seconda passata serve al
«Pagina 1 di 1» del piede — e toglie i file di servizio (`.aux`, `.log`).
I PDF restano nella stessa cartella, accanto ai sorgenti.

## 3. Come si scrive una scheda nuova

Un file `.tex` in `schede/<argomento>/`, con questo preambolo e nient'altro:

```latex
\documentclass[10pt]{article}
\usepackage{schede}                 % ← la libreria, trovata da TEXINPUTS

\schedaTitolo{I Radicali: Semplificazione}{Proprietà invariantiva & portar fuori}
\schedaPiede{Schema di Matematica — I Radicali (2)}

\begin{document}
\schedaSezione{1}{La proprietà invariantiva}

\begin{schedaTabella}{Cosa si fa}{Schema visivo (stesso numero $n$)}{Esempio}
  \riga{\voce{Portar fuori}{(se il radicando è un prodotto)}}
       {$\radice[n]{\formaQuadrato^{n}\cdot\formaTriangolo}
         \;\freccia\;\formaQuadrato\cdot\radice[n]{\formaTriangolo}$}
       {$\radice[3]{\formaQuadrato^{3}\cdot\formaTriangolo}
         =\formaQuadrato\cdot\radice[3]{\formaTriangolo}$}
\end{schedaTabella}
\end{document}
```

Poi si aggiunge il nome del PDF a `SCHEDE` nel `Makefile` (`radicali-2.pdf`)
e si compila. **Se ti serve un comando che non c'è, si aggiunge in
`schede.sty`** — mai copiando il preambolo in una scheda: è la regola che
tiene in piedi tutto il resto.

## 4. I comandi della libreria

| comando | cosa scrive |
|---|---|
| `\schedaTitolo{titolo}{occhiello}` | testata: titolo grande a sinistra, occhiello in blu a destra |
| `\schedaPiede{testo}` | la riga grigia in fondo, a sinistra |
| `\schedaSezione{n}{titolo}` | la barretta blu, il numero e il filo sotto |
| `\begin{schedaTabella}{a}{b}{c} … \end{schedaTabella}` | tabella a tre colonne, intestazione a fascia |
| `\riga{voce}{schema}{esempio}` | una riga della tabella |
| `\voce{titolo}{nota}` | dentro una cella: titolo in grassetto, nota piccola e grigia sotto |
| `\schedaColonne{0.22}{0.40}{0.38}` | le tre larghezze (frazioni di riga), se servono diverse |
| `\riquadro[titolo]{testo}` | un riquadro con la regola in evidenza |
| `\formaQuadrato` `\formaTriangolo` `\formaCerchio` | le tre forme, **col colore già dentro** |
| `\formaRombo`, `\freccia`, `\freccia[etichetta]` | rombo e frecce, grigi della casa |
| `\radice{…}` `\radice[3]{…}` `\radice[n]{…}` | il segno di radice con l'indice, disegnato attorno al contenuto |
| `\cePari{…}` `\cePari[4]{…}` `\ceDispari{…}` | il campo di esistenza in un comando |
| `\sistema{riga\\riga}` | la graffa con le condizioni, una per riga |

Le forme reggono qualunque contenuto: una radice dentro una radice, un
esponente, una somma — il segno cresce da solo.

## 5. La regola dei colori (operatore, 26/11/2026)

**La forma porta il colore: quadrato = blu, triangolo = rosso, cerchio =
verde.** Nelle schede il codice non cambia mai, per non confondere. Chi
scrive una scheda non sceglie un colore: `\formaQuadrato` esce blu e basta.
Le forme che non sono una delle tre — il rombo, le frecce — sono **grigie**.

I quattro colori sono definiti **una volta sola**, in cima a `schede.sty`
(sezione 1, «LA PALETTE»): cambiare il blu è una riga, e cambia in tutte le
schede insieme. La prova è `./prova-palette.sh`: cambia quella riga,
ricompila le due schede, misura i pixel blu prima e dopo, e rimette tutto
com'era.

```sh
cd schede
./prova-palette.sh
```

## 6. Cosa finisce sul sito (`teaching.tazlab.net/schede/…`)

Le schede pubblicate si leggono e si scaricano da **`teaching.tazlab.net`**, sezione
**Schede** del menu. Tre regole, e sono quelle che rendono il link affidabile:

1. **Il nome del PDF è stabile.** Il link è sempre
   `/schede/radicali/radicali-1.pdf`: chi lo salva nei preferiti ci torna e trova
   **l'ultima versione**, perché una ricompilazione sostituisce i byte dietro lo stesso
   indirizzo. Mai mettere la data nel nome del file: il link si romperebbe.
2. **Si pubblica solo ciò che è dichiarato in `schede/schede.json`.** Un PDF compilato e
   lasciato nella cartella non è pubblicato: pubblicare è una decisione, non un effetto
   collaterale del copiare un file. Per pubblicare una scheda nuova si aggiunge una voce:

   ```json
   {"file": "radicali/radicali-1.pdf", "title": "I Radicali: Schema Visivo",
    "subtitle": "Campo di esistenza e operazioni", "order": 10}
   ```

   La pagina le elenca tutte in ordine di `order`; le prossime compaiono da sole.
3. **La pagina dice quale versione è**, perché il nome non può dirlo: `aggiornata al
   2026-11-26, da c72747d` (data e commit dell'ultima modifica al PDF) e lo **sha256**
   del file. Il numero viene da `schede/versions.json`, scritto a ogni build da
   `scripts/schede_versions.py` con la storia git completa: l'immagine non ha `.git`, e
   senza quel file la pagina potrebbe dire solo *compilata il …*.
   `versions.json` **non si committa** (è nella `.gitignore`): è un prodotto della build.

Quindi, per aggiornare una scheda già pubblicata:

```sh
cd schede/radicali && make radicali-1.pdf      # ricompila: il link resta lo stesso
git add radicali-1.pdf && git commit && git push   # su master: il sito si aggiorna da solo
```

La data e il commit in pagina si aggiornano da soli alla build successiva, perché sono
quelli dell'ultimo commit che ha toccato il PDF. Il sha256 è calcolato **sui byte
serviti**: non può dichiarare un file diverso da quello che scarichi.

I test che difendono tutto questo sono `tests/test_schede_page.py` (lato server: link
stabile, sha256 servito uguale a quello dichiarato, PDF non dichiarati non serviti, data e
commit uguali a quelli di git) e `web/test/schede.test.js` (lato pagina: menu, link,
versione, sha256).
