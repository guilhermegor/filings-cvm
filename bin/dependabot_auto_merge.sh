#!/usr/bin/env bash

set -uo pipefail

readonly DEPENDABOT_LOGIN="dependabot[bot]"

classify_update() {
	local str_json="${1:-}"
	if printf '%s' "$str_json" | jq -e 'type == "array" and length > 0 and all(.[]; .updateType == "version-update:semver-patch" or .updateType == "version-update:semver-minor")' >/dev/null 2>&1; then
		echo minor
	else
		echo major
	fi
}

is_pure_dependabot() {
	local str_pr="$1" str_bad
	[[ "$(gh api "repos/$GH_REPO/pulls/$str_pr" | jq -r .user.login)" == "$DEPENDABOT_LOGIN" ]] || return 1
	str_bad=$(gh api "repos/$GH_REPO/pulls/$str_pr/commits" --paginate |
		jq -s --arg bot "$DEPENDABOT_LOGIN" \
			'[.[][]] as $c | if ($c | length) == 0 then -1 else [$c[] | select((.author.login == $bot and .committer.login == "web-flow" and .commit.verification.verified == true) | not)] | length end') || return 1
	[[ "$str_bad" == 0 ]]
}

pushed_by_dependabot() {
	local str_head="$1" str_n
	if [[ "${EVENT_NAME:-}" == pull_request_target ]]; then
		[[ "${SENDER:-}" == "$DEPENDABOT_LOGIN" ]]
		return
	fi
	str_n=$(gh api "repos/$GH_REPO/actions/runs?head_sha=$str_head&event=pull_request&per_page=100" |
		jq --arg bot "$DEPENDABOT_LOGIN" \
			'if .total_count == (.workflow_runs | length) and .total_count > 0
			 then [.workflow_runs[] | select(.actor.login != $bot)] | length else -1 end') || return 1
	[[ "$str_n" == 0 ]]
}

roster_bots() {
	local str_pr="$1" str_base
	str_base=$(gh api "repos/$GH_REPO/pulls/$str_pr" | jq -r .base.sha) || return 1
	{ gh api -H "Accept: application/vnd.github.raw" \
		"repos/$GH_REPO/contents/.review-bots.yaml?ref=$str_base" 2>/dev/null || true; } |
		awk '/^[[:space:]]*-[[:space:]]+login:/ { sub(/^[^:]*:[[:space:]]*/, ""); sub(/#.*/, ""); gsub(/["\047[:space:]]/, ""); str_login = $0 }
			/^[[:space:]]+posts:[[:space:]]*threads[[:space:]]*(#.*)?$/ && str_login != "" { print str_login; str_login = "" }'
}

has_review_on_head() {
	local str_pr="$1" str_head="$2" str_n str_roster
	str_roster=$(roster_bots "$str_pr" | jq -R -s -c 'split("\n") | map(select(. != ""))') || return 1
	str_n=$(gh api "repos/$GH_REPO/pulls/$str_pr/reviews" --paginate |
		jq -s --arg head "$str_head" --arg bot "$DEPENDABOT_LOGIN" --argjson roster "$str_roster" \
			'[.[][] | select(.user.login != $bot and (
				(.user.type != "Bot" and (.author_association | IN("OWNER", "MEMBER", "COLLABORATOR")))
				or (.user.type == "Bot" and (.user.login | IN($roster[]))) ))] as $trusted
			| ($trusted | map(select(.state | IN("APPROVED", "CHANGES_REQUESTED", "DISMISSED"))) | group_by(.user.login) | map(last)) as $latest
			| if any($latest[]; .state == "CHANGES_REQUESTED") then 0
			  else [$trusted[] | select(.commit_id == $head and (.state | IN("APPROVED", "COMMENTED")))] | length end') || return 1
	[[ "$str_n" =~ ^[0-9]+$ ]] && ((str_n > 0))
}

disarm() {
	local str_out
	str_out=$(gh pr merge "$1" --disable-auto --repo "$GH_REPO" 2>&1) && return 0
	grep -qi "not enabled" <<<"$str_out" && return 0
	echo "::error::could not disable auto-merge: $str_out"
	return 1
}

decide() {
	local str_pr="$1" str_head="$2" str_json="$3"
	is_pure_dependabot "$str_pr" || {
		echo skip
		return 0
	}
	pushed_by_dependabot "$str_head" || {
		echo skip
		return 0
	}
	if [[ "$(classify_update "$str_json")" == minor ]]; then
		echo arm
	elif has_review_on_head "$str_pr" "$str_head"; then
		echo arm
	else
		echo wait-review
	fi
}

main() {
	local str_decision
	str_decision=$(decide "$PR" "$HEAD_SHA" "${DEPS_JSON:-}") || return 1
	case "$str_decision" in
	arm) gh pr merge "$PR" --auto --squash --match-head-commit "$HEAD_SHA" --repo "$GH_REPO" ;;
	wait-review)
		disarm "$PR" || return 1
		echo "::notice::major update: waiting for a review on $HEAD_SHA"
		;;
	*)
		disarm "$PR" || return 1
		echo "::notice::not a pure Dependabot PR: auto-merge not armed"
		;;
	esac
}

if [[ "${BASH_SOURCE[0]}" == "$0" ]]; then
	main
fi
