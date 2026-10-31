"""Cap a function or method at 60 lines of code — its docstring excluded.

WHY A HAND-ROLLED GATE. The house rule is "do not reimplement what the tool already
does", and here the tool does not do it: ruff has **no** per-function line-count rule.
``PLR0915`` (``too-many-statements``) counts *statements*, which is a different metric
and answers a different question — a function can hold 20 statements across 90 lines, or
80 statements across 80. So this is an ``ast``-based gate in the same shape as its
siblings (``check_provenance.py``, ``check_all_exports.py``): no module import, no new
dependency.

WHY THE DOCSTRING IS SUBTRACTED. This repo mandates NumPy docstrings with
``Parameters`` / ``Returns`` / ``Raises`` sections, so a raw line span measures how well a
function is **documented**, not how long it is — and a raw ceiling would punish exactly
the habit enforced everywhere else. Measured on this tree at the same 60-line ceiling:
13 Python functions exceed a raw span, **3** exceed it once the docstring is removed.
``download_daily`` (95 raw) and ``apply_dtypes`` (87 raw) *pass* — they are short,
heavily documented functions, and they are precisely the pair a raw ceiling would flag.

THE DEFINITION, stated exactly, because a gate is only as pinned as its metric
(the trap recorded in blueprintx#167, where a hand-rolled counter reported 85%
violations against standard mccabe's 8% — and which caught this file too: the first
implementation over-reported ``retry_with_backoff`` by counting its nested closures'
docstrings, so agreement with the issue's numbers was itself the bug):

- **Python** — ``node.end_lineno - node.lineno + 1``, minus **every docstring inside that
  span, nested definitions included**. ``node.lineno`` is the ``def`` line, so
  **decorators are excluded** for free. Applies to ``def``, ``async def``, and methods
  alike. Blank lines and comments inside the body DO count: they are part of what a reader
  scrolls through.

  ⚠️ The "nested included" half was WRONG in the first implementation, and it is the
  reason this file says so out loud. Subtracting only the outer docstring makes a decorator
  factory pay for its closures' documentation: ``retry_with_backoff`` measured 69 and
  "needed" a refactor, when almost all the excess was the ``decorator`` and ``wrapper``
  NumPy sections. Shortening those to get under the ceiling is documentation deleted to
  satisfy a counter — precisely the incentive the exclusion exists to remove. Corrected, it
  measures well under the limit untouched, and the tree's real count went 21 → 20.
- **Shell** — from the ``name() {`` line to the first line that is exactly ``}`` at
  column 0, inclusive. This is exact rather than heuristic **because the repo runs
  ``shfmt``**, which guarantees that shape; it deliberately avoids brace-depth counting,
  which would have to reason about braces inside strings, comments, and parameter
  expansions. Bash has no docstrings, so nothing is subtracted — the number is the number.

Every finding is a hard error (exit 1).
"""

import ast
import pathlib
import sys


INT_MAX_LINES = 60

PATH_ROOT = pathlib.Path(__file__).resolve().parent.parent

TUPLE_SKIP_DIRS = (
    ".git",
    ".claude",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".venv",
    "__pycache__",
    "htmlcov",
    "node_modules",
    "site",
)

STR_SHELL_OPEN_SUFFIX = "() {"


class UnparsableFileError(Exception):
    """Raised when a discovered ``.py`` file cannot be parsed.

    Its own type rather than a printed warning, so the caller must decide what it means —
    and the only defensible decision is a failure.
    """


def own_docstring_span(cls_node: ast.AST) -> int:
    """Return how many lines one node's own docstring occupies.

    Parameters
    ----------
    cls_node : ast.AST
        A function, method, or class node.

    Returns
    -------
    int
        Line count of the docstring expression, or 0 when there is none.
    """
    list_body = getattr(cls_node, "body", [])
    if not list_body:
        return 0
    cls_first = list_body[0]
    bool_is_docstring = (
        isinstance(cls_first, ast.Expr)
        and isinstance(cls_first.value, ast.Constant)
        and isinstance(cls_first.value.value, str)
    )
    if not bool_is_docstring:
        return 0
    return (cls_first.end_lineno or cls_first.lineno) - cls_first.lineno + 1


def docstring_span(cls_node: ast.AST) -> int:
    """Return every docstring line inside a function, nested definitions included.

    ⚠️ NESTED DOCSTRINGS COUNT AS DOCUMENTATION TOO, and subtracting only the outer one was
    a real defect in this metric. A decorator factory holds its `decorator` and `wrapper`
    closures inside its own span, so their docstrings landed on the OUTER function's tally —
    which is the rule contradicting itself, since the whole reason docstrings are excluded is
    that a ceiling must not measure how well something is documented.

    Measured, and the reason this is not a cosmetic fix: `retry_with_backoff` came out at 69
    lines and "needed" a refactor. Nearly all of the excess was the two closures' NumPy
    sections. Trimming them to get under the ceiling is documentation deleted to satisfy a
    counter — the exact incentive the exclusion exists to prevent.

    Parameters
    ----------
    cls_node : ast.AST
        A function or method node.

    Returns
    -------
    int
        Total docstring lines in the node's own body and in every definition nested in it.
    """
    int_total = own_docstring_span(cls_node)
    for cls_child in ast.walk(cls_node):
        if cls_child is cls_node:
            continue
        if isinstance(cls_child, ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef):
            int_total += own_docstring_span(cls_child)
    return int_total


