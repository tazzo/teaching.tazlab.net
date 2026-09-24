"""Wire items -> printable worksheet PDF (STRUCTURE §4.4).

One document, one source of truth per fact:

* the LaTeX on the item drives the screen (KaTeX in the browser) and the PDF (KaTeX in
  Node, here) — the renderer never re-derives a value;
* the label table ``app/i18n/it.json`` drives both surfaces; no prose lives in code;
* the layout is ``app/templates/print.css``, the markup ``worksheet.html.j2``.

KaTeX runs **once per document**, not once per formula: the whole formula set travels as
a single JSON payload on stdin and the rendered HTML comes back on stdout. The Node
binary and the ``katex`` package are copied into the runtime image by the Dockerfile, so
a render needs neither npm nor the network. A malformed formula comes back as a KaTeX
error node, exactly as in the browser (``throwOnError: false``) — a broken formula is
visible, never silently dropped.

Byte-reproducible: ``SOURCE_DATE_EPOCH`` (the only wall-clock input in the pipeline —
fontTools stamps it into every subset font's ``head.modified``) is pinned when the
environment does not provide one, and the PDF identifier is derived from the document
instead of letting pydyf write its random default. ``tests/test_pdf.py`` asserts that
two renders of the same items are byte-identical.
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
from contextlib import contextmanager
from fractions import Fraction
from functools import lru_cache
from pathlib import Path
from typing import Any, Iterator, Mapping, Sequence

from jinja2 import Environment, FileSystemLoader, StrictUndefined, select_autoescape

from app.core.strings import render_template
from app.core.units import fmt
from app.render.figure import KINEMATICS

#: Every label this module reads from the string table. A missing key is a packaging bug
#: (the label table and this module ship together), so it raises instead of printing a
#: blank line into a sheet a teacher is about to hand out.
DOCUMENT_LABELS = (
    "pdf.title",
    "pdf.field_name",
    "pdf.field_class",
    "pdf.field_date",
    "pdf.page",
    "pdf.page_of",
    "pdf.answer_key",
    "ui.answer",
)

#: 2026-09-24T00:00:00Z. Only used when the environment does not set SOURCE_DATE_EPOCH:
#: without it the two subset-font timestamps differ between renders and the "same sheet
#: every time" promise dies (research artifact §Q2, measured).
_FALLBACK_EPOCH = "1790208000"

_KATEX_TIMEOUT = 30  # seconds; a full worksheet is ~0.2 s of KaTeX

#: KaTeX runs under Node with the same options as web/src/formula.js, except for
#: ``output: "html"``: WeasyPrint has no MathML support (upstream issue #59), so the
#: parallel MathML tree the browser uses for accessibility would only inflate the page.
_KATEX_SCRIPT = r"""
import { readFileSync } from "node:fs";
import { pathToFileURL } from "node:url";

