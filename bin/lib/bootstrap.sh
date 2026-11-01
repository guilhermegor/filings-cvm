#!/bin/bash
if [[ "${BASH_SOURCE[0]}" == "$0" ]]; then
	echo "bin/lib/bootstrap.sh is meant to be sourced, not executed." >&2
	exit 1
fi

[ "${_BX_BOOTSTRAP_LOADED:-}" = "1" ] && return 0
_BX_BOOTSTRAP_LOADED=1

BOOTSTRAP_LIB_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# shellcheck source=bin/lib/common.sh
source "$BOOTSTRAP_LIB_DIR/common.sh"

POETRY_CMD=()

detect_os() {
	case "$(uname -s)" in
	Linux*) echo "linux" ;;
	Darwin*) echo "macos" ;;
	CYGWIN* | MINGW* | MSYS*) echo "windows" ;;
	*) echo "unknown" ;;
	esac
}

resolve_abs_path() {
	local str_path="$1"
	local str_dir
	local str_base

	str_dir="$(cd "$(dirname "$str_path")" && pwd)"
	str_base="$(basename "$str_path")"

	printf '%s/%s\n' "$str_dir" "$str_base"
}

to_native_path() {
	local str_path="$1"
	local str_abs
	local str_native

	str_abs="$(resolve_abs_path "$str_path")"

	if [[ "${OS_TYPE:-$(detect_os)}" == "windows" ]] && command -v cygpath >/dev/null 2>&1; then
		str_native="$(cygpath -am "$str_abs")"
	else
		str_native="$str_abs"
	fi

	str_native="${str_native//$'\r'/}"
	str_native="${str_native//$'\n'/}"

	printf '%s\n' "$str_native"
}

resolve_python() {
	local str_candidate
	for str_candidate in python3 python py; do
		if command -v "$str_candidate" >/dev/null 2>&1 &&
			"$str_candidate" --version >/dev/null 2>&1; then
			echo "$str_candidate"
			return 0
		fi
	done
	print_status "error" "No Python interpreter found (tried: python3, python, py)"
	return 1
}

python_in_venv() {
	"$1" -c 'import sys; sys.exit(sys.prefix == sys.base_prefix)' >/dev/null 2>&1
}

running_inside_project_venv() {
	local str_venv="$PROJECT_ROOT/.venv"

	if [[ -n "${VIRTUAL_ENV:-}" && "$VIRTUAL_ENV" -ef "$str_venv" ]]; then
		return 0
	fi
	[[ ":$PATH:" == *":$str_venv/bin:"* || ":$PATH:" == *":$str_venv/Scripts:"* ]]
}

