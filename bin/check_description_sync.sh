#!/bin/bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/lib/common.sh"

ROOT="${1:-.}"

manifest_description() {
	python3 "$SCRIPT_DIR/lib/description_sources.py" manifest "$ROOT"
}

mkdocs_description() {
	python3 "$SCRIPT_DIR/lib/description_sources.py" mkdocs "$ROOT/mkdocs.yml"
}

github_about() {
	local str_slug
	str_slug="$(git -C "$ROOT" remote get-url origin 2>/dev/null |
		sed -E 's#^(git@github\.com:|https://github\.com/)##; s#\.git$##')" || true
	if [[ -z "$str_slug" || "$str_slug" == *:* || "$str_slug" == */*/* ]]; then
		return 3
	fi
	if [[ -z "${GH_TOKEN:-${GITHUB_TOKEN:-}}" ]] || ! command -v gh >/dev/null 2>&1; then
		return 3
	fi
	GH_TOKEN="${GH_TOKEN:-${GITHUB_TOKEN:-}}" gh api "repos/$str_slug" --jq '.description // ""'
}

compare() {
	local str_label="$1" str_expected="$2" str_actual="$3"
	if [[ "$str_expected" == "$str_actual" ]]; then
		print_status "success" "$str_label matches the manifest description"
		return 0
	fi
	print_status "error" "$str_label differs from the manifest description"
	print_status "error" "  manifest: $str_expected"
	print_status "error" "  $str_label: $str_actual"
	return 1
}

main() {
	local str_manifest str_other int_status=0 int_compared=0 int_rc=0

	str_manifest="$(manifest_description)" || int_rc=$?
	if [[ "$int_rc" -eq 3 ]]; then
		print_status "warning" "SKIPPED description sync: no pyproject.toml or package.json in $ROOT"
		return 0
	elif [[ "$int_rc" -ne 0 ]]; then
		print_status "error" "the manifest in $ROOT exists but its description cannot be read"
		return 1
	fi

	int_rc=0
	str_other="$(mkdocs_description)" || int_rc=$?
	if [[ "$int_rc" -eq 0 ]]; then
		compare "mkdocs.yml site_description" "$str_manifest" "$str_other" || int_status=1
		int_compared=$((int_compared + 1))
	elif [[ "$int_rc" -eq 4 ]]; then
		print_status "warning" "SKIPPED mkdocs.yml comparison: no site_description in $ROOT/mkdocs.yml"
	else
		print_status "error" "mkdocs.yml site_description is present but cannot be parsed"
		int_status=1
	fi

	if str_other="$(github_about)"; then
		compare "GitHub About" "$str_manifest" "$str_other" || int_status=1
		int_compared=$((int_compared + 1))
	else
		print_status "warning" "SKIPPED GitHub About comparison: needs a github.com origin remote, gh and GH_TOKEN/GITHUB_TOKEN"
	fi

	if [[ "$int_compared" -eq 0 ]]; then
		print_status "warning" "description sync compared nothing: every counterpart was skipped"
	fi
	return "$int_status"
}

main "$@"
