"""The publish workflow must be able to *name* a sheet's version — the way it could not.

On 2026-11-26 and 2026-11-27 five `Publish Teaching` runs went red on `master`
(691b3e4, 5b33224, 8a6d677, f352740, 0d16293) and `build-and-push` was skipped every
time. The log of run 46013294159 says it in one line:

    ERROR schede: git log refused …/schede/radicali/radicali.pdf:
    fatal: not a git repository (or any parent up to mount point /)
    Stopping at filesystem boundary (GIT_DISCOVERY_ACROSS_FILESYSTEM not set).

The test was right and the code was right: the *job* was wrong. Every step of a container
job runs inside the image, `python:3.14-slim` ships no git, and `actions/checkout` without
git on PATH falls back to downloading the commit as a TARBALL — no `.git`, no history,
`fetch-depth: 0` silently ignored. Installing git afterwards (5b33224) was one step too
late: the tarball was already on disk.

So the regression is an ORDERING and a FLAG, and both are asserted here, on the workflow
itself. This is the cheap test that would have kept that pipeline green for free; the
suite it protects needs pango, KaTeX and a browser-free PDF stack to say the same thing.
"""

from __future__ import annotations

import re
from pathlib import Path

WORKFLOW = Path(__file__).resolve().parent.parent / ".github" / "workflows" / "publish.yml"


def job(name: str) -> list[str]:
    """The step blocks of one job, in the order the runner executes them."""
    text = WORKFLOW.read_text(encoding="utf-8")
    start = text.index(f"\n  {name}:\n")
    rest = text[start + 1:]
    end = re.search(r"\n  [A-Za-z][\w-]*:\n", rest)
    body = rest[:end.start()] if end else rest
    return [block for block in body.split("\n      - ")[1:]]


def run_lines(steps: list[str]) -> list[str]:
    """The `run:` command of every step that has one, as written."""
    return [line.split("run:", 1)[1].strip()
            for block in steps for line in block.splitlines()
            if line.strip().startswith("run:")]


def test_git_is_installed_before_the_checkout_in_the_container_job() -> None:
    """In a container job the checkout runs inside the image: without git, no history.

    Asserted on the order, not on a step name: what matters is that a step which puts git
    on PATH runs before the block that checks the repository out.
    """
    steps = job("test")
    installs_git = [i for i, block in enumerate(steps)
                    if "apt-get install" in block and re.search(r"\bgit\b", block)]
    checkouts = [i for i, block in enumerate(steps) if "actions/checkout@" in block]
    assert installs_git, (
        "the `test` job installs no git at all: actions/checkout will download a tarball "
        "and every sheet's commit will be unnameable (five red runs, 2026-11-26/27)"
    )
    assert checkouts, "the `test` job has no actions/checkout step"
    assert min(installs_git) < min(checkouts), (
        f"git is installed in step {min(installs_git) + 1} but the checkout is step "
        f"{min(checkouts) + 1}: in a container job the checkout runs inside the image, so "
        "a tarball is downloaded before git exists — the failure this file is about"
    )


def test_the_checkout_asks_for_the_whole_history() -> None:
    """The commit that last touched a PDF is usually not HEAD: a shallow clone answers
    nothing, and the page would print a date with no author."""
    for name in ("test", "build-and-push"):
        steps = [block for block in job(name) if "actions/checkout@" in block]
        assert steps, f"{name}: no checkout"
        assert any("fetch-depth: 0" in block for block in steps), (
            f"{name}: the checkout is shallow — a version cannot be named from it"
        )


def test_every_version_step_requires_a_commit() -> None:
    """`--require-commit` is what turns "cannot name it" into a red step.

    Without it the script warns, writes a versions.json with no commit, exits 0, and the
    pipeline breaks two steps later in the suite — which is how this went unnoticed.
    """
    commands = [line for line in run_lines(job("test") + job("build-and-push"))
                if "schede_versions.py" in line]
    assert len(commands) >= 2, (
        "expected the version step in both jobs (test and build-and-push), found: "
        f"{commands}"
    )
    for command in commands:
        assert "--require-commit" in command, (
            f"`{command}` publishes a version it may not be able to name: add "
            "--require-commit so a missing commit is a red step, not a quiet warning"
        )


def test_the_local_echo_runs_the_same_commands() -> None:
    """`make ci` must be what the workflow runs, or nobody runs it before the push."""
    makefile = (WORKFLOW.parent.parent.parent / "Makefile").read_text(encoding="utf-8")
    assert "-m pytest tests -q" in makefile, "make ci does not run the Python suite"
    assert "npm test" in makefile, "make ci does not run the frontend suite"
    assert "schede_versions.py --require-commit" in makefile, (
        "make ci does not name the versions the way the workflow does"
    )
