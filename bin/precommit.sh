#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/lib/common.sh"
# shellcheck source=bin/lib/bootstrap.sh
source "$SCRIPT_DIR/lib/bootstrap.sh"

ensure_safe_directory() {
	local str_probe
	str_probe="$(git rev-parse --is-inside-work-tree 2>&1)" && return 0
	case "$str_probe" in
	*"dubious ownership"*) ;;
	*) return 0 ;;
	esac
	local str_path
	str_path="$(printf '%s\n' "$str_probe" | sed -n 's/.*--add safe.directory //p' | head -n1)"
	str_path="${str_path#\'}"
	str_path="${str_path%\'}"
	if [ -z "$str_path" ]; then
		print_status "warning" "git flagged dubious ownership but no path could be parsed — skipping safe.directory"
		return 0
	fi
	print_status "config" "Registering git safe.directory for a shared work tree: $str_path"
	git config --global --add safe.directory "$str_path"
}

ensure_git_repo() {
	if ! command -v git >/dev/null 2>&1; then
		print_status "warning" "git not found — skipping pre-commit hooks (a runtime box never commits)"
		return 1
	fi

	ensure_safe_directory

	if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
		print_status "warning" "No git repository here — skipping pre-commit hooks (run inside a checkout to install them)"
		return 1
	fi

	return 0
}

install_hooks() {
	print_status "info" "Installing pre-commit hooks (commit-msg + pre-push)..."
	run_poetry run pre-commit install
	run_poetry run pre-commit install --hook-type commit-msg
	run_poetry run pre-commit install --hook-type pre-push
	print_status "success" "Pre-commit hooks installed"
}

main() {
	print_status "section" "Pre-commit Hook Setup"

	if ! ensure_git_repo; then
		return 0
	fi

	bootstrap_init
	if ! ensure_poetry; then
		print_status "error" "Poetry could not be resolved — cannot install pre-commit hooks"
		return 1
	fi
	install_hooks
}

main "$@"
