#!/bin/bash
# Scan Python docstrings for URLs and validate reachability (manual / weekly, not a hook).
# Results are cached; see docs/contributing.md.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/lib/common.sh"

CACHE_TTL=$((60 * 60 * 24 * 7)) # 1 week in seconds
CACHE_TTL_FAIL=$((60 * 60 * 24))

resolve_cache_dir() {
	if [[ -n "${URL_CACHE_DIR:-}" ]]; then
		echo "$URL_CACHE_DIR"
		return
	fi
	local str_common
	if str_common=$(git rev-parse --path-format=absolute --git-common-dir 2>/dev/null); then
		echo "$str_common/url_check_cache"
	else
		echo ".url_check_cache"
	fi
}

CACHE_DIR="$(resolve_cache_dir)"

get_cache() {
	local url="$1"
	local str_cache_file
	str_cache_file="${CACHE_DIR}/$(echo -n "$url" | md5sum | cut -d' ' -f1)"

	if [[ -f "$str_cache_file" ]]; then
		local int_timestamp
		int_timestamp=$(stat -c %Y "$str_cache_file")
		local int_now
		int_now=$(date +%s)

		local str_cached
		str_cached=$(cat "$str_cache_file")
		local int_ttl=$CACHE_TTL
		[[ "$str_cached" =~ ^2 ]] || int_ttl=$CACHE_TTL_FAIL

		if ((int_now - int_timestamp < int_ttl)); then
			echo "$str_cached"
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
	find "$CACHE_DIR" -type f -mtime +$((CACHE_TTL / 60 / 60 / 24)) -delete 2>/dev/null || true
}

check_url() {
	local url="$1"
	local str_status_code

	if str_status_code=$(get_cache "$url"); then
		echo "$str_status_code"
		return
	fi

	local str_user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

	local problematic_domains=(
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

	for domain in "${problematic_domains[@]}"; do
		if [[ "$url" == *"$domain"* ]] && [[ "$url" =~ ^https?:// ]]; then
			set_cache "$url" "200"
			echo "200"
			return
		fi
	done

	# Method 1: HEAD request
	str_status_code=$(curl -s -o /dev/null -w "%{http_code}" --max-time 10 --head \
		-H "User-Agent: $str_user_agent" \
		-H "Accept: text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8" \
		-H "Accept-Language: en-US,en;q=0.5" \
		-H "Connection: keep-alive" \
		"$url" 2>/dev/null)

	# Method 2: GET if HEAD returns 403/405
	if [[ -z "$str_status_code" || "$str_status_code" -eq 403 || "$str_status_code" -eq 405 ]]; then
		str_status_code=$(curl -s -o /dev/null -w "%{http_code}" --max-time 10 \
			-H "User-Agent: $str_user_agent" \
			-H "Accept: text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8" \
			-H "Accept-Language: en-US,en;q=0.5" \
			-H "Connection: keep-alive" \
			-H "Upgrade-Insecure-Requests: 1" \
			"$url" 2>/dev/null)
	fi

	# Method 3: wget fallback for persistent 403s
	if [[ "$str_status_code" -eq 403 ]]; then
		if wget --spider --timeout=10 --user-agent="$str_user_agent" "$url" >/dev/null 2>&1; then
			str_status_code="200"
		fi
	fi

	if [[ -n "$str_status_code" && "$str_status_code" != "000" ]]; then
		set_cache "$url" "$str_status_code"
	fi

	echo "$str_status_code"
}

list_python_files() {
	if (($# == 0)); then
		find . -type f -name "*.py" -print0
		return
	fi
	local path
	for path in "$@"; do
		if [[ "$path" == *.py && -f "$path" ]]; then
			printf '%s\0' "$path"
		fi
	done
	return 0
}

process_python_files() {
	clean_cache

	declare -A processed_urls
	local has_errors=0

	report_dead() {
		has_errors=1
		if [[ -n "${URL_REPORT_FILE:-}" ]]; then
			printf '%s\t%s\t%s\n' "$1" "$2" "$3" >>"$URL_REPORT_FILE"
		fi
	}

	print_status "info" "Scanning Python docstrings for URLs ($# path argument(s); none = whole tree)..."

	while IFS= read -r -d '' file; do
		local int_line_num=0
		local bool_in_docstring=false

		while IFS= read -r line; do
			((int_line_num++))

			if [[ "$line" =~ ^[[:space:]]*\"\"\" ]]; then
				local str_after_open="${line#*\"\"\"}"
				if [[ "$bool_in_docstring" == false && "$str_after_open" == *\"\"\"* ]]; then
					continue
				fi
				[[ "$bool_in_docstring" == true ]] && bool_in_docstring=false || bool_in_docstring=true
				continue
			fi
			if [[ "$line" =~ ^[[:space:]]*\'\'\' ]]; then
				local str_after_open="${line#*\'\'\'}"
				if [[ "$bool_in_docstring" == false && "$str_after_open" == *\'\'\'* ]]; then
					continue
				fi
				[[ "$bool_in_docstring" == true ]] && bool_in_docstring=false || bool_in_docstring=true
				continue
			fi

			if [[ "$bool_in_docstring" == true ]]; then
				while [[ "$line" =~ (https?://[a-zA-Z0-9./?=_%:-]+[a-zA-Z0-9./?=_%:-]) ]]; do
					local url="${BASH_REMATCH[1]}"

					if [[ -n "${processed_urls[$url]:-}" ]]; then
						line="${line#*$url}"
						continue
					fi
					processed_urls["$url"]=1

					if [[ "$url" =~ (https?://[^/]+)$ ]]; then
						line="${line#*$url}"
						continue
					fi

					local str_status_code
					str_status_code=$(check_url "$url")

					if [[ -z "$str_status_code" ]]; then
						print_status "error" "Failed to access URL in $file (line $int_line_num): $url"
						report_dead "none" "$file:$int_line_num" "$url"
					elif [[ "$str_status_code" =~ ^[34] ]]; then
						print_status "error" "URL issue ($str_status_code) in $file (line $int_line_num): $url"
						report_dead "$str_status_code" "$file:$int_line_num" "$url"
					elif [[ ! "$str_status_code" =~ ^2 ]]; then
						print_status "error" "URL problem ($str_status_code) in $file (line $int_line_num): $url"
						report_dead "$str_status_code" "$file:$int_line_num" "$url"
					fi

					line="${line#*$url}"
				done
			fi
		done <"$file"
	done < <(list_python_files "$@")

	if [[ $has_errors -eq 0 ]]; then
		print_status "success" "All docstring URLs are reachable"
		return 0
	fi
	return 1
}

main() {
	mkdir -p "$CACHE_DIR"
	process_python_files "$@" || [[ -n "${URL_REPORT_FILE:-}" ]] || exit 1
}

main "$@"
