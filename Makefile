# Every Poetry call routes through bin/poetry_exec.sh, which resolves Poetry
# (poetry -> python -m poetry) on THIS machine — so no recipe depends on a bare
# `poetry` being on PATH (which breaks after a `pip install --user` Poetry on
# Windows/Git Bash). Never call a bare `poetry` in a recipe.
POETRY := bash bin/poetry_exec.sh

# -------------------
# VIRTUAL ENVIRONMENT
# -------------------
.PHONY: init ensure_env venv update_venv precommit enable_pages changelog

init: ensure_env venv precommit enable_pages

# Seed .env from .env.example for a fresh checkout. The leading '-' makes a failed
# seed (e.g. no .env.example) non-blocking for init — venv + precommit still run.
ensure_env:
	-@bash bin/ensure_env.sh

venv:
	@bash bin/venv.sh

update_venv:
	@$(POETRY) update
	@echo "Poetry project updated"

# Pre-commit hook install lives in bin/precommit.sh so it can skip gracefully on a
# non-git deploy tree (a shipped zip with no .git) instead of aborting init.
precommit:
	@bash bin/precommit.sh

# Enable GitHub Pages (source = GitHub Actions) once, so the docs deploy workflow can publish.
# The workflow's GITHUB_TOKEN is a GitHub App token that CAN'T create the Pages site itself
# (first run fails "Resource not accessible by integration"); this uses the maintainer's gh
# auth. bin/enable_pages.sh is idempotent + non-blocking — it skips (never fails init) when gh
# is absent/unauthenticated or the caller isn't a repo admin, so contributors run it harmlessly.
enable_pages:
	@bash bin/enable_pages.sh

# Regenerate CHANGELOG.md from git tags + Conventional Commits (cz derives sections from tags).
# Preview locally; the published site regenerates it in the docs workflow. CI never commits it.
changelog:
	@$(POETRY) run cz changelog
	@echo "CHANGELOG.md regenerated"

# -------------------
# CORPORATE CA
# -------------------
.PHONY: get_corporate_ca

get_corporate_ca:
	@bash bin/get_corporate_ca.sh

# -------------------
# TESTING
# -------------------
.PHONY: unit_tests integration_tests test_cov test_cov_report test_cov_serve test_slowest test_feat test_urls_docstrings fix_playwright

unit_tests:
	@$(POETRY) run pytest tests/unit/

integration_tests:
	@$(POETRY) run pytest tests/integration/

test_cov:
	@$(POETRY) run pytest tests/unit/ --cov=src
	@$(POETRY) run coverage report -m
	@$(POETRY) run coverage xml -o coverage.xml
	@$(POETRY) run genbadge coverage -i coverage.xml -o coverage.svg

# Whole-tree HTML coverage for drill-down (never narrow --cov=<module>, which
# reports "no data" on the full suite). Open htmlcov/index.html or `make test_cov_serve`.
test_cov_report:
	@$(POETRY) run pytest tests/unit/ --cov=src --cov-report=term-missing --cov-report=html
	@echo "HTML coverage report at htmlcov/index.html"

test_cov_serve:
	@cd htmlcov && python3 -m http.server $${PORT:-8000}

test_slowest:
	@echo "Running tests to identify the 20 slowest tests..."
	@$(POETRY) run pytest tests/unit/ --durations=20 --tb=short

test_feat:
	@$(POETRY) run pytest tests/unit/ -k "$(FEAT)"

test_urls_docstrings:
	@bash bin/test_urls_docstrings.sh

fix_playwright:
	@bash bin/fix_playwright.sh

# -------------------
# LINTING
# -------------------
.PHONY: lint check_docstrings install_shell_linters

# Optional: install shellcheck + shfmt as SYSTEM binaries (choco/scoop/brew/apt).
# The primary route is pip (shellcheck-py/shfmt-py dev-deps via `poetry install`);
# this is only for boxes whose venv drive blocks executing the vendored binary.
install_shell_linters:
	@bash bin/install_shell_linters.sh

lint:
	@$(POETRY) run ruff check --fix .
	@$(POETRY) run ruff format .
	@cd src && bash ../bin/poetry_exec.sh run mypy --config-file ../mypy.ini .
	@$(POETRY) run codespell .
	@$(POETRY) run pydocstyle .
	@$(POETRY) run python bin/check_docstrings.py
	@bash bin/lint_shell.sh
	@bash bin/lint_sql.sh
	@bash bin/lint_yaml.sh

check_docstrings:
	@$(POETRY) run python bin/check_docstrings.py

