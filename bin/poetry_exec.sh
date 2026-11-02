#!/usr/bin/env bash

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

	{
		bootstrap_init
		wire_corporate_ca
		ensure_poetry
	} 1>&2

	exec "${POETRY_CMD[@]}" "$@"
}

main "$@"
