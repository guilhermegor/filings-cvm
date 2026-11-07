#!/usr/bin/env bash

set -euo pipefail

shopt -s dotglob nullglob

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
case "$(basename "$SCRIPT_DIR")" in
ci) REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)" ;;
*) REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)" ;;
esac
if [ "${1:-}" = "--root" ]; then
	[ -n "${2:-}" ] && [ -d "$2" ] || {
		echo "ERROR: --root needs an existing directory (got '${2:-}')" >&2
		exit 2
	}
	REPO_ROOT="$(cd "$2" && pwd)"
	shift 2
fi
[ "$#" -eq 0 ] || {
	echo "ERROR: unexpected argument '$1' (usage: check_specs_structure.sh [--root <dir>])" >&2
	exit 2
}
SPECS_DIR="$REPO_ROOT/.specs"
errors=0

is_change_type() {
	case "$1" in
	feat | feature | fix | bugfix | hotfix | chore | docs | refactor | perf | test | tests | style | build | ci | revert | release)
		return 0
		;;
	*) return 1 ;;
	esac
}

check_tasks_markers() {
	local file="$1" label="$2" bad
	bad="$(awk '
        fence {
            if (match($0, /^[[:space:]]*(```+|~~~+)[[:space:]]*$/)) {
                run = $0; gsub(/[[:space:]]/, "", run)
                if (substr(run, 1, 1) == fchar && length(run) >= flen) fence = 0
            }
            next
        }
        match($0, /^[[:space:]]*(```+|~~~+)/) {
            run = substr($0, RSTART, RLENGTH); gsub(/[[:space:]]/, "", run)
            fence = 1; fchar = substr(run, 1, 1); flen = length(run); fline = NR; next
        }
        match($0, /^[[:space:]]*([-*+]|[0-9]+[.)]) \[[^]]*\]/) {
            mark = substr($0, RSTART, RLENGTH); sub(/^[^[]*\[/, "", mark); sub(/\]$/, "", mark)
            rest = substr($0, RLENGTH + 1)
            if (mark != " " && mark != "~" && mark != "x") print NR ": " $0
            else if (mark == "~" && rest !~ /^[[:space:]]+[a-z]+\/[^[:space:]]+/) print NR ": " $0
        }
        END { if (fence) print fline ": unclosed code fence" }' "$file")"
	if [ -n "$bad" ]; then
		printf '%s\n' "$bad" | while IFS= read -r line; do
			echo "ERROR: $label line $line — markers are [ ], [~] <branch> and [x]" >&2
		done
		errors=$((errors + $(printf '%s\n' "$bad" | wc -l)))
	fi
}

if [ ! -d "$SPECS_DIR" ]; then
	echo "check_specs_structure: no .specs/ directory — nothing to check."
	exit 0
fi

if [ ! -f "$SPECS_DIR/CLAUDE.md" ]; then
	echo "ERROR: .specs/ exists but .specs/CLAUDE.md is missing" >&2
	errors=$((errors + 1))
fi

for entry in "$SPECS_DIR"/*; do
	name="$(basename "$entry")"
	case "$name" in
	CLAUDE.md | features | backlog | _lessons) ;;
	*)
		echo "ERROR: unexpected top-level entry .specs/$name (only CLAUDE.md, features/, backlog/, _lessons/ are allowed)" >&2
		errors=$((errors + 1))
		;;
	esac
done

if [ -d "$SPECS_DIR/features" ]; then
	for entry in "$SPECS_DIR/features"/*; do
		[ -e "$entry" ] || continue
		name="$(basename "$entry")"
		[ "$name" = ".gitkeep" ] && [ -f "$entry" ] && continue
		if [ ! -d "$entry" ]; then
			echo "ERROR: .specs/features/$name is not a directory" >&2
			errors=$((errors + 1))
			continue
		fi
		if ! printf '%s' "$name" | grep -qE '^[a-z0-9]+(-[a-z0-9]+)*$' ||
			! printf '%s' "$name" | grep -q '[a-z]'; then
			echo "ERROR: .specs/features/$name is not kebab-case — .specs/CLAUDE.md" \
				"requires lowercase words joined by single hyphens (e.g. 'specs-directory'," \
				"not '447' or 'Specs_Directory')" >&2
			errors=$((errors + 1))
		fi
		if is_change_type "$name"; then
			echo "ERROR: .specs/features/$name is a change type, not a feature — features/ splits" \
				"on lifecycle; the type already lives in the branch name and the commit prefix" \
				"(dotfiles-dev#442)" >&2
			errors=$((errors + 1))
		fi
		if [ ! -f "$entry/design.md" ] && [ ! -f "$entry/plan.md" ] &&
			[ ! -f "$entry/tasks.md" ]; then
			echo "ERROR: .specs/features/$name has none of design.md, plan.md or tasks.md" \
				"(pr.md alone is not a feature)" >&2
			errors=$((errors + 1))
		fi
		for member in "$entry"/[pP][rR].md "$entry"/[pP][rR][-_0-9]*.md; do
			if [ ! -f "$member" ]; then
				echo "ERROR: .specs/features/$name/$(basename "$member") is not a file" >&2
				errors=$((errors + 1))
				continue
			fi
			member_name="$(basename "$member")"
			if ! printf '%s' "$member_name" | grep -qE '^pr(-[0-9]+-[a-z0-9]+(-[a-z0-9]+)*)?\.md$'; then
				echo "ERROR: .specs/features/$name/$member_name is not pr.md or" \
					"pr-<N>-<kebab-slug>.md" >&2
				errors=$((errors + 1))
			fi
		done
		if [ -f "$entry/tasks.md" ]; then
			check_tasks_markers "$entry/tasks.md" ".specs/features/$name/tasks.md"
		fi
	done
fi

if [ -d "$SPECS_DIR/backlog" ]; then
	for entry in "$SPECS_DIR/backlog"/*; do
		[ -e "$entry" ] || continue
		name="$(basename "$entry")"
		[ "$name" = ".gitkeep" ] && [ -f "$entry" ] && continue
		if [ ! -f "$entry" ]; then
			echo "ERROR: .specs/backlog/$name is not a file — .specs/backlog/ is flat" >&2
			errors=$((errors + 1))
			continue
		fi
		if ! printf '%s' "$name" | grep -qE '^[a-z0-9]+(-[a-z0-9]+)*_[0-9]{8}_[0-9]{6}\.md$'; then
			echo "ERROR: .specs/backlog/$name does not match" \
				"<kebab-topic>_YYYYMMDD_HHMMSS.md — .specs/CLAUDE.md" >&2
			errors=$((errors + 1))
		fi
	done
fi

if [ "$errors" -gt 0 ]; then
	echo "check_specs_structure: $errors error(s) found." >&2
	exit 1
fi

echo "check_specs_structure: .specs/ layout is valid."
