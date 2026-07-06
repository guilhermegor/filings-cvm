#!/usr/bin/env bash
# Run the scaffolded project entrypoint.
# Strategy:
#  1) Resolve the entrypoint module automatically.
#  2) Ensure a local project virtualenv exists and is up to date enough to run.
#  3) Prefer Poetry for dependency installation.
#  4) Fall back to stdlib venv + pip requirements from pyproject.toml when Poetry
#     is unavailable or when Poetry bootstrap fails in restricted environments.
# pyenv-preferred: when a bootstrap is needed, the pinned .python-version is
# selected first so both the Poetry and pip-fallback branches use it.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/lib/common.sh"
# shellcheck source=bin/lib/bootstrap.sh
source "$SCRIPT_DIR/lib/bootstrap.sh"
# shellcheck source=bin/lib/pip_fallback.sh
source "$SCRIPT_DIR/lib/pip_fallback.sh"

resolve_entrypoint_module() {
	local project_root="$PROJECT_ROOT"
	local -a arr_candidates=()
	local str_file
	local str_module

	if [[ -f "$project_root/src/main.py" ]]; then
		arr_candidates+=("src.main")
	fi

	if [[ -f "$project_root/src/controller/main.py" ]]; then
		arr_candidates+=("src.controller.main")
	fi

	while IFS= read -r str_file; do
		[[ -n "$str_file" ]] || continue

		case "$str_file" in
		"$project_root/src/main.py" | "$project_root/src/controller/main.py")
			continue
			;;
		esac

		str_module="${str_file#"$project_root/"}"
		str_module="${str_module%.py}"
		str_module="${str_module//\//.}"
		arr_candidates+=("$str_module")
	done < <(find "$project_root/src" -mindepth 2 -maxdepth 2 -type f -name "main.py" 2>/dev/null | sort)

	if [[ "${#arr_candidates[@]}" -eq 0 ]]; then
		print_status "error" "No runnable entrypoint found."
		print_status "error" "Expected one of:"
		print_status "error" "  - src/main.py"
		print_status "error" "  - src/controller/main.py"
		print_status "error" "  - src/<package>/main.py"
		return 1
	fi

	if [[ "${#arr_candidates[@]}" -gt 1 ]]; then
		print_status "warning" "Multiple entrypoints found; using the first one."
		for str_module in "${arr_candidates[@]}"; do
			print_status "config" "Candidate entrypoint: $str_module"
		done
	fi

	echo "${arr_candidates[0]}"
}

runtime_env_needs_bootstrap() {
	local str_venv_python
	str_venv_python="$(pip_fallback_project_venv_python)"

	if [[ ! -x "$str_venv_python" ]]; then
		return 0
	fi

	if [[ "$PROJECT_ROOT/pyproject.toml" -nt "$str_venv_python" ]]; then
		return 0
	fi

	if [[ -f "$PROJECT_ROOT/poetry.lock" && "$PROJECT_ROOT/poetry.lock" -nt "$str_venv_python" ]]; then
		return 0
	fi

	return 1
}

bootstrap_runtime_with_poetry() {
	print_status "info" "Bootstrapping runtime environment with Poetry..."

	export POETRY_VIRTUALENVS_IN_PROJECT=true

	if [[ -f "$PROJECT_ROOT/poetry.toml" ]]; then
		print_status "config" "Using Poetry local config from poetry.toml"
	fi

	run_poetry env use "$PYTHON" >/dev/null 2>&1 || true

	if ! pip_fallback_poetry_env_is_local; then
		print_status "warning" "Poetry is not using the local .venv for this project"
		return 1
	fi

	if run_poetry install --only main --no-interaction; then
		print_status "success" "Runtime dependencies installed with Poetry"
		return 0
	fi

	print_status "warning" "Poetry runtime bootstrap failed"
	return 1
}

bootstrap_runtime_with_pip() {
	local str_venv_python

	print_status "warning" "Falling back to stdlib venv + pip requirements install"
	rm -rf "$PROJECT_ROOT/.venv"
	"$PYTHON" -m venv "$PROJECT_ROOT/.venv"

	str_venv_python="$(pip_fallback_project_venv_python)"
	pip_fallback_install_groups_in_venv \
		"$str_venv_python" \
		"main" \
		"runtime dependencies"

	print_status "success" "Runtime dependencies installed with pip"
}

ensure_runtime_env() {
	local str_venv_python

	str_venv_python="$(pip_fallback_project_venv_python)"

	if ! runtime_env_needs_bootstrap; then
		print_status "info" "Using existing project virtualenv: $str_venv_python"
		return 0
	fi

	# A bootstrap is required — pin the interpreter first so a pyenv-pinned
	# Python is used on both the Poetry and pip-fallback branches below.
	ensure_python_version

	if pip_fallback_ensure_project_poetry; then
		if bootstrap_runtime_with_poetry; then
			return 0
		fi
	fi

	bootstrap_runtime_with_pip
}

run_entrypoint() {
	local str_entrypoint="$1"
	local str_venv_python

	str_venv_python="$(pip_fallback_project_venv_python)"
	print_status "info" "Entrypoint module: $str_entrypoint"

	if [[ -x "$str_venv_python" ]]; then
		"$str_venv_python" -m "$str_entrypoint"
		return 0
	fi

	if pip_fallback_ensure_project_poetry; then
		run_poetry run python -m "$str_entrypoint"
		return 0
	fi

	"$PYTHON" -m "$str_entrypoint"
}

main() {
	local str_entrypoint

	bootstrap_init
	wire_corporate_ca

	export PYTHONPATH=".:src"

	str_entrypoint="$(resolve_entrypoint_module)"
	ensure_runtime_env
	run_entrypoint "$str_entrypoint"
}

main "$@"
