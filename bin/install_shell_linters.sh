#!/usr/bin/env bash
#
# install_shell_linters.sh — OPTIONAL system-binary install of shellcheck + shfmt.
#
# The PRIMARY route is pip: shellcheck-py / shfmt-py are dev-deps, vendored into the
# venv and used by bin/lint_shell.sh via `poetry run` (works on every OS, incl. a
# Windows UNC/mapped A: drive). This helper is a CONVENIENCE for machines that prefer
# — or need — a SYSTEM binary on PATH, e.g. where the venv lives on a network share
# that blocks executing the vendored binary. bin/lint_shell.sh falls back to exactly
# such a system binary.
#
# It detects the OS and uses the available package manager. Each branch is GUARDED with
# `command -v` and SKIPS gracefully with guidance when no supported manager is found —
# it never hard-fails (a box without a usable manager just keeps using the pip route).
#
# Managers, by OS (first one found wins):
#   windows : chocolatey (choco) -> scoop
#   macos   : homebrew (brew)
#   linux   : apt-get -> dnf -> pacman -> zypper  (shellcheck; shfmt via pip/go — see below)
#
# Flags / env:
#   --dry-run | DRY_RUN=1   print the install commands instead of running them (preview).

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/lib/common.sh"
# shellcheck source=bin/lib/bootstrap.sh
source "$SCRIPT_DIR/lib/bootstrap.sh" # detect_os

bool_dry_run=false
if [[ "${1:-}" == "--dry-run" || "${DRY_RUN:-0}" == "1" ]]; then
	bool_dry_run=true
fi

# Run a (state-mutating) install command, or echo it under --dry-run. Keeps the actual
# package-manager invocations in one guarded place so a preview never installs anything.
run_cmd() {
	if [[ "$bool_dry_run" == true ]]; then
		print_status info "[dry-run] $*"
		return 0
	fi
	"$@"
}

install_windows() {
	# Chocolatey and Scoop both package shellcheck AND shfmt.
	if command -v choco >/dev/null 2>&1; then
		print_status info "chocolatey: installing shellcheck + shfmt..."
		run_cmd choco install shellcheck shfmt -y
		print_status success "shellcheck + shfmt via chocolatey"
		return 0
	fi
	if command -v scoop >/dev/null 2>&1; then
		print_status info "scoop: installing shellcheck + shfmt..."
		run_cmd scoop install shellcheck shfmt
		print_status success "shellcheck + shfmt via scoop"
		return 0
	fi
	print_status warning "Windows without choco/scoop — use the pip route (already covered): poetry install --with dev"
	print_status info "To install chocolatey: https://chocolatey.org"
	return 0
}

install_macos() {
	if command -v brew >/dev/null 2>&1; then
		print_status info "homebrew: installing shellcheck + shfmt..."
		run_cmd brew install shellcheck shfmt
		print_status success "shellcheck + shfmt via homebrew"
		return 0
	fi
	print_status warning "macOS without homebrew — use the pip route (already covered) or install brew: https://brew.sh"
	return 0
}

install_linux() {
	# Most distro repos package shellcheck; shfmt is a Go binary rarely packaged, so it
	# stays on the pip dev-dep (shfmt-py) — or `go install mvdan.cc/sh/v3/cmd/shfmt`.
	local bool_done=false
	if command -v apt-get >/dev/null 2>&1; then
		print_status info "apt-get: installing shellcheck..."
		run_cmd sudo apt-get update
		run_cmd sudo apt-get install -y shellcheck
		bool_done=true
	elif command -v dnf >/dev/null 2>&1; then
		print_status info "dnf: installing ShellCheck..."
		run_cmd sudo dnf install -y ShellCheck
		bool_done=true
	elif command -v pacman >/dev/null 2>&1; then
		print_status info "pacman: installing shellcheck..."
		run_cmd sudo pacman -S --noconfirm shellcheck
		bool_done=true
	elif command -v zypper >/dev/null 2>&1; then
		print_status info "zypper: installing ShellCheck..."
		run_cmd sudo zypper install -y ShellCheck
		bool_done=true
	fi

	if [[ "$bool_done" == true ]]; then
		print_status success "shellcheck via the distro package manager"
	else
		print_status warning "No apt/dnf/pacman/zypper — use the pip route (already covered): poetry install --with dev"
	fi
	print_status info "shfmt on Linux: comes from the shfmt-py dev-dep (pip), or 'go install mvdan.cc/sh/v3/cmd/shfmt@latest'"
	return 0
}

main() {
	local str_os
	str_os="$(detect_os)"
	print_status config "Detected OS: $str_os"
	print_status info "The primary route is pip (shellcheck-py/shfmt-py via poetry); this installer is optional."

	case "$str_os" in
	windows) install_windows ;;
	macos) install_macos ;;
	linux) install_linux ;;
	*)
		print_status warning "OS '$str_os' not recognised — use the pip route: poetry install --with dev"
		;;
	esac
}

main "$@"