# -------------------
# DATABASE
# -------------------
.PHONY: db_up db_backup db_restore

db_up:
	@bash bin/db.sh up

db_backup:
	@bash bin/db.sh backup

db_restore:
	@bash bin/db.sh restore

# -------------------
# RUN
# -------------------
.PHONY: run

run:
	@bash bin/run.sh

# -------------------
# CONTEXT
# -------------------
.PHONY: export_context

export_context:
	@bash bin/export_repo_content.sh

# -------------------
# SHIP
# -------------------
.PHONY: ship

ship:
	@bash bin/ship.sh

# -------------------
# DOCS
# -------------------
.PHONY: docs_server

docs_server:
	@$(POETRY) install --with docs
	@$(POETRY) run mkdocs serve -a 0.0.0.0:8000 --livereload

# -------------------
# HELP
# -------------------
.PHONY: help

help:
	@echo ""
	@echo "Usage: make <target>"
	@echo ""
	@echo "Virtual Environment"
	@echo "  init                 Seed .env, bootstrap venv, install pre-commit hooks"
	@echo "  ensure_env           Seed .env from .env.example if .env is missing"
	@echo "  venv                 Create Poetry venv and install dependencies"
	@echo "  update_venv          Update all Poetry dependencies"
	@echo "  precommit            Install pre-commit hooks (commit-msg + pre-push; skips off a git tree)"
	@echo "  enable_pages         Enable GitHub Pages (Actions source) once; needs gh + repo admin"
	@echo "  changelog            Regenerate CHANGELOG.md from git tags (cz changelog)"
	@echo ""
	@echo "Corporate CA"
	@echo "  get_corporate_ca     Extract a TLS-proxy CA into bin/corporate_ca.pem (corporate networks)"
	@echo ""
	@echo "Testing"
	@echo "  unit_tests           Run unit tests with pytest"
	@echo "  integration_tests    Run integration tests with pytest"
	@echo "  test_cov             Run unit tests with coverage report and badge"
	@echo "  test_slowest         Report the 20 slowest unit tests"
	@echo "  test_feat FEAT=<kw>  Run unit tests matching keyword <kw>"
	@echo "  test_urls_docstrings Check all URLs inside docstrings"
	@echo "  fix_playwright       Reinstall Playwright browsers"
	@echo ""
	@echo "Linting"
	@echo "  lint                 Run ruff, codespell, pydocstyle, check_docstrings"
	@echo "  check_docstrings     Check docstring type/raises consistency"
	@echo "  install_shell_linters  Install shellcheck + shfmt as system binaries (optional; pip is primary)"
	@echo ""
	@echo "Database"
	@echo "  db_up                Start Docker services, ensure schema, apply migrations"
	@echo "  db_backup            Dump the database to BACKUP_STORE_PATH"
	@echo "  db_restore DUMP=<p>  Restore database from a dump file at path <p>"
	@echo ""
	@echo "Docs"
	@echo "  docs_server          Serve MkDocs site locally at http://0.0.0.0:8000"
	@echo ""
	@echo "Library (only present for the library scaffold)"
	@echo "  install_dist_locally Build the wheel, install it, and smoke-import the package"
	@echo ""
	@echo "Run"
	@echo "  run                  Run src/main.py (auto-installs Poetry if missing)"
	@echo ""
	@echo "Context / Ship"
	@echo "  export_context       Flatten the repo into repo_context.txt for pasting into a web-UI LLM"
	@echo "  ship                 Package the committed main tree into dist/<name>_<ts>.zip"
	@echo ""
	@echo "Offline (only present when scaffolded without GitHub)"
	@echo "  new_branch NAME=<x>  Create a branch (feat/…, fix/…) off the default branch (main/master)"
	@echo "  git_merge_to_main    Merge the current clean branch into main/master and delete it"
	@echo "  git_diff_export              Export commits (DIFF_RANGE, default main..HEAD) to git_diffs/"
	@echo "  git_diff_check FILE=<path>   Check whether a .diff applies cleanly"
	@echo "  git_diff_apply FILE=<path>   Apply a .diff to the working tree (no commit)"
	@echo ""

# Library-only targets (install_dist_locally) — present only when scaffolded as a
# distributable library (lib-minimal). The leading '-' silently skips this when absent.
-include make/library.mk

# Offline-only targets (new_branch, git_merge_to_main, git_diff_*) — present only
# when scaffolded without GitHub. The leading '-' silently skips this when absent.
-include make/offline.mk
