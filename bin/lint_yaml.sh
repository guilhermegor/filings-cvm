#!/usr/bin/env bash
#
# lint_yaml.sh — yamllint over the repo's YAML files.
#
# Single source of truth for YAML style linting: called by both `make lint` / `./tasks.sh
# lint` and the pre-commit `yamllint` hook. yamllint is a poetry dev-dep, so this is GUARDED
# on `command -v poetry` and SKIPPED gracefully (exit 0) when poetry is absent — a constrained
# box never hard-fails. When poetry IS present, yamllint's real exit status propagates (a true
# style failure fails the gate; it is never masked).

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/lib/common.sh"
# shellcheck source=bin/lib/bootstrap.sh
source "$SCRIPT_DIR/lib/bootstrap.sh"

cd "$SCRIPT_DIR/.."

# Resolve, don't install: an optional linter must not bootstrap Poetry. Resolve via the
# bootstrap lib (poetry -> python -m poetry) so a `python -m poetry`-only box is not
# silently skipped (the old `command -v poetry` guard saw only a bare `poetry`).
PYTHON="$(resolve_python)" || true
export PYTHON
if ! resolve_poetry; then
	print_status warning "skip: poetry/yamllint unavailable for YAML lint"
	exit 0
fi

print_status info "yamllint ."
run_poetry run yamllint .
print_status success "yamllint OK"
