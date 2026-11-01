#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/lib/common.sh"
# shellcheck source=bin/lib/bootstrap.sh
source "$SCRIPT_DIR/lib/bootstrap.sh"

cd "$SCRIPT_DIR/.."

str_queries="src/config/queries"

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
