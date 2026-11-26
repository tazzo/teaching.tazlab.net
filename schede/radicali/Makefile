# Makefile delle schede — una scheda si compila con una riga:
#
#     make radicali-1.pdf
#     make            (tutte)
#     make pulisci    (toglie i file di servizio di LaTeX)
#
# La libreria sta in ../schede.sty: si trova da sola (TEXINPUTS), e non si
# copia in ogni scheda. Se un comando manca, si aggiunge lì.
#
# Serve pdflatex (TeX Live): `apt-get install texlive-latex-base
# texlive-latex-recommended texlive-pictures texlive-lang-italian lmodern`.
# Due passate: la seconda serve al «Pagina n di N» del piede.

TEXINPUTS_ := .:$(CURDIR)/..:
LATEX = TEXINPUTS="$(TEXINPUTS_)" pdflatex -interaction=nonstopmode -halt-on-error
LIB := ../schede.sty
SCHEDE := radicali-1.pdf radicali-2.pdf

.PHONY: all pulisci

all: $(SCHEDE)

%.pdf: %.tex $(LIB)
	$(LATEX) $*.tex
	$(LATEX) $*.tex
	@rm -f $*.aux $*.log $*.out

pulisci:
	@rm -f *.aux *.log *.out
