"""Name the version of every published sheet, from git, into ``schede/versions.json``.

The image has no ``.git``, so the page cannot ask git which commit last changed a PDF.
This script asks it once, at build time, and writes the answer beside the sheets:

    python3 scripts/schede_versions.py                 # writes schede/versions.json
    python3 scripts/schede_versions.py --check         # exit 1 if the file is out of date
    python3 scripts/schede_versions.py --require-commit  # exit 1 if a sheet has no commit

One entry per sheet declared in ``schede/schede.json``:

    "radicali/radicali-1.pdf": {
      "sha256": "3c35…",          # the bytes this version describes
      "bytes": 161113,
      "updated": "2026-11-26",    # committer date of the last commit touching the PDF
      "commit": "c72747d"         # its short sha
    }

The sha256 is what makes the file safe to trust later: the application only uses an
entry whose digest still matches the bytes it is about to serve, and ignores a stale
one with a warning — a version that describes another file is worse than no version.

Needs the FULL history (``actions/checkout`` with ``fetch-depth: 0``): the commit that
last touched a PDF is usually not HEAD, and on a shallow clone ``git log -- <path>``
finds nothing and this would write no version at all.

``--require-commit`` is what the publish workflow runs, and it is the whole point of the
flag existing: without it a job whose checkout brought no history *succeeds* here and
writes a ``versions.json`` with no ``commit`` key, and the breakage only shows up two
steps later as a failing assertion about the page. With it, a version that cannot be
named is a red pipeline at the step that could not name it (2026-11-27: the checkout
was a tarball — no ``.git`` — and five runs went red before anybody read why).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCHEDE_DIR = ROOT / "schede"
MANIFEST = SCHEDE_DIR / "schede.json"
VERSIONS = SCHEDE_DIR / "versions.json"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 16), b""):
            digest.update(chunk)
    return digest.hexdigest()


def last_commit(path: Path) -> tuple[str, str] | None:
    """(committer date, short sha) of the last commit that touched ``path``."""
    try:
        done = subprocess.run(
            ["git", "-C", str(ROOT), "log", "-1", "--format=%cs%x09%h", "--", str(path)],
            capture_output=True, text=True, timeout=30,
        )
    except FileNotFoundError:
        # the container image may ship no git (python:3.14-slim does not): say it, so the
        # job that needs the version can install it instead of reading a bare traceback
        print("ERROR schede: git not found on PATH — the version cannot be named here",
              file=sys.stderr)
        return None
    except (OSError, subprocess.SubprocessError) as exc:
        print(f"ERROR schede: git failed ({exc})", file=sys.stderr)
        return None
    if done.returncode != 0:
        print(f"ERROR schede: git log refused {path}: {done.stderr.strip()}", file=sys.stderr)
        return None
    parts = done.stdout.strip().split("\t")
    if len(parts) != 2 or not parts[0] or not parts[1]:
        return None
    return parts[0], parts[1]


def build() -> tuple[dict, list[str]]:
    """(the file to write, the declared sheets it could not name a commit for)."""
    if not MANIFEST.is_file():
        raise SystemExit(f"ERROR schede: manifest missing at {MANIFEST}")
    entries = json.loads(MANIFEST.read_text(encoding="utf-8")).get("schede") or []
    sheets: dict[str, dict] = {}
    unnamed: list[str] = []
    for entry in entries:
        rel = str(entry.get("file", "")).strip().lstrip("/")
        if not rel:
            continue
        path = SCHEDE_DIR / rel
        if not path.is_file():
            raise SystemExit(f"ERROR schede: declared file missing: {rel}")
        record: dict = {"sha256": sha256(path), "bytes": path.stat().st_size}
        committed = last_commit(path)
        if committed is None:
            unnamed.append(rel)
            print(f"WARN schede: no commit found for {rel} (shallow clone?)", file=sys.stderr)
        else:
            record["updated"], record["commit"] = committed
            print(f"INFO schede version file={rel} updated={record['updated']} "
                  f"commit={record['commit']} sha256={record['sha256'][:12]}")
        sheets[rel] = record
    return {"generatedBy": "scripts/schede_versions.py", "sheets": sheets}, unnamed


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--check", action="store_true",
                        help="do not write: exit 1 if versions.json is out of date")
    parser.add_argument("--require-commit", action="store_true",
                        help="exit 1 if a declared sheet cannot be named a commit — the "
                             "page would say only 'compilata il', and a version nobody "
                             "can name must not reach a page or an image")
    args = parser.parse_args(argv)

    wanted, unnamed = build()
    if unnamed and args.require_commit:
        print(f"ERROR schede: {len(unnamed)} declared sheet(s) cannot be named a commit "
              f"({', '.join(unnamed)}) — is this checkout a tarball with no .git? "
              "The publish workflow needs git installed BEFORE actions/checkout.",
              file=sys.stderr)
        return 1
    rendered = json.dumps(wanted, indent=2, ensure_ascii=False, sort_keys=True) + "\n"
    if args.check:
        current = VERSIONS.read_text(encoding="utf-8") if VERSIONS.is_file() else ""
        if json.loads(current or "{}") != wanted:
            print("ERROR schede: versions.json is out of date — run "
                  "python3 scripts/schede_versions.py", file=sys.stderr)
            return 1
        print("INFO schede versions.json is up to date")
        return 0
    VERSIONS.write_text(rendered, encoding="utf-8")
    print(f"wrote {VERSIONS.relative_to(ROOT)} ({len(wanted['sheets'])} sheets)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
