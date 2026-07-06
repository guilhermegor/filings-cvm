#!/usr/bin/env bash
#
# lint_shell.sh — shellcheck + shfmt over the project's shell scripts.
#
# Single source of truth for shell linting: called by both `make lint` /
# `./tasks.sh lint` and the pre-commit `lint-shell` hook.
#
# Both tools are pip-installable dev-deps (shellcheck-py / shfmt-py vendor their
# binaries, incl. win_amd64 wheels), so each is resolved PREFERABLY through the Poetry
# venv: `poetry run <tool>` finds the vendored binary wherever the venv lives —
# INCLUDING a Windows UNC/mapped A: drive. A bare-PATH lookup runs outside the venv, so
# a Windows box would silently skip BOTH linters. It then falls back to a SYSTEM binary
# (e.g. installed via bin/install_shell_linters.sh: choco/scoop/brew/apt) and only SKIPS
# gracefully (exit 0 + message) when neither exists — a constrained box never hard-fails
# the lint/commit flow. A real lint failure always propagates.
#
# This is a resolve, not an install: an optional linter must never trigger a Poetry
# install (matches lint_yaml.sh / lint_sql.sh).
#
# Modes:
#   (default)  shfmt -w  — format in place (matches `ruff format` in `make lint`).
#   --check    shfmt -d  — diff only, non-mutating (used by the pre-commit gate).

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/lib/common.sh"
# shellcheck source=bin/lib/bootstrap.sh
source "$SCRIPT_DIR/lib/bootstrap.sh" # resolve_python / resolve_poetry / run_poetry

bool_check=false
bool_poetry_ok=false

# Resolve how to launch a vendored CLI: prints "poetry" (pip wheel inside the venv —
# preferred, found on any drive incl. A:), "system" (a binary on PATH), or "" when
# absent. Probes with --version so a real lint exit code is never mistaken for "absent".
resolve_linter_mode() {
	local str_tool="$1"
	if [[ "$bool_poetry_ok" == true ]] && run_poetry run "$str_tool" --version >/dev/null 2>&1; then
		printf 'poetry'
		return 0
	fi
	if command -v "$str_tool" >/dev/null 2>&1; then
		printf 'system'
		return 0
	fi
	printf ''
}

# Run a resolved linter in the given mode ("poetry" via the venv, else a system binary).
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
	# Canonical gate (bin/CLAUDE.md): warning-and-above, SC1091 excluded globally
	# (siblings are sourced via runtime paths shellcheck cannot follow).
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

	# Resolve Poetry once (resolve, never install). PYTHON feeds the `python -m poetry`
	# fallback inside resolve_poetry.
	PYTHON="$(resolve_python 2>/dev/null)" || true
	export PYTHON
	if resolve_poetry; then
		bool_poetry_ok=true
	fi

	# The shell files to lint: the task runner, the bin scripts and the shared libs.
	mapfile -t list_files < <(
		printf '%s\n' tasks.sh
		find bin -name '*.sh' -type f
	)

	run_shellcheck
	run_shfmt
}

main "$@"
