#!/usr/bin/env bash

if [[ "${BASH_SOURCE[0]}" == "$0" ]]; then
	echo "bin/lib/pip_fallback.sh is meant to be sourced, not executed." >&2
	exit 1
fi

if [[ "${_BX_PIP_FALLBACK_LOADED:-}" == "1" ]]; then
	return 0
fi
_BX_PIP_FALLBACK_LOADED=1

PIP_FALLBACK_LIB_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# shellcheck source=bin/lib/common.sh
source "$PIP_FALLBACK_LIB_DIR/common.sh"
# shellcheck source=bin/lib/bootstrap.sh
source "$PIP_FALLBACK_LIB_DIR/bootstrap.sh"

PIP_FALLBACK_ARGS=()
PIP_FALLBACK_USER_ARGS=()

pip_fallback_project_venv_python() {
	if [[ "$OS_TYPE" == "windows" ]]; then
		echo "$PROJECT_ROOT/.venv/Scripts/python.exe"
	else
		echo "$PROJECT_ROOT/.venv/bin/python"
	fi
}

pip_fallback_recreate_project_venv() {
	if running_inside_project_venv; then
		print_status "error" "Refusing to recreate .venv from inside it — that would delete the interpreter in use"
		print_status "error" "Run 'bash bin/venv.sh' from a shell outside 'poetry run', 'poe' and any activated virtualenv"
		return 1
	fi

	rm -rf "$PROJECT_ROOT/.venv"
	"$PYTHON" -m venv "$PROJECT_ROOT/.venv"
}

pip_fallback_normalize_path_for_compare() {
	local str_path="$1"

	str_path="${str_path//$'\r'/}"
	str_path="${str_path//$'\n'/}"
	str_path="${str_path//\\//}"
	str_path="${str_path%/}"

	printf '%s\n' "${str_path,,}"
}

