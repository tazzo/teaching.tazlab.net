"""The PDF path (app/render/pdf.py).

WeasyPrint is a heavy optional import on a workstation; the test skips only if the
package is genuinely absent, and the Dockerfile change is verified separately (see the
report): nothing here is silently skipped when the runtime image's libraries exist.
"""

from __future__ import annotations

import os
import shutil
import subprocess
from dataclasses import replace
from fractions import Fraction

import pytest

pytest.importorskip("weasyprint", reason="WeasyPrint not installed")

from app.core.rng import make_rng  # noqa: E402
from app.generators.base import Answer, Item, Step  # noqa: E402
from app.generators.registry import TOPICS  # noqa: E402
from app.render.figure import cartesian_trace, linear_samples  # noqa: E402
from app.render.pdf import DOCUMENT_LABELS, render_worksheet, worksheet_html  # noqa: E402

# The renderer reads DOCUMENT_LABELS from the shipped table (app/i18n/it.json). The
# fixture repeats them on purpose: this file must not start failing (or passing) because
# of a label-table edit elsewhere.
STRINGS: dict[str, str] = {
    "pdf.title": "Scheda di esercizi",
    "pdf.field_name": "Nome",
    "pdf.field_class": "Classe",
    "pdf.field_date": "Data",
    "pdf.page": "Pagina",
    "pdf.page_of": "di",
    "pdf.answer_key": "Soluzioni",
    "ui.answer": "Soluzione",
    # fixture labels
    "stmt.test": "Risolvi l'equazione: {a}x {+b} = 0",
    "step.test": "Sottraggo il termine noto",
    "step.result": "Risultato",
    "trace.position": "s(t)",
    "trace.velocity": "v(t)",
    "marker.asked_instant": "istante richiesto",
    "axis.time": "t",
}


def _figure(v: Fraction, t_max: Fraction, *, velocity: bool = False) -> dict:
    """A real payload from the shared figure builder: one measured quantity per axis."""
    return cartesian_trace(
        x_unit="s",
        y_unit="m/s" if velocity else "m",
        t_max=t_max,
        samples=linear_samples(v, t_max),
        trace_label="trace.velocity" if velocity else "trace.position",
        phase_label="phase.uniform",
        markers=[(t_max, v * t_max, "marker.asked_instant")],
    )


def _items() -> list[Item]:
    """Two exercises, one with a figure: enough for statement, figure, steps, answer."""
    return [
        Item(
            topic="math.equations.first_degree",
            difficulty="easy",
            seed=1,
            index=1,
            params={"a": Fraction(2), "b": Fraction(-8), "solution": Fraction(4)},
            statement_key="stmt.test",
            steps=(
                Step("step.test", "2x = 8"),
                Step("step.result", "x = 4"),
            ),
            answer=Answer("x = 4", "value", {"solutions": ["4"]}),
        ),
        Item(
            topic="physics.kinematics.uniform",
            difficulty="hard",
            seed=1,
            index=2,
            params={"v": Fraction(4), "t": Fraction(5)},
            statement_key="stmt.test",
            steps=(Step("step.test", "s = v\\,t"),),
            answer=Answer("20\\,\\text{m}", "scalar_with_unit", {"value": ["20"], "unit": ["m"]}),
            figure=_figure(Fraction(4), Fraction(5)),
        ),
    ]


def _pdf_text(pdf: bytes) -> str | None:
    """Extracted text, or ``None`` when poppler is not installed on this host."""
    exe = shutil.which("pdftotext")
    if exe is None:
        return None
    done = subprocess.run([exe, "-", "-"], input=pdf, capture_output=True, check=True)
    return done.stdout.decode("utf-8", "replace")


# ------------------------------------------------------------------ the artefact


def test_render_produces_a_pdf():
    pdf = render_worksheet(_items(), answers=False, strings=STRINGS)
    assert pdf.startswith(b"%PDF-")
    assert pdf.rstrip().endswith(b"%%EOF")
    assert len(pdf) > 5000  # a two-exercise sheet with a figure is never a stub


def test_two_renders_are_byte_identical(monkeypatch):
    """The product promise: the same sheet every time (research §Q2, D9)."""
    monkeypatch.setenv("SOURCE_DATE_EPOCH", "1700000000")
    items = _items()
    for answers in (False, True):
        assert render_worksheet(items, answers=answers, strings=STRINGS) == render_worksheet(
            items, answers=answers, strings=STRINGS
        )


def test_reproducible_without_source_date_epoch(monkeypatch):
    """An in-cluster render that was never handed the variable is still reproducible."""
    monkeypatch.delenv("SOURCE_DATE_EPOCH", raising=False)
    items = _items()
    assert render_worksheet(items, answers=True, strings=STRINGS) == render_worksheet(
        items, answers=True, strings=STRINGS
    )
    # the pinning is scoped to the call: the web process gets its environment back
    assert "SOURCE_DATE_EPOCH" not in os.environ


