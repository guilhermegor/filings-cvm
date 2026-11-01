#!/bin/bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/lib/common.sh"

STR_ROOT="."
BOOL_STAGED=0

parse_args() {
	while [[ $# -gt 0 ]]; do
		case "$1" in
		--root)
			STR_ROOT="${2:-.}"
			shift 2
			;;
		--staged)
			BOOL_STAGED=1
			shift
			;;
		*)
			print_status "error" "Unknown argument: $1 (only --root <dir> and --staged are accepted)"
			exit 2
			;;
		esac
	done
}

scan_gitleaks() {
	if [[ "$BOOL_STAGED" != "1" ]]; then
		gitleaks git "$STR_ROOT" --no-banner --redact -v
	elif gitleaks git --help 2>&1 | grep -q -- '--staged'; then
		gitleaks git --staged "$STR_ROOT" --no-banner --redact -v
	else
		gitleaks protect --staged --source "$STR_ROOT" --no-banner --redact -v
	fi
}

run_gitleaks() {
	print_status "section" "Secret scan (gitleaks)"
	if scan_gitleaks; then
		print_status "success" "gitleaks: no leaks found"
		return 0
	fi
	print_status "error" "gitleaks found a potential secret (see output above). A confirmed false positive gets a narrow, reasoned entry in .gitleaks.toml - never remove [extend] useDefault."
	return 1
}

main() {
	parse_args "$@"

	if ! command -v gitleaks >/dev/null 2>&1; then
		if [[ "${GITLEAKS_REQUIRED:-0}" == "1" ]]; then
			print_status "error" "gitleaks is required here but absent - a skipped gate in CI is a gate reporting its own blindness as OK"
			exit 1
		fi
		print_status "warning" "skip: gitleaks not installed (https://github.com/gitleaks/gitleaks#installing)"
		exit 0
	fi

	run_gitleaks
}

main "$@"
