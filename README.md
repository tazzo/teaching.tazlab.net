# teaching.tazlab.net

Applicazione didattica servita su `teaching.tazlab.net`: generatore di esercizi di matematica
(equazioni, disequazioni, sistemi) e di problemi di fisica (cinematica), con soluzioni
passo-passo verificate da SymPy, e le **schede** da leggere e stampare (sezione *Schede*:
PDF in LaTeX serviti a un indirizzo stabile che dà sempre l'ultima versione, con data,
commit e sha256 dichiarati in pagina).

Backend FastAPI + SymPy, frontend statico (JSXGraph + KaTeX), export PDF. Senza stato: nessun
database, nessun account. La pubblicazione dell'immagine avviene via GitHub Actions su Docker Hub
(`tazzo/tazlab-teaching`) e la distribuzione sul cluster via Flux GitOps.

## Come si lavora e come si pubblica (scritto una volta, il 2026-11-28)

`origin/master` **non è un ramo di lavoro: pubblica.** Un push su `master` fa partire
`Publish Teaching` (`.github/workflows/publish.yml`), che costruisce `tazzo/tazlab-teaching` e la manda
al cluster via Flux. Per questo il parto di un ramo e il push hanno **una porta sola**:

```bash
sh scripts/work.sh w/subagent-<id>          # un ramo nasce SEMPRE da origin/integra-schede-master
sh scripts/ship.sh                          # HEAD -> origin/integra-schede-master (il caso normale)
sh scripts/ship.sh --branch w/subagent-42   # un ramo di lavoro (backup)
ADA_ALLOW_PUBLISH=1 sh scripts/ship.sh --publish   # HEAD -> origin/master: PUBBLICA
```

`sh scripts/ship.sh` è l'unico modo di pushare: rifiuta `master` (a meno che l'operatore non abbia detto
«pubblica»), rifiuta un albero sporco, e **legge indietro** con `git ls-remote` stampando
`INFO ship pushed=<sha> ref=origin/integra-schede-master readback=<sha> ok=true` — quella riga è la
prova, non il «fatto». `make hooks` installa il `pre-push` che rifiuta a monte tutto il resto, anche per
chi fa un `git push` a mano.

Storia, perché è scritta qui e non in un brief: il 27/11/2026 un ramo nato da `github/master` è finito
su `master` (`f352740 -> 0d16293`), cinque run della pipeline sono andate rosse e la pubblicazione si è
fermata al run 40. Le prove di questo metodo stanno in `tests/test_push_method.py`.