const input = JSON.parse(readFileSync(0, "utf8"));
const katex = (await import(pathToFileURL(input.katex).href)).default;
const rendered = {};
for (const [key, latex, display] of input.formulas) {
  rendered[key] = katex.renderToString(latex, {
    displayMode: display,
    throwOnError: false,
    strict: false,
    output: "html",
  });
}
process.stdout.write(JSON.stringify(rendered));
"""

# --------------------------------------------------------------- resources


def _template_dir() -> Path:
    """Locate ``app/templates`` in both layouts we run in.

    From the source tree (tests, ``uvicorn`` with the checkout as cwd) it sits next to
    the ``app`` package. The image installs the package into site-packages *and* keeps
    the source copy at ``/app/app``, so the cwd-relative candidate is what matches there.
    """
    override = os.environ.get("TEACHING_TEMPLATE_DIR")
    candidates = [
        *([Path(override)] if override else []),
        Path(__file__).resolve().parent.parent / "templates",
        Path.cwd() / "app" / "templates",
    ]
    for candidate in candidates:
        if (candidate / "worksheet.html.j2").is_file():
            return candidate
    raise FileNotFoundError(
        "worksheet template not found; looked in "
        + ", ".join(str(candidate) for candidate in candidates)
    )


def _katex_dir() -> Path:
    """The ``katex/dist`` directory holding ``katex.mjs``, ``katex.min.css`` and fonts."""
    override = os.environ.get("TEACHING_KATEX_DIR")
    candidates = [
        *([Path(override)] if override else []),
        Path("/opt/katex"),  # the runtime image (see Dockerfile)
        Path(__file__).resolve().parents[2] / "web" / "node_modules" / "katex" / "dist",
    ]
    for candidate in candidates:
        if (candidate / "katex.mjs").is_file() and (candidate / "katex.min.css").is_file():
            return candidate
    raise FileNotFoundError(
        "katex not found; looked in " + ", ".join(str(candidate) for candidate in candidates)
    )


@lru_cache(maxsize=8)
def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


@lru_cache(maxsize=1)
def _environment() -> Environment:
    # autoescape must cover .j2: the statement is prose with wire-supplied numbers in it,
    # and a worksheet is generated from a body anyone can post to /api/export.
    return Environment(
        loader=FileSystemLoader(str(_template_dir())),
        undefined=StrictUndefined,
        autoescape=select_autoescape(enabled_extensions=("html", "htm", "xml", "j2")),
        trim_blocks=True,
        lstrip_blocks=True,
    )


@contextmanager
def _frozen_clock() -> Iterator[None]:
    """Pin SOURCE_DATE_EPOCH for the duration of a render, then put the env back.

    Scoped rather than set-and-forget: this module is imported by a web process that has
    other business in ``os.environ``. Two concurrent renders write the same constant, so
    the window is harmless.
    """
    if "SOURCE_DATE_EPOCH" not in os.environ:
        os.environ["SOURCE_DATE_EPOCH"] = _FALLBACK_EPOCH
        try:
            yield
        finally:
            del os.environ["SOURCE_DATE_EPOCH"]
    else:
        yield


# ------------------------------------------------------------------- KaTeX


def _render_katex(formulas: Sequence[tuple[str, str, bool]], katex_dir: Path) -> dict[str, str]:
    """Render every formula of one document in a single Node process."""
    node = os.environ.get("TEACHING_NODE") or shutil.which("node")
    if node is None:
        raise RuntimeError("node is required to render formulas; see the Dockerfile runtime stage")
    payload = {
        "katex": str(katex_dir / "katex.mjs"),
        "formulas": [list(formula) for formula in formulas],
    }
    process = subprocess.run(
        [node, "--input-type=module", "-e", _KATEX_SCRIPT],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        timeout=_KATEX_TIMEOUT,
        check=False,
    )
    if process.returncode != 0:
        raise RuntimeError(f"katex failed (node exit {process.returncode}): {process.stderr.strip()[:400]}")
    return json.loads(process.stdout)


# ------------------------------------------------------------------- items


def _statement(item: Any, strings: Mapping[str, str]) -> str:
    """The statement sentence: the label template with the exact item numbers in it.

    Expansion is delegated to ``app.core.strings.render_template`` — the Python twin of
    web/src/formula.js ``renderText`` — so ``{name}``/``{+name}`` (and the typographic
    minus) read identically on both surfaces. Values are numeric: the wire path parses
    every parameter into a Fraction before an item reaches the renderer.
    """
    wire = getattr(item, "statement", None)
    if wire is not None:  # WireItem (app/api/schemas.py)
        key, params = wire.key, {name: str(value) for name, value in wire.params.items()}
    else:  # Item (app/generators/base.py) — what the export route passes
        key, params = item.statement_key, {name: str(value) for name, value in item.params.items()}
    return render_template(strings.get(key, key), params)


# ----------------------------------------------------------------- figures

#: Same two trace colours and marker colour as web/src/figure.js. They live here (and are
#: written as SVG presentation attributes) because WeasyPrint does not cascade document
#: CSS into an inline <svg>; the legend swatch next to each trace takes its colour from
#: the same constants, so the palette has exactly one home.
_TRACE_COLORS = ("#1f6feb", "#d29922")
_MARKER_COLOR = "#c0392b"

# SVG user units; the plot box is inset so the axis names have room of their own: the
# x name sits on a second line below the tick numbers, the y unit above the top tick.
_SVG_W, _SVG_H = 1000, 600
_PLOT_LEFT, _PLOT_RIGHT = 74, 26
_PLOT_TOP, _PLOT_BOTTOM = 44, 84
#: Trace labels that name the measured quantity of a series (it.json ``trace.*``).
_POSITION_TRACE, _VELOCITY_TRACE = "trace.position", "trace.velocity"
_MAX_TICKS = 6
#: Tick ladder — all exact Fractions, so a tick label is never a rounded float.
_STEP_LADDER = (
    Fraction(1, 4), Fraction(1, 2), Fraction(1), Fraction(2), Fraction(5), Fraction(10),
    Fraction(20), Fraction(30), Fraction(60), Fraction(100), Fraction(200), Fraction(500),
)


def _q(value: Fraction, places: int = 2) -> str:
    """Exact fixed-point SVG coordinate: no float ever touches the output."""
    scale = 10 ** places
    scaled = Fraction(value) * scale
    numerator, denominator = scaled.numerator, scaled.denominator
    whole, remainder = divmod(abs(numerator), denominator)
    if 2 * remainder >= denominator:
        whole += 1
    sign = "-" if numerator < 0 and whole else ""
    digits = f"{whole // scale}.{whole % scale:0{places}d}".rstrip("0").rstrip(".")
    return f"{sign}{digits or '0'}"


def _decimal(value: Fraction) -> str | None:
    """Exact decimal form when the expansion terminates (2^a·5^b), else ``None``."""
    remainder, twos, fives = value.denominator, 0, 0
    while remainder % 2 == 0:
        remainder //= 2
        twos += 1
    while remainder % 5 == 0:
        remainder //= 5
        fives += 1
    if remainder != 1:
        return None
    places = max(twos, fives)
    if places == 0:
        return fmt(value)
    scaled = abs(value * 10 ** places)
    digits = str(int(scaled)).rjust(places + 1, "0")
    sign = "-" if value < 0 else ""
    return f"{sign}{digits[:-places]}.{digits[-places:]}".rstrip("0").rstrip(".")


def _tick_label(value: Fraction) -> str:
    return _decimal(value) or fmt(value)


def _samples(trace: Mapping[str, Any], index: int) -> tuple[tuple[Fraction, Fraction], ...]:
    points = []
    for position, pair in enumerate(trace.get("samples") or []):
        try:
            x, y = pair
            points.append((Fraction(x), Fraction(y)))
        except (TypeError, ValueError, ZeroDivisionError) as exc:
            raise ValueError(f"figure trace {index} sample {position}: {exc!r}") from exc
    if not points:
        raise ValueError(f"figure trace {index} carries no samples")
    return tuple(points)


def _check_axis_unit(traces: list, y_unit: str) -> None:
    """One measured quantity per y axis, or refuse to draw.

    A shared y axis cannot be captioned ``[m]`` while also carrying an m/s trace: the
    student would read a speed off a metre scale. The trace label vocabulary says what
    the series measures, so the mismatch is detectable and is a payload bug — the axis
    caption would otherwise be a lie, on screen and in print alike.
    """
    keys = {key for key, _ in traces}
    if {_POSITION_TRACE, _VELOCITY_TRACE} <= keys:
        raise ValueError(
            "figure puts a position trace and a velocity trace on one y axis; "
            "a figure carries one measured quantity"
        )
    if _VELOCITY_TRACE in keys and "/" not in y_unit:
        raise ValueError(f"figure carries a {_VELOCITY_TRACE} trace under y_unit={y_unit!r}")
    if _POSITION_TRACE in keys and "/" in y_unit:
        raise ValueError(f"figure carries a {_POSITION_TRACE} trace under y_unit={y_unit!r}")


def _axis(low: Fraction, high: Fraction) -> tuple[Fraction, Fraction, list[Fraction]]:
    """Snap an axis to a nice exact step and list its ticks (at most ``_MAX_TICKS``)."""
    if high <= low:
        high = low + 1
    span = high - low
    step = next((candidate for candidate in _STEP_LADDER if span / candidate <= _MAX_TICKS), span / _MAX_TICKS)
    low = Fraction(low // step) * step
    high = Fraction(-(-high // step)) * step
    return low, high, [step * index for index in range(int(low / step), int(high / step) + 1)]


def _figure_html(figure: Mapping[str, Any], strings: Mapping[str, str]) -> str:
    """Draw a kinematics figure as inline SVG plus an HTML legend.

    The markup lives here rather than in the template because the swatch colour and the
    polyline stroke must come from one constant (see ``_TRACE_COLORS``); everything else
    — no prose, only labels from the table — matches the browser figure, which draws the
    same payload with JSXGraph. ``vectors``/``annotations`` are empty in every figure the
    generators emit today and are not drawn.
    """
    kind = figure.get("kind")
    if kind != KINEMATICS:
        raise ValueError(f"cannot draw figure kind {kind!r}")
    x_unit = str(figure.get("x_unit", ""))
    y_unit = str(figure.get("y_unit", ""))
    label = lambda key: strings.get(key, key)  # noqa: E731 - mirrors figure.js's fallback

    traces = [
        (str(trace.get("label_key", "")), _samples(trace, index))
        for index, trace in enumerate(figure.get("traces") or [])
    ]
    _check_axis_unit(traces, y_unit)
    markers = []
    for index, marker in enumerate(figure.get("markers") or []):
        try:
            t, s = marker["at"]
            markers.append((label(marker.get("label_key", "")), Fraction(t), Fraction(s)))
        except (KeyError, TypeError, ValueError, ZeroDivisionError) as exc:
            raise ValueError(f"figure marker {index}: {exc!r}") from exc
    if not traces:
        raise ValueError("figure carries no traces")

    domain = figure.get("domain") or {"t_min": "0", "t_max": "1"}
    t_min, t_max = Fraction(domain["t_min"]), Fraction(domain["t_max"])
    ts = [t for _, points in traces for t, _ in points] + [t for _, t, _ in markers]
    ss = [s for _, points in traces for _, s in points] + [s for _, _, s in markers]
    x_low, x_high, x_ticks = _axis(min(t_min, *ts), max(t_max, *ts))
    y_low, y_high, y_ticks = _axis(min(Fraction(0), *ss), max(ss))

    left, right, top = _PLOT_LEFT, _SVG_W - _PLOT_RIGHT, _PLOT_TOP
    bottom = _SVG_H - _PLOT_BOTTOM
    to_x = lambda t: left + (t - x_low) * (right - left) / (x_high - x_low)  # noqa: E731
    to_y = lambda s: bottom - (s - y_low) * (bottom - top) / (y_high - y_low)  # noqa: E731

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {_SVG_W} {_SVG_H}" '
        f'font-family="DejaVu Sans, sans-serif" font-size="22">',
    ]
    for tick in y_ticks:
        y = _q(to_y(tick))
        parts.append(
            f'<line x1="{left}" y1="{y}" x2="{right}" y2="{y}" stroke="#e8e8e8" '
            f'stroke-width="1" stroke-dasharray="6 6"/>'
        )
        parts.append(
            f'<text x="{_PLOT_LEFT - 12}" y="{y}" text-anchor="end" dominant-baseline="middle" '
            f'fill="#444">{_tick_label(tick)}</text>'
        )
    for tick in x_ticks:
        x = _q(to_x(tick))
        parts.append(
            f'<line x1="{x}" y1="{top}" x2="{x}" y2="{bottom}" stroke="#e8e8e8" '
            f'stroke-width="1" stroke-dasharray="6 6"/>'
        )
        parts.append(
            f'<text x="{x}" y="{bottom + 30}" text-anchor="middle" fill="#444">'
            f'{_tick_label(tick)}</text>'
        )
    parts.append(f'<line x1="{left}" y1="{top}" x2="{left}" y2="{bottom}" stroke="#333" stroke-width="2"/>')
    parts.append(f'<line x1="{left}" y1="{bottom}" x2="{right}" y2="{bottom}" stroke="#333" stroke-width="2"/>')
    # Axis names sit on the axes themselves, as in web/src/figure.js (`defaultAxes`):
    # the x axis gets "t [s]" on its own line under the tick numbers, the y axis its
    # unit from the payload above the top tick.
    parts.append(
        f'<text x="{right}" y="{bottom + 62}" text-anchor="end" fill="#333">'
        f'{label("axis.time")} [{x_unit}]</text>'
    )
    parts.append(
        f'<text x="{left}" y="{top - 20}" text-anchor="start" fill="#333">[{y_unit}]</text>'
    )

    for index, (key, points) in enumerate(traces):
        colour = _TRACE_COLORS[index % len(_TRACE_COLORS)]
        coordinates = " ".join(f"{_q(to_x(t))},{_q(to_y(s))}" for t, s in points)
        parts.append(
            f'<polyline points="{coordinates}" fill="none" stroke="{colour}" stroke-width="3"/>'
        )
    for _, t, s in markers:
        parts.append(
            f'<circle cx="{_q(to_x(t))}" cy="{_q(to_y(s))}" r="7" fill="{_MARKER_COLOR}"/>'
        )
    parts.append("</svg>")

    # The legend names the traces and locates the markers; it deliberately does not
    # repeat the y unit per trace (the payload's y_unit governs the whole y axis).
    legend = [
        f'<li><span style="display:inline-block;width:14px;height:3px;background:{colour}"></span> '
        f'{label(key)}</li>'
        for colour, (key, _) in zip(
            (_TRACE_COLORS[index % len(_TRACE_COLORS)] for index in range(len(traces))), traces
        )
    ]
    legend += [
        f'<li><span style="display:inline-block;width:8px;height:8px;border-radius:4px;'
        f'background:{_MARKER_COLOR}"></span> {text} ({_tick_label(t)} {x_unit}; '
        f'{_tick_label(s)} {y_unit})</li>'
        for text, t, s in markers
    ]
    return "".join(parts) + '<ul class="legend">' + "".join(legend) + "</ul>"


# ------------------------------------------------------------------- build


def _build(items: Sequence[Any], answers: bool, strings: Mapping[str, str]) -> tuple[dict[str, Any], Path | None]:
    """Assemble the template context and the KaTeX directory it needs.

    The directory is ``None`` when the document has no formula at all: a statements-only
    sheet carries no LaTeX (the statements are prose with exact numbers in them, as on
    screen), so it neither spawns Node nor embeds the KaTeX webfonts.
    """
    labels = {key: strings[key] for key in DOCUMENT_LABELS}

    formulas: list[tuple[str, str, bool]] = []
    if answers:
        for number, item in enumerate(items, start=1):
            formulas.extend(
                (f"step-{number}-{position}", step.latex, False)
                for position, step in enumerate(item.steps, start=1)
            )
            formulas.append((f"answer-{number}", item.answer.latex, True))
    katex_dir = _katex_dir() if formulas else None
    rendered = _render_katex(formulas, katex_dir) if katex_dir else {}

    built = []
    for number, item in enumerate(items, start=1):
        built.append({
            "number": number,
            "statement": _statement(item, strings),
            "figure": _figure_html(item.figure, strings) if item.figure else "",
            "steps": [
                {
                    "label": strings.get(step.label_key, step.label_key),
                    "html": rendered.get(f"step-{number}-{position}", ""),
                }
                for position, step in enumerate(item.steps, start=1)
            ],
            "answer": rendered.get(f"answer-{number}", ""),
        })

    context = {
        "lang": "it",
        "labels": labels,
        "answers": answers,
        "items": built,
        "print_css": _read(_template_dir() / "print.css"),
        # KaTeX's own stylesheet carries the @font-face rules; the webfonts resolve
        # against base_url (the katex dist directory), never against the network.
        "katex_css": _read(katex_dir / "katex.min.css") if katex_dir else "",
    }
    return context, katex_dir


def _document(context: Mapping[str, Any]) -> str:
    return _environment().get_template("worksheet.html.j2").render(**context)


def worksheet_html(items: Sequence[Any], answers: bool, strings: Mapping[str, str]) -> str:
    """The document the PDF is made of — the layout seam, and what tests inspect."""
    context, _ = _build(items, answers, strings)
    return _document(context)


def render_worksheet(items: Sequence[Any], answers: bool, strings: Mapping[str, str]) -> bytes:
    """Render a worksheet — and, when ``answers``, an answer key on a fresh page — to PDF.

    ``items`` are wire items as produced by ``app/api/schemas.py`` or the internal ``Item``
    they mirror; both carry the same fields and the export route passes the latter.
    ``strings`` is the label table (``app.core.strings.load_strings``). No FastAPI, no
    request object, no state beyond the clock pinned for the duration of the call.
    """
    from weasyprint import HTML  # lazy: WeasyPrint is heavy to import (research §Q2)

    context, katex_dir = _build(items, answers, strings)
    html = _document(context)
    with _frozen_clock():
        return HTML(
            string=html,
            # Relative @font-face URLs must land on the vendored katex files.
            base_url=str(katex_dir) + "/" if katex_dir else None,
        ).write_pdf(pdf_identifier=hashlib.sha256(html.encode("utf-8")).digest()[:16])
