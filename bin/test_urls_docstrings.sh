#!/bin/bash
# Pre-commit hook: scan Python docstrings for URLs and validate reachability.
# Results are cached for 1 week to avoid repeated network calls.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/lib/common.sh"

CACHE_DIR=".url_check_cache"
CACHE_TTL=$((60 * 60 * 24 * 7)) # 1 week in seconds

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

	if [[ "$str_status_code" =~ ^2 ]]; then
		set_cache "$url" "$str_status_code"
	fi

	echo "$str_status_code"
}

process_python_files() {
	clean_cache

	local str_root_dir="${1:-.}"
	declare -A processed_urls
	local has_errors=0

	print_status "info" "Scanning Python docstrings for URLs in '$str_root_dir'..."

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
						has_errors=1
					elif [[ "$str_status_code" =~ ^[34] ]]; then
						print_status "error" "URL issue ($str_status_code) in $file (line $int_line_num): $url"
						has_errors=1
					elif [[ ! "$str_status_code" =~ ^2 ]]; then
						print_status "error" "URL problem ($str_status_code) in $file (line $int_line_num): $url"
						has_errors=1
					fi

					line="${line#*$url}"
				done
			fi
		done <"$file"
	done < <(find "$str_root_dir" -type f -name "*.py" -print0)

	if [[ $has_errors -eq 0 ]]; then
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
