#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/lib/common.sh"

main() {
	cd "$SCRIPT_DIR/.." || exit 1

	local -a list_poetry=(bash "$SCRIPT_DIR/poetry_exec.sh")

	print_status info "pytest tests/unit/ --cov=src"
	"${list_poetry[@]}" run pytest tests/unit/ --cov=src

	print_status info "coverage report"
	"${list_poetry[@]}" run coverage report -m

	print_status info "coverage xml"
	"${list_poetry[@]}" run coverage xml -o coverage.xml

	print_status info "coverage badge"
	"${list_poetry[@]}" run genbadge coverage --local -i coverage.xml -o coverage.svg

	print_status success "coverage report and badge written"
}

main "$@"
