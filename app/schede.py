"""The sheets (*schede*) the site publishes, and which version of each is behind the link.

A sheet is a PDF compiled from LaTeX under ``schede/`` and published at a **stable
address** — ``/schede/radicali/radicali-1.pdf``. Recompiling replaces the bytes behind
that address, so a link the operator saved keeps giving him the latest version; what the
name cannot say is *which* version that is, and the page says it instead: the date the
sheet was produced, the commit that last changed it, and the sha256 of the bytes served.

Two rules keep the announcement honest, and both are load-bearing:

* **the sha256 is computed from the very bytes that are served.** The digest and the
  response body come from one object in memory (``Scheda.content``), so a declaration
  cannot outlive the file it describes — the page cannot be right about a PDF that has
  changed under it.
* **a sheet is published only when ``schede/schede.json`` lists it.** A PDF sitting in
  the tree is not served until it is declared: publishing is a decision somebody took,
  not a side effect of copying a file into a directory. The allowlist *is* the manifest,
  which is also why a request for any other path is a plain 404 and not a path check.

Where the date and the commit come from, in order (the first that answers wins):

1. ``schede/versions.json`` — written at image build time by ``scripts/schede_versions.py``,
   the one place where the whole git history is at hand (the image has no ``.git``);
2. git itself, when this runs inside a checkout (local development);
3. the PDF's own ``/CreationDate`` — a date with no commit, which the page renders as
   "compilata il …" instead of inventing an author.

A missing commit is never filled in with something else: the page would then say "da
<sha>" about a commit that never touched the sheet, and the operator would learn to stop
trusting the line.
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import re
import subprocess
from dataclasses import dataclass, field
from pathlib import Path

logger = logging.getLogger("teaching.schede")

ROOT = Path(__file__).resolve().parent.parent
SCHEDE_DIR = Path(os.environ.get("TEACHING_SCHEDE_DIR") or (ROOT / "schede"))
MANIFEST = SCHEDE_DIR / "schede.json"
VERSIONS = SCHEDE_DIR / "versions.json"
URL_PREFIX = "/schede/"

# pdflatex writes the moment it compiled into the PDF's Info dictionary, uncompressed.
_CREATION = re.compile(rb"/CreationDate\s*\(D:(\d{4})(\d{2})(\d{2})")


@dataclass(frozen=True)
class Scheda:
    """One published sheet: what it is, and the version behind its stable address."""

    id: str                 # "radicali/radicali-1"
    file: str               # "radicali/radicali-1.pdf" — relative to schede/
    url: str                # "/schede/radicali/radicali-1.pdf"
    title: str
    subtitle: str
    order: int
    sha256: str
    bytes: int
    updated: str | None     # "2026-11-26" — when this version was produced
    commit: str | None      # "c72747d" — the commit that last changed the sheet
    version_source: str     # "versions" | "git" | "pdf" | "none"
    # the exact bytes behind `url`; the digest above is theirs. Not serialised.
    content: bytes = field(default=b"", repr=False, compare=False)

    def as_payload(self) -> dict:
        """The wire form: everything the page shows, and not the PDF itself."""
        return {
            "id": self.id,
            "file": self.file,
            "url": self.url,
            "title": self.title,
            "subtitle": self.subtitle,
            "order": self.order,
            "sha256": self.sha256,
            "bytes": self.bytes,
            "updated": self.updated,
            "commit": self.commit,
            "versionSource": self.version_source,
        }


# signature of the file the cached entry was built from, so a recompiled PDF on a
# developer's machine is noticed without restarting the server
_CACHE: dict[str, tuple[tuple[int, int], Scheda]] = {}


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 16), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _pdf_date(content: bytes) -> str | None:
    match = _CREATION.search(content)
    if not match:
        return None
    year, month, day = (part.decode("ascii") for part in match.groups())
    return f"{year}-{month}-{day}"


def _manifest() -> list[dict]:
    """The declared sheets, in the order the manifest gives them.

    An unreadable manifest publishes nothing rather than everything: the failure then
    shows as an empty page, which somebody reports, instead of a tree of PDFs nobody
    reviewed going live.
    """
    if not MANIFEST.is_file():
        return []
    try:
        data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        logger.error("schede: manifest unreadable", extra={"path": str(MANIFEST),
                                                           "error": str(exc)})
        return []
    entries = data.get("schede") if isinstance(data, dict) else None
    return [entry for entry in entries or []
            if isinstance(entry, dict) and isinstance(entry.get("file"), str)]


def _versions() -> dict[str, dict]:
    """What ``scripts/schede_versions.py`` wrote at build time, keyed by relative path.

    Read fresh on purpose (it is a few hundred bytes, and it only exists in a built
    image): a cache here would buy nothing and could hold a stale version across a
    local rebuild.
    """
    if not VERSIONS.is_file():
        return {}
    try:
        data = json.loads(VERSIONS.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        logger.warning("schede: versions.json unreadable", extra={"error": str(exc)})
        return {}
    sheets = data.get("sheets") if isinstance(data, dict) else None
    return {key: value for key, value in (sheets or {}).items() if isinstance(value, dict)}


def _git_version(path: Path) -> tuple[str, str] | None:
    """(date, short sha) of the last commit that touched the file — only inside a checkout."""
    if not (ROOT / ".git").exists():
        return None
    try:
        done = subprocess.run(
            ["git", "-C", str(ROOT), "log", "-1", "--format=%cs%x09%h", "--", str(path)],
            capture_output=True, text=True, timeout=5,
        )
    except (OSError, subprocess.SubprocessError):   # no git binary, or it hung
        return None
    if done.returncode != 0:
        return None
    parts = done.stdout.strip().split("\t")
    if len(parts) != 2 or not parts[0] or not parts[1]:
        return None
    return parts[0], parts[1]


def _fallback_title(rel: str) -> tuple[str, str]:
    """A title for a declared sheet whose manifest entry forgot one: the file's own name.

    Ugly is better than invisible — a sheet listed as "radicali-1" can still be opened,
    and the operator can see at once which entry needs its title.
    """
    folder, _, name = rel.rpartition("/")
    stem = name.removesuffix(".pdf").replace("-", " ").replace("_", " ")
    return stem[:1].upper() + stem[1:], folder[:1].upper() + folder[1:]


def _build(rel: str, entry: dict, versions: dict[str, dict]) -> Scheda | None:
    path = (SCHEDE_DIR / rel).resolve()
    if SCHEDE_DIR.resolve() not in path.parents or not path.is_file():
        logger.warning("schede: declared file missing", extra={"file": rel})
        return None
    content = path.read_bytes()
    sha256 = hashlib.sha256(content).hexdigest()
    fallback_title, fallback_subtitle = _fallback_title(rel)

    updated: str | None = None
    commit: str | None = None
    source = "none"
    declared = versions.get(rel)
    if declared is not None:
        if declared.get("sha256") == sha256:
            updated = declared.get("updated") or None
            commit = declared.get("commit") or None
            if updated or commit:
                source = "versions"
        else:
            # the declaration describes other bytes: it is dropped, not shown
            logger.warning(
                "schede: versions.json describes another file, ignoring it",
                extra={"file": rel, "declared": declared.get("sha256"), "actual": sha256},
            )
    if updated is None:
        from_git = _git_version(path)
        if from_git is not None:
            updated, commit = from_git
            source = "git"
    if updated is None:
        updated = _pdf_date(content)
        source = "pdf" if updated is not None else "none"

    stem = rel.rpartition("/")[2].removesuffix(".pdf")
    return Scheda(
        id=rel.removesuffix(".pdf"),
        file=rel,
        url=f"{URL_PREFIX}{rel}",
        title=str(entry.get("title") or fallback_title),
        subtitle=str(entry.get("subtitle") or fallback_subtitle),
        order=int(entry.get("order") or 0),
        sha256=sha256,
        bytes=len(content),
        updated=updated,
        commit=commit,
        version_source=source,
        content=content,
    )


def list_schede() -> list[Scheda]:
    """Every published sheet, in manifest order (then by file name)."""
    versions = _versions()
    sheets: list[Scheda] = []
    for entry in _manifest():
        rel = entry["file"].strip().lstrip("/")
        if not rel:
            continue
        path = SCHEDE_DIR / rel
        try:
            stat = path.stat()
        except OSError:
            logger.warning("schede: declared file missing", extra={"file": rel})
            continue
        signature = (stat.st_mtime_ns, stat.st_size)
        cached = _CACHE.get(rel)
        if cached is not None and cached[0] == signature:
            sheets.append(cached[1])
            continue
        built = _build(rel, entry, versions)
        if built is None:
            continue
        _CACHE[rel] = (signature, built)
        sheets.append(built)
    return sorted(sheets, key=lambda scheda: (scheda.order, scheda.file))


def find_scheda(rel: str) -> Scheda | None:
    """The published sheet at this relative path — the only files the site will serve."""
    wanted = rel.strip().lstrip("/")
    return next((scheda for scheda in list_schede() if scheda.file == wanted), None)
