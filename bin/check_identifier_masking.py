"""Structural gate: unnormalised identifier comparisons (blueprintx#355, item 4).

Sibling of ``check_sql_guards.py`` (WHERE-less mutations / ``WITH (NOLOCK)``) — split into
its own file per the issue's own instruction ("ship one per PR"; the sibling gate's own
docstring lists this as explicitly out of its scope, with its own false-positive shape).

**The failure mode**: a masked CPF/CNPJ literal (``"123.456.789-01"``) compared against a
``cpf``/``cnpj`` column matches **zero rows and raises nothing** — not an error, an empty
result that reads as "no such customer". ``filings_cvm._internal.utils.br_identifiers`` ships
``unmask_cpf``/``unmask_cnpj`` for exactly this; the gate catches the case where a masked
literal reaches a comparison without going through them.

**Scope, deliberately narrow** (per the issue's own warning not to build the registry
first): CPF and CNPJ only — the two identifiers this codebase actually has ``unmask_*``
helpers for. CNH has no such helper yet, so there is nothing to normalise TO; adding a rule
for it now would be guessing at a fix that does not exist. A per-column-treatment registry
was considered and rejected here for the same reason the issue names: it needs a maintainer,
and a stale registry is worse than none.

Two shapes are decidable without dataflow tracking (which variable was or wasn't unmasked):

1. **A masked literal hardcoded into SQL text** — a raw ``.sql`` file, or a Python
   string/f-string used as a query — matching ``<column> = '<masked value>'``. Detected the
   same way the sibling gate finds ``NOLOCK``: walk string/f-string constant segments (AST
   for ``.py``, full text for ``.sql``), regex the segment.
2. **A masked literal in an ORM comparison or keyword** — ``Model.cpf == "123.456.789-01"``,
   ``.filter_by(cnpj="12.345.678/0001-95")``. Detected via AST ``Compare``/``keyword`` nodes.

A masked literal compared against a column that only *coincidentally* looks like an
identifier (unlikely — the mask formats are distinctive: 11-digit CPF punctuation, 14-char
CNPJ punctuation including the 2026 alphanumeric form) is the false-positive risk accepted
here; a column-name filter (``cpf``/``cnpj`` substring) narrows it further.

**Escape hatch**, same shape as ``sql-guard-ok:``/``dtype-ok:`` elsewhere in this tree::

    stmt = query.filter_by(cpf="123.456.789-01")  # identifier-mask-ok: <reason>

An empty or whitespace-only reason after the marker is rejected.

⚠️ **Zero findings on a real project tree is the expected result, not a broken gate** — the
templates' own code never hardcodes a masked identifier. The synthetic probes in this gate's
own test suite are what prove discovery actually works.
"""

from __future__ import annotations

import ast
import pathlib
import re
import sys


_ALLOW_MARKER = "identifier-mask-ok:"
_SRC_ROOT = "src"

_RE_MASKED_CPF = re.compile(r"^\d{3}\.\d{3}\.\d{3}-\d{2}$")
_RE_MASKED_CNPJ = re.compile(
    r"^[0-9A-Za-z]{2}\.[0-9A-Za-z]{3}\.[0-9A-Za-z]{3}/[0-9A-Za-z]{4}-\d{2}$"
)

_RE_TEXT_COMPARE = re.compile(
    r"\b(\w*(?:cpf|cnpj)\w*)\s*(?:==|=)\s*['\"]([0-9A-Za-z./-]+)['\"]", re.IGNORECASE
)
_RE_IDENT_NAME = re.compile(r"cpf|cnpj", re.IGNORECASE)


def _is_masked_value(str_value: str) -> bool:
    """Return whether a string is a masked CPF or CNPJ literal.

    Parameters
    ----------
    str_value : str
        Candidate value.

    Returns
    -------
    bool
        ``True`` when it matches the CPF or CNPJ mask format.
    """
    return bool(_RE_MASKED_CPF.match(str_value) or _RE_MASKED_CNPJ.match(str_value))


def _hatch_reason(str_line: str) -> str | None:
    """Return the escape-hatch reason on a line, or ``None`` when there isn't one.

    Parameters
    ----------
    str_line : str
        The source line to inspect.

    Returns
    -------
    str or None
        The written reason, or ``None`` when the marker is absent OR the reason after it is
        empty/whitespace-only — a bare marker is not a decision anyone made on purpose.
    """
    if _ALLOW_MARKER not in str_line:
        return None
    return str_line.split(_ALLOW_MARKER, 1)[1].strip() or None


def _line_allowed(list_lines: list[str], int_line: int) -> bool:
    """Return whether a 1-indexed line carries a valid escape-hatch reason.

    Parameters
    ----------
    list_lines : list of str
        The source file, split into lines.
    int_line : int
        The 1-indexed line number to check.

    Returns
    -------
    bool
        ``True`` only when the line exists and carries a non-empty reason.
    """
    if not (1 <= int_line <= len(list_lines)):
        return False
    return _hatch_reason(list_lines[int_line - 1]) is not None


