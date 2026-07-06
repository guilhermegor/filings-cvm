#!/bin/bash
# Sourced lib — cross-platform environment resolution for venv.sh and run.sh.
# Provides OS/interpreter/Poetry resolution, a pyenv-preferred / system-Python
# fallback, and optional corporate-CA wiring. Definitions only — no work runs on
# source; the caller invokes `bootstrap_init` then the helpers it needs.
if [[ "${BASH_SOURCE[0]}" == "$0" ]]; then
	echo "bin/lib/bootstrap.sh is meant to be sourced, not executed." >&2
	exit 1
fi

# Idempotency guard — safe to source multiple times.
[ "${_BX_BOOTSTRAP_LOADED:-}" = "1" ] && return 0
_BX_BOOTSTRAP_LOADED=1

BOOTSTRAP_LIB_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# shellcheck source=bin/lib/common.sh
source "$BOOTSTRAP_LIB_DIR/common.sh"

# Poetry invocation as an array so a "python -m poetry" fallback stays quotable.
POETRY_CMD=()

# ── detect_os ─────────────────────────────────────────────────────────────────
detect_os() {
	case "$(uname -s)" in
	Linux*) echo "linux" ;;
	Darwin*) echo "macos" ;;
	CYGWIN* | MINGW* | MSYS*) echo "windows" ;;
	*) echo "unknown" ;;
	esac
}

# ── resolve_abs_path ──────────────────────────────────────────────────────────
# Resolve a path to an absolute POSIX path.
resolve_abs_path() {
	local str_path="$1"
	local str_dir
	local str_base

	str_dir="$(cd "$(dirname "$str_path")" && pwd)"
	str_base="$(basename "$str_path")"

	printf '%s/%s\n' "$str_dir" "$str_base"
}

# ── to_native_path ────────────────────────────────────────────────────────────
# Convert a POSIX path to the native OS path when needed. On Git Bash / MINGW
# this turns /a/foo/bar into A:/foo/bar (via cygpath); elsewhere it is a no-op.
# Shell-only — no Python subprocess — and strips stray CR/LF.
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

# ── resolve_python ────────────────────────────────────────────────────────────
# Echo the first working interpreter (python3 → python → py). Fail if none.
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

# ── resolve_poetry ────────────────────────────────────────────────────────────
# Populate POETRY_CMD. Return 1 when Poetry is unavailable.
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

# ── run_poetry ────────────────────────────────────────────────────────────────
run_poetry() {
	"${POETRY_CMD[@]}" "$@"
}

# ── ensure_poetry ─────────────────────────────────────────────────────────────
# Resolve Poetry, installing the pinned version via pip when absent.
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

# ── bootstrap_init ────────────────────────────────────────────────────────────
# Resolve and export OS_TYPE, PYTHON, PROJECT_ROOT, BIN_DIR, CORPORATE_CA_PEM,
# PY_VERSION. Call this once before the other helpers.
bootstrap_init() {
	BIN_DIR="$(cd "$BOOTSTRAP_LIB_DIR/.." && pwd)"
	PROJECT_ROOT="$(cd "$BOOTSTRAP_LIB_DIR/../.." && pwd)"
	CORPORATE_CA_PEM="$BIN_DIR/corporate_ca.pem"
	export BIN_DIR PROJECT_ROOT CORPORATE_CA_PEM

	OS_TYPE="$(detect_os)"
	export OS_TYPE
	print_status "info" "Detected OS: $OS_TYPE"

	PYTHON="$(resolve_python)"
	export PYTHON
	print_status "info" "Python binary: $PYTHON ($("$PYTHON" --version 2>&1))"

	PY_VERSION="$(cat "$PROJECT_ROOT/.python-version" 2>/dev/null || echo "3.12.2")"
	export PY_VERSION
}

# ── ensure_python_version ─────────────────────────────────────────────────────
# Prefer pyenv (pin the project version); fall back to the system interpreter
# with a version-mismatch warning when pyenv is unavailable (e.g. locked-down
# corporate hosts that forbid installing it).
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

# ── append_ca_to_certifi ──────────────────────────────────────────────────────
# Append the corporate CA to the certifi bundle so httpx/requests trust it too.
# Idempotent — keyed on the cert's base64 body, not its shared BEGIN header.
append_ca_to_certifi() {
	local str_cert="$1"

	if ! "$PYTHON" -c "import certifi" >/dev/null 2>&1; then
		print_status "config" "Installing certifi..."
		if ! "$PYTHON" -m pip install --quiet certifi; then
			print_status "warning" "Could not install certifi — skipping bundle merge"
			return 0
		fi
	fi

	local str_bundle str_marker
	str_bundle="$("$PYTHON" -c 'import certifi; print(certifi.where())')"
	str_bundle="${str_bundle//$'\r'/}"
	str_bundle="${str_bundle//$'\n'/}"
	str_marker="$(sed -n '2p' "$str_cert")"

	if [[ -z "$str_marker" || ! -f "$str_bundle" ]]; then
		return 0
	fi
	if grep -qF "$str_marker" "$str_bundle" 2>/dev/null; then
		print_status "info" "Corporate CA already in certifi bundle"
		return 0
	fi
	cat "$str_cert" >>"$str_bundle"
	print_status "config" "Corporate CA appended to certifi bundle"
}

# ── wire_corporate_ca ─────────────────────────────────────────────────────────
# Wire the corporate CA into the SSL toolchain — but only if bin/corporate_ca.pem
# exists. Absent the pem this is a no-op, so non-corporate setups keep full TLS
# verification. Run `make corporate_ca` to generate the pem.
wire_corporate_ca() {
	if [[ ! -f "$CORPORATE_CA_PEM" ]]; then
		print_status "debug" "No corporate CA at $CORPORATE_CA_PEM — using standard SSL"
		return 0
	fi

	print_status "config" "Corporate CA found: $CORPORATE_CA_PEM"

	# Resolve the absolute (Windows-safe) path in the shell via to_native_path —
	# one less Python subprocess, and cygpath handles Git Bash drive mapping.
	local str_cert_abs
	str_cert_abs="$(to_native_path "$CORPORATE_CA_PEM")"

	export REQUESTS_CA_BUNDLE="$str_cert_abs"
	export SSL_CERT_FILE="$str_cert_abs"
	export CURL_CA_BUNDLE="$str_cert_abs"
	export PIP_CERT="$str_cert_abs"
	export PIP_TRUSTED_HOST="pypi.org files.pythonhosted.org pypi.python.org"
	print_status "config" "SSL bundle: $str_cert_abs"

	append_ca_to_certifi "$str_cert_abs"

	# Point Poetry's resolver at the cert too (best-effort).
	if resolve_poetry; then
		run_poetry config certificates.pypi.cert "$str_cert_abs" 2>/dev/null || true
	fi
}
