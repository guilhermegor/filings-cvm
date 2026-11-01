# CLAUDE.md — bin/

Shell-script conventions for every `*.sh` in this directory.

## Shebang

- `#!/usr/bin/env bash` — user-facing scripts and any script that must be
  `$PATH`-portable (e.g. `venv.sh`, `run.sh`).
- `#!/bin/bash` — all other scripts (pre-commit hooks, CI helpers,
  internal utilities).

## Strict mode

```bash
set -euo pipefail
```

Use `set -e` (without `-u`/`-o pipefail`) only when the script reads
environment values that may be unset (e.g. `db.sh`, which loads `.env` values
via `_read_env_var` before applying defaults).

## Boilerplate (every script)

```bash
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# Optional: cd "$SCRIPT_DIR/.." to run from the project root
source "$SCRIPT_DIR/lib/common.sh"
```

## Cross-platform env resolution (`lib/bootstrap.sh`)

`lib/bootstrap.sh` is a sourced lib (like `lib/common.sh`) holding the
cross-platform setup logic shared by `venv.sh`, `run.sh`, and
`get_corporate_ca.sh`. It runs no work on source — the caller invokes
`bootstrap_init` first, then the helpers it needs:

| Function | Purpose |
|----------|---------|
| `bootstrap_init` | Resolve + export `OS_TYPE`, `PYTHON`, `PROJECT_ROOT`, `BIN_DIR`, `CORPORATE_CA_PEM`, `PY_VERSION`. Call once before the rest. `PYTHON` is a base interpreter found outside every active venv whenever one exists, so a bootstrap run through `poe`/`poetry run` never builds on the venv it may rebuild. |
| `running_inside_project_venv` | True when `VIRTUAL_ENV` or `PATH` puts the project `.venv` in use. `pip_fallback_recreate_project_venv` refuses to `rm -rf .venv` then, and pip installs drop `--user` when the interpreter is itself a venv. |
| `detect_os` | `linux` / `macos` / `windows` / `unknown` from `uname`. |
| `resolve_python` | First working of `python3` → `python` → `py`. |
| `resolve_poetry` / `run_poetry` | Populate the `POETRY_CMD` array (`poetry` or `python -m poetry`) and invoke it. |
| `ensure_poetry` | Resolve Poetry, installing the pinned version (`requirements.txt`) when absent. |
| `ensure_python_version` | **pyenv-preferred, system-Python fallback** — pin via pyenv when present, else use the system interpreter with a version-mismatch warning (for hosts where pyenv cannot be installed). |
| `wire_corporate_ca` | No-op unless `bin/corporate_ca.pem` exists; when it does, export `REQUESTS_CA_BUNDLE`/`SSL_CERT_FILE`/`CURL_CA_BUNDLE`/`PIP_TRUSTED_HOST`, append the CA to the certifi bundle, and point Poetry at it. |

Source both libs after `SCRIPT_DIR`, with a `source=` directive so shellcheck
can follow the second one:

```bash
source "$SCRIPT_DIR/lib/common.sh"
# shellcheck source=bin/lib/bootstrap.sh
source "$SCRIPT_DIR/lib/bootstrap.sh"
```

### The lib's Python companions — and why they are files

`bin/lib/` holds three `.py` helpers beside the shell libs that invoke them:

| File | Invoked by | Interface |
|------|-----------|-----------|
| `lib/ca_bundle.py` | `bootstrap.sh::build_union_ca_bundle` | `BX_CA_CORPORATE` + `BX_CA_OUT` in; certificate count out; non-zero when the union would NARROW the trust store |
| `lib/pip_requirements.py` | `pip_fallback.sh::pip_fallback_emit_pip_requirements_from_pyproject` | `PROJECT_ROOT` + `BX_GROUPS` in; one pip requirement per line out |
| `lib/wheelhouse_select.py` | `build_wheelhouse.sh` (`poe wheelhouse` / `poe wheelhouse_assemble`) | subcommands `select`/`pack`/`assemble` — see `docs/offline-wheelhouse.md` |
| `lib/description_sources.py` | `check_description_sync.sh` | subcommands `manifest ROOT` / `mkdocs FILE`; description on stdout; exit 3/4 when the source is absent, 5 when it is present but unreadable |

