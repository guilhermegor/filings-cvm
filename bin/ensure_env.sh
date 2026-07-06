#!/usr/bin/env bash
# Ensure a local .env exists before the rest of `make init` runs.
#
# If .env is already present, do nothing. Otherwise seed it from .env.example
# so a fresh checkout starts with a working config skeleton. When .env.example
# itself is missing there is nothing to copy: report the error and abort THIS
# script with a non-zero status. The Makefile invokes it with a leading '-' so
# make ignores that failure and still runs the remaining init steps (venv,
# precommit) — the missing template blocks only the env-seeding step.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
source "$SCRIPT_DIR/lib/common.sh"

ensure_env_file() {
	local path_env="$PROJECT_ROOT/.env"
	local path_example="$PROJECT_ROOT/.env.example"

	if [[ -f "$path_env" ]]; then
		print_status "info" ".env already exists — leaving it untouched"
		return 0
	fi

	if [[ ! -f "$path_example" ]]; then
		print_status "error" ".env.example not found at $path_example — cannot seed .env"
		return 1
	fi

	print_status "info" "No .env found — seeding it from .env.example..."
	cp "$path_example" "$path_env"
	print_status "success" "Created .env from .env.example (review and fill in secrets)"
	return 0
}

main() {
	ensure_env_file
}

main "$@"
