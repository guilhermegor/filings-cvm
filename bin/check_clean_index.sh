#!/bin/bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/lib/common.sh"

main() {
	if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
		return 0
	fi

	if git diff --cached --quiet; then
		return 0
	fi

	print_status "error" "Push blocked: the index is not empty (staged changes with no commit)."
	print_status "error" "This almost always means a commit was REJECTED after 'git add' ran -"
	print_status "error" "the push would ship the PREVIOUS commit and still print success."
	print_status "error" ""
	print_status "error" "Staged but uncommitted:"
	git diff --cached --name-only | sed 's/^/    /' >&2
	print_status "error" ""
	print_status "error" "Fix: re-run the commit and read its FULL output (never pipe it through"
	print_status "error" "tail/grep - that is how the rejection scrolls off), then confirm HEAD"
	print_status "error" "moved with 'git log --oneline -1'."
	print_status "error" "Deliberate exception: 'git push --no-verify'."
	return 1
}

main "$@"
