#!/bin/bash
# ---------------------------------------------------------------------------
#  prova-palette.sh — la prova che la palette sta in un punto solo
#
#  Regola della casa (operatore, 26/11/2026): quadrato = blu, triangolo =
#  rosso, cerchio = verde, e i colori si definiscono UNA volta sola. Qui si
#  cambia il blu in quel punto (una riga di schede.sty), si ricompilano le
#  schede e si misura: il blu vecchio deve sparire e quello nuovo comparire
#  in TUTTE le schede. Poi la riga torna com'era e si ricompila.
#
#  QUALI schede: quelle dichiarate in schede.json (le stesse che il sito
#  elenca) PIU' quelle che stanno in una cartella con Makefile e .tex — così
#  una scheda nuova entra nella prova da sola, anche quando non è pubblicata
#  sul sito (la scheda dei polinomi: c'è, si compila, ma non è in schede.json).
#  Fino al 27/11/2026 lo script conosceva solo `radicali`: la scheda delle
#  potenze sarebbe rimasta fuori dalla prova senza che nessuno se ne
#  accorgesse, e i polinomi — che da schede.json non passano — ci sarebbero
#  rimasti anche dopo.
#
#  I PDF: la prova li RICOMPILA per misurarli, e poi rimette i byte che ha
#  trovato. Un PDF committato non cambia per una prova — se cambiasse, la
#  prova stessa lascerebbe la cartella sporca e il confronto col fixture del
#  sito salterebbe per un orologio, non per la palette.
#
#  Uso:  cd schede && ./prova-palette.sh
#  Esce 1 se una scheda non cambia colore. Serve pdflatex, pdftoppm, python3.
# ---------------------------------------------------------------------------
set -u

QUI=$(cd "$(dirname "$0")" && pwd)
STY="$QUI/schede.sty"
PRIMA="2563EB"            # il blu della casa
DOPO="7C3AED"             # un altro colore, solo per la prova
DPI=60                    # bassa risoluzione: bastano i pixel pieni

# Le schede da provare: prima quelle che schede.json dichiara (una riga per
# PDF), poi quelle che si presentano da sole — una cartella con <nome>.tex,
# <nome>.pdf e il suo Makefile. La cartella da ricompilare è quella del PDF.
mappa=$(python3 - "$QUI/schede.json" "$QUI" <<'PY'
import json, os, sys
dichiarate = []
for scheda in json.load(open(sys.argv[1]))["schede"]:
    dichiarate.append(scheda["file"])
    print(scheda["file"])
radice = sys.argv[2]
for nome in sorted(os.listdir(radice)):
    cartella = os.path.join(radice, nome)
    file = nome + "/" + nome + ".pdf"
    if not os.path.isdir(cartella) or file in dichiarate:
        continue
    if all(os.path.isfile(os.path.join(cartella, f))
           for f in (nome + ".tex", nome + ".pdf", "Makefile")):
        print(file)
PY
) || { echo "ERRORE: schede.json non si legge"; exit 1; }
if [ -z "$mappa" ]; then echo "ERRORE: schede.json non dichiara nessuna scheda"; exit 1; fi

copia=$(mktemp)
cp "$STY" "$copia"
# I byte dei PDF, uno per scheda: si rimettono alla fine (vedi l'intestazione).
magazzino=$(mktemp -d)
for file in $mappa; do
  [ -f "$QUI/$file" ] && cp "$QUI/$file" "$magazzino/$(echo "$file" | tr '/' '_')"
done
rimetti_pdf() {
  local file
  for file in $mappa; do
    [ -f "$magazzino/$(echo "$file" | tr '/' '_')" ] &&
      cp "$magazzino/$(echo "$file" | tr '/' '_')" "$QUI/$file"
  done
  rm -rf "$magazzino"
}
ripristina() {
  cp "$copia" "$STY"
  rm -f "$copia"
  compila_tutte >/dev/null 2>&1
  rimetti_pdf
}
trap ripristina EXIT INT TERM

# quanti pixel ESATTAMENTE di un colore (r,g,b) in un PDF
conta() { # $1=pdf $2=RRGGBB
  local pdf=$1 esa=$2 ppm
  ppm=$(mktemp)
  pdftoppm -r "$DPI" -singlefile "$pdf" "${ppm%.*}" >/dev/null 2>&1 || true
  if [ ! -f "${ppm%.*}.ppm" ]; then echo -1; rm -f "$ppm"; return; fi
  python3 - "$2" "${ppm%.*}.ppm" <<'PY'
import sys
esa, path = sys.argv[1].lower(), sys.argv[2]
vuoto = (int(esa[0:2],16), int(esa[2:4],16), int(esa[4:6],16))
f = open(path,'rb')
assert f.readline().strip() == b'P6'
linea = f.readline()
while linea.startswith(b'#'): linea = f.readline()
w,h = map(int, linea.split()); f.readline()
dati = f.read(w*h*3)
n = sum(1 for i in range(0, len(dati), 3)
        if (dati[i], dati[i+1], dati[i+2]) == vuoto)
print(n)
PY
  rm -f "${ppm%.*}.ppm" "$ppm"
}

# ricompila TUTTE le schede: ogni cartella che ha un Makefile e un .tex
compila_tutte() {
  local file cartella
  for file in $mappa; do
    cartella="$QUI/$(dirname "$file")"
    ( cd "$cartella" && make >/dev/null 2>&1 ) || { echo "ERRORE: make in $cartella"; return 1; }
  done
  return 0
}

compila() { compila_tutte || exit 1; }

echo "== 1. le schede come sono adesso (blu $PRIMA) =="
compila
for file in $mappa; do printf '  %-24s blu=%s\n' "$file" "$(conta "$QUI/$file" "$PRIMA")"; done

echo "== 2. cambio il blu in un punto solo: $PRIMA -> $DOPO =="
sed -i "s/^\\\\definecolor{schedeBlu}{HTML}{$PRIMA}/\\\\definecolor{schedeBlu}{HTML}{$DOPO}/" "$STY"
if ! grep -q "definecolor{schedeBlu}{HTML}{$DOPO}" "$STY"; then
  echo "ERRORE: la riga della palette non è stata cambiata (il file è cambiato di forma?)"
  exit 1
fi
compila
esito=0
for file in $mappa; do
  vecchio=$(conta "$QUI/$file" "$PRIMA")
  nuovo=$(conta "$QUI/$file" "$DOPO")
  printf '  %-24s blu=%s  %s=%s\n' "$file" "$vecchio" "$DOPO" "$nuovo"
  if [ "$vecchio" != "0" ] || [ "$nuovo" -le 0 ]; then
    echo "  ROSSO: $file non ha seguito la palette"; esito=1
  fi
done

echo "== 3. rimetto il blu della casa e ricompilo =="
cp "$copia" "$STY"
compila
for file in $mappa; do printf '  %-24s blu=%s\n' "$file" "$(conta "$QUI/$file" "$PRIMA")"; done
echo "== 4. rimetto i PDF com'erano =="
rm -f "$copia"
rimetti_pdf
trap - EXIT INT TERM

if [ "$esito" -eq 0 ]; then
  echo "VERDE: il blu si cambia in una riga e le schede lo seguono."
else
  echo "ROSSO: la palette non è in un punto solo."
fi
exit "$esito"
