#!/usr/bin/env bash
# Enable this repo's free GitHub security features — once, scripted.
#
# WHY THIS EXISTS: a published PyPI library should have its supply-chain + vuln-reporting
# hygiene turned on, but the toggles under Settings -> Security live behind manual checkboxes
# that are silently forgotten on a fresh clone/fork. Every one below is settable through the
# REST API, so the whole set is declared here and applied with one command — the sibling of
# bin/enable_repo_rules.sh (which owns the branch ruleset; this owns the repo security settings).
#
# The three toggles (all PUT, all return 204):
#   - private-vulnerability-reporting  — let researchers report privately (see SECURITY.md),
#                                        instead of opening a public issue.
#   - vulnerability-alerts             — Dependabot alerts (notify on a vulnerable dependency).
#   - automated-security-fixes         — Dependabot security updates (auto-PRs for the above).
#                                        Requires vulnerability-alerts first, so it is PUT last.
#
# The weekly *version* bumps (distinct from the *security* fixes above) are declared statically
# in .github/dependabot.yml, which needs no API call — GitHub reads it from the default branch.
#
# THIS IS REPO-SETTINGS WORK: CI's GITHUB_TOKEN (a GitHub App installation token) cannot flip
# these; a maintainer running `make init` / `tasks.sh init` has repo-admin via `gh auth`, so it
# belongs here, not in CI.
#
# Idempotent + non-blocking: each PUT is safe to re-run; missing gh / no auth / no repo-admin all
# WARN and return 0 so `init` still completes.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/lib/common.sh"

require_gh() {
	# gh must be installed and authenticated. Missing either is a skip, not a failure.
	if ! command -v gh >/dev/null 2>&1; then
		print_status "warning" "gh CLI not found — skipping security setup (Settings -> Security)"
		return 1
	fi
	if ! gh auth status >/dev/null 2>&1; then
		print_status "warning" "gh not authenticated — skipping security setup (run 'gh auth login', then 'make enable_security')"
		return 1
	fi
	return 0
}

resolve_repo() {
	# Print owner/repo for the current checkout, or empty when no GitHub remote resolves.
	gh repo view --json nameWithOwner --jq .nameWithOwner 2>/dev/null || true
}

enable_toggle() {
	# PUT one security toggle. A failure (usually: not a repo admin) WARNs and returns 0 so a
	# later toggle — and init — still run.
	local str_repo="$1"
	local str_endpoint="$2"
	local str_label="$3"
	if gh api -X PUT "repos/$str_repo/$str_endpoint" >/dev/null 2>&1; then
		print_status "success" "$str_label enabled"
		return 0
	fi
	print_status "warning" "Could not enable $str_label on $str_repo (needs repo-admin rights) — a maintainer must run 'make enable_security' or set it in Settings -> Security"
	return 0
}

enable_security() {
	local str_repo
	str_repo="$(resolve_repo)"
	if [ -z "$str_repo" ]; then
		print_status "warning" "No GitHub remote resolved — skipping security setup (push the repo to GitHub first)"
		return 0
	fi

	print_status "info" "Enabling GitHub security features on $str_repo..."
	print_status "config" "private vulnerability reporting, Dependabot alerts, Dependabot security updates"
	enable_toggle "$str_repo" "private-vulnerability-reporting" "Private vulnerability reporting"
	enable_toggle "$str_repo" "vulnerability-alerts" "Dependabot alerts"
	# Security updates depend on alerts being on, so this PUT runs last.
	enable_toggle "$str_repo" "automated-security-fixes" "Dependabot security updates"
}

main() {
	print_status "section" "GitHub Security Setup"
	# A skip (no gh / not authed) must not fail init — return 0 either way.
	if ! require_gh; then
		return 0
	fi
	enable_security
}

main "$@"