def python_functions(path_file: pathlib.Path) -> list:
    """Return every function in a Python file with its docstring-excluded length.

    Parameters
    ----------
    path_file : pathlib.Path
        Path to a ``.py`` source file.

    Returns
    -------
    list of tuple
        ``(name, lineno, length)`` per function, including nested ones and methods.
    """
    try:
        cls_tree = ast.parse(path_file.read_text(encoding="utf-8"), filename=str(path_file))
    except SyntaxError as cls_err:
        raise UnparsableFileError(f"{path_file}: could not parse ({cls_err})") from cls_err

    list_found = []
    for cls_node in ast.walk(cls_tree):
        if not isinstance(cls_node, ast.FunctionDef | ast.AsyncFunctionDef):
            continue
        int_span = (cls_node.end_lineno or cls_node.lineno) - cls_node.lineno + 1
        list_found.append((cls_node.name, cls_node.lineno, int_span - docstring_span(cls_node)))
    return list_found


def shell_functions(path_file: pathlib.Path) -> list:
    """Return every shell function in a file with its length.

    Relies on the ``shfmt`` shape the repo already enforces: an opening ``name() {`` at
    column 0 and a closing ``}`` at column 0. See the module docstring for why this is
    exact here rather than a heuristic.

    Parameters
    ----------
    path_file : pathlib.Path
        Path to a ``.sh`` source file.

    Returns
    -------
    list of tuple
        ``(name, lineno, length)`` per function.
    """
    list_lines = path_file.read_text(encoding="utf-8", errors="replace").splitlines()
    list_found = []
    str_open_name = ""
    int_open_line = 0
    for int_index, str_line in enumerate(list_lines, start=1):
        if str_open_name and str_line == "}":
            list_found.append((str_open_name, int_open_line, int_index - int_open_line + 1))
            str_open_name = ""
            continue
        if str_open_name or not str_line.endswith(STR_SHELL_OPEN_SUFFIX):
            continue
        str_candidate = str_line[: -len(STR_SHELL_OPEN_SUFFIX)].strip()
        if str_candidate.startswith("function "):
            str_candidate = str_candidate[len("function ") :].strip()
        if str_candidate and str_candidate.replace("_", "").replace("-", "").isalnum():
            str_open_name = str_candidate
            int_open_line = int_index
    return list_found


def file_problems(path_file: pathlib.Path) -> list:
    """Return one message per function in the file that exceeds the ceiling.

    Parameters
    ----------
    path_file : pathlib.Path
        Path to a ``.py`` or ``.sh`` file.

    Returns
    -------
    list of str
        Human-readable findings; empty when every function fits.
    """
    if path_file.suffix not in (".py", ".sh"):
        return []

    try:
        str_shown = str(path_file.relative_to(PATH_ROOT))
    except ValueError:
        str_shown = str(path_file)

    str_note = ", docstring excluded" if path_file.suffix == ".py" else ""
    try:
        list_functions = (
            python_functions(path_file)
            if path_file.suffix == ".py"
            else shell_functions(path_file)
        )
    except UnparsableFileError as cls_err:
        return [str(cls_err)]

    return [
        f"{str_shown}:{int_line}: {str_name}() is {int_length} lines"
        f" (max {INT_MAX_LINES}{str_note})"
        for str_name, int_line, int_length in list_functions
        if int_length > INT_MAX_LINES
    ]


def audit_paths() -> list:
    """Discover every checkable file under the repository root.

    Returns
    -------
    list of pathlib.Path
        Sorted ``.py`` and ``.sh`` paths, skipping vendored and generated trees.
    """
    list_paths = []
    for str_suffix in ("*.py", "*.sh"):
        for path_file in PATH_ROOT.rglob(str_suffix):
            if any(
                str_part in TUPLE_SKIP_DIRS for str_part in path_file.relative_to(PATH_ROOT).parts
            ):
                continue
            list_paths.append(path_file)
    return sorted(list_paths)


_INT_FLAG_WITH_VALUE = 2


def main(list_argv: list) -> int:
    """Check every named file for a function longer than the ceiling.

    Parameters
    ----------
    list_argv : list of str
        Filenames, as pre-commit passes them. Empty means audit the whole repository.

    Returns
    -------
    int
        0 when every function fits, 1 on a violation.
    """
    global PATH_ROOT  # noqa: PLW0603
    if list_argv[:1] == ["--root"]:
        if len(list_argv) < _INT_FLAG_WITH_VALUE:
            print("❌ --root needs a directory")
            return 1
        PATH_ROOT = pathlib.Path(list_argv[1]).resolve()
        list_argv = list_argv[2:]

    bool_audit = not list_argv
    list_paths = (
        [pathlib.Path(str_name).resolve() for str_name in list_argv]
        if list_argv
        else audit_paths()
    )

    if bool_audit and not list_paths:
        print(
            f"❌ no .py or .sh file found under {PATH_ROOT} — this gate would pass "
            f"vacuously. Check TUPLE_SKIP_DIRS against the layout."
        )
        return 1

    list_problems = []
    for path_file in list_paths:
        list_problems.extend(file_problems(path_file))
    for str_problem in list_problems:
        print(str_problem)

    if not list_problems:
        print(f"✅ function length OK ({len(list_paths)} file(s) checked)")
        return 0

    print(
        f"\n{len(list_problems)} finding(s). Any function over {INT_MAX_LINES} lines: split it "
        f"rather than raising the ceiling, which is about what one reader holds in their head "
        f"at once and does not move because one function is special. For Python the docstring "
        f"is already excluded, so the number shown is code only. A file reported as unparsable "
        f"is a finding in its own right — it cannot be checked, which is not the same as clean."
    )
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
