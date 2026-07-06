#!/usr/bin/env bash
#
# lint_sql.sh — sqlfluff over the project's SQL query files.
#
# Single source of truth for SQL linting: called by both `make lint` / `./tasks.sh lint`
# and the pre-commit `lint-sql` hook. Lints every `.sql` under src/config/queries with the
# default dialect from .sqlfluff (sqlfluff honours .sqlfluffignore for runtime-templated
# queries). sqlfluff is a poetry dev-dep, so this is GUARDED on `command -v poetry` and
# SKIPPED gracefully (exit 0) when absent — a constrained box never hard-fails.
#
# Mixing engines? Encode the db in each query's filename prefix and run one sqlfluff pass
# per --dialect here (see the .sqlfluff header comment).

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/lib/common.sh"
# shellcheck source=bin/lib/bootstrap.sh
source "$SCRIPT_DIR/lib/bootstrap.sh"

cd "$SCRIPT_DIR/.."

str_queries="src/config/queries"

# Resolve, don't install: an optional linter must not bootstrap Poetry. Resolve via the
# bootstrap lib (poetry -> python -m poetry) so a `python -m poetry`-only box is not
# silently skipped (the old `command -v poetry` guard saw only a bare `poetry`).
PYTHON="$(resolve_python)" || true
export PYTHON
if ! resolve_poetry; then
	print_status warning "skip: poetry/sqlfluff unavailable for SQL lint"
	exit 0
fi

if [[ ! -d "$str_queries" ]] || [[ -z "$(find "$str_queries" -name '*.sql' -type f -print -quit)" ]]; then
	print_status info "no .sql files under $str_queries — skipping"
	exit 0
fi

print_status info "sqlfluff lint $str_queries"
run_poetry run sqlfluff lint "$str_queries"
print_status success "sqlfluff OK"
