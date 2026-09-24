"""The page catalogue: the site's information architecture (three levels).

    macro (Matematica | Fisica)
      └─ sub (Equazioni, Disequazioni, Cinematica, ...)
           └─ page — a *kind of exercise* with its own layout:
                problem        statement + steps + answer
                graph_reading  a graph is shown and the answer is read off it
                graph_filling  the data are given and the student fills an EMPTY graph

A page binds a kind to a topic (and optionally a difficulty), because the same
generator can be presented in different ways: reading a graph and completing one use
the same physics but require different work from the student.

Adding a page is one entry here plus its label in ``app/i18n``; the frontend routes and
renders from this catalogue, so no navigation logic is duplicated in the client.
"""

from __future__ import annotations

from dataclasses import dataclass

# page kinds — each maps to a renderer in web/src/pages.js
PROBLEM = "problem"
GRAPH_READING = "graph_reading"
GRAPH_FILLING = "graph_filling"
KINDS = (PROBLEM, GRAPH_READING, GRAPH_FILLING)


@dataclass(frozen=True)
class Page:
    id: str
    macro: str            # "matematica" | "fisica"
    sub: str              # sub-topic slug
    kind: str             # one of KINDS
    topic: str            # the generator that backs it
    difficulty: str | None = None   # None = the page exposes the difficulty selector
    label_key: str = ""
    order: int = 0


PAGES: tuple[Page, ...] = (
    # --- Fisica / Cinematica -------------------------------------------------
    Page("cinematica-grafici-lettura", "fisica", "cinematica", GRAPH_READING,
         "physics.kinematics.uniform", "hard", "page.cinematica.graph_reading", 10),
    Page("cinematica-grafici-completamento", "fisica", "cinematica", GRAPH_FILLING,
         "physics.kinematics.uniform", "easy", "page.cinematica.graph_filling", 20),
    Page("cinematica-problemi", "fisica", "cinematica", PROBLEM,
         "physics.kinematics.uniform", None, "page.cinematica.problems", 30),
    Page("cinematica-accelerato-problemi", "fisica", "cinematica", PROBLEM,
         "physics.kinematics.accelerated", None, "page.cinematica.accelerated_problems", 40),
    Page("cinematica-accelerato-grafici", "fisica", "cinematica", GRAPH_READING,
         "physics.kinematics.accelerated", "medium", "page.cinematica.accelerated_graphs", 50),
    Page("cinematica-multifase-problemi", "fisica", "cinematica", PROBLEM,
         "physics.kinematics.multi_phase", None, "page.cinematica.multiphase_problems", 60),
    Page("cinematica-multifase-grafici", "fisica", "cinematica", GRAPH_READING,
         "physics.kinematics.multi_phase", "easy", "page.cinematica.multiphase_graphs", 70),
    Page("cinematica-relativo-problemi", "fisica", "cinematica", PROBLEM,
         "physics.kinematics.relative", None, "page.cinematica.relative_problems", 80),
    Page("cinematica-relativo-grafici", "fisica", "cinematica", GRAPH_READING,
         "physics.kinematics.relative", "easy", "page.cinematica.relative_graphs", 90),
    Page("cinematica-circolare-problemi", "fisica", "cinematica", PROBLEM,
         "physics.kinematics.circular", None, "page.cinematica.circular_problems", 100),
    # --- Matematica / Equazioni ---------------------------------------------
    Page("equazioni-primo-grado", "matematica", "equazioni", PROBLEM,
         "math.equations.first_degree", None, "page.equazioni.first_degree", 10),
)

MACROS: tuple[str, ...] = ("matematica", "fisica")


def subs(macro: str) -> list[str]:
    """Sub-topics present under a macro, in page order."""
    seen: list[str] = []
    for page in sorted(PAGES, key=lambda p: p.order):
        if page.macro == macro and page.sub not in seen:
            seen.append(page.sub)
    return seen


def pages_for(macro: str, sub: str) -> list[Page]:
    return [p for p in sorted(PAGES, key=lambda p: p.order) if p.macro == macro and p.sub == sub]


def find_page(page_id: str) -> Page | None:
    return next((p for p in PAGES if p.id == page_id), None)
