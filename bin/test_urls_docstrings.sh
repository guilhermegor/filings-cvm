#!/bin/bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/lib/common.sh"

CACHE_DIR=".url_check_cache"
CACHE_TTL=$((60 * 60 * 24 * 7))

get_cache() {
	local url="$1"
	local str_cache_file
	str_cache_file="${CACHE_DIR}/$(echo -n "$url" | md5sum | cut -d' ' -f1)"

	if [[ -f "$str_cache_file" ]]; then
		local int_timestamp
		int_timestamp=$(stat -c %Y "$str_cache_file")
		local int_now
		int_now=$(date +%s)

		if ((int_now - int_timestamp < CACHE_TTL)); then
			cat "$str_cache_file"
			return 0
		fi
	fi
	return 1
}

set_cache() {
	local url="$1"
	local str_status="$2"
	local str_cache_file
	str_cache_file="${CACHE_DIR}/$(echo -n "$url" | md5sum | cut -d' ' -f1)"
	echo "$str_status" >"$str_cache_file"
}

clean_cache() {
	find "$CACHE_DIR" -type f -mtime +$((CACHE_TTL / 60 / 60 / 24)) -delete 2>/dev/null
}

STR_URL_USER_AGENT="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
LIST_URL_ALLOWLIST=(
	"platform.openai.com"
	"openai.com"
	"stackoverflow.com"
	"reuters.com"
	"investing.com"
	"code.activestate.com"
	"geeksforgeeks.org"
	"towardsdatascience.com"
	"udemy.com"
)