def test_answer_key_differs_from_worksheet_only(monkeypatch):
    monkeypatch.setenv("SOURCE_DATE_EPOCH", "1700000000")
    items = _items()
    worksheet = render_worksheet(items, answers=False, strings=STRINGS)
    key = render_worksheet(items, answers=True, strings=STRINGS)
    assert worksheet.startswith(b"%PDF-") and key.startswith(b"%PDF-")
    assert worksheet != key


def test_answer_key_text_is_only_in_the_key(monkeypatch):
    """The difference is the key section, not just a different PDF identifier."""
    monkeypatch.setenv("SOURCE_DATE_EPOCH", "1700000000")
    items = _items()
    worksheet_text = _pdf_text(render_worksheet(items, answers=False, strings=STRINGS))
    key_text = _pdf_text(render_worksheet(items, answers=True, strings=STRINGS))
    if worksheet_text is None or key_text is None:
        pytest.skip("pdftotext (poppler) is not installed")
    assert "Soluzioni" in key_text and "Soluzioni" not in worksheet_text
    assert "Risolvi l'equazione" in worksheet_text and "Risolvi l'equazione" in key_text
    # page counters come from the @page margin boxes in print.css
    assert "Pagina 1 di" in worksheet_text and "Pagina 1 di" in key_text
    # D9: the sheet never carries the seed
    assert "seed" not in worksheet_text.lower()


def test_answer_key_paginates_the_key_onto_its_own_page(monkeypatch):
    monkeypatch.setenv("SOURCE_DATE_EPOCH", "1700000000")
    key_text = _pdf_text(render_worksheet(_items(), answers=True, strings=STRINGS))
    if key_text is None:
        pytest.skip("pdftotext (poppler) is not installed")
    key_page = key_text[key_text.index("Soluzioni") :]
    assert "Pagina 2 di" in key_page  # break-before: page put the key on a new sheet


# ------------------------------------------------------------------- inputs


def test_wire_items_and_internal_items_render_the_same_document(monkeypatch):
    """The export route passes Items; the wire schema carries the same fields."""
    monkeypatch.setenv("SOURCE_DATE_EPOCH", "1700000000")
    from app.api.schemas import WireAnswer, WireItem, WireStatement, WireStep

    items = _items()
    wire = [
        WireItem(
            index=item.index,
            statement=WireStatement(
                key=item.statement_key, params={k: str(v) for k, v in item.params.items()}
            ),
            steps=[WireStep(label_key=s.label_key, latex=s.latex) for s in item.steps],
            answer=WireAnswer(latex=item.answer.latex, kind=item.answer.kind, payload=item.answer.payload),
            figure=item.figure,
        )
        for item in items
    ]
    assert render_worksheet(wire, answers=True, strings=STRINGS) == render_worksheet(
        items, answers=True, strings=STRINGS
    )


def test_missing_label_is_an_error_not_a_blank_line():
    strings = {key: value for key, value in STRINGS.items() if key != "pdf.title"}
    with pytest.raises(KeyError):
        render_worksheet(_items(), answers=False, strings=strings)


def test_declared_labels_cover_every_string_the_renderer_reads():
    assert set(DOCUMENT_LABELS) <= set(STRINGS)


# ------------------------------------------------------------------ refusals


def test_figure_whose_traces_disagree_with_the_axis_unit_is_refused():
    """A metre axis over a v(t) trace prints a lie, so the renderer refuses to draw it."""
    items = _items()
    items[-1] = replace(
        items[-1],
        figure=cartesian_trace(
            x_unit="s",
            y_unit="m",
            t_max=Fraction(5),
            samples=linear_samples(Fraction(4), Fraction(5)),
            trace_label="trace.velocity",
            phase_label="phase.uniform",
        ),
    )
    with pytest.raises(ValueError, match="y_unit"):
        render_worksheet(items, answers=False, strings=STRINGS)


def test_figure_with_two_quantities_on_one_axis_is_refused():
    figure = _figure(Fraction(4), Fraction(5))
    figure["traces"].append({"label_key": "trace.velocity", "samples": [["0", "0"], ["5", "5"]]})
    items = _items()
    items[-1] = replace(items[-1], figure=figure)
    with pytest.raises(ValueError, match="one measured quantity"):
        render_worksheet(items, answers=False, strings=STRINGS)


# ----------------------------------------------------------------- integration


def test_generated_items_render(monkeypatch):
    """Real generator payloads (figure included) survive the PDF path."""
    monkeypatch.setenv("SOURCE_DATE_EPOCH", "1700000000")
    strings = dict(STRINGS)
    items = []
    for position, (topic, difficulty) in enumerate(
        [("math.equations.first_degree", "medium"), ("physics.kinematics.uniform", "hard")], start=1
    ):
        impl = TOPICS[topic]
        items.append(impl.generate(make_rng(11, topic, difficulty, position), difficulty, 11, position))
    html = worksheet_html(items, answers=True, strings=strings)
    assert "katex" in html  # the key carries KaTeX markup, so the fonts must resolve
    pdf = render_worksheet(items, answers=True, strings=strings)
    assert pdf.startswith(b"%PDF-")
    assert pdf == render_worksheet(items, answers=True, strings=strings)
