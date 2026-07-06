#!/usr/bin/env bash
#
# commit.sh — commit with a one-shot retry for auto-fixing pre-commit hooks.
#
# Hooks like ruff-format, end-of-file-fixer, and trailing-whitespace REWRITE the
# staged file and then exit non-zero, aborting the first `git commit`. Run naively
# that leaves HEAD unmoved while looking like "it ran" — a silent no-commit. This
# helper re-stages the hook-modified paths, retries the commit exactly once, and
# then verifies HEAD actually advanced (failing loudly if it did not).
#
# Usage:
#   bin/commit.sh "<conventional message>" [path ...]
#
# With no paths it commits whatever is already staged.

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
		# Most often an auto-fixing hook reformatted staged files and aborted.
		# Re-stage what changed and retry exactly once.
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
