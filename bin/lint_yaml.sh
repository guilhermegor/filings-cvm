#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/lib/common.sh"
# shellcheck source=bin/lib/bootstrap.sh
source "$SCRIPT_DIR/lib/bootstrap.sh"

cd "$SCRIPT_DIR/.."

PYTHON="$(resolve_python)" || true
export PYTHON
if ! resolve_poetry; then
	print_status warning "skip: poetry/yamllint unavailable for YAML lint"
	exit 0
fi

print_status info "yamllint ."
run_poetry run yamllint .
print_status success "yamllint OK"
