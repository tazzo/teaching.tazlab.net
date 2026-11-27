# Makefile della scheda — una scheda si compila con una riga:
#
#     make potenze.pdf
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
# LE POTENZE (ordine dell'operatore, 27/11/2026): le due sezioni del suo PDF
# — operazioni con la stessa base, stesso esponente e casi particolari — in
# una pagina A4, senza togliere nessuna proprietà.

TEXINPUTS_ := .:$(CURDIR)/..:
LATEX = TEXINPUTS="$(TEXINPUTS_)" pdflatex -interaction=nonstopmode -halt-on-error
LIB := ../schede.sty
SCHEDE := potenze.pdf

.PHONY: all pulisci

all: $(SCHEDE)

%.pdf: %.tex $(LIB)
	$(LATEX) $*.tex
	$(LATEX) $*.tex
	@rm -f $*.aux $*.log $*.out

pulisci:
	@rm -f *.aux *.log *.out
