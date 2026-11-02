#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/lib/common.sh"

main() {
	cd "$SCRIPT_DIR/.." || exit 1

	local -a list_poetry=(bash "$SCRIPT_DIR/poetry_exec.sh")

	print_status info "ruff check --fix"
	"${list_poetry[@]}" run ruff check --fix .

	print_status info "ruff format"
	"${list_poetry[@]}" run ruff format .

	print_status info "mypy (from src/)"
	(cd src && "${list_poetry[@]}" run mypy --config-file ../mypy.ini .)

	print_status info "codespell"
	"${list_poetry[@]}" run codespell .

	print_status info "pydocstyle"
	"${list_poetry[@]}" run pydocstyle .

	print_status info "docstring/signature agreement"
	"${list_poetry[@]}" run python bin/check_docstrings.py

	print_status info "runtime type-checker application"
	"${list_poetry[@]}" run python bin/check_typing.py

	print_status info "ingestion provenance stamp"
	"${list_poetry[@]}" run python bin/check_provenance.py

	print_status info "schema modules hold only pydantic models"
	"${list_poetry[@]}" run python bin/check_schemas.py

	print_status info "numeric dtype policy"
	"${list_poetry[@]}" run python bin/check_dtypes.py

	print_status info "shell"
	bash bin/lint_shell.sh

	print_status info "sql"
	bash bin/lint_sql.sh

	print_status info "yaml"
	bash bin/lint_yaml.sh

	print_status info "github actions"
	bash bin/lint_actions.sh

	print_status success "lint OK — every gate passed"
}

main "$@"
