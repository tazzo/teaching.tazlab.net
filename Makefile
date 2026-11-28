# What Publish Teaching runs, runnable here — in the same order, with the same commands.
#
# The workflow (.github/workflows/publish.yml) is the source of truth; this file is its
# local echo, and tests/test_publish_workflow.py fails when the two drift apart. The point
# of the echo is the rule that cost five red runs on 2026-11-26/27: **a test that can only
# be run on GitHub is a test nobody runs before the push**.
#
#   make deps        once: the Python and the frontend dependencies
#   make ci          the three commands of the workflow's `test` job
#   make ci-no-history   reproduce GitHub's tarball checkout (no .git) and prove the guard bites
#
# `make deps` installs the Python packages, not the system libraries they load: pytest needs
# libpango-1.0-0/libpangocairo-1.0-0/libgdk-pixbuf-2.0-0 (WeasyPrint) and the CI image is
# where they exist (`apt-get install` in .github/workflows/publish.yml). On a machine without
# them the first two commands of `make ci` still run — `make versions` and `make ci-no-history` —
# but the pytest half says `cannot load library libpango-1.0-0` instead of a test result.
#
# PYTHON=... selects the interpreter (the image runs 3.14: `PYTHON=python3.14 make ci`).

PYTHON ?= python3

.PHONY: deps ci versions ci-no-history clean

deps: ## the dependencies the workflow installs, in one go
	$(PYTHON) -m pip install --upgrade pip
	$(PYTHON) -m pip install -e '.[dev]'
	cd web && npm ci --no-audit --no-fund

ci: versions ## the `test` job: name the versions, then both suites
	$(PYTHON) -m pytest tests -q
	cd web && npm test

versions: ## name the version of every sheet (red if a sheet cannot be named)
	$(PYTHON) scripts/schede_versions.py --require-commit

# The failure of 2026-11-26/27 was NOT in the tests: `actions/checkout` found no git in the
# python:3.14-slim container and downloaded the commit as a tarball, so the tree had no
# `.git` and the sheets' commit could not be named. The recipe below copies the WORKING
# tree (tracked files, no .git — the shape that tarball had), so the breakage is
# reproducible on any machine, without GitHub, and before the fix is committed:
ci-no-history: ## reproduce the no-.git checkout and prove the version guard refuses
	rm -rf .ci-no-history
	mkdir -p .ci-no-history
	git ls-files -z | tar --null -T - -c | tar -x -C .ci-no-history
	@$(PYTHON) .ci-no-history/scripts/schede_versions.py --require-commit; \
	rc=$$?; \
	if [ $$rc -eq 1 ]; then \
	  echo "OK: no .git here, and the version script refuses to name a version it cannot see"; \
	elif [ $$rc -eq 0 ]; then \
	  echo "FAIL: a tree with no .git passed --require-commit — the guard is gone"; exit 1; \
	else \
	  echo "FAIL: the script did not even understand --require-commit (rc=$$rc)"; exit 1; \
	fi

clean:
	rm -rf .ci-no-history
