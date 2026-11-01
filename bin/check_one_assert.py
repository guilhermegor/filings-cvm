"""Cap assertion sites per ``test_*`` function: zero anywhere, one under ``tests/unit/``.

Counts every assertion SITE — ``assert``, an ``assert_*()`` call (pandas/mock), and
``pytest.raises``/``pytest.warns`` used as a context manager — never bare ``ast.Assert`` alone,
which misreads every ``raises``-only test as "zero assertions".

TWO RULES, SCOPED BY PATH, AND THE SPLIT IS THE WHOLE DESIGN.

**Zero sites fails in every suite** (blueprintx#431). A ``test_*`` that asserts nothing proves
nothing under any reading of any convention, and nothing else in this repo's gate family
(``check_complexity.sh``'s tests/ ceiling of 1, ruff's ``PT018``) looks for it.

**One site is the ceiling under ``tests/unit/``** (blueprintx#544, owner's decision 2026-09-19:
enforce immediately, no warning phase, no grandfathering). A unit test with two asserts that
goes red does not say which behaviour broke — the failure names a line, and the reader
reconstructs which of two claims the code stopped honouring. Worse, the GREEN never says which
assert ran: one placed after an early ``return``, a ``raise``, or a ``raises`` block is never
reached, and the passing suite reports that unexecuted claim as proven.

**``tests/integration/`` stays on zero-only, deliberately.** An integration test asserts a
SEQUENCE of observable effects of one call — a row written, a status returned, a webhook fired —
and splitting those re-runs the whole expensive *arrange* to prove no new fact. Measured
2026-09-20 over ``templates/**``: 828 unit tests with 201 (24%) over the cap, against 68
integration tests with 52 (76%) over it. At 24% the rule is a finishable remediation; at 76% it
is a wall, and a gate at a threshold nobody pays is a gate nobody keeps. (This supersedes
blueprintx#429's "554 / 31%" and #431's "188 / 33%" — both stale, do not re-cite them.)

Scope is decided by PATH (``--unit-dir``, default ``tests/unit``), never by filename: a project
that renames the suite re-points the flag, and a file named ``test_x.py`` sitting in
``tests/integration/`` is judged as an integration test, which is what it is.

``--max-per-test N`` overrides the unit cap; ``--max-per-test 0`` disables it, leaving the
zero-assertion check alone — the measurement mode this file's distribution table was produced in.

The one narrow, decidable slice of "one assert hides two facts" — ``assert a and b`` — is ruff's
``PT018``; this gate does not re-implement it.

Escape hatch, matching ``# complexity-ok: <reason>`` elsewhere in this repo: a
``# one-assert-ok: <reason>`` comment anywhere in a flagged function's source exempts it from
BOTH checks — the reason is required, a bare marker is rejected.

SELF-SKIPS when ``tests/`` is absent (this repo's own root, per ``CLAUDE.md``: "BlueprintX's own
tree has no ``src/`` or ``tests/``"). A ``tests/`` directory that exists but yields zero
``test_*.py`` files is NOT a skip — it is the broken-discovery failure this repo's gates exist to
catch (blueprintx#111's shape, recurring: `check_provenance.py`, `check_docstrings.py`).
"""

import ast
import io
import pathlib
import re
import sys
import tokenize


RE_HATCH = re.compile(r"#[ \t]*one-assert-ok:[ \t]*(\S.*)$", re.M)

DEFAULT_UNIT_MAX = 1
DEFAULT_UNIT_DIR = "tests/unit"

_SET_VALUE_FLAGS = frozenset({"--root", "--max-per-test", "--unit-dir"})

_SET_CTX_ASSERTIONS = frozenset({"raises", "warns"})


def _split_flags(list_argv: list) -> tuple:
    """Split an argv tail of ``--flag value`` pairs into a dict, or report the first error.

    Parameters
    ----------
    list_argv : list of str
        The raw argv tail.

    Returns
    -------
    tuple
        ``(dict_flags, str_error)`` — ``str_error`` is ``""`` when every token parsed.
    """
    dict_flags: dict = {}
    list_rest = list(list_argv)
    while list_rest:
        str_arg = list_rest.pop(0)
        if str_arg not in _SET_VALUE_FLAGS:
            return dict_flags, f"unrecognised argument: {str_arg}"
        if not list_rest:
            return dict_flags, f"{str_arg} needs a value"
        dict_flags[str_arg] = list_rest.pop(0)
    return dict_flags, ""


