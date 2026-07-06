#!/usr/bin/env bash
# Sourced lib — shared Poetry/bootstrap/pip-fallback helpers for venv.sh and run.sh.

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

pip_fallback_project_venv_python() {
	if [[ "$OS_TYPE" == "windows" ]]; then
		echo "$PROJECT_ROOT/.venv/Scripts/python.exe"
	else
		echo "$PROJECT_ROOT/.venv/bin/python"
	fi
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
	"$PYTHON" -m pip install "${PIP_FALLBACK_ARGS[@]}" --user tomli
}

pip_fallback_ensure_project_poetry() {
	local str_poetry_spec

	pip_fallback_populate_pip_args
	str_poetry_spec="$(pip_fallback_poetry_spec_from_requirements)"

	print_status "info" "Ensuring Poetry matches spec: $str_poetry_spec"
	"$PYTHON" -m pip install "${PIP_FALLBACK_ARGS[@]}" --upgrade --user "$str_poetry_spec"

	if "$PYTHON" -m poetry --version >/dev/null 2>&1; then
		# POETRY_CMD is consumed by run_poetry (defined in the sourced bootstrap.sh).
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

	PROJECT_ROOT="$PROJECT_ROOT" BX_GROUPS="$str_groups_csv" "$PYTHON" - <<'PYEOF'
from __future__ import annotations

import os
from pathlib import Path

try:
    import tomllib
except ModuleNotFoundError:
    import tomli as tomllib


def parse_version_parts(raw: str) -> list[int]:
    parts = raw.strip().split(".")
    numbers: list[int] = []

    for part in parts:
        digits = ""
        for char in part:
            if char.isdigit():
                digits += char
            else:
                break
        numbers.append(int(digits or "0"))

    return numbers


def caret_to_range(raw: str) -> str:
    base = raw[1:].strip()
    parts = parse_version_parts(base)

    while len(parts) < 3:
        parts.append(0)

    major, minor, patch = parts[:3]

    if major > 0:
        upper = f"{major + 1}.0.0"
    elif minor > 0:
        upper = f"0.{minor + 1}.0"
    else:
        upper = f"0.0.{patch + 1}"

    return f">={base},<{upper}"


def tilde_to_range(raw: str) -> str:
    base = raw[1:].strip()
    parts_raw = base.split(".")
    parts = parse_version_parts(base)

    while len(parts) < 3:
        parts.append(0)

    major, minor, _patch = parts[:3]

    if len(parts_raw) <= 1:
        upper = f"{major + 1}.0.0"
    else:
        upper = f"{major}.{minor + 1}.0"

    return f">={base},<{upper}"


def normalize_version_spec(spec: str) -> str:
    spec = str(spec).strip()

    if spec in {"", "*"}:
        return ""

    if spec.startswith("^"):
        return caret_to_range(spec)

    if spec.startswith("~") and not spec.startswith("~="):
        return tilde_to_range(spec)

    if spec.startswith((">=", "<=", "==", "!=", ">", "<", "~=")) or "," in spec:
        return spec

    return f"=={spec}"


def build_requirement(name: str, spec) -> str | None:
    if name.lower() == "python":
        return None

    if isinstance(spec, str):
        version = normalize_version_spec(spec)
        return f"{name}{version}"

    if isinstance(spec, dict):
        if spec.get("optional"):
            return None

        for unsupported_key in ("path", "git", "url"):
            if unsupported_key in spec:
                raise SystemExit(
                    f"Unsupported dependency type for pip fallback: {name} -> {unsupported_key}"
                )

        extras = spec.get("extras") or []
        extras_part = f"[{','.join(extras)}]" if extras else ""
        version = normalize_version_spec(spec.get("version", ""))
        markers = spec.get("markers", "")

        requirement = f"{name}{extras_part}{version}"
        if markers:
            requirement = f"{requirement} ; {markers}"

        return requirement

    raise SystemExit(f"Unsupported dependency format for {name}: {spec!r}")


project_root = Path(os.environ["PROJECT_ROOT"])
groups = [group for group in os.environ.get("BX_GROUPS", "main").split(",") if group]
pyproject = tomllib.loads(project_root.joinpath("pyproject.toml").read_text(encoding="utf-8"))

requirements: list[str] = []

project_table = pyproject.get("project") or {}
if "main" in groups and project_table.get("dependencies"):
    requirements.extend(project_table.get("dependencies", []))
    groups = [group for group in groups if group != "main"]

    optional_dependencies = project_table.get("optional-dependencies", {})
    for group in groups:
        requirements.extend(optional_dependencies.get(group, []))
else:
    poetry_table = pyproject.get("tool", {}).get("poetry", {})

    if "main" in groups:
        for dep_name, dep_spec in poetry_table.get("dependencies", {}).items():
            line = build_requirement(dep_name, dep_spec)
            if line:
                requirements.append(line)

    group_table = poetry_table.get("group", {})
    for group in groups:
        for dep_name, dep_spec in group_table.get(group, {}).get("dependencies", {}).items():
            line = build_requirement(dep_name, dep_spec)
            if line:
                requirements.append(line)

seen: set[str] = set()
for requirement in requirements:
    if requirement not in seen:
        print(requirement)
        seen.add(requirement)
PYEOF
}

pip_fallback_write_requirements_file() {
	local str_groups_csv="$1"
	local str_req_file="$2"

	pip_fallback_ensure_toml_reader
	pip_fallback_emit_pip_requirements_from_pyproject "$str_groups_csv" >"$str_req_file"
}

pip_fallback_install_requirements_file_into_venv() {
	local str_venv_python="$1"
	local str_req_file="$2"

	if [[ ! -s "$str_req_file" ]]; then
		print_status "warning" "No dependencies were generated from pyproject.toml for pip fallback"
		return 0
	fi

	"$str_venv_python" -m pip install "${PIP_FALLBACK_ARGS[@]}" -r "$str_req_file"
}

pip_fallback_install_groups_in_venv() {
	local str_venv_python="$1"
	local str_groups_csv="$2"
	local str_label="${3:-dependencies}"
	local str_req_file

	pip_fallback_populate_pip_args
	str_req_file="$(mktemp "${TMPDIR:-/tmp}/bx_pip_fallback.XXXXXX.txt")"

	print_status "info" "Installing $str_label with pip fallback..."
	pip_fallback_write_requirements_file "$str_groups_csv" "$str_req_file"

	"$str_venv_python" -m pip install "${PIP_FALLBACK_ARGS[@]}" --upgrade pip setuptools wheel
	pip_fallback_install_requirements_file_into_venv "$str_venv_python" "$str_req_file"

	rm -f "$str_req_file"
	print_status "success" "$str_label installed with pip fallback"
}