url_is_allowlisted() {
	local str_url="$1"
	local str_domain str_host

	[[ "$str_url" =~ ^https?:// ]] || return 1
	str_host="${str_url#*://}"
	str_host="${str_host##*@}"
	str_host="${str_host%%/*}"
	str_host="${str_host%%\?*}"
	str_host="${str_host%%#*}"
	str_host="${str_host%%:*}"

	for str_domain in "${LIST_URL_ALLOWLIST[@]}"; do
		if [[ "$str_host" == "$str_domain" || "$str_host" == *".$str_domain" ]]; then
			return 0
		fi
	done
	return 1
}

probe_url_status() {
	local str_url="$1"
	local str_status_code
	local -a list_headers=(
		-H "User-Agent: $STR_URL_USER_AGENT"
		-H "Accept: text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
		-H "Accept-Language: en-US,en;q=0.5"
		-H "Connection: keep-alive"
	)

	str_status_code=$(curl -s -o /dev/null -w "%{http_code}" --max-time 10 --head \
		"${list_headers[@]}" "$str_url" 2>/dev/null)

	if [[ -z "$str_status_code" || "$str_status_code" -eq 403 || "$str_status_code" -eq 405 ]]; then
		str_status_code=$(curl -s -o /dev/null -w "%{http_code}" --max-time 10 \
			"${list_headers[@]}" -H "Upgrade-Insecure-Requests: 1" "$str_url" 2>/dev/null)
	fi

	if [[ "$str_status_code" -eq 403 ]]; then
		if wget --spider --timeout=10 --user-agent="$STR_URL_USER_AGENT" "$str_url" >/dev/null 2>&1; then
			str_status_code="200"
		fi
	fi

	echo "$str_status_code"
}

check_url() {
	local str_url="$1"
	local str_status_code

	if str_status_code=$(get_cache "$str_url"); then
		echo "$str_status_code"
		return
	fi

	if url_is_allowlisted "$str_url"; then
		set_cache "$str_url" "200"
		echo "200"
		return
	fi

	str_status_code=$(probe_url_status "$str_url")
	if [[ "$str_status_code" =~ ^2 ]]; then
		set_cache "$str_url" "$str_status_code"
	fi
	echo "$str_status_code"
}

declare -A DICT_PROCESSED_URLS=()
INT_URL_ERRORS=0

report_url_status() {
	local str_file="$1" int_line_num="$2" str_url="$3" str_status_code="$4"

	if [[ -z "$str_status_code" ]]; then
		print_status "error" "Failed to access URL in $str_file (line $int_line_num): $str_url"
	elif [[ "$str_status_code" =~ ^[34] ]]; then
		print_status "error" "URL issue ($str_status_code) in $str_file (line $int_line_num): $str_url"
	elif [[ ! "$str_status_code" =~ ^2 ]]; then
		print_status "error" "URL problem ($str_status_code) in $str_file (line $int_line_num): $str_url"
	else
		return 0
	fi
	INT_URL_ERRORS=1
}

check_urls_in_line() {
	local str_file="$1" int_line_num="$2" str_line="$3"
	local str_url str_status_code

	while [[ "$str_line" =~ (https?://[a-zA-Z0-9./?=_%:-]+[a-zA-Z0-9./?=_%:-]) ]]; do
		str_url="${BASH_REMATCH[1]}"
		str_line="${str_line#*"$str_url"}"

		[[ -n "${DICT_PROCESSED_URLS[$str_url]:-}" ]] && continue
		DICT_PROCESSED_URLS["$str_url"]=1

		[[ "$str_url" =~ (https?://[^/]+)$ ]] && continue

		str_status_code=$(check_url "$str_url")
		report_url_status "$str_file" "$int_line_num" "$str_url" "$str_status_code"
	done
}

STR_DOC_QUOTE=""
STR_DOC_TEXT=""
readonly STR_DQ='"""'
readonly STR_SQ="'''"

# Pick the delimiter that appears first in a line, or empty when it has neither.
first_delimiter() {
	local str_line="$1"
	local str_dq_head="${str_line%%"$STR_DQ"*}"
	local str_sq_head="${str_line%%"$STR_SQ"*}"

	if [[ "$str_line" != *"$STR_DQ"* && "$str_line" != *"$STR_SQ"* ]]; then
		return 0
	elif [[ "$str_line" != *"$STR_SQ"* ]] || [[ "$str_line" == *"$STR_DQ"* && ${#str_dq_head} -lt ${#str_sq_head} ]]; then
		printf '%s' "$STR_DQ"
	else
		printf '%s' "$STR_SQ"
	fi
}

# Advance the docstring state by one line. Sets STR_DOC_QUOTE (the delimiter that opened the
# docstring still in progress, or empty) and STR_DOC_TEXT (only the part of the line that is
# docstring text, so a URL outside the delimiters is never probed). Only the opening
# delimiter can close the docstring.
advance_docstring_state() {
	local str_rest="$1"

	STR_DOC_TEXT=""
	if [[ -z "$STR_DOC_QUOTE" ]]; then
		STR_DOC_QUOTE="$(first_delimiter "$str_rest")"
		[[ -n "$STR_DOC_QUOTE" ]] || return 0
		str_rest="${str_rest#*"$STR_DOC_QUOTE"}"
	fi

	if [[ "$str_rest" == *"$STR_DOC_QUOTE"* ]]; then
		STR_DOC_TEXT="${str_rest%%"$STR_DOC_QUOTE"*}"
		STR_DOC_QUOTE=""
	else
		STR_DOC_TEXT="$str_rest"
	fi
}

scan_file_for_urls() {
	local str_file="$1"
	local int_line_num=0
	local str_line

	STR_DOC_QUOTE=""
	while IFS= read -r str_line; do
		((int_line_num++))
		advance_docstring_state "$str_line"
		[[ -z "$STR_DOC_TEXT" ]] || check_urls_in_line "$str_file" "$int_line_num" "$STR_DOC_TEXT"
	done <"$str_file"
}

process_python_files() {
	clean_cache

	local str_root_dir="${1:-.}"
	local str_file
	DICT_PROCESSED_URLS=()
	INT_URL_ERRORS=0

	print_status "info" "Scanning Python docstrings for URLs in '$str_root_dir'..."

	while IFS= read -r -d '' str_file; do
		scan_file_for_urls "$str_file"
	done < <(find "$str_root_dir" -type f -name "*.py" -print0)

	if [[ $INT_URL_ERRORS -eq 0 ]]; then
		print_status "success" "All docstring URLs are reachable"
		return 0
	fi
	return 1
}

main() {
	mkdir -p "$CACHE_DIR"
	process_python_files "${1:-.}" || exit 1
}

main "$@"