def parse_args(list_argv: list) -> tuple:
    """Parse ``--root <dir>``, ``--max-per-test <int>`` and ``--unit-dir <relpath>``.

    Parameters
    ----------
    list_argv : list of str
        The raw argv tail.

    Returns
    -------
    tuple
        ``(path_root, int_max, str_unit_dir, bool_ok)`` — ``int_max`` defaults to
        ``DEFAULT_UNIT_MAX`` and applies only under ``str_unit_dir``; ``0`` disables the cap.
        ``bool_ok`` is ``False`` on bad usage (already reported to stdout).
    """
    dict_flags, str_error = _split_flags(list_argv)
    path_root = pathlib.Path(dict_flags.get("--root", ".")).resolve()
    str_unit_dir = dict_flags.get("--unit-dir", DEFAULT_UNIT_DIR)
    str_max = dict_flags.get("--max-per-test", str(DEFAULT_UNIT_MAX))
    if not str_error and not str_max.isdigit():
        str_error = "--max-per-test needs a non-negative integer (0 disables the cap)"
    if str_error:
        print(f"❌ {str_error}")
        return path_root, DEFAULT_UNIT_MAX, str_unit_dir, False
    return path_root, int(str_max), str_unit_dir, True


def _test_files(path_root: pathlib.Path) -> list:
    """Return every ``test_*.py`` file under ``<root>/tests/``.

    Parameters
    ----------
    path_root : pathlib.Path
        The tree to scan.

    Returns
    -------
    list of pathlib.Path
        Sorted matches, empty when ``tests/`` holds none.
    """
    path_tests = path_root / "tests"
    if not path_tests.is_dir():
        return []
    return sorted(path_tests.rglob("test_*.py"))


def _has_non_python_tests(path_tests: pathlib.Path) -> bool:
    """Return whether ``tests/`` holds a ``test_*`` file in a non-Python language.

    Distinguishes "this tree tests in another language here" — BlueprintX's own root ships
    ``tests/test_check_issue_scope.sh`` and two siblings, zero ``.py`` — from a genuinely
    empty or broken ``tests/``. Only the latter is a failure; the former is the same
    legitimate skip ``check_complexity.sh`` already grants this exact repo (its own
    ``CLAUDE.md``: "BlueprintX's own tree has no src/ or tests/ [in the Python sense]").

    Parameters
    ----------
    path_tests : pathlib.Path
        The ``tests/`` directory (already known to exist).

    Returns
    -------
    bool
        ``True`` when at least one ``test_*.<ext>`` file exists with ``ext`` other than
        ``py``.
    """
    return any(path_file.suffix != ".py" for path_file in path_tests.rglob("test_*.*"))


def vacuous_discovery_reason(path_root: pathlib.Path) -> str | None:
    """Return why a missing ``tests/`` directory is a legitimate skip, or ``None`` otherwise.

    Parameters
    ----------
    path_root : pathlib.Path
        The tree to scan.

    Returns
    -------
    str or None
        A skip reason when ``tests/`` does not exist at all; ``None`` when it does (whether
        or not it holds any matching files — an existing-but-empty ``tests/`` is a broken
        discovery, handled by the caller as a failure, never a skip).
    """
    if not (path_root / "tests").is_dir():
        return "no tests/ directory in this tree — skipping"
    return None


def _is_assert_call(node_call: ast.Call) -> bool:
    """Return whether a call is an ``assert*`` check (unittest, pandas, mock, ...).

    Parameters
    ----------
    node_call : ast.Call
        The call node.

    Returns
    -------
    bool
        ``True`` for ``self.assertX(...)``, ``mock.assert_called_once()``,
        ``pd.testing.assert_frame_equal(...)``, or a bare ``assert_x(...)`` free function.
    """
    func = node_call.func
    if isinstance(func, ast.Attribute):
        return func.attr.startswith("assert")
    if isinstance(func, ast.Name):
        return func.id.startswith("assert_")
    return False


def _ctx_call_name(node_call: ast.Call) -> str | None:
    """Return a ``with``-item's context-expression callable name.

    Parameters
    ----------
    node_call : ast.Call
        A ``with`` item's context expression.

    Returns
    -------
    str or None
        The callable's bare or attribute name, or ``None`` when neither shape matches.
    """
    func = node_call.func
    if isinstance(func, ast.Attribute):
        return func.attr
    if isinstance(func, ast.Name):
        return func.id
    return None


def _assertion_with_count(node_with: ast.With | ast.AsyncWith) -> int:
    """Count the ``pytest.raises``/``pytest.warns`` contexts in a ``with`` statement.

    Parameters
    ----------
    node_with : ast.With or ast.AsyncWith
        The ``with`` or ``async with`` statement.

    Returns
    -------
    int
        How many items call ``raises`` or ``warns`` — each is its own assertion site, so
        ``with pytest.raises(A), pytest.warns(B):`` is two, not one.
    """
    return sum(
        isinstance(item.context_expr, ast.Call)
        and _ctx_call_name(item.context_expr) in _SET_CTX_ASSERTIONS
        for item in node_with.items
    )