path_without_active_venvs() {
	local str_dir
	local str_clean=""
	local -a arr_dirs

	IFS=: read -ra arr_dirs <<<"$PATH"
	for str_dir in "${arr_dirs[@]}"; do
		case "$str_dir" in
		"$PROJECT_ROOT/.venv"/* | "${VIRTUAL_ENV:-/nonexistent}"/*) continue ;;
		esac
		str_clean+="${str_clean:+:}$str_dir"
	done

	printf '%s\n' "$str_clean"
}

resolve_base_python() {
	local str_candidate
	local str_found
	local str_path_clean

	str_path_clean="$(path_without_active_venvs)"
	for str_candidate in python3 python py; do
		str_found="$(PATH="$str_path_clean" command -v "$str_candidate" 2>/dev/null)" || continue
		if "$str_found" --version >/dev/null 2>&1 && ! python_in_venv "$str_found"; then
			printf '%s\n' "$str_found"
			return 0
		fi
	done
	return 1
}

resolve_poetry() {
	if command -v poetry >/dev/null 2>&1; then
		POETRY_CMD=(poetry)
		return 0
	fi
	if [[ -n "${PYTHON:-}" ]] && "$PYTHON" -m poetry --version >/dev/null 2>&1; then
		POETRY_CMD=("$PYTHON" -m poetry)
		return 0
	fi
	return 1
}

run_poetry() {
	"${POETRY_CMD[@]}" "$@"
}

ensure_poetry() {
	if resolve_poetry; then
		print_status "info" "Poetry found: $(run_poetry --version 2>&1 | head -n1)"
		return 0
	fi

	print_status "warning" "Poetry not found — installing via $PYTHON -m pip ..."
	if [[ -f "$PROJECT_ROOT/requirements.txt" ]]; then
		"$PYTHON" -m pip install -r "$PROJECT_ROOT/requirements.txt"
	else
		"$PYTHON" -m pip install "poetry>=2.4"
	fi

	if resolve_poetry; then
		print_status "success" "Poetry installed: $(run_poetry --version 2>&1 | head -n1)"
		return 0
	fi
	print_status "error" "Poetry install failed — install manually: https://python-poetry.org/docs/"
	return 1
}

bootstrap_init() {
	BIN_DIR="$(cd "$BOOTSTRAP_LIB_DIR/.." && pwd)"
	PROJECT_ROOT="$(cd "$BOOTSTRAP_LIB_DIR/../.." && pwd)"
	CORPORATE_CA_PEM="$BIN_DIR/corporate_ca.pem"
	export BIN_DIR PROJECT_ROOT CORPORATE_CA_PEM

	OS_TYPE="$(detect_os)"
	export OS_TYPE
	print_status "info" "Detected OS: $OS_TYPE"

	PYTHON="$(resolve_python)"
	if python_in_venv "$PYTHON"; then
		PYTHON="$(resolve_base_python)" || PYTHON="$(resolve_python)"
	fi
	export PYTHON
	print_status "info" "Python binary: $PYTHON ($("$PYTHON" --version 2>&1))"

	PY_VERSION="$(cat "$PROJECT_ROOT/.python-version" 2>/dev/null || echo "3.12.2")"
	export PY_VERSION
}

ensure_python_version() {
	if command -v pyenv >/dev/null 2>&1; then
		print_status "info" "pyenv found — pinning Python $PY_VERSION"
		pyenv install "$PY_VERSION" -s
		pyenv local "$PY_VERSION"
		print_status "success" "Python $PY_VERSION active via pyenv"
		return 0
	fi

	local str_current
	str_current="$("$PYTHON" --version 2>&1 | grep -oE '[0-9]+\.[0-9]+\.[0-9]+' || true)"
	print_status "warning" "pyenv not found — using system Python ${str_current:-unknown}"
	if [[ -n "$str_current" && "$str_current" != "$PY_VERSION" ]]; then
		print_status "warning" "Expected $PY_VERSION but found $str_current — proceeding anyway"
	fi
}

build_union_ca_bundle() {
	local str_cert="$1"

	CA_BUNDLE_PEM="$BIN_DIR/ca_bundle.pem"
	export CA_BUNDLE_PEM

	BX_CA_CORPORATE="$str_cert" BX_CA_OUT="$CA_BUNDLE_PEM" \
		"$PYTHON" "$(dirname "${BASH_SOURCE[0]}")/ca_bundle.py"
}

wire_corporate_ca() {
	if [[ ! -f "$CORPORATE_CA_PEM" ]]; then
		print_status "debug" "No corporate CA at $CORPORATE_CA_PEM — using standard SSL"
		return 0
	fi

	print_status "config" "Corporate CA found: $CORPORATE_CA_PEM"

	local str_cert_abs str_bundle_abs str_count

	str_cert_abs="$(to_native_path "$CORPORATE_CA_PEM")"

	if ! str_count="$(build_union_ca_bundle "$str_cert_abs")"; then
		print_status "error" "Could not build the union CA bundle — leaving TLS settings untouched"
		print_status "error" "Pointing them at the corporate CA alone would NARROW the trust store and break every other TLS connection."
		return 1
	fi

	str_bundle_abs="$(to_native_path "$CA_BUNDLE_PEM")"

	export REQUESTS_CA_BUNDLE="$str_bundle_abs"
	export SSL_CERT_FILE="$str_bundle_abs"
	export CURL_CA_BUNDLE="$str_bundle_abs"
	export PIP_CERT="$str_bundle_abs"
	print_status "config" "SSL bundle (union, ${str_count} certs): $str_bundle_abs"

	if resolve_poetry; then
		run_poetry config certificates.pypi.cert "$str_bundle_abs" 2>/dev/null || true
	fi
}
