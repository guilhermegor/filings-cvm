"""Translate this project's ``pyproject.toml`` dependencies into pip requirement lines.

Used by ``bin/lib/pip_fallback.sh`` on hosts where Poetry cannot run at all (locked-down
corporate boxes, slim containers, air-gapped transfers) but ``pip install -r`` can. It
reads the same declarations Poetry would and prints one requirement per line on stdout.

⚠️ WHY THIS IS A FILE AND NOT A HEREDOC. It used to live inside
``pip_fallback_emit_pip_requirements_from_pyproject`` as a 151-line ``"$PYTHON" - <<'PYEOF'``
block. Four lines of shell wrapped a Python program that **no Python tool could see**: ruff
never linted it, mypy never checked it, pytest could not import it, and an editor showed it
as one long string. The 60-line function gate flagged the enclosing shell function at 155
lines, which is the gate working exactly as intended — the length was the symptom, and
invisibility to the toolchain was the disease.

Both Poetry layouts are handled, PEP 621 first:

- ``[project] dependencies`` / ``optional-dependencies`` are already pip-shaped and pass
  through untouched;
- ``[tool.poetry] dependencies`` / ``[tool.poetry.group.<g>.dependencies]`` use Poetry's
  own constraint grammar and are normalised below.

Interface (kept identical to the heredoc it replaced, so the caller did not change):
``PROJECT_ROOT`` and ``BX_GROUPS`` come from the environment; requirement lines go to
stdout; an unsupported declaration exits non-zero with a message naming the dependency.
"""

from __future__ import annotations

import os
from pathlib import Path
import sys


try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - Python < 3.11
    import tomli as tomllib  # type: ignore[no-redef]


TUPLE_PIP_NATIVE_PREFIXES = (">=", "<=", "==", "!=", ">", "<", "~=")

TUPLE_UNSUPPORTED_KEYS = ("path", "git", "url")


_INT_SEMVER_PARTS = 3


def version_parts(str_raw: str) -> list[int]:
    """Split a version string into its leading integer components.

    Trailing non-digits within a part are dropped (``1.2.0rc1`` → ``[1, 2, 0]``), which is
    what the caret/tilde expansion needs: the bound is computed from the release numbers.

    Parameters
    ----------
    str_raw : str
        A version string such as ``"1.4"`` or ``"2.0.0rc1"``.

    Returns
    -------
    list of int
        The parsed components, one per dot-separated part.
    """
    list_numbers: list[int] = []
    for str_part in str_raw.strip().split("."):
        str_digits = ""
        for str_char in str_part:
            if not str_char.isdigit():
                break
            str_digits += str_char
        list_numbers.append(int(str_digits or "0"))
    return list_numbers


def caret_to_range(str_raw: str) -> str:
    """Expand Poetry's ``^`` constraint into an explicit pip range.

    ``^`` allows changes that do not modify the left-most non-zero component, so the upper
    bound depends on where that component sits: ``^1.2.3`` → ``<2.0.0``, ``^0.2.3`` →
    ``<0.3.0``, ``^0.0.3`` → ``<0.0.4``.

    Parameters
    ----------
    str_raw : str
        The constraint including its leading ``^``.

    Returns
    -------
    str
        A ``">=X,<Y"`` range.
    """
    str_base = str_raw[1:].strip()
    list_parts = version_parts(str_base)
    while len(list_parts) < _INT_SEMVER_PARTS:
        list_parts.append(0)
    int_major, int_minor, int_patch = list_parts[:3]

    if int_major > 0:
        str_upper = f"{int_major + 1}.0.0"
    elif int_minor > 0:
        str_upper = f"0.{int_minor + 1}.0"
    else:
        str_upper = f"0.0.{int_patch + 1}"
    return f">={str_base},<{str_upper}"


def tilde_to_range(str_raw: str) -> str:
    """Expand Poetry's ``~`` constraint into an explicit pip range.

    ``~`` pins the last specified component: ``~1.2`` allows ``<1.3.0`` while a bare ``~1``
    allows ``<2.0.0``. The distinction depends on how many components were WRITTEN, not on
    their values, so the raw split is inspected rather than the parsed numbers.

    Parameters
    ----------
    str_raw : str
        The constraint including its leading ``~``.

    Returns
    -------
    str
        A ``">=X,<Y"`` range.
    """
    str_base = str_raw[1:].strip()
    int_written = len(str_base.split("."))
    list_parts = version_parts(str_base)
    while len(list_parts) < _INT_SEMVER_PARTS:
        list_parts.append(0)
    int_major, int_minor = list_parts[:2]

    str_upper = f"{int_major + 1}.0.0" if int_written <= 1 else f"{int_major}.{int_minor + 1}.0"
    return f">={str_base},<{str_upper}"


def normalize_version_spec(str_spec: str) -> str:
    """Convert one Poetry version constraint into pip syntax.

    Parameters
    ----------
    str_spec : str
        A Poetry constraint (``"^1.2"``, ``"~1.2"``, ``">=1,<2"``, ``"1.2.3"``, ``"*"``).

    Returns
    -------
    str
        The pip-syntax equivalent, or an empty string for "any version".
    """
    str_spec = str(str_spec).strip()
    if str_spec in {"", "*"}:
        return ""
    if str_spec.startswith("^"):
        return caret_to_range(str_spec)
    if str_spec.startswith("~") and not str_spec.startswith("~="):
        return tilde_to_range(str_spec)
    if str_spec.startswith(TUPLE_PIP_NATIVE_PREFIXES) or "," in str_spec:
        return str_spec
    return f"=={str_spec}"


