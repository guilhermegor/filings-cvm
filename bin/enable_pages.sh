#!/usr/bin/env bash
# Point GitHub Pages at the `gh-pages` branch for this repo — once.
#
# WHY THIS EXISTS: the docs are versioned with mike (https://github.com/jimporter/mike),
# which publishes each release to the `gh-pages` branch. GitHub Pages must therefore serve
# from "Deploy from a branch -> gh-pages", NOT from the "GitHub Actions" artifact source.
# Switching the source is a repo-settings change, and the docs deploy runs in CI where the
# workflow's GITHUB_TOKEN (a GitHub App installation token) CANNOT change Pages settings or
# create a Pages site. A maintainer running `make init` / `tasks.sh init` has repo-admin via
# `gh auth`, so this one-time call belongs here, not in CI.
#
# NO 404 WINDOW: we switch the source ONLY once the `gh-pages` branch actually exists (the
# first `mike deploy` in the release workflow creates it). Until then Pages is left exactly as
# it is, so the live site is never pointed at an empty branch. Re-run `make enable_pages` after
# the first release if it was skipped for that reason.
#
# Idempotent + non-blocking: an already-correct source no-ops; missing gh / no auth / no
# repo-admin / no gh-pages yet all WARN and return 0 so `init` still completes.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/lib/common.sh"

require_gh() {
	# gh must be installed and authenticated. Missing either is a skip, not a failure.
	if ! command -v gh >/dev/null 2>&1; then
		print_status "warning" "gh CLI not found — skipping Pages setup (Settings -> Pages -> Deploy from a branch -> gh-pages)"
		return 1
	fi
	if ! gh auth status >/dev/null 2>&1; then
		print_status "warning" "gh not authenticated — skipping Pages setup (run 'gh auth login', then 'make enable_pages')"
		return 1
	fi
	return 0
}

resolve_repo() {
	# Print owner/repo for the current checkout, or empty when no GitHub remote resolves.
	gh repo view --json nameWithOwner --jq .nameWithOwner 2>/dev/null || true
}

point_pages_at_gh_pages() {
	# Create the Pages site pointing at gh-pages if it does not exist yet; otherwise update the
	# existing site's source to the branch. The nested `source` object needs a JSON body, so it
	# is piped via --input (gh does not nest bracketed form keys).
	local str_repo="$1"
	local str_body='{"source": {"branch": "gh-pages", "path": "/"}, "build_type": "legacy"}'

	if gh api "repos/$str_repo/pages" >/dev/null 2>&1; then
		if printf '%s' "$str_body" | gh api -X PUT "repos/$str_repo/pages" --input - >/dev/null 2>&1; then
			print_status "success" "GitHub Pages now serves from the gh-pages branch"
			return 0
		fi
	elif printf '%s' "$str_body" | gh api -X POST "repos/$str_repo/pages" --input - >/dev/null 2>&1; then
		print_status "success" "GitHub Pages created, serving from the gh-pages branch"
		return 0
	fi

	print_status "warning" "Could not set the gh-pages source for $str_repo (needs repo-admin rights) — a maintainer must run 'make enable_pages' or set it in Settings -> Pages"
	return 0
}

enable_pages() {
	local str_repo
	str_repo="$(resolve_repo)"
	if [ -z "$str_repo" ]; then
		print_status "warning" "No GitHub remote resolved — skipping Pages setup (push the repo to GitHub first)"
		return 0
	fi

	# Guard: never point Pages at gh-pages before that branch has content — that would 404 the
	# live site. The first `mike deploy` (release workflow) creates it; re-run this afterwards.
	if ! git ls-remote --exit-code --heads origin gh-pages >/dev/null 2>&1; then
		print_status "info" "gh-pages branch not created yet — leaving Pages as-is (the first release's mike deploy creates it; re-run 'make enable_pages' after that)"
		return 0
	fi

	print_status "info" "Pointing GitHub Pages at the gh-pages branch for $str_repo..."
	point_pages_at_gh_pages "$str_repo"
}

main() {
	print_status "section" "GitHub Pages Setup (mike / gh-pages branch)"
	# A skip (no gh / not authed) must not fail init — return 0 either way.
	if ! require_gh; then
		return 0
	fi
	enable_pages
}

main "$@"
