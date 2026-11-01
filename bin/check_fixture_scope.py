"""Flag a non-function-scope pytest fixture in ``tests/`` without a written reason (#442).

WHY THIS EXISTS. Test order dependence is a RUNTIME property — it is about execution order
and the state a fixture leaves behind, and no static tool can see either. `pytest-randomly`
(wired alongside this gate) is the real detector: it shuffles order and makes a hidden
dependency fail, sometimes only under a particular seed. But a shuffle is also flaky BY
DESIGN — a bad order might happen not to be drawn, so the finding can surface days later in
an unrelated PR and read as CI flakiness rather than a real defect.

THIS GATE IS A PROXY, NOT A PROOF. It cannot detect order dependence — that would require
running the suite. What it CAN decide, from source alone, is the cheapest and most common way
independence gets broken by accident: a fixture whose `scope=` is widened from the default
(`"function"`) to `"module"`/`"class"`/`"session"`/`"package"`. A wider scope means the fixture
instance — and anything it mutates — is SHARED across tests, which is exactly the shape a
`get`-depends-on-a-prior-`post"` bug takes. Measured at the time this gate was written (see
blueprintx#442): every fixture across `templates/python-common/tests/` and every service
tier's `tests/unit/conftest.py` was already function-scoped — a clean baseline this gate exists
to PIN, not remediate. Nobody had chosen that; nothing recorded it. The first `scope="module"`
anyone adds would have removed the protection silently, in a diff that reads as a performance
improvement.

NOT decidable, and deliberately not attempted: whether a widened scope is actually SAFE (a
read-only fixture that mutates nothing is fine at any scope). That needs the same judgment a
human review already provides — the escape hatch below is exactly that judgment, written down.

THE ESCAPE HATCH: a `# fixture-scope-ok: <reason>` comment anywhere from the `@pytest.fixture`
decorator line through the `def` line (inclusive), with a non-empty reason — the same shape as
`# complexity-ok: <reason>` (`check_complexity.sh`) and `test-change-ok: <reason>`
(`check_assertion_weakening.py`) elsewhere in this repo.

Every finding is a hard error (exit 1). Discovery is `tests/**/*.py` under `--root`; zero files
found is itself a failure (see `audit_paths`) — the same vacuous-pass guard every gate in this
family carries (blueprintx#111).
"""

import ast
import pathlib
import re
import sys


SET_WIDE_SCOPES = frozenset({"module", "class", "session", "package"})

RE_JUSTIFICATION = re.compile(r"fixture-scope-ok:\s*(\S.*)")

PATH_ROOT = pathlib.Path(__file__).resolve().parent.parent

TUPLE_SKIP_DIRS = (
    ".git",
    ".claude",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".venv",
    "__pycache__",
    "node_modules",
)


class UnparsableFileError(Exception):
    """Raised when a discovered test file cannot be parsed.

    Its own type, not a printed warning and an empty result — a file this gate cannot read
    must not be silently reported as clean.
    """


def _decorator_call_name(node_dec: ast.expr) -> str | None:
    """Return a decorator's callable name when it looks like a fixture registration.

    Parameters
    ----------
    node_dec : ast.expr
        One entry of a function's ``decorator_list``.

    Returns
    -------
    str or None
        ``"fixture"`` for `@pytest.fixture(...)` / `@fixture(...)`; ``None`` for anything
        else, including a bare `@fixture` with no call (which carries no `scope=` to widen).
    """
    if not isinstance(node_dec, ast.Call):
        return None
    func = node_dec.func
    if isinstance(func, ast.Attribute):
        return func.attr
    if isinstance(func, ast.Name):
        return func.id
    return None


def _fixture_scope(node_call: ast.Call) -> str | None:
    """Return a fixture decorator's ``scope=`` keyword value, or ``None`` when absent.

    Parameters
    ----------
    node_call : ast.Call
        The `@pytest.fixture(...)` call node.

    Returns
    -------
    str or None
        The scope string when it is a plain string literal; ``None`` when unset or when the
        value is not a literal (e.g. a variable) — a dynamic scope is not decidable from
        source, so it is not flagged.
    """
    for kw in node_call.keywords:
        if kw.arg != "scope":
            continue
        if isinstance(kw.value, ast.Constant) and isinstance(kw.value.value, str):
            return kw.value.value
    return None


def _justified(list_lines: list, int_start: int, int_end: int) -> bool:
    """Return whether a written justification appears in a line range.

    Parameters
    ----------
    list_lines : list of str
        The file's lines (0-indexed list; line numbers below are 1-indexed).
    int_start : int
        First line to check (the decorator's own line), 1-indexed.
    int_end : int
        Last line to check (the `def` line), 1-indexed, inclusive.

    Returns
    -------
    bool
        ``True`` when a `fixture-scope-ok: <reason>` comment with a non-empty reason appears
        anywhere in the range.
    """
    for int_lineno in range(int_start, int_end + 1):
        if int_lineno < 1 or int_lineno > len(list_lines):
            continue
        cls_match = RE_JUSTIFICATION.search(list_lines[int_lineno - 1])
        if cls_match and cls_match.group(1).strip():
            return True
    return False


def _parse_or_raise(path_file: pathlib.Path, str_source: str) -> ast.Module:
    """Parse a file's source, raising the gate's own error type on failure.

    Parameters
    ----------
    path_file : pathlib.Path
        Path shown in the error (the file being parsed).
    str_source : str
        The file's full text.

    Returns
    -------
    ast.Module
        The parsed tree.
    """
    try:
        return ast.parse(str_source, filename=str(path_file))
    except SyntaxError as cls_err:
        raise UnparsableFileError(f"{path_file}: could not parse ({cls_err})") from cls_err


