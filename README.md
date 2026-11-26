# teaching.tazlab.net

Applicazione didattica servita su `teaching.tazlab.net`: generatore di esercizi di matematica
(equazioni, disequazioni, sistemi) e di problemi di fisica (cinematica), con soluzioni
passo-passo verificate da SymPy, e le **schede** da leggere e stampare (sezione *Schede*:
PDF in LaTeX serviti a un indirizzo stabile che dà sempre l'ultima versione, con data,
commit e sha256 dichiarati in pagina).

Backend FastAPI + SymPy, frontend statico (JSXGraph + KaTeX), export PDF. Senza stato: nessun
database, nessun account. La pubblicazione dell'immagine avviene via GitHub Actions su Docker Hub
(`tazzo/tazlab-teaching`) e la distribuzione sul cluster via Flux GitOps.