def _assertion_sites(node_fn: ast.FunctionDef | ast.AsyncFunctionDef) -> list:
    """Return the assertion-like nodes inside a test function, in source order.

    Parameters
    ----------
    node_fn : ast.FunctionDef or ast.AsyncFunctionDef
        The test function (or method).

    Returns
    -------
    list of ast.AST
        One entry per ``assert`` statement, ``assert*()`` call, or ``raises``/``warns``
        ``with`` block. Does not descend into a nested function/lambda — that is its own
        unit (mirrors ``check_assertion_weakening.py``'s identical walk).
    """
    list_sites: list = []

    def _walk(node: ast.AST) -> None:
        for child in ast.iter_child_nodes(node):
            if isinstance(child, ast.FunctionDef | ast.AsyncFunctionDef | ast.Lambda):
                continue
            if isinstance(child, ast.Assert):
                list_sites.append(child)
            elif isinstance(child, ast.With | ast.AsyncWith):
                list_sites.extend([child] * _assertion_with_count(child))
            elif (
                isinstance(child, ast.Expr)
                and isinstance(child.value, ast.Call)
                and _is_assert_call(child.value)
            ):
                list_sites.append(child.value)
            _walk(child)

    _walk(node_fn)
    return list_sites


def _index_test_functions(cls_tree: ast.AST) -> dict:
    """Return every ``test_*`` function/method under a module, keyed by qualified name.

    Parameters
    ----------
    cls_tree : ast.AST
        The parsed module.

    Returns
    -------
    dict of str to ast.FunctionDef or ast.AsyncFunctionDef
        Qualified name (``ClassName.test_x`` or bare ``test_x``) to its node — qualified so
        two classes sharing a method name are tracked separately.
    """
    dict_funcs: dict = {}

    def _walk(node_parent: ast.AST, str_prefix: str) -> None:
        for node in ast.iter_child_nodes(node_parent):
            if isinstance(node, ast.ClassDef):
                _walk(node, f"{str_prefix}{node.name}.")
            elif isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef) and node.name.startswith(
                "test_"
            ):
                dict_funcs[f"{str_prefix}{node.name}"] = node

    _walk(cls_tree, "")
    return dict_funcs


def _hatch_reason(str_source: str, node_fn: ast.FunctionDef | ast.AsyncFunctionDef) -> str:
    """Return the ``# one-assert-ok: <reason>`` text inside a function, or ``""``.

    Parameters
    ----------
    str_source : str
        The file's full source text.
    node_fn : ast.FunctionDef or ast.AsyncFunctionDef
        The function to scan.

    Returns
    -------
    str
        The non-empty reason, or ``""`` when no valid hatch is present — a bare marker with
        no reason does not exempt, matching ``# complexity-ok:``'s convention.
    """
    int_end = node_fn.end_lineno or node_fn.lineno
    cls_tokens = tokenize.generate_tokens(io.StringIO(str_source).readline)
    for cls_tok in cls_tokens:
        if cls_tok.type != tokenize.COMMENT or not node_fn.lineno <= cls_tok.start[0] <= int_end:
            continue
        cls_match = RE_HATCH.search(cls_tok.string)
        if cls_match and cls_match.group(1).strip():
            return cls_match.group(1).strip()
    return ""


def cap_for_file(
    path_file: pathlib.Path, path_root: pathlib.Path, str_unit_dir: str, int_max: int
) -> int | None:
    """Return the assertion-site cap that applies to one file, or ``None`` for zero-only.

    Scope is decided by PATH, never by filename: a ``test_x.py`` under ``tests/integration/``
    is an integration test and keeps the loose rule, while the same name under ``tests/unit/``
    is capped (blueprintx#544).

    Parameters
    ----------
    path_file : pathlib.Path
        The test file being checked.
    path_root : pathlib.Path
        The tree root the file was discovered under.
    str_unit_dir : str
        Root-relative directory holding the unit suite (``--unit-dir``).
    int_max : int
        The cap to apply inside that directory; ``0`` disables it everywhere.

    Returns
    -------
    int or None
        The cap, or ``None`` when only the zero-assertion check applies to this file.
    """
    if int_max <= 0:
        return None
    str_prefix = f"{str_unit_dir.strip('/')}/"
    if path_file.relative_to(path_root).as_posix().startswith(str_prefix):
        return int_max
    return None