pip_fallback_poetry_spec_from_requirements() {
	local str_line
	local str_file="$PROJECT_ROOT/requirements.txt"

	if [[ -f "$str_file" ]]; then
		str_line="$(grep -E '^[[:space:]]*poetry([[:space:]]|[<>=!~])' "$str_file" | head -n1 || true)"
		str_line="${str_line%%;*}"
		str_line="${str_line#"${str_line%%[![:space:]]*}"}"
		str_line="${str_line%"${str_line##*[![:space:]]}"}"

		if [[ -n "$str_line" ]]; then
			echo "$str_line"
			return 0
		fi
	fi

	echo "poetry>=2.4,<2.5"
}

pip_fallback_populate_pip_args() {
	PIP_FALLBACK_ARGS=(
		--trusted-host pypi.org
		--trusted-host files.pythonhosted.org
		--trusted-host pypi.python.org
	)

	if [[ -n "${PIP_CERT:-}" ]]; then
		PIP_FALLBACK_ARGS+=(--cert "$PIP_CERT")
	fi

	PIP_FALLBACK_USER_ARGS=(--user)
	if python_in_venv "$PYTHON"; then
		PIP_FALLBACK_USER_ARGS=()
	fi
}

pip_fallback_ensure_toml_reader() {
	if "$PYTHON" -c "import tomllib" >/dev/null 2>&1; then
		return 0
	fi

	if "$PYTHON" -c "import tomli" >/dev/null 2>&1; then
		return 0
	fi

	pip_fallback_populate_pip_args
	print_status "info" "Installing tomli for pyproject fallback parsing..."
	"$PYTHON" -m pip install "${PIP_FALLBACK_ARGS[@]}" ${PIP_FALLBACK_USER_ARGS[@]+"${PIP_FALLBACK_USER_ARGS[@]}"} tomli
}

pip_fallback_ensure_project_poetry() {
	local str_poetry_spec

	pip_fallback_populate_pip_args
	str_poetry_spec="$(pip_fallback_poetry_spec_from_requirements)"

	print_status "info" "Ensuring Poetry matches spec: $str_poetry_spec"
	"$PYTHON" -m pip install "${PIP_FALLBACK_ARGS[@]}" --upgrade ${PIP_FALLBACK_USER_ARGS[@]+"${PIP_FALLBACK_USER_ARGS[@]}"} "$str_poetry_spec"

	if "$PYTHON" -m poetry --version >/dev/null 2>&1; then
		# shellcheck disable=SC2034
		POETRY_CMD=("$PYTHON" -m poetry)
		print_status "info" "Poetry found: $(run_poetry --version 2>&1 | head -n1)"
		print_status "config" "Using Poetry via $PYTHON -m poetry"
		return 0
	fi

	print_status "error" "Poetry could not be loaded via $PYTHON -m poetry after installation"
	return 1
}

pip_fallback_poetry_env_is_local() {
	local str_env_path
	local str_expected_env
	local str_env_cmp
	local str_expected_cmp

	str_env_path="$(run_poetry env info --path 2>/dev/null || true)"
	str_env_path="${str_env_path//$'\r'/}"
	str_env_path="${str_env_path//$'\n'/}"

	str_expected_env="$(to_native_path "$PROJECT_ROOT/.venv")"

	if [[ -n "$str_env_path" ]]; then
		print_status "config" "Poetry env path: $str_env_path"
	fi

	str_env_cmp="$(pip_fallback_normalize_path_for_compare "$str_env_path")"
	str_expected_cmp="$(pip_fallback_normalize_path_for_compare "$str_expected_env")"

	[[ -n "$str_env_path" && "$str_env_cmp" == "$str_expected_cmp" ]]
}

pip_fallback_emit_pip_requirements_from_pyproject() {
	local str_groups_csv="$1"

	PROJECT_ROOT="$PROJECT_ROOT" BX_GROUPS="$str_groups_csv" \
		"$PYTHON" "$(dirname "${BASH_SOURCE[0]}")/pip_requirements.py"
}

pip_fallback_write_requirements_file() {
	local str_groups_csv="$1"
	local str_req_file="$2"

	pip_fallback_ensure_toml_reader || return 1
	pip_fallback_emit_pip_requirements_from_pyproject "$str_groups_csv" >"$str_req_file" ||
		return 1
	pip_fallback_prune_unused_db_drivers "$str_req_file" || return 1
}

pip_fallback_requirement_name() {
	local str_req="$1"

	str_req="${str_req%%;*}"
	str_req="${str_req%%[*}"
	str_req="${str_req%%[<>=!~]*}"
	str_req="${str_req#"${str_req%%[![:space:]]*}"}"
	str_req="${str_req%"${str_req##*[![:space:]]}"}"

	printf '%s\n' "$str_req"
}

pip_fallback_backends_needing_driver() {
	case "$1" in
	psycopg) echo "postgresql" ;;
	oracledb) echo "oracle" ;;
	pyodbc) echo "mssql" ;;
	mysql-connector-python) echo "mysql mariadb" ;;
	*) echo "" ;;
	esac
}

pip_fallback_resolve_db_backend() {
	local str_backend

	str_backend="$(ENV_FILE="$PROJECT_ROOT/.env" _read_env_var DB_BACKEND 2>/dev/null || true)"
	str_backend="${str_backend//$'\r'/}"
	str_backend="${str_backend//[[:space:]]/}"

	printf '%s\n' "${str_backend:-sqlite}" | tr '[:upper:]' '[:lower:]'
}

