#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/lib/common.sh"
# shellcheck source=bin/lib/bootstrap.sh
source "$SCRIPT_DIR/lib/bootstrap.sh"

bool_dry_run=false
if [[ "${1:-}" == "--dry-run" || "${DRY_RUN:-0}" == "1" ]]; then
	bool_dry_run=true
fi

run_cmd() {
	if [[ "$bool_dry_run" == true ]]; then
		print_status info "[dry-run] $*"
		return 0
	fi
	"$@"
}

install_windows() {
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
