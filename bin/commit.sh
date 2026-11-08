#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/lib/common.sh"

PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

main() {
	cd "$PROJECT_ROOT" || exit 1

	if ! command -v git >/dev/null 2>&1; then
		print_status "error" "git is required"
		exit 1
	fi

	local str_message="${1:-}"
	if [[ -z "$str_message" ]]; then
		print_status "error" "commit message required: bin/commit.sh \"<msg>\" [path ...]"
		exit 1
	fi
	shift || true

	if [[ "$#" -gt 0 ]]; then
		git add -- "$@"
	fi

	local str_head_before
	str_head_before="$(git rev-parse HEAD 2>/dev/null || echo none)"

	if ! git commit -m "$str_message"; then
		print_status "warning" "commit aborted (likely a reformatting hook) — re-staging and retrying once"
		git add -u
		if [[ "$#" -gt 0 ]]; then
			git add -- "$@"
		fi
		git commit -m "$str_message"
	fi

	local str_head_after
	str_head_after="$(git rev-parse HEAD 2>/dev/null || echo none)"
	if [[ "$str_head_after" == "$str_head_before" ]]; then
		print_status "error" "HEAD did not advance — commit did not land (check hook output above)"
		exit 1
	fi

	print_status "success" "committed: $(git log -1 --oneline)"
}

main "$@"