def build_requirement(str_name: str, union_spec: str | dict) -> str | None:
    """Render one Poetry dependency declaration as a pip requirement line.

    Parameters
    ----------
    str_name : str
        The dependency name as declared.
    union_spec : str or dict
        Its declaration: a version string, or a table carrying ``version``/``extras``/
        ``markers``/``optional``.

    Returns
    -------
    str or None
        The requirement line, or ``None`` when the dependency must be skipped (the
        ``python`` pseudo-dependency, and anything marked ``optional``).

    Raises
    ------
    SystemExit
        If the declaration is a path/git/url dependency, or a shape not handled here.
    """
    if str_name.lower() == "python":
        return None

    if isinstance(union_spec, str):
        return f"{str_name}{normalize_version_spec(union_spec)}"

    if isinstance(union_spec, dict):
        if union_spec.get("optional"):
            return None
        for str_key in TUPLE_UNSUPPORTED_KEYS:
            if str_key in union_spec:
                raise SystemExit(
                    f"Unsupported dependency type for pip fallback: {str_name} -> {str_key}"
                )

        list_extras = union_spec.get("extras") or []
        str_extras = f"[{','.join(list_extras)}]" if list_extras else ""
        str_version = normalize_version_spec(union_spec.get("version", ""))
        str_markers = union_spec.get("markers", "")

        str_requirement = f"{str_name}{str_extras}{str_version}"
        return f"{str_requirement} ; {str_markers}" if str_markers else str_requirement

    raise SystemExit(f"Unsupported dependency format for {str_name}: {union_spec!r}")


def pep621_requirements(dict_project: dict, list_groups: list) -> list:
    """Collect requirements from a PEP 621 ``[project]`` table.

    Parameters
    ----------
    dict_project : dict
        The parsed ``[project]`` table.
    list_groups : list of str
        Requested groups; ``"main"`` maps to ``dependencies``, the rest to
        ``optional-dependencies``.

    Returns
    -------
    list of str
        Requirement lines, already pip-shaped.
    """
    list_requirements = list(dict_project.get("dependencies", [])) if "main" in list_groups else []
    dict_optional = dict_project.get("optional-dependencies", {})
    for str_group in (str_group for str_group in list_groups if str_group != "main"):
        list_requirements.extend(dict_optional.get(str_group, []))
    return list_requirements


def poetry_requirements(dict_poetry: dict, list_groups: list) -> list:
    """Collect requirements from a ``[tool.poetry]`` table.

    Parameters
    ----------
    dict_poetry : dict
        The parsed ``[tool.poetry]`` table.
    list_groups : list of str
        Requested groups; ``"main"`` maps to the top-level ``dependencies`` table.

    Returns
    -------
    list of str
        Requirement lines, normalised from Poetry's constraint grammar.
    """
    list_requirements: list[str] = []
    if "main" in list_groups:
        for str_name, union_spec in dict_poetry.get("dependencies", {}).items():
            str_line = build_requirement(str_name, union_spec)
            if str_line:
                list_requirements.append(str_line)

    dict_group_table = dict_poetry.get("group", {})
    for str_group in list_groups:
        dict_deps = dict_group_table.get(str_group, {}).get("dependencies", {})
        for str_name, union_spec in dict_deps.items():
            str_line = build_requirement(str_name, union_spec)
            if str_line:
                list_requirements.append(str_line)
    return list_requirements


def select_requirements(dict_pyproject: dict, list_groups: list) -> list:
    """Choose the declaration layout and collect the requested groups from it.

    The question this answers is "does this project use the PEP 621 layout at all?", not
    "does it declare main dependencies?". Those come apart for a project carrying only
    ``[project.optional-dependencies]``: asking the narrower question sent it down the Poetry
    path, where an empty ``[tool.poetry]`` yielded nothing at all (blueprintx#211). A project
    with an EMPTY standard table alongside a populated Poetry one must still resolve, which is
    why the test is on content rather than on the table's presence.

    Parameters
    ----------
    dict_pyproject : dict
        The parsed ``pyproject.toml``.
    list_groups : list of str
        Requested groups, ``"main"`` included when the runtime set is wanted.

    Returns
    -------
    list of str
        Requirement lines from whichever layout the project actually uses.
    """
    dict_project = dict_pyproject.get("project") or {}
    if dict_project.get("dependencies") or dict_project.get("optional-dependencies"):
        return pep621_requirements(dict_project, list_groups)
    return poetry_requirements(dict_pyproject.get("tool", {}).get("poetry", {}), list_groups)


def main() -> int:
    """Print one pip requirement per line for the requested dependency groups.

    Returns
    -------
    int
        0 on success.
    """
    path_root = Path(os.environ["PROJECT_ROOT"])
    list_groups = [
        str_group for str_group in os.environ.get("BX_GROUPS", "main").split(",") if str_group
    ]
    dict_pyproject = tomllib.loads(
        path_root.joinpath("pyproject.toml").read_text(encoding="utf-8")
    )

    list_requirements = select_requirements(dict_pyproject, list_groups)

    if list_groups and not list_requirements:
        raise SystemExit(
            f"No requirements resolved for group(s) {','.join(list_groups)} in "
            f"{path_root / 'pyproject.toml'}. Check that the groups exist and that the "
            f"project declares them under [project] or [tool.poetry]."
        )

    set_seen: set[str] = set()
    for str_requirement in list_requirements:
        if str_requirement not in set_seen:
            print(str_requirement)
            set_seen.add(str_requirement)
    return 0


if __name__ == "__main__":
    sys.exit(main())
