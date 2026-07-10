"""Enforce that every read through the contract seam is also provenance-stamped.

``read_table`` (the mandatory contract + dtype seam) and ``stamp_provenance`` (the ``url`` /
``updated_at`` / ``source_key`` / ``package_version`` / ``ingestion_run_id`` / ``content_hash``
columns every ingested frame carries) are two halves of a trustworthy bronze row: a read that
validates its source but forgets to stamp provenance yields data that can't be traced back to
where and when it came from. Ruff/mypy can't assert that the second call accompanies the first,
so this hook does — the provenance analogue of ``bin/check_typing.py``, and the companion to the
ruff ``TID251`` ban that already forces every read through ``read_table``.

Rule, for every ``.py`` under ``src/``: **a module that calls ``read_table`` must also call
``stamp_provenance``.** Modules that call neither (thin subclasses inheriting ``read``, the
seam-defining modules themselves) are unaffected. Every violation is a hard error (exit 1).
"""

import ast
import pathlib
import sys


_READ_FUNC = "read_table"
_STAMP_FUNC = "stamp_provenance"


def _called_names(tree: ast.Module) -> set[str]:
    """Return the unqualified names of every function called in a module.

    Parameters
    ----------
    tree : ast.Module
        The parsed module.

    Returns
    -------
    set[str]
        Unqualified callee names (``read_table(...)`` -> ``read_table``; ``a.b(...)`` -> ``b``).
    """
    names: set[str] = set()
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        if isinstance(func, ast.Name):
            names.add(func.id)
        elif isinstance(func, ast.Attribute):
            names.add(func.attr)
    return names


def check_file(filepath: str) -> int:
    """Check that a file calling ``read_table`` also calls ``stamp_provenance``.

    Parameters
    ----------
    filepath : str
        Path to a Python source file under ``src/``.

    Returns
    -------
    int
        Number of hard errors found in the file (0 or 1).
    """
    with open(filepath, encoding="utf-8") as fh:
        tree = ast.parse(fh.read(), filename=filepath)
    names = _called_names(tree)
    if _READ_FUNC in names and _STAMP_FUNC not in names:
        print(
            f"❌ {filepath}: calls {_READ_FUNC}() but never {_STAMP_FUNC}() — every ingested "
            f"frame must be provenance-stamped (url, updated_at, source_key, …) before return."
        )
        return 1
    return 0


def _source_files() -> list[pathlib.Path]:
    """Collect every Python file under ``src/``.

    Returns
    -------
    list[pathlib.Path]
        Python source files to check.
    """
    return sorted(pathlib.Path("src").rglob("*.py"))


if __name__ == "__main__":
    total_errors = sum(check_file(str(p)) for p in _source_files())
    sys.exit(1 if total_errors > 0 else 0)
