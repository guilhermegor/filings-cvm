#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/lib/common.sh"

cd "$SCRIPT_DIR/.."

POETRY="bash $SCRIPT_DIR/poetry_exec.sh"

print_status info "ruff check --fix"
$POETRY run ruff check --fix .

print_status info "ruff format"
$POETRY run ruff format .

print_status info "mypy (from src/)"
(cd src && bash "$SCRIPT_DIR/poetry_exec.sh" run mypy --config-file ../mypy.ini .)

print_status info "codespell"
$POETRY run codespell .

print_status info "pydocstyle"
$POETRY run pydocstyle .

print_status info "docstring/signature agreement"
$POETRY run python bin/check_docstrings.py

print_status info "shell"
bash bin/lint_shell.sh

print_status info "sql"
bash bin/lint_sql.sh

print_status info "yaml"
bash bin/lint_yaml.sh

print_status info "github actions"
bash bin/lint_actions.sh

print_status success "lint OK — every gate passed"
