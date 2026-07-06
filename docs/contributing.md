# **Contributing**

Everything you need to develop, test, and release this library.

> **See also:** [Usage](usage.md) · [API Reference](api.md) · the repository's root
> `CONTRIBUTING.md` holds the authoritative branch/PR and commit-message policy.

---

## Setting up for development

The project ships both a `Makefile` and a parallel `tasks.sh`, so use whichever suits your
machine — **`make init`**, or **`bash tasks.sh init`** when `make` is unavailable (e.g. a stock
Windows shell).

```bash
make init        # seed .env, create the Poetry venv + install deps, install pre-commit hooks
# or, without make:
bash tasks.sh init
```

`init` composes `ensure_env` (seed `.env`), `venv` (create the Poetry virtualenv, install **all**
dependencies including dev + docs), and `precommit` (install the git hooks). Poetry is
auto-installed if missing.

## Tests and linting

```bash
make unit_tests          # poetry run pytest tests/unit/
make integration_tests   # poetry run pytest tests/integration/
make lint                # ruff + mypy + codespell + pydocstyle + shell/sql/yaml gates
```

CI runs the same gates on every pull request; keep them green locally before pushing.

## Verifying the built package

Before opening a release PR, confirm the wheel actually builds and imports — this catches
packaging mistakes (a missing `__init__`, an unshipped `_internal/` subpackage) that source-tree
tests never surface:

```bash
make install_dist_locally    # python -m build → install → smoke-import → report the built wheel
```

## Pull requests

1. Branch off the default branch following the prefix policy (`feat/…`, `fix/…`, …).
2. Fill out the PR template completely.
3. Ensure the CI checks (tests, lint, docs build) pass — they are the merge gate.

## Releasing

Releases are **tag-driven and secret-free** when the project is connected to a GitHub remote:

- The version is the **git tag** (via `poetry-dynamic-versioning`); `pyproject.toml` holds a
  `0.0.0` placeholder. Do not hand-edit it. Trigger a release from the Actions tab
  (`Release to PyPI` / `Release to Test PyPI`, `workflow_dispatch` with the version), or by pushing
  a `vX.Y.Z` tag.
- The release workflow runs the **full test suite** as a hard gate, builds with `python -m build`,
  and publishes via **OIDC trusted publishing** (`pypa/gh-action-pypi-publish`) — no stored
  `PYPI_TOKEN`.
- The changelog is regenerated from tags at release/build time (`make changelog` locally); CI never
  commits `CHANGELOG.md` back to the protected default branch.

### Maintainer setup — trusted publisher (one time, before the first release)

Register a **trusted publisher** on **both** [pypi.org](https://pypi.org) and
[test.pypi.org](https://test.pypi.org). Every claim must match the workflow exactly or the upload
fails with an opaque `invalid-publisher`:

| Claim | Value |
|-------|-------|
| Owner / repository | your GitHub `<owner>` / `<repo>` |
| Workflow filename | `release-pypi.yaml` (PyPI) / `release-test-pypi.yaml` (Test PyPI) |
| Environment | `release-pypi` / `release-test-pypi` |
| PyPI **Project Name** | must equal the distribution name (`name` in `pyproject.toml`) |

For the very first upload the project does not exist yet — register a **pending publisher** at the
account level (not under an existing project's settings). Publishing from a laptop instead of CI is
the one case that still needs an API token; OIDC works only from GitHub Actions.

### Choosing publish targets

The scaffold wires the release workflows for the official public registry (PyPI) and a staging
registry (Test PyPI). To publish to a **private / non-official** source instead — a git source
(`pip install git+https://…`), a private PEP 503 index, or (for ecosystems that support it) GitHub
Packages — wire the consumer-side source in `pyproject.toml` with an explicit-priority guard
against dependency confusion (`poetry`'s `priority = "explicit"`; `pip --index-url`, never
`--extra-index-url`).
