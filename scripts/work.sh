#!/bin/sh
# work.sh — A WORK BRANCH IS BORN FROM THE INTEGRATION LINE. Never from `master`, which publishes.
#
# Why this file exists, 2026-11-28. On 2026-11-27 the branch of a worker reads, in its own reflog:
# «branch: Created from github/master». Two commits later it was pushed to `master` and the pipeline
# went red on it. The push was the obvious next step of the day, not a mistake in the middle of a good
# one: the branch was already a descendant of the line that publishes. `scripts/ship.sh` decides where
# a commit goes; this script decides where the branch it lives on comes from. Without both, one of the
# three choices is still left to each worker.
#
#   sh scripts/work.sh w/subagent-<id>              a work branch from origin/integra-schede-master
#   sh scripts/work.sh w/subagent-<id> <base>       from <base>, and it says which one
#
# Exit codes: 0 = the branch exists and is on <base>; 1 = refused (a base that publishes); 64 = usage.

set -eu

[ $# -ge 1 ] || { echo "usage: sh scripts/work.sh <branch> [<base>]" >&2; exit 64; }
NAME="$1"
BASE="${2:-origin/integra-schede-master}"

case "$BASE" in
	refs/heads/master|*/master|master)
		echo "ERROR work: «$BASE» is the line that PUBLISHES — a work branch must be born from integra-schede-master. Nothing was created." >&2
		echo "ERROR work: sh scripts/work.sh $NAME" >&2
		exit 1 ;;
esac

git fetch --prune --quiet origin
git switch --create "$NAME" "$BASE"
echo "INFO work branch=$NAME base=$BASE head=$(git rev-parse --short HEAD)"
