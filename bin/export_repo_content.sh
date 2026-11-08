#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR/.." || exit 1
source "$SCRIPT_DIR/lib/common.sh"

OUTPUT_FILE="${1:-repo_context.txt}"
OUTPUT_REL="${OUTPUT_FILE#./}"
TMP_OUTPUT=""
TMP_LIST=""

PRUNE_DIRS=(
	.git .venv venv env .uv
	__pycache__ .pytest_cache .ruff_cache .mypy_cache
	.idea build dist htmlcov coverage .nyc_output
	node_modules git_diffs
	playwright-report test-results blob-report .cache
)

cleanup() {
	[[ -n "${TMP_OUTPUT:-}" && -f "$TMP_OUTPUT" ]] && rm -f "$TMP_OUTPUT"
	[[ -n "${TMP_LIST:-}" && -f "$TMP_LIST" ]] && rm -f "$TMP_LIST"
	return 0
}

trap cleanup EXIT

prepare_output_path() {
	local output_dir
	output_dir="$(dirname "$OUTPUT_FILE")"
	ensure_dir "$output_dir"
}

create_temp_files() {
	TMP_OUTPUT="$(mktemp)"
	TMP_LIST="$(mktemp)"
}

is_output_file() {
	local file="${1:-}"
	[[ "${file#./}" == "$OUTPUT_REL" ]]
}

is_secret_or_noise() {
	local rel="${1#./}"
	local base
	base="$(basename "$rel")"
	case "$base" in
	.env.example)
		return 1
		;;
	.env | .env.*)
		return 0
		;;
	*.log | .DS_Store)
		return 0
		;;
	esac
	[[ "$rel" == "bin/corporate_ca.pem" ]]
}

should_include() {
	local file="$1"
	[[ -f "$file" ]] || return 1
	is_output_file "$file" && return 1
	is_secret_or_noise "$file" && return 1
	return 0
}

is_probably_text_file() {
	local file="${1:-}"
	[[ ! -s "$file" ]] && return 0
	LC_ALL=C grep -Iq . "$file"
}

collect_file_list_find() {
	local find_args=(.)
	local dir
	for dir in "${PRUNE_DIRS[@]}"; do
		find_args+=(-name "$dir" -prune -o)
	done
	find_args+=(-name '*.egg-info' -prune -o -type f -print)
	find "${find_args[@]}" | LC_ALL=C sort
}

collect_file_list() {
	print_status "info" "Collecting repository files..."
	if git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
		print_status "config" "Using git ls-files (honors .gitignore)"
		git ls-files -z --cached --others --exclude-standard |
			tr '\0' '\n' | LC_ALL=C sort >"$TMP_LIST"
		return
	fi
	print_status "config" "No git repo detected — using find with prune list"
	collect_file_list_find >"$TMP_LIST"
}

write_file_paths_section() {
	print_status "info" "Writing file paths..."
	{
		echo '===== FILE PATHS ====='
		while IFS= read -r file; do
			should_include "$file" || continue
			printf '%s\n' "${file#./}"
		done <"$TMP_LIST"
		echo
	} >>"$TMP_OUTPUT"
}

write_file_contents_section() {
	print_status "info" "Writing file contents..."
	{
		echo '===== FILE CONTENTS ====='
		echo
	} >>"$TMP_OUTPUT"

	while IFS= read -r file; do
		should_include "$file" || continue
		local rel_path="${file#./}"
		{
			printf '===== FILE: %s =====\n\n' "$rel_path"
			if is_probably_text_file "$file"; then
				cat "$file"
			else
				printf '[skipped: non-text/binary file]\n'
			fi
			printf '\n\n'
		} >>"$TMP_OUTPUT"
	done <"$TMP_LIST"
}

finalize_output() {
	mv "$TMP_OUTPUT" "$OUTPUT_FILE"
	TMP_OUTPUT=""
	print_status "success" "Exported repository context to: $OUTPUT_FILE"
}

main() {
	print_status "section" "Export repository content"
	prepare_output_path
	create_temp_files
	collect_file_list
	write_file_paths_section
	write_file_contents_section
	finalize_output
}

main "$@"
