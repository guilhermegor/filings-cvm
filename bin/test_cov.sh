#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/lib/common.sh"

cd "$SCRIPT_DIR/.."

POETRY="bash $SCRIPT_DIR/poetry_exec.sh"

print_status info "pytest tests/unit/ --cov=src"
$POETRY run pytest tests/unit/ --cov=src

print_status info "coverage report"
$POETRY run coverage report -m

print_status info "coverage xml"
$POETRY run coverage xml -o coverage.xml

print_status info "coverage badge"
$POETRY run genbadge coverage --local -i coverage.xml -o coverage.svg

print_status success "coverage report and badge written"
