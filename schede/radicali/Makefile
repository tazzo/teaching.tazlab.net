# Makefile delle schede — una scheda si compila con una riga:
#
#     make radicali.pdf
#     make            (la scheda)
#     make pulisci    (toglie i file di servizio di LaTeX)
#
# La libreria sta in ../schede.sty: si trova da sola (TEXINPUTS), e non si
# copia in ogni scheda. Se un comando manca, si aggiunge lì.
#
# Serve pdflatex (TeX Live): `apt-get install texlive-latex-base
# texlive-latex-recommended texlive-pictures texlive-lang-italian lmodern`.
# Due passate: la seconda serve al «Pagina n di N» del piede.
#
# UNA SOLA SCHEDA (ordine dell'operatore, 26/11/2026): i radicali hanno una
# scheda sola — campo di esistenza, operazioni e semplificazione in una
# pagina. C'era anche radicali-2 (la semplificazione): il suo contenuto è
# dentro radicali.tex, e il file non c'è più.

TEXINPUTS_ := .:$(CURDIR)/..:
LATEX = TEXINPUTS="$(TEXINPUTS_)" pdflatex -interaction=nonstopmode -halt-on-error
LIB := ../schede.sty
SCHEDE := radicali.pdf

.PHONY: all pulisci

all: $(SCHEDE)

%.pdf: %.tex $(LIB)
	$(LATEX) $*.tex
	$(LATEX) $*.tex
	@rm -f $*.aux $*.log $*.out

pulisci:
	@rm -f *.aux *.log *.out
