"""Enforce that a package's ``__all__`` names every public member its submodules define.

A convention that every member of a family must follow deserves an executable check, not a
doc paragraph. The usual shape of that check is an introspective test that **discovers the
family through ``__all__``** and asserts something about each member — and that shape has a
hole it cannot see: **a member missing from ``__all__`` is invisible to it.** The sweep simply
returns one fewer item, `parametrize` generates one fewer case, and the suite passes by not
looking.

Measured (filings-cvm#164): three readers registered by an anchor-replace landed in the import
block but never in ``__all__``. They were importable, unexported, and every test was green.
The sibling failure is worse: narrowing an ``__all__`` **empties** every gate that discovers
through it — 2182 → 1311 tests with no new failure, four gates silently inert.

So this walks the FILES, not the exports. For every package whose ``__init__.py`` declares
``__all__``, it collects the public module-level names its sibling submodules define and fails
on any that the list omits.

Scope is opt-in by design: a package with no ``__all__`` is not checked. Declaring an export
list is the promise; this enforces it. Reading is done with ``ast`` — never by importing —
so the gate has no side effects and needs no dependency installed.

⚠️ Discovery matching **zero** packages is a FAILURE, not a pass. A gate that scanned nothing
also found nothing wrong, and exits 0 forever the day a path is renamed.
"""

import ast
import pathlib
import sys


_SRC = pathlib.Path("src")
_EXCLUDED_PARTS = frozenset({"typing", "__pycache__", "example_feature"})


def declared_all(path_init: pathlib.Path) -> list[str] | None:
    """Return the names in a module's ``__all__``, or ``None`` when it declares none.

    Parameters
    ----------
    path_init : pathlib.Path
        The ``__init__.py`` to read.

    Returns
    -------
    list of str or None
        The exported names, or ``None`` when the module has no ``__all__``.
    """
    cls_tree = ast.parse(path_init.read_text(encoding="utf-8"))
    for cls_node in cls_tree.body:
        if not isinstance(cls_node, ast.Assign):
            continue
        for cls_target in cls_node.targets:
            if isinstance(cls_target, ast.Name) and cls_target.id == "__all__":
                if not isinstance(cls_node.value, ast.List | ast.Tuple):
                    return []
                return [
                    cls_elt.value
                    for cls_elt in cls_node.value.elts
                    if isinstance(cls_elt, ast.Constant) and isinstance(cls_elt.value, str)
                ]
    return None


def public_names(path_module: pathlib.Path) -> set[str]:
    """Return the public module-level names a submodule defines.

    Only definitions count — a name this module merely IMPORTED belongs to whoever defined it,
    and requiring re-export of every import would force the package to publish its dependencies.

    Parameters
    ----------
    path_module : pathlib.Path
        The submodule to read.

    Returns
    -------
    set of str
        Public names bound at module level by a def, class, or assignment.
    """
    set_names: set[str] = set()
    cls_tree = ast.parse(path_module.read_text(encoding="utf-8"))
    for cls_node in cls_tree.body:
        if isinstance(cls_node, ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef):
            set_names.add(cls_node.name)
        elif isinstance(cls_node, ast.Assign):
            set_names.update(
                cls_target.id
                for cls_target in cls_node.targets
                if isinstance(cls_target, ast.Name)
            )
        elif isinstance(cls_node, ast.AnnAssign) and isinstance(cls_node.target, ast.Name):
            set_names.add(cls_node.target.id)
    return {str_name for str_name in set_names if not str_name.startswith("_")}


def check_package(path_init: pathlib.Path) -> list[str]:
    """Return one message per public name the package defines but does not export.

    Parameters
    ----------
    path_init : pathlib.Path
        The package's ``__init__.py``.

    Returns
    -------
    list of str
        Human-readable problems; empty when the export list is complete.
    """
    list_exported = declared_all(path_init)
    if list_exported is None:
        return []
    set_exported = set(list_exported)
    list_problems: list[str] = []
    for path_module in sorted(path_init.parent.glob("*.py")):
        if path_module.name == "__init__.py":
            continue
        for str_name in sorted(public_names(path_module) - set_exported):
            list_problems.append(
                f"{path_init}: '{str_name}' is defined in {path_module.name} but missing from "
                f"__all__ — importable, unexported, and invisible to every gate that "
                f"discovers the family THROUGH __all__"
            )
    return list_problems


def main() -> int:
    """Run the gate over every package under ``src/`` that declares ``__all__``.

    Returns
    -------
    int
        ``0`` when every declared export list is complete, ``1`` otherwise.
    """
    list_inits = [
        path_init
        for path_init in _SRC.rglob("__init__.py")
        if _EXCLUDED_PARTS.isdisjoint(path_init.parts) and declared_all(path_init) is not None
    ]
    if not list_inits:
        print(
            "check_all_exports: found ZERO packages declaring __all__ under src/ — refusing to "
            "report success. Either the layout moved or the discovery is broken; a gate that "
            "scanned nothing also found nothing wrong.",
            file=sys.stderr,
        )
        return 1

    list_problems = [
        str_problem for path_init in list_inits for str_problem in check_package(path_init)
    ]
    for str_problem in list_problems:
        print(f"❌ {str_problem}", file=sys.stderr)
    if list_problems:
        return 1
    print(f"__all__ exports complete in {len(list_inits)} package(s).")
    return 0


if __name__ == "__main__":
    for cls_stream in (sys.stdout, sys.stderr):
        if hasattr(cls_stream, "reconfigure"):
            cls_stream.reconfigure(encoding="utf-8", errors="replace")
    sys.exit(main())
