# Le schede — LaTeX, in locale

Schede di matematica in LaTeX, da leggere e stampare, **non pubblicate online**:
stanno qui nel repository e si compilano con una riga. La grafica sta in una
libreria sola, così la prossima scheda è un file di venti righe e non un
copia-incolla di preambolo.

```
schede/
├── schede.sty            ← LA LIBRERIA: palette, forme, radice, tabelle, testata
├── radicali/
│   ├── Makefile          ← make radicali-1.pdf
│   ├── radicali-1.tex    ← «I Radicali: Schema Visivo» (la scheda del modello)
│   ├── radicali-1.pdf    ← compilata, pronta da guardare
│   ├── radicali-2.tex    ← «I Radicali: Semplificazione» (riusa la libreria)
│   └── radicali-2.pdf
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

## 6. Cosa NON è pubblicato

Niente di questa cartella va su `teaching.tazlab.net`: nessun deploy, nessuna
immagine Docker, nessun push su `master` da qui. I PDF si guardano in locale
(e si scaricano dal repository) finché l'operatore non chiede il contrario.