`ca_bundle.py` and `pip_requirements.py` were `"$PYTHON" - <<'PYEOF'` heredocs inside their shell functions — 151 and 66
lines of Python that **no Python tool could see**: ruff never linted them, mypy never
checked them, pytest could not import them, and an editor rendered them as one long
string. The 60-line function gate flagged the enclosing shell functions at 155 and 73
lines; the length was the symptom and the invisibility was the disease. Extracting them
surfaced three real ruff findings on the first run.

⚠️ **A shell lib and its `.py` companion travel together.** Copying `bootstrap.sh`
alone now yields a lib that cannot run — which the integration suite caught immediately,
because its fixture globbed only `*.sh`. Anything that materialises `bin/lib/` must take
both extensions.

⚠️ **Do not push new logic back into a heredoc.** A heredoc is right for inert text a
script *emits*; the moment it is fed to an interpreter it is a program, and a program
belongs in a file its language's tooling can read.

`bin/help.txt` is **gone**, and its lesson is now enforced by construction rather than by a
rule. It existed because the command list lived in two places — a heredoc in `tasks.sh` and
~65 `@echo` lines in the `Makefile` — kept in sync by a CLAUDE.md paragraph, and they had
already drifted: `make help` was missing `test_cov_report` and `test_cov_serve` entirely, so
two real targets were undiscoverable from the entry point most people use (blueprintx#189).
Single-sourcing the text fixed the symptom. The poe migration removed the cause: bare `poe`
builds its listing from each task's own `help =` field, so the help and the recipe are one
declaration and cannot disagree. The rule that replaces the sync rule is simply: every task
carries a `help =`.

`get_corporate_ca.sh` is the **manual** generator for `bin/corporate_ca.pem` — it
disables TLS verification *on purpose* to capture a TLS-inspecting proxy's CA,
so run it only on such a network. The pem is git-ignored; its mere presence
opts a project into corporate-SSL mode on the next `poe venv` / `poe run`.

## Resolve Poetry — never call a bare `poetry`

A `pip install --user` Poetry (the venv fallback on Windows/Git Bash) is reachable
only as `python -m poetry` — the user-scripts dir is not on `PATH` — so a bare
`poetry …` dies "command not found" even after `venv` succeeds. **Every Poetry call
must route through the resolver.** How each surface routes:

| Surface | How it calls Poetry |
|---------|---------------------|
| a `poe_tasks.toml` task / `.pre-commit-config.yaml` | `bash bin/poetry_exec.sh <args>` — the wrapper resolves+`exec`s Poetry, routing resolution status to **stderr** so `$(… version -s)` stays clean |
| sourcing `bin/*.sh` that needs Poetry (`db.sh`, `fix_playwright.sh`, `precommit.sh`) | source `lib/bootstrap.sh`, `bootstrap_init` + `ensure_poetry`, then `run_poetry run …` |
| optional-linter `bin/*.sh` (`lint_sql.sh`, `lint_yaml.sh`, `lint_shell.sh`) | **resolve, don't install**: `resolve_python` → `resolve_poetry \|\| skip (exit 0)` → `run_poetry run …`. Never guard on `command -v poetry` (it misses a `python -m poetry`-only box and skips silently) |

**Pip-vendored lint CLIs (`shellcheck`, `shfmt`) resolve via `poetry run`, not bare
PATH.** `shellcheck-py`/`shfmt-py` are dev-deps that vendor their binaries into the
venv (incl. `win_amd64` wheels), so `lint_shell.sh` tries `poetry run <tool>` first
(found wherever the venv lives, incl. a Windows UNC/mapped `A:` drive), then a system
binary, then skips — probing with `--version` so a real lint failure is never mistaken
for "absent". A bare-PATH `command -v` would silently skip both linters when `poe lint`
runs outside the venv. `bin/install_shell_linters.sh` (`poe install_shell_linters`) is
an **optional** system-binary installer (choco/scoop/brew/apt) for boxes whose venv drive
blocks executing the vendored binary; the pip route is primary.

`bin/export_deps.sh` (`poe export_deps`) exports the locked set to `requirements-lock.txt`
for pip-only hosts. It is the reference for the **diagnostic half** of this rule: it captures
the export output instead of discarding it, re-prints Poetry's own words on failure, and names
the remedy against `${POETRY_CMD[*]}` — never a bare `poetry`, which may not be the install
that failed. `export` is a *plugin* subcommand, so `requirements.txt` pins
`poetry-plugin-export` beside Poetry: the audit question is never "is Poetry installed?" but
"which install resolves when `.venv/bin` is NOT on `PATH`, and does that one have the
subcommand?".

`bin/ensure_env.sh` seeds `.env` from `.env.example` for `init` (no-op if `.env`
exists; an info-line no-op when the tier ships no template). `bin/precommit.sh` installs the
pre-commit hooks and **skips gracefully** when run off a git work tree (a shipped zip
with no `.git`) so `init` still completes.

## Testing shell scripts

A bash script has no conventional unit test, so map the tests-with-every-change rule:

- **Unit gate** = `shellcheck --severity=warning --exclude=SC1091` + `bash -n` (run by
  `bin/lint_shell.sh` / the `lint-shell` pre-commit hook). State this explicitly when a
  shell change ships without a Python unit test — it is a documented choice, not an omission.
- **Integration** = invoke the script via `subprocess` and assert observable behaviour
  (exit code, a created file/dir, a status line). Resolve bash with `shutil.which("bash")
  or "bash"`, build a constant trusted argv, scope-ignore bandit `S603` with a reason, and
  self-skip when a dependency is unavailable offline. See
  `tests/integration/test_bin_scripts.py` for the reference example.

## A GATE fails closed. A JANITOR must not — and that is not failing open

Most scripts in `bin/` are **gates**: they answer "may this proceed?", so an error must exit
non-zero. A few are **janitors** — they clean up after a verdict someone else reached
(`rerun_stale_gate_runs.sh` re-runs the stale failed runs that still block a PR). A janitor
that fails the step **manufactures the very artifact it came to remove**: a failed CI job is
one more red run in the rollup the cleanup exists to clear.

So a janitor reports loudly and returns 0 — via `print_status "warning"` plus a
`::warning::` annotation so it surfaces in the run summary.

⚠️ **This is the one place the repo's fail-closed default is deliberately inverted, so state
the test rather than the exception.** Ask: *when this exits 0 having done nothing, is anything
hidden?* For a gate the answer is yes — an unchecked condition passes silently, which is the
failure this whole directory exists to prevent. For a janitor the answer is no: the block it
failed to clear is still there, still red, still blocking, fully visible. **Exiting 0 is only
acceptable when the untouched status quo is itself the visible signal.** If a janitor's
failure would leave the tree *looking* clean, it is a gate wearing a janitor's coat — fail it.

⚠️ **A janitor is exactly where a false all-clear hides**, because nobody reads a cleanup
step's log. Measured (blueprintx#263): the first draft used
`mapfile -t list < <(list_stale_failed_runs …)`, which **discards the producer's exit status**
and reports only mapfile's own — so a failing `gh api` yielded an EMPTY list and the script
announced *"the rollup is already clean"* over a query that never ran. Capture to a string
with an explicit status check instead, and never let "found nothing" and "could not look"
print the same sentence. `bin/lint_docker.sh` documents the same trap at its own discovery
call — read the siblings before writing a new discovery.

## Structure

All logic goes in named functions. A `main()` function wires them together
and is called at the bottom of the file:

```bash
main() {
    step_one
    step_two
}

main "$@"
```

### Explanatory comments belong in docs, not in the function body

`bin/check_function_length.py` caps a function at **60 lines of code** and subtracts the
**docstring** — and nothing else. Every explanatory comment inside the body counts. In a
codebase whose house style is a long ⚠️ block explaining why measured reality contradicts
the obvious reading, that means the better you document a change, the likelier the gate
rejects it — and the reflex fix is to delete the reasoning, which is the one thing worth
keeping.

So: anything explaining a **policy**, a **supersede**, a measured **trade-off**, or why a
whole approach was rejected belongs in `docs/` or the function's docstring (which the
budget subtracts). Delete the comment and leave no pointer: BlueprintX's ruling
(blueprintx#304) is that a hoisted block and a one-line pointer both rot.

Measured (blueprintx#264): `find_thread_problems` hit 62 lines and `main` 63 with **no
logic change** in either — comments alone. Both fell well under after hoisting, and no
prose was lost.

⚠️ **Do not "fix" this by making the gate subtract comments.** A 200-line function is
unreadable whether the lines are code or commentary, and a gate that excludes comments is
defeated by commenting out the body. The ceiling is about what one reader holds in their
head at once, and a comment is something they read.

### Decision records move to docs, not a changelog inside the comment

(blueprintx#239.) The signal for a comment to go is a `SUPERSEDED …` block: a
comment that narrates what the line *used to* say and why that reasoning was replaced,
i.e. a changelog living inside the file. Git, the issue, and the PR body already keep that
history rigorously, which is exactly why the comment is redundant rather than precious.

The rule: a narrative of what the line used to say belongs in the issue or PR, and the
comment is deleted.
No pointer is left behind (blueprintx#304). A
measurement that justifies today's value moves to docs the same way. Only QA-suppression
comments (`noqa`, `complexity-ok`, `type: ignore`, `codespell:ignore`) stay, with their reason.

## Status output

Use `print_status <level> <message>` (from `lib/common.sh`) for all
user-facing output. Never use bare `echo`/`printf` for status messages.

| Level     | Use for                        | Routing |
|-----------|--------------------------------|---------|
| `success` | completed action               | stdout  |
| `error`   | failure the user must see      | stderr  |
| `warning` | recoverable / skipped state    | stdout  |
| `info`    | progress narration             | stdout  |
| `config`  | a chosen setting being applied | stdout  |
| `debug`   | verbose diagnostics            | stdout  |
| `section` | banner separating major phases | stdout  |

Plain data the caller will capture (a path, a resolved value) may still go
to stdout via `echo`/`printf` — the rule is about *status*, not all output.

## Reading `.env` values

Use `_read_env_var VAR_NAME` (from `lib/common.sh`) to read a variable
from `.env` directly. This bypasses Make's `$` and `#` expansion, which
corrupts passwords containing those characters.

```bash
str_db_password
str_db_password=$(_read_env_var DB_PASSWORD)
```

## Docstring URL convention (the `check-urls` hook)

`bin/test_urls_docstrings.sh` (pre-commit `check-urls`) fetches every
`https://…` URL it finds in a docstring and fails on any 3xx/4xx — it does
**not** follow redirects. So never put a *fetchable* example URL in a
docstring: doctest-style fakes (`https://hooks.slack.com/services/T000/…` →
404) and truncated real links (`…/l/channel/19%3A…` → 302) will block the
commit. The hook **skips host-only URLs** (regex `https?://[^/]+$`), so write
examples as bare hosts (`https://hooks.slack.com`) and refresh any stale doc
URL to its current 200 home.

## SC2155 — split `local x` from `x=$(…)`

`local x=$(cmd)` swallows `cmd`'s exit code. Declare then assign:

```bash
# ❌ exit code masked
local str_result=$(some_command)

# ✅ failures are visible
local str_result
str_result=$(some_command)
```

## Lint gate

CI runs the following before merging:

```bash
shellcheck --severity=warning --exclude=SC1091 bin/*.sh bin/lib/*.sh
bash -n bin/*.sh bin/lib/*.sh
```

`SC1091` (can't follow sourced file) is excluded globally because scripts
source siblings at runtime paths shellcheck cannot resolve. Any other
`# shellcheck disable=` must be line-scoped and carry a one-line reason comment.
