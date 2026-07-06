# **Usage**

Examples for installing and using this library.

> **See also:** [API Reference](api.md)

---

## Installation

```bash
pip install <package-name>
```

Or with Poetry:

```bash
poetry add <package-name>
```

---

## Basic usage

```python
from <package_name>.main import main

main()
```

---

## Running from the Makefile

```bash
make start         # runs src/<package_name>/main.py via Poetry
```

---

## Running tests

```bash
make unit_tests         # unit tests only
make integration_tests  # integration tests only
make test_cov           # unit tests + coverage report + badge
```

---

## Linting and formatting

```bash
make lint          # ruff check + ruff format + codespell + pydocstyle
```

---

## Publishing to PyPI

Two GitHub Actions workflows handle releases (present when the repo has a GitHub remote):

- **`release-test-pypi.yaml`** — publish to [Test PyPI](https://test.pypi.org) first.
- **`release-pypi.yaml`** — publish to [PyPI](https://pypi.org) and cut a GitHub release.

Trigger either from the **Actions** tab (`workflow_dispatch`) with the version to release.
Both gate on the new version being greater than the latest already published, build with
Poetry, and fall back to `twine` if `poetry publish` is unavailable.

Configure once, in repository settings:

- Secrets `PYPI_TOKEN` and `TEST_PYPI_TOKEN` (API tokens from each index).
- A GitHub **Environment** named `release`.
