#!/usr/bin/env bash
# Provision the `pr-quality-gate` branch ruleset AND the repo merge policy for this repo — once.
#
# Two things: (1) the branch ruleset (PR required, CI green, CodeQL clean, Copilot review), and
# (2) the merge policy the gate's NATIVE auto-merge depends on — `allow_auto_merge` +
# `delete_branch_on_merge` on the repo, plus the `do-not-merge` opt-out label. `allow_auto_merge` is
# the one the gate CANNOT set itself: without it, GitHub's `enablePullRequestAutoMerge` mutation
# silently no-ops, which left auto-merge inert repo-wide until this script set it.
#
# WHY THIS EXISTS: the default branch needs guardrails (every change via a PR, CI green,
# CodeQL clean, Copilot review requested). Clicking ~10 checkboxes in Settings -> Rules is
# not reproducible and is silently forgotten on a fresh clone/fork, so the whole ruleset is
# declared here and applied with one command. This is repo-settings work: CI's GITHUB_TOKEN
# (a GitHub App installation token) CANNOT write rulesets, but a maintainer running
# `make init` / `tasks.sh init` has repo-admin via `gh auth` — so it belongs here, not in CI.
#
# EVERY rule below is settable through the REST API (verified against this repo), INCLUDING
# the Copilot auto-review, which is its OWN rule type (`copilot_code_review`) — it is NOT a
# parameter of `pull_request` (that spelling returns HTTP 422). Nothing here needs a click.
#
# THE ONE THING THIS CANNOT DO — and it is an ACCOUNT PLAN, not a REPO setting: the
# `copilot_code_review` rule only fires "if the author has access to Copilot code review", and code
# review is NOT included in Copilot Free (GitHub's own plan page lists "AI reviews" as an upgrade
# feature). Without a plan that includes it (Pro / Pro+ / Business), the rule stays correctly
# configured but INERT: no review appears and NOTHING ERRORS — the silence is the trap. Copilot Pro
# is free for verified students / teachers / popular-OSS maintainers; otherwise use a free-tier LLM
# in a `pull_request` workflow instead. Every OTHER rule here (PR required, CI green, CodeQL clean)
# works regardless of any Copilot plan.
#
# DELIBERATELY NOT ENABLED (both would be a second source of truth for gates we already own):
#   - "Require code quality results" — subjective AI severity levels on the merge path; ruff,
#     mypy and the bin/check_*.py gates already enforce quality deterministically.
#   - "Restrict code coverage" (preview) — the floor is single-sourced in `.coveragerc`
#     (`fail_under`) and enforced by pre-commit + CI; a second threshold would drift.
#
# Idempotent + non-blocking: an existing `pr-quality-gate` is UPDATED in place (PUT), a missing
# one is CREATED (POST); missing gh / no auth / no repo-admin all WARN and return 0 so `init`
# still completes.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/lib/common.sh"

readonly STR_RULESET_NAME="pr-quality-gate"

require_gh() {
	# gh must be installed and authenticated. Missing either is a skip, not a failure.
	if ! command -v gh >/dev/null 2>&1; then
		print_status "warning" "gh CLI not found — skipping ruleset setup (Settings -> Rules -> Rulesets)"
		return 1
	fi
	if ! gh auth status >/dev/null 2>&1; then
		print_status "warning" "gh not authenticated — skipping ruleset setup (run 'gh auth login', then 'make enable_repo_rules')"
		return 1
	fi
	return 0
}

resolve_repo() {
	# Print owner/repo for the current checkout, or empty when no GitHub remote resolves.
	gh repo view --json nameWithOwner --jq .nameWithOwner 2>/dev/null || true
}

ruleset_id() {
	# Print the id of an existing ruleset named $STR_RULESET_NAME, or empty when absent.
	local str_repo="$1"
	gh api "repos/$str_repo/rulesets" \
		--jq ".[] | select(.name == \"$STR_RULESET_NAME\") | .id" 2>/dev/null || true
}

