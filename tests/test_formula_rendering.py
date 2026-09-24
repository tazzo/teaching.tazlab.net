"""Every formula the site can show must render — checked by rendering it.

Both surfaces (the browser and the PDF) call KaTeX with ``throwOnError: false``, so a
broken formula does not raise: it becomes a red error node. That is how
``1\\,\\text{m/s^2}`` reached a live page — a caret inside ``\\text{}`` is a parse error —
while 400 tests passed. The only check that catches it is rendering the real formulas of
real generated items through the same Node/KaTeX bridge the PDF uses.
"""

from __future__ import annotations

import shutil

import pytest

pytest.importorskip("weasyprint", reason="the KaTeX assets ship with the render path")

from app.core.rng import make_rng  # noqa: E402
from app.generators.registry import TOPICS  # noqa: E402
from app.render.pdf import _katex_dir, _render_katex  # noqa: E402

DIFFICULTIES = ("easy", "medium", "hard")
SEEDS = (1, 42)
if shutil.which("node") is None:
    pytest.skip("node is required to render formulas", allow_module_level=True)


def item_options(topic):
    """Every configuration a page can ask for: the topic's own list, or a single default."""
    configurer = getattr(topic, "configurer", None)
    if configurer is None:
        return [None]
    controls = configurer()
    values = {control["id"]: [choice["value"] for choice in control["choices"]]
              for control in controls if control["kind"] == "select"}
    segment_control = next((c for c in controls if c["kind"] == "segment_list"), None)
    if segment_control is None:
        kind_lists = [None]
    else:
        kinds = [choice["value"] for choice in segment_control["choices"]]
        kind_lists = [[kind] for kind in kinds] + [kinds[:2]]     # single segments, then a mix

    options = []
    for kind_list in kind_lists:
        for quantity in values.get("quantity", [None]):
            for units in values.get("units", [None]):
                for ask in values.get("ask", [None]):
                    candidate = {name: value for name, value in
                                 (("kinds", kind_list), ("quantity", quantity),
                                  ("units", units), ("ask", ask)) if value is not None}
                    try:
                        options.append(topic.validate_options(candidate))
                    except ValueError:
                        continue            # a combination the topic refuses by design
    return options


def formulas_of(item):
    """Every string that will be handed to KaTeX with its display mode."""
    return [(f"step{i}", step.latex, False) for i, step in enumerate(item.steps)] + \
           [("answer", item.answer.latex, True)]


def test_no_generated_formula_fails_to_render():
    formulas = []
    for topic_id, topic in sorted(TOPICS.items()):
        for options in item_options(topic):
            for difficulty in DIFFICULTIES:
                for seed in SEEDS:
                    item = topic.generate(make_rng(seed, topic.id, difficulty, 0),
                                          difficulty, seed, 0, options)
                    assert topic.verify(item).ok, f"{topic_id} produced an unverified item"
                    for name, latex, display in formulas_of(item):
                        formulas.append((f"{topic_id}|{difficulty}|{seed}|{name}",
                                         latex, display))
    assert len(formulas) > 200, "the sweep must cover the real catalogue"
    rendered = _render_katex(formulas, _katex_dir())
    broken = sorted(key for key, html in rendered.items() if "katex-error" in html)
    assert not broken, f"formulas the site cannot draw: {broken}"
