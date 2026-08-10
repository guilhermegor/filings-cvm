#!/usr/bin/env bash
#
# lint_actions.sh — actionlint over the repository's GitHub Actions workflows.
#
# Single source of truth for WORKFLOW SCHEMA linting: called by `make lint_actions` /
# `./tasks.sh lint_actions`, the pre-commit `lint-actions` hook, and the CI step.
#
# WHY THIS EXISTS, AND WHY yamllint IS NOT IT. yamllint validates YAML; it says nothing
# about whether the document is a workflow GitHub will run. Measured in #217: a `on:`
# block declaring `pull_request_review_thread` (a real WEBHOOK event, but NOT a workflow
# trigger) passed yamllint and every other hook, and GitHub then rejected the file whole —
# run 31335491644, "This run likely failed because of a workflow file issue". The failure
# is not partial: the workflow does not run AT ALL, so the PR silently gets no labels and
# no gate comment, which reads as a merely slow gate. actionlint catches it by name
# (`unknown Webhook event`).
#
# RESOLVE, DON'T INSTALL — the same contract as lint_shell.sh / lint_yaml.sh: prefer the
# venv (`poetry run actionlint`, if someone pip-installed actionlint-py), fall back to a
# system binary, and SKIP LOUDLY (exit 0 + warning) when neither exists, so a constrained
# box never hard-fails the commit flow. A real lint failure always propagates.
#
# ⚠️ actionlint is deliberately NOT a poetry dev-dep. `actionlint-py` publishes an
# sdist ONLY (no wheels), and its build step downloads the Go binary from GitHub — so
# adding it would make every `poetry install`, on all three CI matrices, depend on a
# network fetch at BUILD time. shellcheck-py/shfmt-py ship real wheels; this one does not,
# and the difference is what decides it. CI therefore installs the binary explicitly
# (see .github/workflows/tests.yaml) so the gate can never silently skip where it counts.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/lib/common.sh"
# shellcheck source=bin/lib/bootstrap.sh
source "$SCRIPT_DIR/lib/bootstrap.sh" # resolve_python / resolve_poetry / run_poetry

bool_poetry_ok=false

# Resolve how to launch actionlint: "poetry" (vendored in the venv), "system" (on PATH),
# or "" when absent. Probes with --version so a real lint exit code is never mistaken for
# "absent" — the failure mode that turns a gate into a placebo.
resolve_actionlint_mode() {
	if [[ "$bool_poetry_ok" == true ]] && run_poetry run actionlint --version >/dev/null 2>&1; then
		printf 'poetry'
		return 0
	fi
	if command -v actionlint >/dev/null 2>&1; then
		printf 'system'
		return 0
	fi
	printf ''
}

run_actionlint() {
	local str_mode
	str_mode="$(resolve_actionlint_mode)"
	if [[ -z "$str_mode" ]]; then
		print_status warning "skip: actionlint absent — install from https://github.com/rhysd/actionlint (CI installs a pinned binary and FAILS if absent)"
		return 0
	fi
	print_status info "actionlint [$str_mode]: ${#list_files[@]} workflow(s)"
	# actionlint shells out to shellcheck for every `run:` block, and shellcheck honours
	# SHELLCHECK_OPTS. Pin it to the SAME severity the repo's own shell gate uses
	# (bin/CLAUDE.md: warning-and-above) — otherwise the workflows would be held to a
	# STRICTER bar than bin/*.sh, on `info`/`style` notes about inline snippets. This is
	# alignment with the existing standard, not a relaxation: it changed nothing about the
	# schema errors, which are what this gate exists for.
	export SHELLCHECK_OPTS="${SHELLCHECK_OPTS:---severity=warning}"
	# The workflows are passed BY NAME rather than letting actionlint discover them: a
	# discovery run that matches nothing exits 0, and a gate that can pass vacuously is
	# worse than none. The empty case is caught before we get here.
	if [[ "$str_mode" == poetry ]]; then
		run_poetry run actionlint "${list_files[@]}"
	else
		actionlint "${list_files[@]}"
	fi
	print_status success "actionlint OK"
}

main() {
	cd "$SCRIPT_DIR/.."

	# Resolve Poetry once (resolve, never install). PYTHON feeds the `python -m poetry`
	# fallback inside resolve_poetry.
	PYTHON="$(resolve_python 2>/dev/null)" || true
	export PYTHON
	if resolve_poetry; then
		bool_poetry_ok=true
	fi

	# The parentheses are load-bearing: `-o` binds LOOSER than the implicit `-a`, so
	# `-name '*.yaml' -o -name '*.yml' -type f` parses as
	# `(-name '*.yaml') OR (-name '*.yml' AND -type f)` — the `-type f` guards only the
	# second branch, and a DIRECTORY named `*.yaml` under .github/workflows would enter the
	# list and make actionlint fail on it. Reproduced before fixing.
	mapfile -t list_files < <(find .github/workflows \( -name '*.yaml' -o -name '*.yml' \) -type f)
	if [[ ${#list_files[@]} -eq 0 ]]; then
		print_status error "no workflows found under .github/workflows — refusing to pass vacuously"
		exit 1
	fi

	run_actionlint
}

main "$@"
