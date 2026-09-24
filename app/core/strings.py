"""Label lookup (DESIGN §2.8).

The Italian strings live in ``app/i18n/it.json`` — one source of truth shared by the
API (for the PDF) and the frontend (which fetches them from ``GET /api/i18n``). v1 is
Italian-only; adding English is one file plus re-adding the ``lang`` parameter.
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

I18N_DIR = Path(__file__).resolve().parent.parent / "i18n"


@lru_cache(maxsize=4)
def load_strings(lang: str = "it") -> dict[str, str]:
    path = I18N_DIR / f"{lang}.json"
    if not path.exists():
        raise FileNotFoundError(f"no strings for language {lang!r}")
    return json.loads(path.read_text(encoding="utf-8"))


_PLACEHOLDER = "{{key}}"
_SIGNED = "{{+key}}"


def render_template(template: str, params: dict[str, str]) -> str:
    """Expand a template exactly like the frontend's ``renderText``.

    Grammar (keep the browser and the PDF in lockstep — a divergence prints literal
    ``{+b}`` on one surface and the intended value on the other):
      - ``{name}``  -> the value, with a leading ASCII hyphen rendered as U+2212
      - ``{+name}`` -> an explicit sign: ``+ 12`` / ``U+2212 12``
    """
    import re

    def _typographic(value: str) -> str:
        return f"\u2212{value[1:]}" if value.startswith("-") else value

    def _signed(value: str) -> str:
        negative = value.startswith("-")
        return f"{'\u2212' if negative else '+'} {value[1:] if negative else value}"

    out = re.sub(r"\{\+(\w+)\}", lambda m: _signed(str(params.get(m.group(1), "?"))), template)
    return re.sub(r"\{(\w+)\}", lambda m: _typographic(str(params.get(m.group(1), "?"))), out)
