"""Enforce runtime type-checking application across the whole ``src/`` package.

Runtime type checking (``_internal.utils.typing``) is **mandatory everywhere** — it
complements ruff ``ANN`` + mypy by turning annotated signatures into contracts that
fail loudly on values that cross a runtime boundary (deserialised data, DB rows). This
hook enforces the convention structurally, since neither ruff nor mypy can assert the
*presence* of a metaclass or decorator.

Rules, for every ``.py`` under ``src/`` (excluding the typing engine itself,
``**/typing/``). The doctrine is uniform — private helpers are checked too; the only
name-based skip is **dunders**, mirroring the ``TypeChecker`` metaclass which leaves
``__dunder__`` attributes untouched:

- **Standalone functions** (module-level, non-dunder) must be decorated with
  ``@type_checker``.
- **Classes** (top-level, non-dunder) that are **hierarchy roots** (declare no base
  class) must declare a checker metaclass (``TypeChecker`` / ``ABCTypeCheckerMeta`` /
  ``ProtocolTypeCheckerMeta``). A class *with* bases is left alone — Python inherits the
  metaclass, so a subclass of a checked class is already checked (e.g.
  ``LogsEmitter(LogEmitter)``).
- **Pydantic ``BaseModel`` subclasses** must **not** declare ``metaclass=TypeChecker`` —
  Pydantic owns the metaclass (conflict at import) and already validates at construction.

Every finding is a hard error (exit 1).
"""

import ast
import pathlib
import sys


# The metaclasses from ``_internal.utils.typing`` that apply runtime checking.
_CHECKER_METACLASSES = {"TypeChecker", "ABCTypeCheckerMeta", "ProtocolTypeCheckerMeta"}


def _is_dunder(name: str) -> bool:
    """Return whether a name is a Python dunder (``__x__``).

    Dunders are the one enforcement skip: the ``TypeChecker`` metaclass itself leaves
    ``__dunder__`` attributes untouched to avoid interfering with Python internals, so
    the hook mirrors that boundary rather than skipping all ``_``-prefixed names.

    Parameters
    ----------
    name : str
        The class or function name.

    Returns
    -------
    bool
        ``True`` when the name is a dunder.
    """
    return name.startswith("__") and name.endswith("__")


def _base_names(node: ast.ClassDef) -> set[str]:
    """Return the unqualified names of a class's base classes.

    Parameters
    ----------
    node : ast.ClassDef
        The class definition node.

    Returns
    -------
    set[str]
        Unqualified base-class names (``pydantic.BaseModel`` -> ``BaseModel``).
    """
    names: set[str] = set()
    for base in node.bases:
        if isinstance(base, ast.Name):
            names.add(base.id)
        elif isinstance(base, ast.Attribute):
            names.add(base.attr)
    return names


def _metaclass_name(node: ast.ClassDef) -> str | None:
    """Return the name given as ``metaclass=`` in a class header, if any.

    Parameters
    ----------
    node : ast.ClassDef
        The class definition node.

    Returns
    -------
    str or None
        The unqualified metaclass name, or ``None`` when none is declared.
    """
    for keyword in node.keywords:
        if keyword.arg != "metaclass":
            continue
        value = keyword.value
        if isinstance(value, ast.Name):
            return value.id
        if isinstance(value, ast.Attribute):
            return value.attr
    return None


def _decorator_names(node: ast.FunctionDef | ast.AsyncFunctionDef) -> set[str]:
    """Return the unqualified names of a function's decorators.

    Parameters
    ----------
    node : ast.FunctionDef or ast.AsyncFunctionDef
        The function definition node.

    Returns
    -------
    set[str]
        Unqualified decorator names (``@type_checker``, ``@a.b`` -> ``b``).
    """
    names: set[str] = set()
    for dec in node.decorator_list:
        if isinstance(dec, ast.Name):
            names.add(dec.id)
        elif isinstance(dec, ast.Attribute):
            names.add(dec.attr)
        elif isinstance(dec, ast.Call) and isinstance(dec.func, ast.Name):
            names.add(dec.func.id)
    return names


def _check_class(node: ast.ClassDef, filepath: str) -> int:
    """Check one public class for correct runtime-checker application.

    Parameters
    ----------
    node : ast.ClassDef
        The class definition node.
    filepath : str
        Source file (for messages).

    Returns
    -------
    int
        Number of hard errors for this class (0 or 1).
    """
    is_pydantic = "BaseModel" in _base_names(node)
    metaclass = _metaclass_name(node)
    if is_pydantic:
        if metaclass in _CHECKER_METACLASSES:
            print(
                f"❌ {node.name} at line {node.lineno} ({filepath}): a Pydantic model must not "
                f"set metaclass={metaclass} (metaclass conflict at import)."
            )
            return 1
        return 0
    # Metaclasses are inherited: only a hierarchy root (no base) must declare one.
    if node.bases:
        return 0
    if metaclass not in _CHECKER_METACLASSES:
        allowed = ", ".join(sorted(_CHECKER_METACLASSES))
        print(
            f"❌ {node.name} at line {node.lineno} ({filepath}): a root class must declare "
            f"metaclass=<one of: {allowed}> (runtime type checking)."
        )
        return 1
    return 0


def check_file(filepath: str) -> int:
    """Check runtime-checker application for every public class/function in a file.

    Parameters
    ----------
    filepath : str
        Path to a Python source file under ``src/``.

    Returns
    -------
    int
        Number of hard errors found in the file.
    """
    errors = 0
    with open(filepath, encoding="utf-8") as fh:
        tree = ast.parse(fh.read(), filename=filepath)
    for node in tree.body:
        if isinstance(node, ast.ClassDef) and not _is_dunder(node.name):
            errors += _check_class(node, filepath)
        elif (
            isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef)
            and not _is_dunder(node.name)
            and "type_checker" not in _decorator_names(node)
        ):
            print(
                f"❌ {node.name}() at line {node.lineno} ({filepath}): a standalone function must "
                f"be decorated with @type_checker (runtime type checking)."
            )
            errors += 1
    return errors


def _source_files() -> list[pathlib.Path]:
    """Collect every Python file under ``src/`` except the typing engine.

    Returns
    -------
    list[pathlib.Path]
        Python source files to check (``**/typing/`` is the engine, skipped).
    """
    return sorted(p for p in pathlib.Path("src").rglob("*.py") if "typing" not in p.parts)


if __name__ == "__main__":
    total_errors = sum(check_file(str(p)) for p in _source_files())
    sys.exit(1 if total_errors > 0 else 0)