def _mask_message(path_file: pathlib.Path, int_line: int, str_value: str) -> str:
    """Return the masked-identifier finding, naming the failure mode and the fix.

    Parameters
    ----------
    path_file : pathlib.Path
        The offending file.
    int_line : int
        The line carrying the literal.
    str_value : str
        The masked value found.

    Returns
    -------
    str
        A human-readable finding.
    """
    return (
        f"{path_file}:{int_line}: masked identifier literal '{str_value}' compared "
        f"directly - a masked CPF/CNPJ never equals the unmasked value stored in the "
        f"column, so this matches ZERO rows and raises nothing. Pass it through "
        f"unmask_cpf()/unmask_cnpj() (filings_cvm._internal.utils.br_identifiers) first, or if this is "
        f"deliberate, annotate the line: # {_ALLOW_MARKER} <reason>"
    )


def _text_problems(
    str_text: str, path_file: pathlib.Path, int_line_offset: int
) -> list[tuple[int, str]]:
    """Find every masked-identifier comparison in a block of SQL-shaped text.

    Parameters
    ----------
    str_text : str
        The text to scan (a raw ``.sql`` file, or one Python string/f-string segment).
    path_file : pathlib.Path
        The file the text came from, for the message (unused here, kept for symmetry).
    int_line_offset : int
        Line number the text's first line corresponds to in the source file (1-indexed).

    Returns
    -------
    list of (int, str)
        ``(source_line, masked_value)`` pairs for every match.
    """
    del path_file
    list_found: list[tuple[int, str]] = []
    for cls_match in _RE_TEXT_COMPARE.finditer(str_text):
        str_value = cls_match.group(2)
        if not _is_masked_value(str_value):
            continue
        int_line = int_line_offset + str_text.count("\n", 0, cls_match.start())
        list_found.append((int_line, str_value))
    return list_found


def _sql_file_problems(path_file: pathlib.Path) -> list[str]:
    """Report every masked-identifier comparison in a raw ``.sql`` file.

    Parameters
    ----------
    path_file : pathlib.Path
        The ``.sql`` file to scan.

    Returns
    -------
    list of str
        Human-readable findings; empty when the file complies.
    """
    str_text = path_file.read_text(encoding="utf-8")
    list_lines = str_text.splitlines()
    list_problems: list[str] = []
    for int_line, str_value in _text_problems(str_text, path_file, 1):
        if _line_allowed(list_lines, int_line):
            continue
        list_problems.append(_mask_message(path_file, int_line, str_value))
    return list_problems


def _string_literal_problems(
    cls_tree: ast.Module, path_file: pathlib.Path, list_lines: list[str]
) -> list[str]:
    """Report masked-identifier comparisons inside Python string/f-string literals.

    Same segment-walking approach as the sibling gate's ``NOLOCK`` check: matched against
    the literal's SOURCE segment (implicit concatenation can hide a newline that the parsed
    value does not carry), per match rather than per constant.

    Parameters
    ----------
    cls_tree : ast.Module
        The parsed module.
    path_file : pathlib.Path
        The module's path, for the message.
    list_lines : list of str
        The source, split into lines, for the escape-hatch check.

    Returns
    -------
    list of str
        Human-readable findings; empty when the file complies.
    """
    str_source = "\n".join(list_lines)
    list_problems: list[str] = []
    for cls_node in ast.walk(cls_tree):
        if not (isinstance(cls_node, ast.Constant) and isinstance(cls_node.value, str)):
            continue
        str_segment = ast.get_source_segment(str_source, cls_node) or ""
        for int_line, str_value in _text_problems(str_segment, path_file, cls_node.lineno):
            if _line_allowed(list_lines, int_line):
                continue
            list_problems.append(_mask_message(path_file, int_line, str_value))
    return list_problems


def _orm_name(cls_node: ast.expr) -> str | None:
    """Return the identifier name of an ``Attribute`` or ``Name`` node, else ``None``.

    Parameters
    ----------
    cls_node : ast.expr
        The expression to name.

    Returns
    -------
    str or None
        ``cls_node.attr``/``cls_node.id``, or ``None`` when neither applies.
    """
    if isinstance(cls_node, ast.Attribute):
        return cls_node.attr
    if isinstance(cls_node, ast.Name):
        return cls_node.id
    return None


