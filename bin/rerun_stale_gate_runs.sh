#!/bin/bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=lib/common.sh
source "$SCRIPT_DIR/lib/common.sh"

warn_annotated() {
	local str_message="$1"

	echo "::warning::$str_message"
	print_status "warning" "$str_message"
}

preconditions_met() {
	if [[ -z "${GITHUB_REPOSITORY:-}" || -z "${GITHUB_RUN_ID:-}" ]]; then
		print_status "info" "Not inside a GitHub Actions run — nothing to clear."
		return 1
	fi

	if [[ -z "${HEAD_SHA:-}" ]]; then
		print_status "info" "No HEAD_SHA (not a pull-request event) — nothing to clear."
		return 1
	fi

	return 0
}

resolve_workflow_id() {
	gh api "repos/$GITHUB_REPOSITORY/actions/runs/$GITHUB_RUN_ID" --jq '.workflow_id'
}

list_stale_failed_runs() {
	local str_workflow_id="$1"

	gh api --paginate --method GET "repos/$GITHUB_REPOSITORY/actions/runs" \
		-f "head_sha=$HEAD_SHA" \
		-f "status=failure" \
		--jq ".workflow_runs[] | select(.workflow_id == $str_workflow_id) | .id"
}

rerun_one() {
	local str_run_id="$1"

	if gh api --method POST \
		"repos/$GITHUB_REPOSITORY/actions/runs/$str_run_id/rerun-failed-jobs" >/dev/null 2>&1; then
		print_status "success" "Re-ran stale failed run $str_run_id."
		return 0
	fi

	warn_annotated "Could not re-run stale failed run $str_run_id (needs 'actions: write') — the PR stays BLOCKED until it is re-run by hand."
	return 0
}

clear_stale_runs() {
	local str_workflow_id="$1"
	local -a list_run_ids=()
	local str_run_id
	local str_discovered
	local int_cleared=0

	if ! str_discovered="$(list_stale_failed_runs "$str_workflow_id")"; then
		warn_annotated "Could not list runs at $HEAD_SHA — no stale run was cleared."
		return 0
	fi

	mapfile -t list_run_ids <<<"$str_discovered"

	for str_run_id in "${list_run_ids[@]}"; do
		if [[ -n "$str_run_id" && "$str_run_id" != "$GITHUB_RUN_ID" ]]; then
			rerun_one "$str_run_id"
			int_cleared=$((int_cleared + 1))
		fi
	done

	if [[ "$int_cleared" -eq 0 ]]; then
		print_status "info" "No stale failed run at $HEAD_SHA — the rollup is already clean."
		return 0
	fi

	print_status "success" "Re-ran $int_cleared stale failed run(s) at $HEAD_SHA."
	return 0
}

main() {
	if ! preconditions_met; then
		return 0
	fi

	local str_workflow_id
	if ! str_workflow_id="$(resolve_workflow_id)"; then
		warn_annotated "Could not resolve this run's workflow id — no stale run was cleared."
		return 0
	fi

	clear_stale_runs "$str_workflow_id"
	return 0
}

main "$@"
