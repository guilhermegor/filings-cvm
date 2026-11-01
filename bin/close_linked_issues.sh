#!/usr/bin/env bash

set -uo pipefail

BRANCH_TYPES='feat|feature|fix|bugfix|hotfix|docs|refactor|chore|test'
KEYWORDS='(close[sd]?|fix(e[sd])?|resolve[sd]?)'

issue_from_branch() {
	local str_branch="$1" str_num

	str_num=$(printf '%s' "$str_branch" | sed -nE "s#^($BRANCH_TYPES)/([0-9]+)-.*#\2#p")
	if [[ "$str_branch" =~ /(19|20)[0-9]{2}-(0[1-9]|1[0-2])(-|$) ]]; then
		return 0
	fi
	[[ -n "$str_num" ]] && printf '%s\n' "$str_num"
	return 0
}

strip_non_prose() {
	tr -d '\r' | awk '
		/^[[:space:]]*(```|~~~)/ { fence = !fence; next }
		fence { next }
		{
			str_orig = $0
			str_line = $0
			str_out = ""
			while (1) {
				if (int_comment) {
					int_at = index(str_line, "-->")
					if (!int_at) { str_line = ""; break }
					str_line = substr(str_line, int_at + 3)
					int_comment = 0
				}
				int_at = index(str_line, "<!--")
				if (!int_at) break
				str_out = str_out substr(str_line, 1, int_at - 1) " "
				str_line = substr(str_line, int_at + 4)
				int_comment = 1
			}
			str_line = str_out str_line
			if (str_orig ~ /^[[:space:]]*>/) next
			gsub(/`[^`]*`/, " ", str_line)
			print str_line
		}'
}

issues_from_body() {
	local str_body="$1" str_neg='(not|never|cannot|no longer|reverts?|reverted|reverting|without)'

	printf '%s\n' "$str_body" | strip_non_prose | tr '\n' ' ' | tr '[:upper:]' '[:lower:]' |
		sed -E \
			-e "s/(^|[^[:alnum:]_])$str_neg([[:space:]]+[[:alpha:]]+){0,3}[[:space:]]+$KEYWORDS:?[[:space:]]+#[0-9]+/ /g" \
			-e "s/n('|’)t([[:space:]]+[[:alpha:]]+){0,3}[[:space:]]+$KEYWORDS:?[[:space:]]+#[0-9]+/ /g" |
		{ grep -owE "$KEYWORDS:?[[:space:]]+#[0-9]+" || true; } |
		{ grep -oE '[0-9]+$' || true; }
}

resolve_issues() {
	local str_branch="$1" str_body="$2"

	case "$str_branch" in
	dependabot/* | renovate/* | release/*) return 0 ;;
	esac
	{
		issue_from_branch "$str_branch"
		issues_from_body "$str_body"
	} | sed -E 's/^0+//' | { grep -vxE '' || true; } | sort -un
}

close_issue() {
	local str_num="$1" str_state str_err path_err

	path_err=$(mktemp)
	if ! str_state=$(gh api "repos/$GH_REPO/issues/$str_num" \
		--jq 'if .pull_request then "pr" else .state end' 2>"$path_err"); then
		str_err=$(<"$path_err")
		rm -f "$path_err"
		if [[ "$str_err" =~ \(HTTP\ (404|410)\) ]]; then
			echo "#$str_num does not exist (HTTP ${BASH_REMATCH[1]}), skipped"
			return 0
		fi
		echo "::error::could not read #$str_num: $str_err"
		return 1
	fi
	rm -f "$path_err"
	if [[ "$str_state" != "open" ]]; then
		echo "#$str_num is $str_state, skipped"
		return 0
	fi
	if ! gh issue close "$str_num" --reason completed --comment "Delivered in #$PR."; then
		echo "::error::could not close #$str_num"
		return 1
	fi
	echo "closed #$str_num"
}

main() {
	local int_failed=0 str_num str_list

	if ! str_list=$(resolve_issues "$BRANCH" "$BODY"); then
		echo "::error::could not parse the branch and body for issue numbers"
		return 1
	fi
	for str_num in $str_list; do
		[[ "$str_num" == "$PR" ]] && continue
		close_issue "$str_num" || int_failed=1
	done
	return "$int_failed"
}

if [[ "${BASH_SOURCE[0]}" == "$0" ]]; then
	main
fi
