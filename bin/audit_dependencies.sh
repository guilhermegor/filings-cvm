#!/bin/bash
#
# audit_dependencies.sh — fail when a known-vulnerable package is in the LOCKED tree (#90).
#
# Single home for the dependency-vulnerability gate: called by the pre-commit
# `audit-dependencies` hook and by the matching CI step (gate parity). It audits what
# poetry.lock pins (export -> pip-audit -r), not whatever happens to be installed.
#
# --no-deps / --disable-pip: the export is already fully pinned, so pip-audit does no
# resolution and builds no venv — it only queries the PyPA/OSV advisory DB.
#
# Accepting an advisory: add its ID to IGNORE_VULNS below WITH a written reason and a
# tracking issue. An unexplained ignore is a silenced gate.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/lib/common.sh"

# Format: "<ID>  # reason (#issue)". Empty on purpose — nothing is accepted today.
IGNORE_VULNS=()

audit_lock() {
	local req_file="$1"
	local -a args=(-r "$req_file" --no-deps --disable-pip --strict)
	local entry

	for entry in "${IGNORE_VULNS[@]+"${IGNORE_VULNS[@]}"}"; do
		args+=(--ignore-vuln "${entry%% *}")
	done

	print_status "info" "pip-audit over poetry.lock (all groups)"
	bash "$SCRIPT_DIR/poetry_exec.sh" export --with dev,docs -f requirements.txt \
		--without-hashes -o "$req_file"
	bash "$SCRIPT_DIR/poetry_exec.sh" run pip-audit "${args[@]}"
}

main() {
	local req_file
	req_file="$(mktemp)"
	# Expanded now, not at exit: `req_file` is function-local and gone when the trap fires.
	# shellcheck disable=SC2064
	trap "rm -f '$req_file'" EXIT

	cd "$SCRIPT_DIR/.."
	audit_lock "$req_file"
	print_status "success" "pip-audit OK"
}

main "$@"