ruleset_body() {
	# Emit the full ruleset declaration as JSON on stdout.
	#
	# `~DEFAULT_BRANCH` tracks whatever the default branch is called, so the ruleset survives a
	# rename and is portable to a scaffolded project that uses a different name.
	#
	# required_approving_review_count is 0 ON PURPOSE: GitHub does not let an author approve
	# their own PR, so any value >= 1 would lock a SOLO maintainer out of merging their own
	# work. The rule still forces every change through a PR — which is the actual guardrail.
	# required_review_thread_resolution makes the Copilot review comments binding: they must be
	# resolved (or explicitly dismissed) before the merge button unlocks.
	cat <<-JSON
		{
		  "name": "$STR_RULESET_NAME",
		  "target": "branch",
		  "enforcement": "active",
		  "conditions": { "ref_name": { "include": ["~DEFAULT_BRANCH"], "exclude": [] } },
		  "rules": [
		    { "type": "deletion" },
		    { "type": "non_fast_forward" },
		    { "type": "pull_request",
		      "parameters": {
		        "required_approving_review_count": 0,
		        "dismiss_stale_reviews_on_push": false,
		        "require_code_owner_review": false,
		        "require_last_push_approval": false,
		        "required_review_thread_resolution": true,
		        "allowed_merge_methods": ["merge", "squash", "rebase"]
		      }
		    },
		    { "type": "required_status_checks",
		      "parameters": {
		        "strict_required_status_checks_policy": false,
		        "required_status_checks": [
		          { "context": "Run Automated Tests (ubuntu-latest)" },
		          { "context": "Run Automated Tests (macos-latest)" },
		          { "context": "Run Automated Tests (windows-latest)" },
		          { "context": "build" }
		        ]
		      }
		    },
		    { "type": "code_scanning",
		      "parameters": {
		        "code_scanning_tools": [
		          { "tool": "CodeQL",
		            "security_alerts_threshold": "high_or_higher",
		            "alerts_threshold": "errors" }
		        ]
		      }
		    },
		    { "type": "copilot_code_review",
		      "parameters": { "review_on_push": true, "review_draft_pull_requests": false }
		    }
		  ]
		}
	JSON
}

apply_ruleset() {
	# Create the ruleset, or update it in place when one of the same name already exists.
	local str_repo="$1"
	local str_id
	str_id="$(ruleset_id "$str_repo")"

	if [ -n "$str_id" ]; then
		if ruleset_body | gh api -X PUT "repos/$str_repo/rulesets/$str_id" --input - >/dev/null 2>&1; then
			print_status "success" "Ruleset '$STR_RULESET_NAME' updated (active on the default branch)"
			return 0
		fi
	elif ruleset_body | gh api -X POST "repos/$str_repo/rulesets" --input - >/dev/null 2>&1; then
		print_status "success" "Ruleset '$STR_RULESET_NAME' created (active on the default branch)"
		return 0
	fi

	print_status "warning" "Could not apply the '$STR_RULESET_NAME' ruleset to $str_repo (needs repo-admin rights) — a maintainer must run 'make enable_repo_rules' or set it in Settings -> Rules -> Rulesets"
	return 0
}

enable_merge_policy() {
	# Provision the repo-level settings the gate's native auto-merge depends on, plus the opt-out
	# label. `allow_auto_merge` is the prerequisite the gate cannot set itself (without it the
	# enablePullRequestAutoMerge mutation silently no-ops); `delete_branch_on_merge` removes the head
	# branch after the squash; the `do-not-merge` label must exist for a maintainer to apply the
	# opt-out. All idempotent + non-blocking.
	local str_repo="$1"

	if gh api -X PATCH "repos/$str_repo" -F allow_auto_merge=true -F delete_branch_on_merge=true >/dev/null 2>&1; then
		print_status "success" "Merge policy: auto-merge + delete-branch-on-merge enabled"
	else
		print_status "warning" "Could not set merge policy on $str_repo (needs repo-admin) — enable 'Allow auto-merge' and 'Automatically delete head branches' in Settings -> General"
	fi

	# POST is create-only; a 422 (label already exists) is the idempotent no-op, not a failure.
	if gh api -X POST "repos/$str_repo/labels" -f name="do-not-merge" -f color="b60205" \
		-f description="Hold auto-merge for this PR (opt-out escape hatch)" >/dev/null 2>&1; then
		print_status "success" "Label 'do-not-merge' created"
	else
		print_status "info" "Label 'do-not-merge' already present"
	fi
}

enable_repo_rules() {
	local str_repo
	str_repo="$(resolve_repo)"
	if [ -z "$str_repo" ]; then
		print_status "warning" "No GitHub remote resolved — skipping ruleset setup (push the repo to GitHub first)"
		return 0
	fi

	print_status "info" "Applying the '$STR_RULESET_NAME' ruleset to $str_repo..."
	print_status "config" "PR required (0 approvals — a solo maintainer cannot approve their own PR), conversations resolved, CI green, CodeQL clean, Copilot review on every push"
	apply_ruleset "$str_repo"

	print_status "info" "Provisioning the repo merge policy (auto-merge, delete-branch, do-not-merge label)..."
	enable_merge_policy "$str_repo"
}

main() {
	print_status "section" "Branch Ruleset Setup (pr-quality-gate)"
	# A skip (no gh / not authed) must not fail init — return 0 either way.
	if ! require_gh; then
		return 0
	fi
	enable_repo_rules
}

main "$@"
