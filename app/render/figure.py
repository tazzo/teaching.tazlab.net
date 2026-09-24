"""Item -> renderer-agnostic figure JSON (STRUCTURE §4.3).

The canonical schema, consumed by ``web/src/figure.js`` and by the PDF path. The figure
is a *projection of the solved parameters*: the server decides every coordinate, the
browser never derives a value, and the same payload drives screen and print.
"""

from __future__ import annotations

from fractions import Fraction

KINEMATICS = "kinematics"


def _pairs(samples: list[tuple[Fraction, Fraction]]) -> list[list[str]]:
    return [[_num(x), _num(y)] for x, y in samples]


def _num(value: Fraction) -> str:
    """Canonical exact rational string ("7/2"): the client parses it, it never rounds it."""
    value = Fraction(value)
    return str(value.numerator) if value.denominator == 1 else f"{value.numerator}/{value.denominator}"


def cartesian_trace(
    *,
    x_unit: str,
    y_unit: str,
    t_max: Fraction,
    samples: list[tuple[Fraction, Fraction]],
    trace_label: str,
    phase_label: str,
    markers: list[tuple[Fraction, Fraction, str]] | None = None,
    extra_traces: list[tuple[str, list[tuple[Fraction, Fraction]]]] | None = None,
) -> dict:
    """A single-phase kinematic graph: s(t) with optional markers and extra traces.

    ``samples`` must already include both endpoints of the phase, so the plot has exact
    vertices at the boundaries rather than wherever the sampling happened to land.
    """
    traces = [{"label_key": trace_label, "samples": _pairs(samples)}]
    for label, series in extra_traces or []:
        traces.append({"label_key": label, "samples": _pairs(series)})
    return {
        "kind": KINEMATICS,
        "x_unit": x_unit,
        "y_unit": y_unit,
        # graphs start at the origin: the axes meet in the bottom-left corner
        "origin": "corner",
        "domain": {"t_min": "0", "t_max": _num(t_max)},
        "phases": [{"label_key": phase_label, "t_from": "0", "t_to": _num(t_max), "style": "solid"}],
        "traces": traces,
        "markers": [
            {"label_key": label, "at": [_num(x), _num(y)]} for x, y, label in markers or []
        ],
        # dashed vertical dividers marking where one motion segment ends and the next begins
        "guides": [],
        "vectors": [],
        "annotations": [],
    }


def linear_samples(v: Fraction, t_max: Fraction, x0: Fraction = Fraction(0), steps: int = 4) -> list[tuple[Fraction, Fraction]]:
    """Exact samples of s(t) = x0 + v t, endpoints included."""
    pts = [(Fraction(0), x0)]
    for i in range(1, steps):
        ti = Fraction(t_max) * i / steps
        pts.append((ti, x0 + v * ti))
    pts.append((Fraction(t_max), x0 + v * Fraction(t_max)))
    return pts


def quadratic_samples(v0: Fraction, a: Fraction, t_max: Fraction, x0: Fraction = Fraction(0), steps: int = 8) -> list[tuple[Fraction, Fraction]]:
    """Exact samples of s(t) = x0 + v0 t + a t²/2, endpoints included."""
    f = lambda ti: x0 + v0 * ti + a * ti * ti / 2  # noqa: E731 - local, exact
    pts = [(Fraction(0), f(Fraction(0)))]
    for i in range(1, steps):
        ti = Fraction(t_max) * i / steps
        pts.append((ti, f(ti)))
    pts.append((Fraction(t_max), f(Fraction(t_max))))
    return pts