def _display_path(path_file: pathlib.Path) -> str:
    """Return a file path relative to ``PATH_ROOT`` when possible, else as given.

    Parameters
    ----------
    path_file : pathlib.Path
        The file to display.

    Returns
    -------
    str
        A shortened path for findings, falling back to the absolute path when the file
        sits outside ``PATH_ROOT`` (e.g. a filename passed directly by pre-commit).
    """
    try:
        return str(path_file.relative_to(PATH_ROOT))
    except ValueError:
        return str(path_file)


def _iter_fixture_decorators(cls_tree: ast.Module) -> list:
    """Return every `@pytest.fixture(...)` decorator paired with its function.

    Parameters
    ----------
    cls_tree : ast.Module
        A parsed test-file tree.

    Returns
    -------
    list of tuple
        ``(decorator_node, function_node)`` pairs, in tree-walk order.
    """
    list_pairs = []
    for cls_node in ast.walk(cls_tree):
        if not isinstance(cls_node, ast.FunctionDef | ast.AsyncFunctionDef):
            continue
        list_pairs.extend(
            (node_dec, cls_node)
            for node_dec in cls_node.decorator_list
            if _decorator_call_name(node_dec) == "fixture"
        )
    return list_pairs


def _violation_message(
    node_dec: ast.expr, cls_node: ast.FunctionDef, list_lines: list, str_shown: str
) -> str | None:
    """Return a finding for one fixture decorator, or ``None`` when it is clean.

    Parameters
    ----------
    node_dec : ast.expr
        The `@pytest.fixture(...)` decorator node.
    cls_node : ast.FunctionDef
        The fixture function it decorates.
    list_lines : list of str
        The file's lines, for the justification-comment search.
    str_shown : str
        The file's display path, for the finding message.

    Returns
    -------
    str or None
        A human-readable finding when the scope is widened and unjustified; ``None``
        otherwise (default scope, or a written `# fixture-scope-ok:` reason).
    """
    str_scope = _fixture_scope(node_dec)
    if str_scope not in SET_WIDE_SCOPES:
        return None
    if _justified(list_lines, node_dec.lineno, cls_node.lineno):
        return None
    return (
        f"{str_shown}:{cls_node.lineno}: fixture {cls_node.name}() is "
        f"scope={str_scope!r} — shared across tests with no written reason. Add "
        f"'# fixture-scope-ok: <reason>' on the decorator or def line, or narrow it "
        f"back to the default function scope."
    )


def file_problems(path_file: pathlib.Path) -> list:
    """Return one message per unjustified non-function-scope fixture in the file.

    Parameters
    ----------
    path_file : pathlib.Path
        Path to a test `.py` file.

    Returns
    -------
    list of str
        Human-readable findings; empty when every fixture is function-scoped or justified.
    """
    str_source = path_file.read_text(encoding="utf-8")
    cls_tree = _parse_or_raise(path_file, str_source)
    str_shown = _display_path(path_file)
    list_lines = str_source.splitlines()

    list_problems = []
    for node_dec, cls_node in _iter_fixture_decorators(cls_tree):
        str_msg = _violation_message(node_dec, cls_node, list_lines, str_shown)
        if str_msg is not None:
            list_problems.append(str_msg)
    return list_problems


def audit_paths() -> list:
    """Discover every test file under the repository's ``tests/`` tree.

    Returns
    -------
    list of pathlib.Path
        Sorted `.py` paths under any `tests/` directory below `PATH_ROOT`, skipping vendored
        and generated trees.
    """
    list_paths = []
    for path_file in PATH_ROOT.rglob("tests/**/*.py"):
        list_parts = path_file.relative_to(PATH_ROOT).parts
        if any(str_part in TUPLE_SKIP_DIRS for str_part in list_parts):
            continue
        list_paths.append(path_file)
    return sorted(list_paths)


_INT_FLAG_WITH_VALUE = 2


def main(list_argv: list) -> int:
    """Check every named (or discovered) test file for an unjustified wide-scope fixture.

    Parameters
    ----------
    list_argv : list of str
        ``["--root", <dir>]`` optionally, then filenames as pre-commit passes them. No
        filenames means audit the whole `tests/` tree under `--root`.

    Returns
    -------
    int
        0 when clean or every finding is justified, 1 on an unjustified widened scope, or
        when a file could not be parsed, or when discovery finds nothing to check.
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
        [pathlib.Path(str_name).resolve() for str_name in list_argv if str_name.endswith(".py")]
        if list_argv
        else audit_paths()
    )

    if bool_audit and not list_paths:
        print(
            f"❌ no test file found under {PATH_ROOT}/tests/ — this gate would pass "
            f"vacuously. Check the layout or --root."
        )
        return 1

    list_problems = []
    for path_file in list_paths:
        try:
            list_problems.extend(file_problems(path_file))
        except UnparsableFileError as cls_err:
            list_problems.append(str(cls_err))

    if not list_problems:
        print(f"✅ fixture-scope check OK ({len(list_paths)} file(s) checked)")
        return 0

    for str_problem in list_problems:
        print(f"⚠️  {str_problem}")
    print(
        f"\n{len(list_problems)} finding(s). This is a PROXY, not proof of order-independence "
        f"— pair it with `pytest-randomly` (which actually runs the suite out of order). A "
        f"widened scope is not always wrong; it just needs a reason on the record."
    )
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
