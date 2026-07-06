#!/bin/bash
# Pre-commit hook: reject filenames containing characters outside [a-zA-Z0-9._-].

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/lib/common.sh"

check_unix_filenames() {
	local has_errors=0

	for f in "$@"; do
		if [[ -d "$f" ]] || [[ "$f" == .git/* ]]; then
			continue
		fi

		local str_filename
		str_filename=$(basename "$f")

		if [[ "$str_filename" == *[^a-zA-Z0-9._-]* ]]; then
			print_status "error" "Invalid filename '$str_filename' in path: $f"
			print_status "error" "Only alphanumeric, ., - and _ are allowed in filenames"
			has_errors=1
		fi
	done

	if [[ $has_errors -eq 0 ]]; then
		print_status "success" "All filenames are valid"
		return 0
	fi
	return 1
}

main() {
	check_unix_filenames "$@" || exit 1
}

main "$@"
