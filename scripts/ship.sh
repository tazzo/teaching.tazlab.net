#!/bin/sh
# ship.sh — THE ONE WAY TO PUSH THIS REPOSITORY. Nothing here is «pushato» until this script has read
# the remote back and printed `ok=true`.
#
# WHY IT EXISTS, 2026-11-28. This repository has no push door, so every worker chose its own remote and
# its own branch — and one of those branches PUBLISHES. `.github/workflows/publish.yml` runs
# `on: push: branches: [master]` and, when it is green, builds `tazzo/tazlab-teaching` and hands it to
# Flux. On 2026-11-27 a worker's branch was created from `github/master`, its two commits were pushed
# to `master` (`f352740 -> 0d16293`, 15:08:59), five pipeline runs went red and the published image
# stopped at run 40. The same move had already happened with `a7912ec`/`f352740`. A worker pushing «its
# branch» was, in fact, publishing.
#
# The three parts of the defect were three choices left to each worker: which branch to be born from,
# which remote, and which destination. This file writes all three down once:
#
#   1. ONE REFSPEC, WRITTEN OUT — `git push origin <sha>:refs/heads/integra-schede-master`.
#      Never `git push` and never `git push origin`: with no refspec git's destination is the branch
#      you are on, git exits 0, and the push is reported as done about a ref nobody deploys.
#      (The other half of the wound: a branch born from `master` is already in the wrong place. That is
#      `scripts/work.sh`, and it runs before any push.)
#
#   2. `master` IS REFUSED, AND THE REFUSAL NAMES THE REASON. `master` is not a working branch: it
#      publishes. The only way through is `--publish` WITH `ADA_ALLOW_PUBLISH=1` — the operator's word
#      saying «pubblica», in the environment where the decision is taken. Publishing is a decision,
#      never the side effect of a push.
#
#   3. THE PUSH IS THE READ-BACK, NOT THE EXIT CODE. `git ls-remote origin refs/heads/<target>` after
#      the push must answer with the very sha that left this tree:
#        INFO ship pushed=<sha> ref=origin/integra-schede-master readback=<sha> ok=true
#      A push that landed somewhere else is not a push: rc≠0 and
#        ERROR ship: pushed <sha> but origin/<target> is <sha> — the branch went, not the target
#
# WHAT THIS SCRIPT REFUSES TO DO, on purpose: no `--force` and no `--no-verify` (a rewrite of published
# history and a skipped gate are acts a person performs while looking at the reason, not a fallback a
# script takes when a gate says no), no push to any branch that is neither the integration line nor a
# `w/…` backup, and no push of a dirty tree (what you push must be what you tested).
#
# THE WALL BEHIND THE DOOR: `scripts/hooks/pre-push` (installed by `make hooks`) refuses the same
# destinations for a raw `git push` that never went through this script — and hooks live in the common
# `.git`, so it covers every worktree of this clone, including the workers' ones.
#
# USAGE, the whole of it:
#   sh scripts/ship.sh                          HEAD -> origin/integra-schede-master  (the normal case)
#   sh scripts/ship.sh --branch w/subagent-42   HEAD -> origin/w/subagent-42           (a backup)
#   ADA_ALLOW_PUBLISH=1 sh scripts/ship.sh --publish   HEAD -> origin/master           (PUBLISHES)
#
# Exit codes: 0 = the remote carries this sha, read back; 1 = nothing landed, and the reason is on
# stderr in one sentence that names the fix; 64 = usage.

set -u

root=$(git rev-parse --show-toplevel 2>/dev/null) || {
	echo "ERROR ship: not inside a git repository — nothing was pushed" >&2
	exit 1
}
cd "$root" || exit 1

remote=origin
integration=integra-schede-master
PUBLISH=no

usage() {
	sed -n '2,50p' "$0" | sed -n '/^# USAGE/,/^# Exit codes/p' >&2
}

TARGET=$integration
while [ $# -gt 0 ]; do
	case "$1" in
		--publish)
			PUBLISH=yes
			TARGET=master
			shift ;;
		--branch)
			[ $# -ge 2 ] || { echo "ERROR ship: --branch needs a name — nothing was pushed" >&2; exit 64; }
			TARGET="$2"
			shift 2 ;;
		-h|--help)
			usage
			exit 0 ;;
		*)
			echo "ERROR ship: unknown argument «$1» — usage: sh scripts/ship.sh [--branch <name> | --publish]" >&2
			exit 64 ;;
	esac
