# **API Reference**

Public interface for this library.

> **See also:** [Usage](usage.md)

---

## Module: `main`

Entry point module. Extend this with your library's public functions.

### `main() -> None`

Runs the library entry point. Replace the body with your top-level logic.

```python
from <package_name>.main import main

main()
```

---

## Adding new modules

Place new modules under `src/<package_name>/`. Export public symbols from `src/<package_name>/__init__.py` so callers can do:

```python
from <package_name> import my_function
```

Follow the one-class-per-file convention: utility functions with no shared state belong at module level, not wrapped in a class.

---

## Conventions

| Convention | Rule |
|------------|------|
| Type hints | Required on all public functions, including `-> None` return types |
| Docstrings | NumPy style; explain *why*, not *what* |
| Variable names | Type-prefixed (`str_`, `list_`, `cls_`, `dict_`, …) |
| Testing | `unittest`; one assertion per test; name as `test_<unit>_<scenario>_<expected>` |
