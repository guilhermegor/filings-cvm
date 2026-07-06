#!/usr/bin/env bash
# Resolve Poetry by whichever invocation strategy works on THIS machine, then exec
# it with the passed arguments. The single Poetry entrypoint for every Makefile /
# tasks.sh recipe — so no recipe ever depends on a bare `poetry` being on PATH.
#
# Why this exists: venv.sh may install Poetry with `pip install --user`, leaving it
# reachable only as `python -m poetry` (the user-scripts dir is not on PATH on Git
# Bash / MINGW under Windows). A bare `poetry run …` recipe then dies with
# "poetry: command not found" even though Poetry is installed. resolve_poetry()
# already tries bare `poetry` then `$PYTHON -m poetry`; ensure_poetry() additionally
# installs Poetry from requirements.txt when none resolves. This wrapper funnels
# every recipe through that machinery.
#
# Usage: bash bin/poetry_exec.sh <poetry args...>
#   e.g. bash bin/poetry_exec.sh run pytest tests/unit/
#        bash bin/poetry_exec.sh install --with dev,docs
#        VALUE="$(bash bin/poetry_exec.sh version -s)"
#
# stdout discipline: all resolution status is routed to stderr, so the wrapped
# command's own stdout passes through untouched and command substitution
# (e.g. `version -s`) stays clean.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/lib/common.sh"
# shellcheck source=bin/lib/bootstrap.sh
source "$SCRIPT_DIR/lib/bootstrap.sh"

main() {
	if [[ "$#" -eq 0 ]]; then
		print_status "error" "Usage: poetry_exec.sh <poetry args...>"
		return 2
	fi

	# Resolve (and, only if absent, install) Poetry. Redirect this phase's stdout
	# to stderr so a caller capturing the wrapped command's output is not polluted
	# by resolution chatter.
	{
		bootstrap_init
		wire_corporate_ca
		ensure_poetry
	} 1>&2

	exec "${POETRY_CMD[@]}" "$@"
}

main "$@"
