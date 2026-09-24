"""Labelled scalars and an exponent-vector unit table (DESIGN §2.5).

Deliberately NOT ``sympy.physics.units``: it does not enforce dimensions on the answer
path (``3*meter + 2*second`` builds silently), carries a live ``convert_to`` bug class,
never evaluates ``sin(30*degree)``, and prints ``hour`` where ``h`` is expected. Here a
quantity is an exact ``Fraction`` plus a unit label; conversions are exact rational
scales, so 36 km/h is exactly 10 m/s and never 9.999999.
"""

from __future__ import annotations

from fractions import Fraction

# Base dimensions: metre, second, kilogram, radian.
DIMENSIONS = ("m", "s", "kg", "rad")

# Exact conversion factors to SI (multiply the value by the factor).
_TO_SI: dict[str, Fraction] = {
    "m": Fraction(1), "km": Fraction(1000), "cm": Fraction(1, 100),
    "s": Fraction(1), "min": Fraction(60), "h": Fraction(3600),
    "kg": Fraction(1), "g": Fraction(1, 1000),
    "m/s": Fraction(1), "km/h": Fraction(5, 18),
    "m/s^2": Fraction(1),
    "rad": Fraction(1),
    "Hz": Fraction(1),
}

_SPEED_OF_SOUND = Fraction(343)  # m/s in air at 20 °C — a named constant, never a draw


def speed_of_sound() -> Fraction:
    return _SPEED_OF_SOUND


def to_si(value: Fraction, unit: str) -> Fraction:
    """Convert to SI exactly. Unknown units are a programming error, not user input."""
    if unit not in _TO_SI:
        raise KeyError(f"unknown unit: {unit}")
    return Fraction(value) * _TO_SI[unit]


def convert(value: Fraction, frm: str, to: str) -> Fraction:
    """Exact conversion between compatible units (e.g. 36 km/h -> 10 m/s)."""
    if frm == to:
        return Fraction(value)
    si = to_si(value, frm)
    if to not in _TO_SI:
        raise KeyError(f"unknown unit: {to}")
    return si / _TO_SI[to]


def fmt(value: Fraction) -> str:
    """Exact textual form: integers stay integers, fractions stay fractions."""
    value = Fraction(value)
    return str(value.numerator) if value.denominator == 1 else f"{value.numerator}/{value.denominator}"


# A measured quantity is read as a decimal: 7/2 s is not how a textbook writes 3,5 s. The
# value stays an exact Fraction — only its rendering changes, and only when the decimal
# terminates, so nothing is ever rounded away.
_MAX_DECIMALS = 6


def fmt_reading(value: Fraction) -> str:
    """Exact textual form for a *measured* quantity: decimal if it terminates, else the
    fraction. Never a float: ``Fraction(7, 2)`` prints 3.5 but is still exactly 7/2."""
    value = Fraction(value)
    if value.denominator == 1:
        return str(value.numerator)
    for digits in range(1, _MAX_DECIMALS + 1):
        if (10 ** digits) % value.denominator == 0:
            break
    else:
        return f"{value.numerator}/{value.denominator}"
    sign = "-" if value < 0 else ""
    scaled = abs(value.numerator) * (10 ** digits) // value.denominator
    whole, fraction = divmod(scaled, 10 ** digits)
    text = f"{whole}.{fraction:0{digits}d}".rstrip("0").rstrip(".")
    return f"{sign}{text}"


# Unit label -> LaTeX: the caret must sit outside \text{}, or KaTeX refuses the formula
# (observed live: `1\,\text{m/s^2}` rendered as a red parse error).
_UNIT_LATEX = {
    "m": "\\text{m}", "km": "\\text{km}", "s": "\\text{s}", "min": "\\text{min}",
    "m/s": "\\text{m/s}", "km/h": "\\text{km/h}", "m/s^2": "\\text{m/s}^2",
}


def unit_latex(unit: str) -> str:
    """LaTeX for a unit label; an unmapped unit is a programming error, not user input."""
    try:
        return _UNIT_LATEX[unit]
    except KeyError as exc:
        raise KeyError(f"no LaTeX form for unit: {unit}") from exc