def _compare_problems(
    cls_tree: ast.Module, path_file: pathlib.Path, list_lines: list[str]
) -> list[str]:
    """Report ``Model.cpf == "<masked>"``-shaped ORM comparisons.

    Parameters
    ----------
    cls_tree : ast.Module
        The parsed module.
    path_file : pathlib.Path
        The module's path, for the message.
    list_lines : list of str
        The source, split into lines, for the escape-hatch check.

    Returns
    -------
    list of str
        Human-readable findings; empty when the file complies.
    """
    list_problems: list[str] = []
    for cls_node in ast.walk(cls_tree):
        if not isinstance(cls_node, ast.Compare):
            continue
        if not any(isinstance(cls_op, ast.Eq | ast.NotEq) for cls_op in cls_node.ops):
            continue
        list_operands = [cls_node.left, *cls_node.comparators]
        list_names = [_orm_name(cls_op) for cls_op in list_operands]
        list_values = [
            cls_op.value
            for cls_op in list_operands
            if isinstance(cls_op, ast.Constant) and isinstance(cls_op.value, str)
        ]
        bool_ident = any(str_name and _RE_IDENT_NAME.search(str_name) for str_name in list_names)
        list_masked = [str_v for str_v in list_values if _is_masked_value(str_v)]
        if bool_ident and list_masked and not _line_allowed(list_lines, cls_node.lineno):
            list_problems.append(_mask_message(path_file, cls_node.lineno, list_masked[0]))
    return list_problems


def _keyword_problems(
    cls_tree: ast.Module, path_file: pathlib.Path, list_lines: list[str]
) -> list[str]:
    """Report ``filter_by(cpf="<masked>")``-shaped keyword-argument comparisons.

    Parameters
    ----------
    cls_tree : ast.Module
        The parsed module.
    path_file : pathlib.Path
        The module's path, for the message.
    list_lines : list of str
        The source, split into lines, for the escape-hatch check.

    Returns
    -------
    list of str
        Human-readable findings; empty when the file complies.
    """
    list_problems: list[str] = []
    for cls_node in ast.walk(cls_tree):
        if not isinstance(cls_node, ast.keyword) or cls_node.arg is None:
            continue
        if not _RE_IDENT_NAME.search(cls_node.arg):
            continue
        cls_value = cls_node.value
        if not (isinstance(cls_value, ast.Constant) and isinstance(cls_value.value, str)):
            continue
        if not _is_masked_value(cls_value.value):
            continue
        if _line_allowed(list_lines, cls_value.lineno):
            continue
        list_problems.append(_mask_message(path_file, cls_value.lineno, cls_value.value))
    return list_problems


def check_python_file(path_file: pathlib.Path) -> list[str]:
    """Run every masked-identifier guard against one Python source file.

    Parameters
    ----------
    path_file : pathlib.Path
        The module to check.

    Returns
    -------
    list of str
        Human-readable findings; empty when the file complies.
    """
    str_source = path_file.read_text(encoding="utf-8")
    try:
        cls_tree = ast.parse(str_source)
    except SyntaxError as cls_exc:
        return [f"{path_file}: could not parse ({cls_exc})"]

    list_lines = str_source.splitlines()
    list_problems = _string_literal_problems(cls_tree, path_file, list_lines)
    list_problems += _compare_problems(cls_tree, path_file, list_lines)
    list_problems += _keyword_problems(cls_tree, path_file, list_lines)
    return list_problems


def _discovered_files() -> tuple[list[pathlib.Path], list[pathlib.Path]]:
    """Return every Python and ``.sql`` file under ``src/``.

    Returns
    -------
    tuple of (list of pathlib.Path, list of pathlib.Path)
        ``(list_py, list_sql)``, both sorted; empty when ``src/`` has no such files.
    """
    path_src = pathlib.Path(_SRC_ROOT)
    list_py = sorted(p for p in path_src.rglob("*.py") if "__pycache__" not in p.parts)
    list_sql = sorted(path_src.rglob("*.sql"))
    return list_py, list_sql


def main() -> int:
    """Check every Python and ``.sql`` file under ``src/`` for masked-identifier comparisons.

    Returns
    -------
    int
        ``0`` when the tree complies (or ``src/`` does not exist), ``1`` otherwise.
    """
    path_src = pathlib.Path(_SRC_ROOT)
    if not path_src.is_dir():
        print(f"No {_SRC_ROOT}/ directory - skipping the identifier masking check.")
        return 0

    list_py, list_sql = _discovered_files()
    if not list_py and not list_sql:
        print(
            f"FAIL: 0 Python and 0 .sql files discovered under {_SRC_ROOT}/ - the identifier masking "
            f"check checked NOTHING. A wrong working directory or a broken glob reporting "
            f"success for having checked nothing is the exact failure this gate exists to "
            f"prevent."
        )
        return 1

    list_problems: list[str] = []
    for path_file in list_py:
        list_problems += check_python_file(path_file)
    for path_file in list_sql:
        list_problems += _sql_file_problems(path_file)

    for str_problem in list_problems:
        print(f"FAIL: {str_problem}")
    if list_problems:
        print(f"\n{len(list_problems)} identifier masking violation(s).")
        return 1

    print(
        f"OK: Identifier masking OK ({len(list_py)} Python file(s), {len(list_sql)} SQL "
        f"file(s) checked)."
    )
    return 0


if __name__ == "__main__":
    for cls_stream in (sys.stdout, sys.stderr):
        if hasattr(cls_stream, "reconfigure"):
            cls_stream.reconfigure(encoding="utf-8", errors="replace")

    sys.exit(main())
