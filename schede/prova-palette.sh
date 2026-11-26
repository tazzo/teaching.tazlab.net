#!/bin/bash
# ---------------------------------------------------------------------------
#  prova-palette.sh — la prova che la palette sta in un punto solo
#
#  Regola della casa (operatore, 26/11/2026): quadrato = blu, triangolo =
#  rosso, cerchio = verde, e i colori si definiscono UNA volta sola. Qui si
#  cambia il blu in quel punto (una riga di schede.sty), si ricompila la
#  scheda e si misura: il blu vecchio deve sparire e quello nuovo comparire
#  in TUTTE le schede. Poi la riga torna com'era e si ricompila.
#
#  Uso:  cd schede && ./prova-palette.sh
#  Esce 1 se la scheda non cambia colore. Serve pdflatex, pdftoppm, python3.
# ---------------------------------------------------------------------------
set -u

QUI=$(cd "$(dirname "$0")" && pwd)
STY="$QUI/schede.sty"
PRIMA="2563EB"            # il blu della casa
DOPO="7C3AED"             # un altro colore, solo per la prova
CARTELLA="$QUI/radicali"
SCHEDE="radicali"
DPI=60                    # bassa risoluzione: bastano i pixel pieni

copia=$(mktemp)
cp "$STY" "$copia"
ripristina() {
  cp "$copia" "$STY"
  rm -f "$copia"
  ( cd "$CARTELLA" && make >/dev/null 2>&1 )
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

compila() { ( cd "$CARTELLA" && make >/dev/null 2>&1 ) || { echo "ERRORE: make in $CARTELLA"; exit 1; }; }

echo "== 1. la scheda com'è adesso (blu $PRIMA) =="
compila
for s in $SCHEDE; do printf '  %-12s blu=%s\n' "$s" "$(conta "$CARTELLA/$s.pdf" "$PRIMA")"; done

echo "== 2. cambio il blu in un punto solo: $PRIMA -> $DOPO =="
sed -i "s/^\\\\definecolor{schedeBlu}{HTML}{$PRIMA}/\\\\definecolor{schedeBlu}{HTML}{$DOPO}/" "$STY"
if ! grep -q "definecolor{schedeBlu}{HTML}{$DOPO}" "$STY"; then
  echo "ERRORE: la riga della palette non è stata cambiata (il file è cambiato di forma?)"
  exit 1
fi
compila
esito=0
for s in $SCHEDE; do
  vecchio=$(conta "$CARTELLA/$s.pdf" "$PRIMA")
  nuovo=$(conta "$CARTELLA/$s.pdf" "$DOPO")
  printf '  %-12s blu=%s  %s=%s\n' "$s" "$vecchio" "$DOPO" "$nuovo"
  if [ "$vecchio" != "0" ] || [ "$nuovo" -le 0 ]; then
    echo "  ROSSO: $s non ha seguito la palette"; esito=1
  fi
done

echo "== 3. rimetto il blu della casa e ricompilo =="
ripristina
trap - EXIT INT TERM
for s in $SCHEDE; do printf '  %-12s blu=%s\n' "$s" "$(conta "$CARTELLA/$s.pdf" "$PRIMA")"; done

if [ "$esito" -eq 0 ]; then
  echo "VERDE: il blu si cambia in una riga e la scheda lo segue."
else
  echo "ROSSO: la palette non è in un punto solo."
fi
exit "$esito"