pip_fallback_prune_unused_db_drivers() {
	local str_req_file="$1"
	local str_backend
	local str_req
	local str_name
	local str_backends
	local str_pruned
	local -a arr_keep=()
	local -a arr_dropped=()

	[[ -s "$str_req_file" ]] || return 0

	str_backend="$(pip_fallback_resolve_db_backend)"

	while IFS= read -r str_req; do
		str_name="$(pip_fallback_requirement_name "$str_req")"
		str_backends="$(pip_fallback_backends_needing_driver "$str_name")"

		if [[ -n "$str_backends" && " $str_backends " != *" $str_backend "* ]]; then
			arr_dropped+=("$str_name")
			continue
		fi

		arr_keep+=("$str_req")
	done <"$str_req_file"

	if ((${#arr_dropped[@]} == 0)); then
		return 0
	fi

	printf '%s\n' "${arr_keep[@]}" >"$str_req_file"
	str_pruned="$(
		IFS=', '
		echo "${arr_dropped[*]}"
	)"
	print_status "config" "DB_BACKEND=$str_backend — skipping unused DB drivers: $str_pruned"
}

pip_fallback_install_requirements_file_into_venv() {
	local str_venv_python="$1"
	local str_req_file="$2"
	local str_req
	local str_failed
	local -a arr_failed=()

	if [[ ! -s "$str_req_file" ]]; then
		print_status "warning" "No dependencies were generated from pyproject.toml for pip fallback"
		return 0
	fi

	if "$str_venv_python" -m pip install "${PIP_FALLBACK_ARGS[@]}" -r "$str_req_file"; then
		return 0
	fi

	print_status "warning" "Batch install failed — retrying one requirement at a time to isolate it"

	while IFS= read -r str_req; do
		[[ -n "$str_req" && "$str_req" != \#* ]] || continue

		if ! "$str_venv_python" -m pip install "${PIP_FALLBACK_ARGS[@]}" "$str_req"; then
			arr_failed+=("$str_req")
			print_status "warning" "Index refused: $str_req"
		fi
	done <"$str_req_file"

	if ((${#arr_failed[@]} == 0)); then
		print_status "success" "All requirements installed individually"
		return 0
	fi

	str_failed="$(
		IFS=', '
		echo "${arr_failed[*]}"
	)"
	print_status "error" "The package index refused: $str_failed"
	print_status "error" "An HTTP 403 here means the index ALLOWLIST rejected the package, not that the network is down — the remedies are opposite. Ask for it to be allowlisted, or vendor it (an offline wheelhouse is tracked in blueprintx#127)."
	return 1
}

pip_fallback_verify_importable() {
	local str_venv_python="$1"
	local str_req_file="$2"

	if "$str_venv_python" "$PIP_FALLBACK_LIB_DIR/verify_venv_imports.py" "$str_req_file"; then
		return 0
	fi

	print_status "error" "pip reported the install as done, but the target venv cannot import what was declared"
	print_status "error" "This is the silent-empty-venv failure tracked in blueprintx#127 — a blocked package index can report success with nothing usable installed."
	return 1
}

pip_fallback_install_groups_in_venv() {
	local str_venv_python="$1"
	local str_groups_csv="$2"
	local str_label="${3:-dependencies}"
	local str_req_file

	pip_fallback_populate_pip_args
	str_req_file="$(mktemp "${TMPDIR:-/tmp}/bx_pip_fallback.XXXXXX.txt")"

	print_status "info" "Installing $str_label with pip fallback..."
	if ! pip_fallback_write_requirements_file "$str_groups_csv" "$str_req_file"; then
		print_status "error" "Could not build the pip requirements for $str_label."
		rm -f "$str_req_file"
		return 1
	fi

	if ! "$str_venv_python" -m pip install "${PIP_FALLBACK_ARGS[@]}" --upgrade pip setuptools wheel; then
		print_status "error" "Could not upgrade pip/setuptools/wheel in the target venv."
		rm -f "$str_req_file"
		return 1
	fi

	if ! pip_fallback_install_requirements_file_into_venv "$str_venv_python" "$str_req_file"; then
		rm -f "$str_req_file"
		return 1
	fi

	if ! pip_fallback_verify_importable "$str_venv_python" "$str_req_file"; then
		rm -f "$str_req_file"
		return 1
	fi

	rm -f "$str_req_file"
	print_status "success" "$str_label installed with pip fallback"
}
