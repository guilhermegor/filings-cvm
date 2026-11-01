#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/lib/common.sh"
# shellcheck source=bin/lib/bootstrap.sh
source "$SCRIPT_DIR/lib/bootstrap.sh"

bool_check=false
bool_poetry_ok=false

resolve_linter_mode() {
	local str_tool="$1"
	if [[ "$bool_poetry_ok" == true ]] && run_poetry run "$str_tool" --version >/dev/null 2>&1; then
		printf 'poetry'
		return 0
	fi
	if command -v "$str_tool" >/dev/null 2>&1 && "$str_tool" --version >/dev/null 2>&1; then
		printf 'system'
		return 0
	fi
	printf ''
}

invoke_linter() {
	local str_mode="$1"
	local str_tool="$2"
	shift 2
	if [[ "$str_mode" == poetry ]]; then
		run_poetry run "$str_tool" "$@"
	else
		"$str_tool" "$@"
	fi
}

run_shellcheck() {
	local str_mode
	str_mode="$(resolve_linter_mode shellcheck)"
	if [[ -z "$str_mode" ]]; then
		print_status warning "skip: shellcheck absent (poetry install --with dev, or bash bin/install_shell_linters.sh)"
		return 0
	fi
	print_status info "shellcheck [$str_mode]: ${#list_files[@]} script(s)"
	invoke_linter "$str_mode" shellcheck --severity=warning --exclude=SC1091 "${list_files[@]}"
	print_status success "shellcheck OK"
}

run_shfmt() {
	local str_mode
	str_mode="$(resolve_linter_mode shfmt)"
	if [[ -z "$str_mode" ]]; then
		print_status warning "skip: shfmt absent (poetry install --with dev, or bash bin/install_shell_linters.sh)"
		return 0
	fi
	if [[ "$bool_check" == true ]]; then
		print_status info "shfmt --check [$str_mode] (diff only)"
		invoke_linter "$str_mode" shfmt -d "${list_files[@]}"
	else
		print_status info "shfmt -w [$str_mode] (format in place)"
		invoke_linter "$str_mode" shfmt -w "${list_files[@]}"
	fi
	print_status success "shfmt OK"
}

main() {
	cd "$SCRIPT_DIR/.."

	if [[ "${1:-}" == "--check" ]]; then
		bool_check=true
	fi

	PYTHON="$(resolve_python 2>/dev/null)" || true
	export PYTHON
	if resolve_poetry; then
		bool_poetry_ok=true
	fi

	mapfile -t list_files < <(find bin -name '*.sh' -type f)

	run_shellcheck
	run_shfmt
}

main "$@"
