#!/bin/bash
#
# lib/common.sh
#
# Shared shell utilities for scaffolded BlueprintX projects. Sourced by sibling
# scripts so each one shares a single print_status implementation and color set.
#
# Sourcing contract:
#   - Idempotent (guarded with _BX_COMMON_LOADED so re-sourcing is a no-op).
#   - Optional: scripts may set LOG_FILE before sourcing; print_status will tee
#     timestamped output there. If LOG_FILE is unset, console output only.
#   - Refuses direct execution.
#
# NOTE: This file is the single source of truth and is kept BYTE-IDENTICAL in
# templates/common/bin/lib/ and templates/python-common/bin/lib/. CI enforces
# parity (bin/ci/check_version_sync.sh). Offline scaffolds copy the common/
# version over the python-common one, so both must carry resolve_default_branch
# and _read_env_var — do not let them drift.

if [[ "${BASH_SOURCE[0]}" == "$0" ]]; then
	echo "lib/common.sh is meant to be sourced, not executed." >&2
	exit 1
fi

# Re-sourcing guard
if [ -n "${_BX_COMMON_LOADED:-}" ]; then
	return 0
fi
_BX_COMMON_LOADED=1

# ============================================================================
# COLOR VARIABLES
# ============================================================================

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
NC='\033[0m'

# ============================================================================
# print_status — standard status-keyword API
# ============================================================================
#
# Usage:
#   print_status <level> <message>
#
# Levels: success | error | warning | info | config | debug | section
# Unknown levels fall through to a neutral "[ ] message" prefix.
# Errors go to stderr; everything else to stdout.
# If $LOG_FILE is set, every call appends a timestamped line to it.

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
		echo -e "[ ] ${message}"
		;;
	esac

	if [ -n "${LOG_FILE:-}" ]; then
		echo "[$(date '+%Y-%m-%d %H:%M:%S')] [$status] $message" >>"$LOG_FILE"
	fi
}

# ============================================================================
# resolve_default_branch — find the repo's default branch
# ============================================================================
#
# Usage:
#   target="$(resolve_default_branch [explicit_name])"
#
# Resolution order: explicit argument, then $DEFAULT_BRANCH, then the remote's
# origin/HEAD, then a local "main", else "master". Used by new_branch.sh and
# git_merge_to_main.sh so both agree on the integration branch.

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

# ============================================================================
# _read_env_var — read a single variable straight from .env
# ============================================================================
#
# Usage:
#   value="$(_read_env_var DB_PASSWORD)"
#
# Reads NAME=value from .env (override the file with ENV_FILE). Returns the raw
# right-hand side — it does NOT strip inline '#' so passwords containing '#' or
# '$' survive intact (the whole point of bypassing Make's variable/comment
# expansion). A single pair of surrounding quotes is removed; the last matching
# assignment wins; a missing file or key yields an empty string.

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

# ============================================================================
# ensure_dir — create a directory if missing (UNC/CRLF-safe)
# ============================================================================
#
# Usage:
#   ensure_dir "/path/to/dir"
#
# Idempotent: returns early when the directory already exists, then mkdir -p.
# On Windows mapped/UNC drives a bare `mkdir -p` over an existing path can fail
# with "Permission denied"; the existence check sidesteps that. Use this instead
# of bare `mkdir -p` in offline-git recipes and anywhere an output dir is created.

ensure_dir() {
	local dir_path="$1"
	[ -d "$dir_path" ] && return 0
	mkdir -p "$dir_path"
}
