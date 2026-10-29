#!/usr/bin/env bash

set -euo pipefail
export LC_ALL=C

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=templates/common/bin/lib/md_structure.sh
source "$SCRIPT_DIR/lib/md_structure.sh"

readonly -a ARR_SLUGS_HEAD=(getting-started install usage project-structure development)
readonly -a ARR_SLUGS_TAIL=(contributing license authors useful-links)
readonly STR_ICON_RE=$'\xf0\x9f|\xe2[\x98-\x9e]|\xef\xb8\x8f|\xe2\xad[\x90-\x95]|\xe2\x8c[\x9a\x9b]|\xe2\x8f|\xe2\x80\x8d'
readonly STR_LINKEDIN_PLACEHOLDER="linkedin.com/in/your-linkedin-handle"
declare -A MAP_ARCHETYPE=(
	["library"]="public-api publishing"
	["cli"]="releasing"
	["spa"]="deployment"
	["service"]="configuration"
	["usb-tool"]="payload"
	["toolkit"]="commands"
)
declare -A MAP_ARCHETYPE_AFTER_OVERVIEW=(
	["library"]="documentation"
)
declare -a ARR_PROBLEMS=()
STR_ARCHETYPE=""
STR_HEADINGS=""
STR_EXTRA=""
BOOL_TEMPLATE=0

problem() { ARR_PROBLEMS+=("$1: $2"); }

usage() {
	echo "usage: check_readme_structure.sh [--template | --list-archetypes] [README.md ...]" >&2
	exit 2
}

archetype_slugs() {
	local path_file="$1" str_name
	STR_EXTRA=""
	STR_ARCHETYPE=""
	str_name="$(md_strip_fences <"$path_file" | sed -n 's/^<!--[[:space:]]*readme-archetype:[[:space:]]*\([^[:space:]]*\)[[:space:]]*-->.*/\1/p' | head -n1)"
	if [ -z "$str_name" ]; then
		problem "$path_file" "no '<!-- readme-archetype: NAME -->' marker (one of: ${!MAP_ARCHETYPE[*]})"
	elif [[ "$str_name" == *'${'* ]]; then
		[ "$BOOL_TEMPLATE" -eq 1 ] || problem "$path_file" "archetype is still a placeholder: $str_name"
	elif [ -z "${MAP_ARCHETYPE[$str_name]+x}" ]; then
		problem "$path_file" "unknown archetype '$str_name' (one of: ${!MAP_ARCHETYPE[*]})"
	else
		STR_EXTRA="${MAP_ARCHETYPE[$str_name]}"
		STR_ARCHETYPE="$str_name"
	fi
}

check_slugs() {
	local path_file="$1" str_extra="$2" str_slug i_pos i_idx i_last=0 str_after=""
	local -a arr_doc arr_after arr_extra arr_seq=(overview)
	mapfile -t arr_doc < <(printf '%s\n' "$STR_HEADINGS" | awk -F'\t' '$3 != "-" { print $3 }')
	[ -z "$STR_ARCHETYPE" ] || str_after="${MAP_ARCHETYPE_AFTER_OVERVIEW[$STR_ARCHETYPE]:-}"
	if printf '%s\n' "${arr_doc[@]}" | grep -qx 'features'; then
		arr_seq+=(features)
	fi
	read -ra arr_after <<<"$str_after"
	read -ra arr_extra <<<"$str_extra"
	arr_seq+=("${arr_after[@]}" "${ARR_SLUGS_HEAD[@]}" "${arr_extra[@]}" "${ARR_SLUGS_TAIL[@]}")
	for str_slug in "${arr_seq[@]}"; do
		i_pos=0
		for i_idx in "${!arr_doc[@]}"; do
			if [ "${arr_doc[$i_idx]}" = "$str_slug" ]; then
				i_pos=$((i_idx + 1))
				break
			fi
		done
		if [ "$i_pos" -eq 0 ]; then
			problem "$path_file" "missing section '$str_slug': put '<!-- slug: $str_slug -->' on the line above its heading"
		elif [ "$i_pos" -lt "$i_last" ]; then
			problem "$path_file" "section '$str_slug' is out of order"
		else
			i_last="$i_pos"
		fi
	done
}

