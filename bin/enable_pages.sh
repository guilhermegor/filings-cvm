#!/usr/bin/env bash
# Enable GitHub Pages (source = GitHub Actions) for this repo — once.
#
# WHY THIS EXISTS: the docs deploy workflow (.github/workflows/docs.yaml) uses
# actions/configure-pages with `enablement: true`, which is *documented* to
# self-enable Pages on the first run. In practice the workflow's GITHUB_TOKEN is a
# GitHub App installation token that CANNOT create a Pages site from scratch — the
# first run fails with "Resource not accessible by integration / Create Pages site
# failed". Creating the site needs a token with repo-admin rights, which a maintainer
# running `make init` / `tasks.sh init` has (via `gh auth`) but the workflow does not.
# This script makes that one-time API call so the very next workflow run can deploy.
#
# Idempotent + non-blocking: if Pages is already enabled it no-ops; if gh is absent,
# unauthenticated, or the caller lacks repo-admin (a fork/contributor), it WARNS and
# returns 0 so `init` still completes. Only the repo owner's first run creates the site.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/lib/common.sh"

require_gh() {
	# gh must be installed and authenticated. Missing either is a skip, not a failure.
	if ! command -v gh >/dev/null 2>&1; then
		print_status "warning" "gh CLI not found — skipping Pages enablement (enable once in Settings → Pages → Source: GitHub Actions)"
		return 1
	fi
	if ! gh auth status >/dev/null 2>&1; then
		print_status "warning" "gh not authenticated — skipping Pages enablement (run 'gh auth login', then 'make enable_pages')"
		return 1
	fi
	return 0
}

resolve_repo() {
	# Print owner/repo for the current checkout, or empty when no GitHub remote resolves.
	gh repo view --json nameWithOwner --jq .nameWithOwner 2>/dev/null || true
}

enable_pages() {
	local str_repo
	str_repo="$(resolve_repo)"
	if [ -z "$str_repo" ]; then
		print_status "warning" "No GitHub remote resolved — skipping Pages enablement (push the repo to GitHub first)"
		return 0
	fi

	# Already enabled → nothing to do (idempotent; every run after the first lands here).
	if gh api "repos/$str_repo/pages" >/dev/null 2>&1; then
		print_status "info" "GitHub Pages already enabled for $str_repo — leaving it untouched"
		return 0
	fi

	print_status "info" "Enabling GitHub Pages (source = GitHub Actions) for $str_repo..."
	if gh api -X POST "repos/$str_repo/pages" -f build_type=workflow >/dev/null 2>&1; then
		print_status "success" "GitHub Pages enabled — the docs deploy workflow can now publish"
		return 0
	fi

	# Most common cause: the caller is not a repo admin (a fork/contributor). Non-fatal.
	print_status "warning" "Could not enable Pages for $str_repo (needs repo-admin rights) — a maintainer must run 'make enable_pages' or enable it in Settings → Pages"
	return 0
}

main() {
	print_status "section" "GitHub Pages Enablement"
	# A skip (no gh / not authed) must not fail init — return 0 either way.
	if ! require_gh; then
		return 0
	fi
	enable_pages
}

main "$@"
