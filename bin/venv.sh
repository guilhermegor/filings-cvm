#!/usr/bin/env bash
# Set up the Python virtual environment: pyenv-preferred with a system-Python
# fallback (for hosts where pyenv cannot be installed), optional corporate-CA
# wiring, then a Poetry install with a stdlib-venv + pip fallback for restricted
# environments. Cross-platform logic lives in lib/bootstrap.sh and lib/pip_fallback.sh.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/lib/common.sh"
# shellcheck source=bin/lib/bootstrap.sh
source "$SCRIPT_DIR/lib/bootstrap.sh"
# shellcheck source=bin/lib/pip_fallback.sh
source "$SCRIPT_DIR/lib/pip_fallback.sh"

configure_poetry_virtualenv() {
	export POETRY_VIRTUALENVS_IN_PROJECT=true

	if [[ -f "$PROJECT_ROOT/poetry.toml" ]]; then
		print_status "config" "Using Poetry local config from poetry.toml"
	else
		print_status "info" "Configuring Poetry virtualenv (in-project)..."
		run_poetry config virtualenvs.in-project true --local
	fi

	print_status "info" "Selecting Python interpreter for Poetry..."
	run_poetry env use "$PYTHON" >/dev/null

	if ! pip_fallback_poetry_env_is_local; then
		print_status "warning" "Poetry is using a non-local virtualenv."
		print_status "warning" "Trying one reset to recreate .venv locally..."

		run_poetry env remove --all >/dev/null 2>&1 || true
		run_poetry env use "$PYTHON" >/dev/null

		if ! pip_fallback_poetry_env_is_local; then
			print_status "warning" "Poetry still did not switch to .venv inside the project."
			return 1
		fi
	fi

	print_status "success" "Poetry environment configured for $PYTHON"
	return 0
}

upgrade_poetry_env_pip() {
	print_status "info" "Upgrading pip inside the Poetry environment..."
	run_poetry run python -m pip install --upgrade pip
	print_status "success" "pip upgraded inside the Poetry environment"
}

install_full_env_with_poetry() {
	if ! configure_poetry_virtualenv; then
		return 1
	fi

	upgrade_poetry_env_pip

	print_status "info" "Installing project dependencies with Poetry..."
	if ! run_poetry install --with dev,docs --no-interaction; then
		print_status "warning" "Poetry install failed for the full environment"
		return 1
	fi

	print_status "success" "Dependencies installed with Poetry"
	return 0
}

bootstrap_local_venv_with_pip() {
	local str_venv_python

	print_status "warning" "Creating local .venv with stdlib venv + pip fallback..."
	rm -rf "$PROJECT_ROOT/.venv"
	"$PYTHON" -m venv "$PROJECT_ROOT/.venv"

	str_venv_python="$(pip_fallback_project_venv_python)"
	pip_fallback_install_groups_in_venv \
		"$str_venv_python" \
		"main,dev,docs" \
		"project dependencies (main, dev, docs)"

	print_status "success" "Local .venv created with pip fallback"
	print_status "warning" "Fallback mode installed dependencies from pyproject.toml without Poetry package installation"
}

install_playwright_in_local_venv() {
	local str_venv_python
	str_venv_python="$(pip_fallback_project_venv_python)"

	if [[ -x "$str_venv_python" ]] && "$str_venv_python" -c "import playwright" >/dev/null 2>&1; then
		try_install_playwright_browsers "$str_venv_python"
	fi
}

install_playwright() {
	if run_poetry run python -c "import playwright" 2>/dev/null; then
		try_install_playwright_browsers run_poetry run python
	fi
}

try_install_playwright_browsers() {
	# Best-effort Playwright browser install. The Poetry/.venv environment is already
	# usable without browsers, so a failure here must NEVER abort `init` — it warns and
	# points at `make fix_playwright`. This guards against `playwright install` failing on
	# hosts without a compatible browser toolchain (notably `Error: spawn UNKNOWN` under
	# Git Bash/MINGW on Windows). `--with-deps` installs Linux OS packages via apt and is
	# only valid on Debian/Ubuntu, so it is added on Linux only.
	#
	# $@ is the Python launcher to run the install with, e.g. `run_poetry run python`
	# (a shell function is fine as the first word) or an absolute `.venv` python path.
	local -a cmd_python=("$@")
	local -a args_install=(chromium)
	[[ "${OS_TYPE:-$(detect_os)}" == "linux" ]] && args_install+=(--with-deps)

	print_status "info" "Installing Playwright browsers (best-effort)..."
	if "${cmd_python[@]}" -m playwright install "${args_install[@]}"; then
		print_status "success" "Playwright browsers installed"
	else
		print_status "warning" \
			"Could not install Playwright browsers — init continues; run 'make fix_playwright' later if you need them"
	fi
}

main() {
	local bool_full_env_ready=0
	local bool_fallback_used=0

	print_status "section" "Virtual Environment Setup"
	bootstrap_init
	ensure_python_version
	wire_corporate_ca

	if pip_fallback_ensure_project_poetry && install_full_env_with_poetry; then
		bool_full_env_ready=1
	else
		print_status "warning" "Falling back because Poetry could not provide a local full environment"
		bootstrap_local_venv_with_pip
		bool_fallback_used=1
	fi

	if [[ "$bool_full_env_ready" -eq 1 ]]; then
		install_playwright
		print_status "success" "Virtual environment ready"
		return 0
	fi

	if [[ "$bool_fallback_used" -eq 1 ]]; then
		install_playwright_in_local_venv
		print_status "warning" "Local .venv is ready for runtime usage; Poetry-managed package installation was skipped"
	fi
}

main "$@"
