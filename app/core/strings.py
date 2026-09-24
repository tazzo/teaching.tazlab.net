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
