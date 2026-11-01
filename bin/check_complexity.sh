#!/bin/bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/lib/common.sh"
# shellcheck source=bin/lib/bootstrap.sh
source "$SCRIPT_DIR/lib/bootstrap.sh"

declare -A DICT_MAX_COMPLEXITY=(
	["tests"]=1
	["src"]=2
	["bin"]=8
)

declare -A DICT_MAX_NESTED_BLOCKS=(
	["tests"]=2
	["src"]=3
	["bin"]=5
)

STR_ALLOW_MARKER="complexity-ok:"
_INT_SIGNATURE_SCAN_LINES=20
STR_ROOT="."
INT_FILES_SEEN=0

parse_args() {
	while [[ $# -gt 0 ]]; do
		case "$1" in
		--root)
			STR_ROOT="${2:-.}"
			shift 2
			;;
		*)
			print_status "error" "Unknown argument: $1 (only --root <dir> is accepted)"
			exit 2
			;;
		esac
	done
}

STR_RUFF_MODE=""

resolve_ruff() {
	STR_RUFF_MODE=""
	if resolve_poetry >/dev/null 2>&1 && run_poetry run ruff --version >/dev/null 2>&1; then
		STR_RUFF_MODE="poetry"
		return 0
	fi
	if command -v ruff >/dev/null 2>&1; then
		STR_RUFF_MODE="system"
	fi
}

run_ruff_check() {
	local str_dir="$1" str_rule="$2" str_config_key="$3" int_max="$4"
	local str_stderr int_status
	local -a list_args=(
		check "$str_dir"
		--select "$str_rule"
		--config "$SCRIPT_DIR/../ruff.toml"
		--config "$str_config_key = $int_max"
		--output-format concise
		--no-cache
	)

	str_stderr="$(mktemp)"
	int_status=0
	(
		unset FORCE_COLOR CLICOLOR_FORCE
		export NO_COLOR=1
		if [[ "$STR_RUFF_MODE" == "poetry" ]]; then
			run_poetry run ruff "${list_args[@]}"
		else
			ruff "${list_args[@]}"
		fi
	) 2>"$str_stderr" || int_status=$?

	if ((int_status > 1)); then
		print_status "error" "ruff failed on '$str_dir' (exit $int_status):"
		cat "$str_stderr" >&2
		rm -f "$str_stderr"
		exit 1
	fi
	rm -f "$str_stderr"
}

line_has_reasoned_hatch() {
	local str_file="$1" int_line="$2"
	local str_source str_reason int_scan int_last

	int_last=$((int_line + _INT_SIGNATURE_SCAN_LINES))
	for ((int_scan = int_line; int_scan <= int_last; int_scan++)); do
		str_source="$(sed -n "${int_scan}p" "$str_file" 2>/dev/null || true)"
		[[ -n "$str_source" ]] || break

		if [[ "$str_source" == *"$STR_ALLOW_MARKER"* ]]; then
			str_reason="${str_source#*"$STR_ALLOW_MARKER"}"
			str_reason="${str_reason#"${str_reason%%[![:space:]]*}"}"
			[[ -n "$str_reason" ]] && return 0
			return 1
		fi

		[[ "${str_source%%#*}" =~ :[[:space:]]*$ ]] && break
	done
	return 1
}

report_tree() {
	local str_dir="$1" str_rule="$2" str_config_key="$3" int_max="$4"
	local str_findings str_finding str_file int_line int_errors=0

	[[ -d "$str_dir" ]] || return 0

	str_findings="$(mktemp)"
	run_ruff_check "$str_dir" "$str_rule" "$str_config_key" "$int_max" >"$str_findings"

	while IFS= read -r str_finding; do
		[[ "$str_finding" == *"$str_rule"* ]] || continue
		str_file="${str_finding%%:*}"
		int_line="$(printf '%s' "$str_finding" | cut -d: -f2)"

		if line_has_reasoned_hatch "$str_file" "$int_line"; then
			continue
		fi
		print_status "error" "$str_finding (max $int_max in $str_dir/)"
		int_errors=1
	done <"$str_findings"

	rm -f "$str_findings"
	return "$int_errors"
}

count_python_files() {
	local str_dir int_total=0 int_here
	for str_dir in "${!DICT_MAX_COMPLEXITY[@]}"; do
		[[ -d "$str_dir" ]] || continue
		int_here="$(find "$str_dir" -type f -name '*.py' | wc -l)"
		int_total=$((int_total + int_here))
	done
	printf '%s' "$int_total"
}

check_all_trees() {
	local str_dir int_errors=0

	for str_dir in "${!DICT_MAX_COMPLEXITY[@]}"; do
		report_tree "$str_dir" "C901" "lint.mccabe.max-complexity" \
			"${DICT_MAX_COMPLEXITY[$str_dir]}" || int_errors=1
	done
	for str_dir in "${!DICT_MAX_NESTED_BLOCKS[@]}"; do
		report_tree "$str_dir" "PLR1702" "lint.pylint.max-nested-blocks" \
			"${DICT_MAX_NESTED_BLOCKS[$str_dir]}" || int_errors=1
	done

	return "$int_errors"
}

main() {
	parse_args "$@"
	bootstrap_init >/dev/null 2>&1 || true
	cd "$STR_ROOT" || exit 1

	resolve_ruff
	if [[ -z "$STR_RUFF_MODE" ]]; then
		print_status "error" "ruff not resolvable (tried 'poetry run ruff' and PATH)."
		exit 1
	fi

	INT_FILES_SEEN="$(count_python_files)"
	if [[ "$INT_FILES_SEEN" -eq 0 ]]; then
		print_status "error" "No Python files found under ${!DICT_MAX_COMPLEXITY[*]} — refusing to report success."
		exit 1
	fi

	if ! check_all_trees; then
		print_status "error" "Reduce the branching/nesting, or annotate the def line: # $STR_ALLOW_MARKER <reason>"
		exit 1
	fi

	print_status "success" "Cyclomatic complexity and nesting depth within limits ($INT_FILES_SEEN Python file(s))."
}

main "$@"