def _file_findings(path_file: pathlib.Path, path_root: pathlib.Path, int_max: int | None) -> tuple:
    """Return the problems and per-function assertion-site counts for one test file.

    Parameters
    ----------
    path_file : pathlib.Path
        The test file to check.
    path_root : pathlib.Path
        The tree root, for relative message paths.
    int_max : int or None
        The cap that applies to THIS file (from ``cap_for_file``), or ``None`` when only the
        zero-assertion check applies.

    Returns
    -------
    tuple
        ``(problems, counts)`` — ``problems`` is a list of str findings; ``counts`` is a
        list of int, one per ``test_*`` function found, for the distribution table.
    """
    str_source = path_file.read_text(encoding="utf-8")
    str_rel = path_file.relative_to(path_root)
    try:
        cls_tree = ast.parse(str_source)
    except SyntaxError as cls_exc:
        return [f"{str_rel}: not valid Python ({cls_exc}) — not checked"], []

    dict_funcs = _index_test_functions(cls_tree)
    list_problems: list = []
    list_counts: list = []
    for str_name, node_fn in dict_funcs.items():
        int_count = len(_assertion_sites(node_fn))
        list_counts.append(int_count)
        if _hatch_reason(str_source, node_fn):
            continue
        if int_count == 0:
            list_problems.append(
                f"{str_rel}: {str_name}() line {node_fn.lineno}: asserts nothing — 0 assertion "
                f"sites (no assert, assert_*() call, or raises/warns block)"
            )
        elif int_max is not None and int_count > int_max:
            list_problems.append(
                f"{str_rel}: {str_name}() line {node_fn.lineno}: {int_count} assertion sites, "
                f"over the cap of {int_max} — a red test with several asserts does not say "
                f"which behaviour broke, and the green never says which one ran. Split it with "
                f"pytest.mark.parametrize or a scoped fixture (tests/CLAUDE.md)"
            )
    return list_problems, list_counts


def distribution_table(list_counts: list) -> str:
    """Return a human-readable histogram of assertion-site counts, one line per count.

    Parameters
    ----------
    list_counts : list of int
        Per-function assertion-site counts across every checked file.

    Returns
    -------
    str
        One ``"N assertion site(s): M test(s)"`` line per distinct count, sorted by count;
        ``"0 test_* functions found"`` when the list is empty.
    """
    if not list_counts:
        return "0 test_* functions found"
    dict_hist: dict = {}
    for int_count in list_counts:
        dict_hist[int_count] = dict_hist.get(int_count, 0) + 1
    return "\n".join(
        f"  {int_n} assertion site(s): {int_tests} test(s)"
        for int_n, int_tests in sorted(dict_hist.items())
    )


def main(list_argv: list) -> int:
    """Check every ``test_*`` function under ``<root>/tests/`` for assertion sites.

    Parameters
    ----------
    list_argv : list of str
        Any of ``--root <dir>``, ``--max-per-test <int>``, ``--unit-dir <relpath>``, in any
        order.

    Returns
    -------
    int
        0 when ``tests/`` is absent, holds only non-Python ``test_*`` files, or every
        function has at least one assertion site and every unit test stays within the cap; 1
        on a broken (empty) discovery, an unparsable file, a zero-assertion test, or a cap
        violation.
    """
    path_root, int_max, str_unit_dir, bool_ok = parse_args(list_argv)
    if not bool_ok:
        return 1

    str_skip = vacuous_discovery_reason(path_root)
    if str_skip is not None:
        print(f"✅ one-assert gate: {str_skip}")
        return 0

    list_files = _test_files(path_root)
    if not list_files:
        if _has_non_python_tests(path_root / "tests"):
            print(
                "✅ one-assert gate: no test_*.py files under tests/ (non-Python test file(s) "
                "found instead — this tree does not test in Python here)"
            )
            return 0
        print(
            "❌ tests/ exists but 0 test_*.py files were found — broken discovery, not a "
            "legitimate skip",
            file=sys.stderr,
        )
        return 1

    list_problems: list = []
    list_all_counts: list = []
    for path_file in list_files:
        int_cap = cap_for_file(path_file, path_root, str_unit_dir, int_max)
        list_file_problems, list_counts = _file_findings(path_file, path_root, int_cap)
        list_problems.extend(list_file_problems)
        list_all_counts.extend(list_counts)

    print(f"assertion-site distribution across {len(list_all_counts)} test(s):")
    print(distribution_table(list_all_counts))

    if list_problems:
        for str_problem in list_problems:
            print(f"❌ {str_problem}", file=sys.stderr)
        print(
            f"\n{len(list_problems)} problem(s). Add '# one-assert-ok: <reason>' inside the "
            f"function to exempt a legitimate case — the reason is required.",
            file=sys.stderr,
        )
        return 1

    str_cap = f", max {int_max} per test in {str_unit_dir}/" if int_max else " (cap disabled)"
    print(
        f"✅ one-assert gate: {len(list_files)} file(s), {len(list_all_counts)} test(s) "
        f"checked{str_cap}, 0 findings"
    )
    return 0


if __name__ == "__main__":
    for cls_stream in (sys.stdout, sys.stderr):
        if hasattr(cls_stream, "reconfigure"):
            cls_stream.reconfigure(encoding="utf-8", errors="replace")
    sys.exit(main(sys.argv[1:]))
