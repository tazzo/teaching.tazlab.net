"""HTTP surface for the sheets (``/api/schede`` and the PDFs themselves).

The list and the file are one contract: the page shows the sha256 the API declares, and
the response body is the same bytes that digest was computed from — one object, not two
reads of the disk, so a recompiled PDF cannot slip between the two.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from fastapi.responses import Response

from app.schede import find_scheda, list_schede

router = APIRouter(tags=["schede"])


@router.get("/api/schede")
async def schede() -> dict:
    """The published sheets, each with its stable link and the version behind it."""
    return {"schede": [scheda.as_payload() for scheda in list_schede()]}


@router.get("/schede/{path:path}")
async def scheda(path: str) -> Response:
    """The PDF behind a stable address.

    Only a declared sheet is served — the lookup is by exact relative path against the
    manifest, so there is no path to traverse: anything else is a plain 404. The sha256
    travels back in a header too, so a ``curl -I`` alone says which version arrived.
    """
    found = find_scheda(path)
    if found is None:
        raise HTTPException(
            status_code=404,
            detail={"error": {"code": "scheda_not_found",
                              "message_key": "error.scheda_not_found",
                              "detail": path}},
        )
    name = found.file.rsplit("/", 1)[-1]
    return Response(
        content=found.content,
        media_type="application/pdf",
        headers={
            "content-disposition": f'inline; filename="{name}"',
            # the address is stable and the content is not: the browser must revalidate
            "cache-control": "no-cache",
            "etag": f'"{found.sha256}"',
            "x-scheda-sha256": found.sha256,
        },
    )
