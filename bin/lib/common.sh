#!/bin/bash

if [[ "${BASH_SOURCE[0]}" == "$0" ]]; then
	echo "lib/common.sh is meant to be sourced, not executed." >&2
	exit 1
fi

if [ -n "${_BX_COMMON_LOADED:-}" ]; then
	return 0
fi
_BX_COMMON_LOADED=1

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
NC='\033[0m'

print_status() {
	local status="$1"
	local message="$2"

	case "$status" in
	success)
		echo -e "${GREEN}[✓]${NC} ${message}"
		;;
	error)
		echo -e "${RED}[✗]${NC} ${message}" >&2
		;;
	warning)
		echo -e "${YELLOW}[!]${NC} ${message}"
		;;
	info)
		echo -e "${BLUE}[i]${NC} ${message}"
		;;
	config)
		echo -e "${CYAN}[→]${NC} ${message}"
		;;
	debug)
		echo -e "${MAGENTA}[»]${NC} ${message}"
		;;
	section)
		echo -e "\n${MAGENTA}========================================${NC}"
		echo -e "${MAGENTA} $message${NC}"
		echo -e "${MAGENTA}========================================${NC}\n"
		;;
	*)
		echo -e "${YELLOW}[?]${NC} ${message}" >&2
		echo "print_status: unknown status '${status}' — expected one of:" \
			"success|error|warning|info|config|debug|section" >&2
		;;
	esac

	if [ -n "${LOG_FILE:-}" ]; then
		echo "[$(date '+%Y-%m-%d %H:%M:%S')] [$status] $message" >>"$LOG_FILE"
	fi
}

resolve_default_branch() {
	local explicit="${1:-}"
	if [ -n "$explicit" ]; then
		echo "$explicit"
		return 0
	fi
	if [ -n "${DEFAULT_BRANCH:-}" ]; then
		echo "$DEFAULT_BRANCH"
		return 0
	fi

	local head_ref
	head_ref="$(git symbolic-ref --quiet --short refs/remotes/origin/HEAD 2>/dev/null || true)"
	if [ -n "$head_ref" ]; then
		echo "${head_ref#origin/}"
		return 0
	fi

	if git show-ref --verify --quiet refs/heads/main; then
		echo "main"
		return 0
	fi
	echo "master"
}

_read_env_var() {
	local var_name="$1"
	local env_file="${ENV_FILE:-.env}"
	[ -f "$env_file" ] || return 0

	local line
	line="$(grep -E "^[[:space:]]*${var_name}=" "$env_file" | tail -n 1)"
	[ -n "$line" ] || return 0

	local value="${line#*=}"
	value="${value%$'\r'}"
	if [[ "$value" == \"*\" ]]; then
		value="${value#\"}"
		value="${value%\"}"
	elif [[ "$value" == \'*\' ]]; then
		value="${value#\'}"
		value="${value%\'}"
	fi
	printf '%s' "$value"
}

ensure_dir() {
	local dir_path="$1"
	[ -d "$dir_path" ] && return 0
	mkdir -p "$dir_path"
}
