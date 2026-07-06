# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this template is

A **PyPI-ready Python library starter**. A clean, importable package with CI, pre-commit,
tests, docs, and PyPI + Test-PyPI release workflows ready to go. It is scaffolded by
BlueprintX into a new project directory; the scaffold replaces the `<project_name>` package
directory and the `pyproject.toml` placeholders via `envsubst`.

## Layout

```
src/<project_name>/
    __init__.py            # the public API surface (control it with __all__)
    main.py                # library core / entry point — rename or split as it grows
    _internal/             # PRIVATE — ships in the wheel, but not a public API
        utils/             # vendored helpers (dtypes, tabular_reader, retry, http_downloader,
                           #   text, zip_extractor, br_identifiers, typing/)
        config/
            contracts/     # FileContract declarations (one per input source)
tests/
    unit/  integration/  performance/
```

**Public vs private.** Consumers import `<project_name>` (your core). Everything under
`<project_name>._internal` is vendored support code: it ships inside the wheel (so imports
resolve after `pip install`), but the leading underscore marks it off-limits — keep it out
of your public `__all__`. The internal imports are package-qualified
(`from <project_name>._internal.utils.dtypes import …`).

## Architecture

- **One public class per module/file.** The public class is named after the file
  (`user_service.py` → `UserService`). When helpers share no state and need no lifecycle,
  prefer **module-level functions** over a utility class. A private/shared base class gets
  its **own** `_`-prefixed file (`_base_reader.py`) — never share a module with a public
  class.
- **Separate I/O from logic**: pure functions in the core, side effects at the edges.
- Reach for a class only when there is **state + lifecycle**, **interface conformance**, or
  **dependency injection** — otherwise a module of functions is the right shape.
- **No redundant package-name subfolder.** When the package's whole purpose is one domain
  (e.g. `calendars`), do **not** nest a subfolder that repeats the package name
  (`src/<project_name>/<project_name>-ish/`) — the package name already conveys the scope. Keep
  public modules **flat** at `src/<project_name>/` (`src/<project_name>/calendar_br.py`), and put
  non-exported abstract bases / internals under `_internal/`.
- **On migration, reuse the target's own implementation.** When lifting code in from another
  repo, if this project already has an equivalent module (its own `_internal` typing engine, a
  helper), rewrite the imports to **this** project's version and discard the source's duplicate —
  never vendor a second copy (DRY). The scaffold's own `rewrite_internal_imports` embodies this.

## Conventions (inherited from `templates/python-common/`)

- **Ruff**: linter + formatter. Line-length 99, tab indent, double quotes, NumPy docstrings.
- **Pre-commit**: ruff, pydocstyle, codespell, commitizen, gitlint, unit + integration
  tests, coverage badge.
- **Tests**: `pytest` — `make unit_tests` (`poetry run pytest tests/unit/`). Write
  pytest-style functions with fixtures, not `unittest.TestCase`.
- **Explicit column typing & Brazilian identifiers** — if the library touches pandas, type
  every DataFrame on load via `apply_dtypes` (`_internal.utils.dtypes`, never pandas'
  inference), route reads through `_internal.utils.tabular_reader`, and use
  `_internal.utils.br_identifiers` for CNPJ/CPF (alphanumeric-aware for the 2026 CNPJ).
- **No `.env`** — a distributable library has no runtime env to seed (unlike the service
  tiers), so none is shipped.
- **Logging via dependency injection** — never hard-import a logging backend in a helper;
  inject a logger (stdlib default), as `_internal/utils/retry.py`'s `LogEmitter` shows. The
  in-repo `logs.py` helper is **opt-in** at scaffold time; see `_internal/utils/CLAUDE.md`.
- **Every imported package is a direct dependency.** If a module `import`s a package, declare
  it in `pyproject.toml` — even when it is already installed transitively via another dep. A
  transitive presence is an accident of another package's tree and breaks silently the day that
  package drops or version-caps it. Run `poetry add <pkg>` for anything you import.

## Releasing to PyPI

Two workflows ship under `.github/workflows/` (present only when a GitHub remote is set up):

- `release-test-pypi.yaml` — publish to **Test PyPI** first (`workflow_dispatch`).
- `release-pypi.yaml` — publish to **PyPI** and cut a GitHub release.

Both gate on the version being greater than what is already published, build with Poetry,
and fall back to `twine` if `poetry publish` is unavailable. Configure these repository
secrets and a GitHub Environment named **`release`**:

- `PYPI_TOKEN` — a PyPI API token.
- `TEST_PYPI_TOKEN` — a Test PyPI API token.

## Extending this template

- Keep `src/<project_name>/` as the importable package root; grow the public API there.
- Add sub-packages as the project grows — do not dump everything into `main.py`.
- Mirror the test folder hierarchy to match the package structure.
- Drop `_internal/config/contracts` (and the pandas deps) if the library never reads
  tabular inputs.
