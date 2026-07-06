#!/usr/bin/env bash
# Package the committed tree of the default branch (main) into a clean,
# shareable zip. The archive reflects exactly what is committed to main — NOT
# the current working tree or branch — so uncommitted edits, untracked files,
# and work on other branches never leak into a shipped build. `git archive`
# already omits untracked and git-ignored paths; a defensive second pass prunes
# any heavy/secret path that was committed by mistake. The archive lands in
# SHIP_DIR (default ./dist) named <repo-kebab>_YYYYMMDD_HHMMSS.zip.
#
# Env vars:
#   SHIP_DIR      output directory for the zip (default ./dist)
#   SHIP_BRANCH   branch/ref to package (default: the repo's default branch)

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/lib/common.sh"

PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Paths never shipped even if a slip committed them: heavy, regenerable, secret,
# or environment-specific. (Untracked/git-ignored paths are already excluded by
# git archive; this list only guards against tracked mistakes.)
EXCLUDES=(
	".venv" "venv" "env" ".uv"
	"__pycache__" "*.py[cod]"
	".pytest_cache" ".ruff_cache" ".mypy_cache"
	"*.egg-info" "build" "dist"
	".coverage" "htmlcov"
	"repo_context.txt"
	"corporate_ca.pem"
	".env" ".env.local" ".env.dev" ".env.development"
	".env.test" ".env.staging" ".env.prod" ".env.production"
)

resolve_names() {
	# Derive the kebab-case project name and the timestamped archive base name.
	str_repo_name="$(basename "$PROJECT_ROOT")"
	str_repo_kebab="${str_repo_name//_/-}"
	str_stamp="$(date +%Y%m%d_%H%M%S)"
	str_archive_base="${str_repo_kebab}_${str_stamp}"
}

resolve_ship_ref() {
	# Resolve and validate the branch to package: SHIP_BRANCH if set, else the
	# repo's default branch (main/master). Fail fast when the branch is absent so
	# we never silently ship the wrong (or current) tree.
	str_ship_ref="$(resolve_default_branch "${SHIP_BRANCH:-}")"
	if ! git rev-parse --verify --quiet "refs/heads/$str_ship_ref" >/dev/null; then
		print_status "error" "Cannot ship: branch '$str_ship_ref' does not exist locally"
		exit 1
	fi
}

prune_excludes() {
	# Defensive second pass: drop any excluded path committed to the ref by
	# mistake. Patterns with a slash match by path; bare patterns match by name.
	local str_stage_dir="$1"
	local str_pattern
	for str_pattern in "${EXCLUDES[@]}"; do
		if [[ "$str_pattern" == */* ]]; then
			find "$str_stage_dir" -path "$str_stage_dir/$str_pattern" -prune \
				-exec rm -rf {} + 2>/dev/null || true
		else
			find "$str_stage_dir" -name "$str_pattern" -prune \
				-exec rm -rf {} + 2>/dev/null || true
		fi
	done
}

stage_copy() {
	# Extract the committed tree of str_ship_ref into the staging dir, then prune.
	local str_stage_dir="$1"
	print_status "info" "Staging committed tree of '$str_ship_ref' (excluding untracked, caches, secrets)..."
	mkdir -p "$str_stage_dir"
	git archive --format=tar "$str_ship_ref" | tar -x -C "$str_stage_dir"
	prune_excludes "$str_stage_dir"
}

copy_git_diffs() {
	# Bundle the working-tree git_diffs/ payload into the staged copy. It is
	# git-ignored (so `git archive` omits it), but in offline mode git_diffs/ IS
	# the branch-exchange payload — it must travel with the shipped zip so a
	# teammate can apply the diffs. No-op when the folder is absent or empty.
	local str_stage_dir="$1"
	if [[ -d "$PROJECT_ROOT/git_diffs" ]] && compgen -G "$PROJECT_ROOT/git_diffs/*" >/dev/null 2>&1; then
		print_status "info" "Bundling working-tree git_diffs/ (offline share payload)..."
		mkdir -p "$str_stage_dir/git_diffs"
		cp -a "$PROJECT_ROOT/git_diffs/." "$str_stage_dir/git_diffs/"
	fi
}

create_zip() {
	# Zip the staged copy (at str_stage_root/str_repo_kebab) into str_archive.
	local str_stage_root="$1"
	local str_archive="$2"
	mkdir -p "$(dirname "$str_archive")"
	print_status "info" "Zipping to $str_archive ..."
	(cd "$str_stage_root" && zip -q -r "$str_archive" "$str_repo_kebab")
}

main() {
	cd "$PROJECT_ROOT" || exit 1
	if ! command -v git >/dev/null 2>&1; then
		print_status "error" "git is required to ship (it packages the committed main tree)"
		exit 1
	fi
	if ! command -v tar >/dev/null 2>&1; then
		print_status "error" "tar is required to ship; install it (e.g. sudo apt install tar)"
		exit 1
	fi
	if ! command -v zip >/dev/null 2>&1; then
		print_status "error" "zip is required to ship; install it (e.g. sudo apt install zip)"
		exit 1
	fi

	resolve_names
	resolve_ship_ref

	local str_stage_root str_stage_dir str_ship_dir str_archive
	str_stage_root="$(mktemp -d)"
	# Guarantee the staging copy is removed even if zipping fails. Expand the path
	# into the trap NOW (not at EXIT) so it survives the local going out of scope
	# under `set -u`.
	# shellcheck disable=SC2064  # intentional immediate expansion (see above)
	trap "rm -rf '$str_stage_root'" EXIT

	str_stage_dir="$str_stage_root/$str_repo_kebab"
	str_ship_dir="${SHIP_DIR:-$PROJECT_ROOT/dist}"
	str_archive="$str_ship_dir/${str_archive_base}.zip"

	stage_copy "$str_stage_dir"
	[[ -d "$str_stage_dir" ]] || {
		print_status "error" "Staging failed"
		exit 1
	}
	copy_git_diffs "$str_stage_dir"
	create_zip "$str_stage_root" "$str_archive"

	print_status "success" "Shipped '$str_ship_ref': $str_archive"
}

main "$@"