done

# --- master publishes: refused here, by name --------------------------------------------------------
if [ "$TARGET" = master ] || [ "$TARGET" = refs/heads/master ]; then
	if [ "${ADA_ALLOW_PUBLISH:-0}" != 1 ]; then
		echo "ERROR ship: «master» PUBLISHES (publish.yml -> Docker Hub -> Flux) — refusing to push it." >&2
		echo "ERROR ship: publishing is the operator's decision; only when he says «pubblica» set ADA_ALLOW_PUBLISH=1 and use --publish. Nothing was pushed." >&2
		exit 1
	fi
fi

# --- the destination, named once ---------------------------------------------------------------------
target=refs/heads/$TARGET
case "$TARGET" in
	"$integration"|w/*) ;;
	master) ;;
	*)
		echo "ERROR ship: refusing to push «$TARGET» — the integration line is $integration, a backup is w/… — nothing was pushed" >&2
		exit 1 ;;
esac

# --- what we are pushing ----------------------------------------------------------------------------
branch=$(git symbolic-ref --short -q HEAD 2>/dev/null) || branch=HEAD

sha=$(git rev-parse --verify HEAD 2>/dev/null) || {
	echo "ERROR ship: HEAD is not a commit — nothing was pushed" >&2
	exit 1
}

if [ -n "$(git status --porcelain 2>/dev/null)" ]; then
	echo "ERROR ship: the tree is dirty — commit first, then push what you tested. Nothing was pushed." >&2
	exit 1
fi

# --- 1. what the integration line is before the push --------------------------------------------------
# Read before pushing, so a refusal can name both shas instead of leaving a `non-fast-forward` sentence
# about mechanics to be worked around.
before=$(git ls-remote "$remote" "refs/heads/$integration" 2>/dev/null | awk 'NR==1{print $1}')
if [ -z "$before" ]; then
	echo "ERROR ship: cannot read $remote/$integration — nothing was pushed, and a push nobody can verify is not a push" >&2
	exit 1
fi

# --- 2. the branch must descend from the integration line (the parto of 2026-11-27) ------------------
# A branch born from `master` is already in the wrong place: it cannot be integrated, only published.
if [ "$TARGET" = "$integration" ]; then
	git fetch --no-tags --quiet "$remote" "+refs/heads/$integration:refs/remotes/$remote/$integration" 2>/dev/null || true
	if ! git merge-base --is-ancestor "$before" "$sha" 2>/dev/null; then
		echo "ERROR ship: $remote/$integration is $before and HEAD is $sha — the integration line has moved, or this branch was not born from it; nothing was pushed — fetch and rebase on $remote/$integration, then ship again" >&2
		exit 1
	fi
fi

# --- 3. the push, with the refspec written out --------------------------------------------------------
push_output=$(git push "$remote" "$sha:$target" 2>&1)
push_rc=$?
if [ "$push_rc" -ne 0 ]; then
	after=$(git ls-remote "$remote" "$target" 2>/dev/null | awk 'NR==1{print $1}')
	echo "ERROR ship: git refused the push (rc=$push_rc) — $remote/$TARGET is ${after:-unreadable}, HEAD is $sha" >&2
	printf '%s\n' "$push_output" | tail -10 >&2
	exit 1
fi

# --- 4. the read-back: the remote must answer with the sha that left this tree -------------------------
after=$(git ls-remote "$remote" "$target" 2>/dev/null | awk 'NR==1{print $1}')
if [ "$after" != "$sha" ]; then
	echo "ERROR ship: pushed $sha but $remote/$TARGET is ${after:-unreadable} — the branch went, not the target" >&2
	printf '%s\n' "$push_output" | tail -5 >&2
	printf 'INFO ship pushed=%s ref=%s/%s readback=%s ok=false\n' "$sha" "$remote" "$TARGET" "${after:-}"
	exit 1
fi

printf 'INFO ship pushed=%s ref=%s/%s readback=%s ok=true branch=%s publish=%s\n' \
	"$sha" "$remote" "$TARGET" "$after" "$branch" "$PUBLISH"
exit 0
