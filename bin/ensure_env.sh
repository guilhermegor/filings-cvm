#!/usr/bin/env bash

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
		print_status "info" "No .env.example in this project — nothing to seed, skipping .env"
		return 0
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
