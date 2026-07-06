#!/bin/bash
# Clean and reinstall Playwright Chromium browsers.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/lib/common.sh"
# shellcheck source=bin/lib/bootstrap.sh
source "$SCRIPT_DIR/lib/bootstrap.sh" # detect_os (sourced does no work)

fix_playwright_installation() {
	print_status "section" "Playwright Reinstallation"

	print_status "info" "Cleaning Playwright browser cache..."
	rm -rf ~/.cache/ms-playwright/chromium* || true

	print_status "info" "Reinstalling Playwright Python package..."
	run_poetry run pip uninstall -y playwright || {
		print_status "warning" "Playwright package not found — proceeding with fresh installation"
	}
	run_poetry run pip install playwright || {
		print_status "error" "Failed to install Playwright Python package"
		return 1
	}

	# `--with-deps` installs Linux OS packages via apt and is only valid on Debian/Ubuntu;
	# on Windows/macOS it has nothing to spawn (the `spawn UNKNOWN` failure), so add it on
	# Linux only.
	local -a args_install=(chromium)
	[[ "${OS_TYPE:-$(detect_os)}" == "linux" ]] && args_install+=(--with-deps)

	print_status "info" "Installing Playwright browsers..."
	run_poetry run playwright install "${args_install[@]}" || {
		print_status "error" "Failed to install Playwright Chromium browser"
		return 1
	}

	print_status "info" "Verifying Playwright installation..."
	if run_poetry run python -c "
from playwright.sync_api import sync_playwright
try:
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        browser.close()
    print('Playwright working correctly')
except Exception as e:
    print(f'Error: {e}')
    exit(1)
"; then
		print_status "success" "Playwright installation verified"
		return 0
	else
		print_status "error" "Playwright installation verification failed"
		return 1
	fi
}

main() {
	# Resolve Poetry the robust way (bare `poetry` may be absent; see
	# bin/poetry_exec.sh) before any `run_poetry` call.
	bootstrap_init
	ensure_poetry
	fix_playwright_installation || exit 1
}

main "$@"
