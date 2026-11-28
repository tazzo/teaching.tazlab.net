"""The push method is written once, and these are the moves that must not work again.

2026-11-27: a worker's branch was «Created from github/master», its commits were pushed to `master` —
the line that PUBLISHES (`.github/workflows/publish.yml` -> Docker Hub -> Flux) — five pipeline runs
went red and the published image stopped at run 40. 2026-11-28: the same move left `0d16293` on master.

A script and a hook are one line each to bypass if nobody tests them, so the tests drive a scratch
repository: a bare remote that already carries both lines, diverged the way the real one is, a clone,
and the moves.

Written with `unittest` and the standard library only, on purpose: the proof that `master` is refused
must be runnable on the machine where the push is made, before the push — `python3 -m unittest
tests.test_push_method -v`. pytest collects these classes too, so `make ci` and the workflow see the
same tests.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# The two environment variables are the operator's word: a test that inherits them from the shell would
# pass by accident, so they are stripped from every command this file runs.
STRIPPED = ("ADA_ALLOW_PUBLISH", "ADA_ALLOW_BRANCH", "GITHUB_TOKEN")


def _env(extra: dict[str, str] | None = None) -> dict[str, str]:
    env = {k: v for k, v in os.environ.items() if k not in STRIPPED}
    env.update(
        {
            "GIT_AUTHOR_NAME": "t",
            "GIT_AUTHOR_EMAIL": "t@t",
            "GIT_COMMITTER_NAME": "t",
            "GIT_COMMITTER_EMAIL": "t@t",
            # A clone of a local path: never let git reach for a credential or a server.
            "GIT_TERMINAL_PROMPT": "0",
        }
    )
    env.update(extra or {})
    return env


def git(args, cwd, env=None, check=False):
    p = subprocess.run(["git", *args], cwd=cwd, text=True, capture_output=True, env=_env(env))
    if check and p.returncode:
        raise AssertionError(f"git {' '.join(args)} rc={p.returncode}\n{p.stdout}\n{p.stderr}")
    return p


def shell(args, cwd, env=None):
    """Run a script of the repository as a user would — `sh scripts/…` — never through git."""
    return subprocess.run(["sh", *args], cwd=cwd, text=True, capture_output=True, env=_env(env))


def head(cwd):
    return git(["rev-parse", "HEAD"], cwd, check=True).stdout.strip()


def remote_head(cwd, branch):
    out = git(["ls-remote", "origin", f"refs/heads/{branch}"], cwd, check=True).stdout.split()
    return out[0] if out else ""


def commit(cwd, name, text):
    (Path(cwd) / name).write_text(text)
    git(["add", name], cwd, check=True)
    git(["commit", "-m", text], cwd, check=True)


class PushMethod(unittest.TestCase):
    """A bare remote with both lines (diverged), and a clone with the script and the hook installed."""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="push-method-"))
        remote = self.tmp / "remote.git"
        git(["init", "--bare", "-b", "integra-schede-master", str(remote)], self.tmp, check=True)

        seed = self.tmp / "seed"
        git(["clone", str(remote), str(seed)], self.tmp, check=True)
        commit(seed, "f", "one")
        self.base = head(seed)
        git(["push", "origin", "HEAD:refs/heads/integra-schede-master"], seed, check=True)
        git(["push", "origin", "HEAD:refs/heads/master"], seed, check=True)

        # master and the integration line diverge, as the real repository's do: a branch taken from
        # `master` is then a branch that cannot be fast-forwarded onto the integration line.
        git(["reset", "--hard", self.base], seed, check=True)
        commit(seed, "only-on-master", "publish")
        git(["push", "origin", "HEAD:refs/heads/master"], seed, check=True)
        git(["reset", "--hard", self.base], seed, check=True)
        commit(seed, "only-on-integra", "integrate")
        git(["push", "origin", "HEAD:refs/heads/integra-schede-master"], seed, check=True)

        self.master = remote_head(seed, "master")
        self.integra = remote_head(seed, "integra-schede-master")

        self.work = self.tmp / "work"
        git(["clone", str(remote), str(self.work)], self.tmp, check=True)
        (self.work / "scripts" / "hooks").mkdir(parents=True, exist_ok=True)
        for name in ("work.sh", "ship.sh"):
            dst = self.work / "scripts" / name
            dst.write_bytes((ROOT / "scripts" / name).read_bytes())
            dst.chmod(0o755)
        hook = self.work / ".git" / "hooks" / "pre-push"
        hook.write_bytes((ROOT / "scripts" / "hooks" / "pre-push").read_bytes())
        hook.chmod(0o755)
        # The script and the hook are part of the tree they judge: an untracked copy is a dirty tree,
        # and `ship.sh` refuses a dirty tree — correctly.
        git(["add", "scripts"], self.work, check=True)
        git(["commit", "-m", "the door"], self.work, check=True)

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def ship(self, *args, env=None):
        return shell(["scripts/ship.sh", *args], self.work, env=env)

    # --- the normal case ---------------------------------------------------------------------------
    def test_the_script_pushes_the_integration_line_and_reads_it_back(self):
        commit(self.work, "f", "two")
        p = self.ship()
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertIn("ok=true", p.stdout)
        self.assertIn("ref=origin/integra-schede-master", p.stdout)
        self.assertEqual(remote_head(self.work, "integra-schede-master"), head(self.work))
        # the line that publishes is untouched by the normal case
        self.assertEqual(remote_head(self.work, "master"), self.master)

    # --- the 2026-11-27 move, twice refused ---------------------------------------------------------
    def test_the_script_itself_refuses_master(self):
        """`scripts/ship.sh --branch master`: rc≠0, the reason on stderr, master unchanged."""
        commit(self.work, "f", "three")
        p = self.ship("--branch", "master")
        self.assertNotEqual(p.returncode, 0)
        self.assertIn("PUBLISHES", p.stderr)
        self.assertIn("operator", p.stderr)
        self.assertEqual(remote_head(self.work, "master"), self.master)

    def test_a_bare_push_to_master_is_refused_by_the_hook(self):
        """The move of 2026-11-27 exactly as it was made: a branch taken from master, then a raw
        `git push` that skips the script. The push would be a fast-forward — only the hook stops it."""
        git(["switch", "--create", "pubbed", "origin/master"], self.work, check=True)
        commit(self.work, "f", "four")
        p = git(["push", "origin", "HEAD:refs/heads/master"], self.work)
        self.assertNotEqual(p.returncode, 0)
        self.assertIn("PUBLISHES", p.stderr)
        self.assertEqual(remote_head(self.work, "master"), self.master)

    # --- publishing stays the operator's decision ---------------------------------------------------
    def test_publish_needs_the_operator(self):
        commit(self.work, "f", "five")
        p = self.ship("--publish")
        self.assertNotEqual(p.returncode, 0)
        self.assertIn("operator", p.stderr)
        self.assertEqual(remote_head(self.work, "master"), self.master)

        # Publishing happens from a tree that carries master's line too: the branch merges it first,
        # which is what a real publish looks like (and what git requires, fast-forward).
        git(["merge", "--no-ff", "-m", "master", "origin/master"], self.work, check=True)
        q = self.ship("--publish", env={"ADA_ALLOW_PUBLISH": "1"})
        self.assertEqual(q.returncode, 0, q.stderr)
        self.assertIn("ok=true", q.stdout)
        self.assertEqual(remote_head(self.work, "master"), head(self.work))

    # --- a work branch is a backup, and it stays one ------------------------------------------------
    def test_a_work_branch_is_a_backup_and_is_allowed(self):
        git(["switch", "--create", "w/subagent-1"], self.work, check=True)
        commit(self.work, "f", "six")
        p = git(["push", "origin", "HEAD:refs/heads/w/subagent-1"], self.work)
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertEqual(remote_head(self.work, "w/subagent-1"), head(self.work))
        # a backup does not publish, and does not move the integration line
        self.assertEqual(remote_head(self.work, "master"), self.master)
        self.assertEqual(remote_head(self.work, "integra-schede-master"), self.integra)

    # --- the parto of the branch ---------------------------------------------------------------------
    def test_work_refuses_to_be_born_from_master(self):
        p = shell(["scripts/work.sh", "w/subagent-2", "origin/master"], self.work)
        self.assertNotEqual(p.returncode, 0)
        self.assertIn("publishes", (p.stdout + p.stderr).lower())
        self.assertNotEqual(git(["rev-parse", "--verify", "w/subagent-2"], self.work).returncode, 0)

    def test_work_births_the_branch_from_the_integration_line(self):
        p = shell(["scripts/work.sh", "w/subagent-3"], self.work)
        self.assertEqual(p.returncode, 0, p.stderr)
        self.assertIn("base=origin/integra-schede-master", p.stdout)
        self.assertEqual(head(self.work), self.integra)

    def test_the_script_refuses_a_branch_that_does_not_descend_from_integra(self):
        """A branch born from master is already in the wrong place — a perfect push script cannot save it."""
        git(["switch", "--create", "from-master", "origin/master"], self.work, check=True)
        commit(self.work, "f", "seven")
        # `master` carries no scripts/ at all — which is the point of the test — so the door is run
        # from its own path while the cwd is the branch that must be refused.
        p = shell([str(ROOT / "scripts" / "ship.sh")], self.work)
        self.assertNotEqual(p.returncode, 0)
        self.assertIn("integra-schede-master", p.stderr)
        self.assertEqual(remote_head(self.work, "integra-schede-master"), self.integra)

    # --- what you push is what you tested ------------------------------------------------------------
    def test_the_script_refuses_a_dirty_tree(self):
        (self.work / "f").write_text("uncommitted")
        p = self.ship()
        self.assertNotEqual(p.returncode, 0)
        self.assertIn("dirty", p.stderr)


if __name__ == "__main__":
    unittest.main()
