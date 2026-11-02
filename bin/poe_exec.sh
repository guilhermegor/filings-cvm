#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/lib/common.sh"
# shellcheck source=bin/lib/bootstrap.sh
source "$SCRIPT_DIR/lib/bootstrap.sh"

POE_CMD=()

resolve_poe() {
	local str_venv_poe
	for str_venv_poe in "${PROJECT_ROOT:-.}/.venv/bin/poe" "${PROJECT_ROOT:-.}/.venv/Scripts/poe.exe"; do
		if [[ -x "$str_venv_poe" ]]; then
			POE_CMD=("$str_venv_poe")
			print_status "debug" "Poe resolved: $str_venv_poe (in-project venv)"
			return 0
		fi
	done

	if command -v poe >/dev/null 2>&1; then
		POE_CMD=(poe)
		print_status "debug" "Poe resolved: poe (on PATH)"
		return 0
	fi

	if [[ -n "${PYTHON:-}" ]] && "$PYTHON" -m poethepoet --version >/dev/null 2>&1; then
		POE_CMD=("$PYTHON" -m poethepoet)
		print_status "debug" "Poe resolved: $PYTHON -m poethepoet"
		return 0
	fi

	if bash "$SCRIPT_DIR/poetry_exec.sh" poe --help >/dev/null 2>&1; then
		POE_CMD=(bash "$SCRIPT_DIR/poetry_exec.sh" poe)
		print_status "debug" "Poe resolved: poetry poe (Poetry plugin)"
		return 0
	fi

	return 1
}

report_unresolved() {
	print_status "error" "Poe the Poet could not be resolved on this machine."
	print_status "info" "Install it by any ONE of these routes:"
	print_status "info" "  bash bin/venv.sh                             # usual fix: build the venv"
	print_status "info" "  pipx install poethepoet                      # standalone, on PATH"
	print_status "info" "  poetry self add 'poethepoet[poetry_plugin]'  # optional Poetry plugin"
	print_status "info" "Poe is a dev dependency, so 'bash bin/venv.sh' (or 'poetry install"
	print_status "info" "--with dev') normally supplies it at .venv/bin/poe."
}

main() {

	{
		bootstrap_init
		wire_corporate_ca
	} 1>&2

	if ! resolve_poe 1>&2; then
		report_unresolved
		return 1
	fi

	exec "${POE_CMD[@]}" "$@"
}

main "$@"
