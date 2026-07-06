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
| `bootstrap_init` | Resolve + export `OS_TYPE`, `PYTHON`, `PROJECT_ROOT`, `BIN_DIR`, `CORPORATE_CA_PEM`, `PY_VERSION`. Call once before the rest. |
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

`get_corporate_ca.sh` is the **manual** generator for `bin/corporate_ca.pem` — it
disables TLS verification *on purpose* to capture a TLS-inspecting proxy's CA,
so run it only on such a network. The pem is git-ignored; its mere presence
opts a project into corporate-SSL mode on the next `make venv` / `make run`.

## Resolve Poetry — never call a bare `poetry`

A `pip install --user` Poetry (the venv fallback on Windows/Git Bash) is reachable
only as `python -m poetry` — the user-scripts dir is not on `PATH` — so a bare
`poetry …` dies "command not found" even after `venv` succeeds. **Every Poetry call
must route through the resolver.** How each surface routes:

| Surface | How it calls Poetry |
|---------|---------------------|
| `Makefile` / `tasks.sh` / `.pre-commit-config.yaml` | `bash bin/poetry_exec.sh <args>` — the wrapper resolves+`exec`s Poetry, routing resolution status to **stderr** so `$(… version -s)` stays clean |
| sourcing `bin/*.sh` that needs Poetry (`db.sh`, `fix_playwright.sh`, `precommit.sh`) | source `lib/bootstrap.sh`, `bootstrap_init` + `ensure_poetry`, then `run_poetry run …` |
| optional-linter `bin/*.sh` (`lint_sql.sh`, `lint_yaml.sh`, `lint_shell.sh`) | **resolve, don't install**: `resolve_python` → `resolve_poetry \|\| skip (exit 0)` → `run_poetry run …`. Never guard on `command -v poetry` (it misses a `python -m poetry`-only box and skips silently) |

**Pip-vendored lint CLIs (`shellcheck`, `shfmt`) resolve via `poetry run`, not bare
PATH.** `shellcheck-py`/`shfmt-py` are dev-deps that vendor their binaries into the
venv (incl. `win_amd64` wheels), so `lint_shell.sh` tries `poetry run <tool>` first
(found wherever the venv lives, incl. a Windows UNC/mapped `A:` drive), then a system
binary, then skips — probing with `--version` so a real lint failure is never mistaken
for "absent". A bare-PATH `command -v` would silently skip both linters when `make lint`
runs outside the venv. `bin/install_shell_linters.sh` (`make install_shell_linters`) is
an **optional** system-binary installer (choco/scoop/brew/apt) for boxes whose venv drive
blocks executing the vendored binary; the pip route is primary.

`bin/ensure_env.sh` seeds `.env` from `.env.example` for `init` (no-op if `.env`
exists; aborts only itself on a missing template). `bin/precommit.sh` installs the
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