check_headings() {
	local path_file="$1" i_line i_level str_slug str_text
	while IFS=$'\t' read -r i_line i_level str_slug str_text; do
		[ -n "$i_line" ] || continue
		if [[ "$str_text" =~ $STR_ICON_RE ]]; then
			problem "$path_file:$i_line" "heading carries an emoji or icon: $str_text"
		fi
		if printf '%s' "$str_text" | grep -Eiq '<img|<picture|!\['; then
			problem "$path_file:$i_line" "heading carries an image: $str_text"
		fi
	done <<<"$STR_HEADINGS"
}

authors_body() {
	local path_file="$1" i_start i_level i_end
	read -r i_start i_level < <(printf '%s\n' "$STR_HEADINGS" | awk -F'\t' '$3 == "authors" { print $1, $2; exit }') || true
	[ -n "${i_start:-}" ] || return 0
	i_end="$(printf '%s\n' "$STR_HEADINGS" | awk -F'\t' -v s="$i_start" -v l="$i_level" '$1 > s && $2 <= l { print $1 - 1; exit }')"
	md_strip_fences <"$path_file" | sed -n "$((i_start + 1)),${i_end:-\$}p" | md_strip_comments
}

check_authors() {
	local path_file="$1" str_item i_count=0 re_github re_linkedin
	re_github='(^|[^[:alnum:].-])(www\.)?github\.com/[^[:space:])/]+'
	re_linkedin='(^|[^[:alnum:].-])([a-z]{2,3}\.)?linkedin\.com/in/[^[:space:])/]+'
	[ "$BOOL_TEMPLATE" -eq 1 ] && re_linkedin="$re_linkedin|"'\$\{LINKEDIN_URL\}'
	while IFS= read -r str_item; do
		[[ "$str_item" =~ ^[[:space:]]*[-*][[:space:]] ]] || continue
		i_count=$((i_count + 1))
		[[ "$str_item" =~ $re_github ]] || problem "$path_file" "author without a github.com/<user> link: $str_item"
		[[ "$str_item" =~ $re_linkedin ]] || problem "$path_file" "author without a linkedin.com/in/<handle> link: $str_item"
		if [[ "$str_item" == *"$STR_LINKEDIN_PLACEHOLDER"* ]]; then
			problem "$path_file" "LinkedIn link is the scaffold placeholder: set LINKEDIN_URL"
		fi
	done < <(authors_body "$path_file")
	[ "$i_count" -gt 0 ] || problem "$path_file" "the Authors section lists no one"
}

check_placeholders() {
	local path_file="$1" str_hits
	[ "$BOOL_TEMPLATE" -eq 0 ] || return 0
	str_hits="$(md_normalize <"$path_file" | grep -nE '\$\{[A-Za-z_][A-Za-z0-9_]*\}' | head -n3 | tr '\n' ' ' || true)"
	[ -z "$str_hits" ] || problem "$path_file" "unfilled placeholder(s): $str_hits"
}

check_file() {
	local path_file="$1"
	[ -r "$path_file" ] || {
		problem "$path_file" "unreadable"
		return
	}
	STR_HEADINGS="$(md_strip_fences <"$path_file" | md_headings)"
	archetype_slugs "$path_file"
	check_slugs "$path_file" "$STR_EXTRA"
	check_headings "$path_file"
	check_authors "$path_file"
	check_placeholders "$path_file"
}

main() {
	local -a arr_files=()
	while [ $# -gt 0 ]; do
		case "$1" in
		--template)
			BOOL_TEMPLATE=1
			shift
			;;
		--list-archetypes)
			printf '%s\n' "${!MAP_ARCHETYPE[@]}" | sort
			exit 0
			;;
		-h | --help) usage ;;
		*)
			arr_files+=("$1")
			shift
			;;
		esac
	done
	[ "${#arr_files[@]}" -gt 0 ] || arr_files=(README.md)
	local path_file str_problem
	for path_file in "${arr_files[@]}"; do check_file "$path_file"; done
	if [ "${#ARR_PROBLEMS[@]}" -eq 0 ]; then
		echo "[ok] README structure: ${arr_files[*]}"
		exit 0
	fi
	for str_problem in "${ARR_PROBLEMS[@]}"; do echo "[x] $str_problem" >&2; done
	echo "[x] ${#ARR_PROBLEMS[@]} README structure problem(s)" >&2
	exit 1
}

main "$@"
