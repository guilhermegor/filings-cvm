#!/bin/bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/lib/common.sh"

discover_files() {
	if git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
		git ls-files -z
		return 0
	fi
	find . \
		\( -path ./.git -o -path ./.venv -o -path ./node_modules \) -prune \
		-o -type f -print0
}

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
	if [ "$#" -gt 0 ]; then
		check_unix_filenames "$@" || exit 1
		return 0
	fi

	cd "$SCRIPT_DIR/.."
	local -a list_files=()

	local str_tmp
	str_tmp="$(mktemp)"
	# shellcheck disable=SC2064  # expand str_tmp NOW: the trap must name this run's file.
	trap "rm -f '$str_tmp'" RETURN
	if ! discover_files >"$str_tmp"; then
		print_status "error" "file discovery failed — refusing to check a partial list"
		exit 1
	fi
	mapfile -d '' -t list_files <"$str_tmp"

	if [ "${#list_files[@]}" -eq 0 ]; then
		print_status "error" "no files discovered — this gate would pass vacuously"
		exit 1
	fi

	check_unix_filenames "${list_files[@]}" || exit 1
}

main "$@"
