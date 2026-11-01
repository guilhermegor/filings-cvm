"""Detect a PR that turns a red test green by weakening its assertion (blueprintx#324).

THE DEFECT. `check_gate_integrity.py` (blueprintx#309/#313) watches CONFIGURATION — a
pre-commit hook removed, a rule dropped from `ruff.toml`. But the cheapest way to make a red
build green is not in any config file, it is editing the assertion itself:

    - assert to_decimal_strict("1.999", 2) == Decimal("1.99")
    + assert to_decimal_strict("1.999", 2) == Decimal("2.00")

That diff turns a money-truncation BUG into a green suite, and nothing in the repo objects.
blueprintx#323 hit exactly this shape for real, and blueprintx#289's review caught a human
doing the operator-level version by hand (`==` weakened to `in`).

WHY A NEW FILE, NOT AN EXTENSION OF `check_gate_integrity.py` (the issue's stated
preference). `check_gate_integrity.py` is held by another open PR (#330, wiring the
Makefile-pairing gate) in the same working session — editing it here would collide. This
file duplicates a small slice of that script's git-diffing plumbing (`_git`, `show`,
`changed_paths`, `default_branch`, `resolve_base`, `pr_body_text`, `apply_root_flag`) rather
than importing it, because importing a sibling gate mid-flight under another open PR is a
brittle dependency on an interface that may still move. The two files audit different
QUESTIONS (config weakening vs. assertion weakening) rather than being two copies of the
same check, so this is not the drift `check_codespell_sync.sh` exists to police — but the
duplicated plumbing is real and should collapse into one shared module once #330 lands.

WHAT IS DECIDABLE (measured against real history before being written — see the PR body for
the count). Comparing an assertion's AST shape between the merge-base version of a test file
and the index (staged/HEAD) version, for a function whose name is unchanged, catches:

- a test function DELETED, or a whole test file deleted
- a test's assertion COUNT decreased (an assertion removed) between old and new
- an assertion trivialised to a bare truthy constant (`assert True`)
- an `==` comparison weakened by OPERATOR to `in` / `not in` / `>=` / `<=` / `!=`
  (blueprintx#289's live example)
- a `self.assertEqual`-family call weakened to a looser call (`assertTrue`,
  `assertIsNotNone`, `assertIn`, ...)
- `pytest.raises(<SpecificError>)` broadened to no type, `Exception`, or `BaseException`
- a `@pytest.mark.skip` / `@pytest.mark.xfail` newly added to a test that did not carry it
- an `assertEqual`/`==` EXPECTED VALUE changed on one side while a non-test file *also*
  changed in the same diff — the #323 shape. Gated on production code changing in the same
  diff on purpose: a test correction in a PR that touches no production code is legitimate
  and must pass (issue's should-fail witness #3).

NOT decidable, and deliberately not attempted: whether a changed value is the *right* one.
That requires knowing what the test means, which a gate cannot know and must not guess.

MATCHING IS POSITIONAL, not semantic. Assertions inside one function are compared by their
appearance ORDER, old vs new. A reordering that leaves the same set of checks intact can
misreport — noted as the one deliberate simplification measurement did not need to narrow
further (ponytail: escape hatch below covers the rare false positive).

THE ESCAPE HATCH mirrors `check_gate_integrity.py`'s convention: a `test-change-ok: <reason>`
line, with a non-empty reason, in the PR body (`GITHUB_EVENT_PATH`) or as a trailer on any
commit since the merge-base.

CI must check out with `fetch-depth: 0` — a shallow clone has no common ancestor to resolve.
"""

import ast
import json
import os
import pathlib
import re
import subprocess
import sys


PATH_ROOT = pathlib.Path(__file__).resolve().parent.parent

RE_JUSTIFICATION = re.compile(r"^\s*test-change-ok:\s*(\S.*)$", re.I | re.M)
RE_TEST_PATH = re.compile(r"(^|/)tests/.*test_[^/]+\.py$")
RE_DOC_PATH = re.compile(r"\.md$|(^|/)docs/")

STR_INDEX_REF = ""

_INT_MIN_FIELDS = 2
_MIN_EQ_ARGS = 2

_WEAK_FROM_EQ = frozenset({"In", "NotIn", "GtE", "LtE", "NotEq"})
_OP_SYMBOLS = {"In": "in", "NotIn": "not in", "GtE": ">=", "LtE": "<=", "NotEq": "!="}

_WEAKER_ASSERT_CALLS = {
    "assertEqual": frozenset(
        {
            "assertTrue",
            "assertIsNotNone",
            "assertIn",
            "assertIsInstance",
            "assertFalse",
            "assertIsNone",
        }
    ),
    "assertIs": frozenset({"assertIsNotNone", "assertTrue"}),
    "assertListEqual": frozenset({"assertTrue", "assertIn"}),
    "assertDictEqual": frozenset({"assertTrue", "assertIn"}),
}


def _git(list_args: list) -> str:
    """Run a read-only git command and return stdout (empty string on failure).

    Parameters
    ----------
    list_args : list of str
        Arguments after ``git``.

    Returns
    -------
    str
        Captured stdout, stripped.
    """
    try:
        cls_proc = subprocess.run(  # noqa: S603
            ["git", *list_args],  # noqa: S607
            capture_output=True,
            text=True,
            check=False,
            cwd=PATH_ROOT,
        )
    except OSError:
        return ""
    return cls_proc.stdout


def show(str_ref: str, str_path: str) -> str | None:
    """Return a blob's text content at a git ref/path, or ``None`` when unreadable.

    Parameters
    ----------
    str_ref : str
        A commit-ish, or ``""`` for the index (``STR_INDEX_REF``).
    str_path : str
        Repository-relative path.

    Returns
    -------
    str or None
        The blob's content; ``None`` when the path does not exist there or is not valid
        UTF-8 (mirrors ``check_gate_integrity.py::show`` — a binary defines nothing to
        compare, and decoding by extension is the wrong fix, see that file's own note).
    """
    cls_proc = subprocess.run(  # noqa: S603
        ["git", "show", f"{str_ref}:{str_path}"],  # noqa: S607
        capture_output=True,
        check=False,
    )
    if cls_proc.returncode != 0:
        return None
    try:
        return cls_proc.stdout.decode("utf-8")
    except UnicodeDecodeError:
        return None


def default_branch() -> str:
    """Return a resolvable ref for the repository's default branch.

    Returns
    -------
    str
        ``origin/<name>`` when only the remote-tracking branch exists, else a local
        ``<name>``; falls back to the literal ``"main"``. See
        ``check_gate_integrity.py::default_branch`` (blueprintx#313) for why the remote
        prefix is kept rather than stripped.
    """
    str_ref = _git(["symbolic-ref", "--quiet", "--short", "refs/remotes/origin/HEAD"]).strip()
    if str_ref:
        return str_ref
    for str_candidate in ("main", "master"):
        for str_full in (f"origin/{str_candidate}", str_candidate):
            if _git(["rev-parse", "--verify", "--quiet", str_full]).strip():
                return str_full
    return "main"


def changed_paths(str_base: str) -> list:
    """Return the branch's cumulative changed paths with their status, INDEX included.

    Parameters
    ----------
    str_base : str
        The merge-base commit to diff against.

    Returns
    -------
    list of tuple
        ``(status_letter, source_path, destination_path)``. The two paths differ only for
        a rename; the base version lives at the source, the head version at the
        destination (blueprintx#590).
    """
    str_out = _git(["diff", "--cached", "--name-status", "--find-renames", str_base])
    list_rows = []
    for str_line in str_out.splitlines():
        list_parts = str_line.split("\t")
        if len(list_parts) >= _INT_MIN_FIELDS:
            list_rows.append((list_parts[0][0], list_parts[1], list_parts[-1]))
    return list_rows


def pr_body_text() -> str:
    """Return the current PR's body from the GitHub Actions event payload (I/O seam).

    Returns
    -------
    str
        The PR body, or ``""`` outside a ``pull_request`` workflow run.
    """
    str_event_path = os.environ.get("GITHUB_EVENT_PATH", "")
    if not str_event_path:
        return ""
    try:
        dict_event = json.loads(pathlib.Path(str_event_path).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return ""
    dict_pr = dict_event.get("pull_request") or {}
    return str(dict_pr.get("body") or "")


def justification_reason(str_base: str) -> str:
    """Return the ``test-change-ok`` reason from the PR body or a commit trailer, or ``""``.

    Parameters
    ----------
    str_base : str
        The merge-base commit — commit messages since it are searched for a trailer.

    Returns
    -------
    str
        The non-empty reason text, or ``""`` when no valid justification is present.
    """
    str_trailers = _git(["log", f"{str_base}..HEAD", "--format=%B"])
    for str_text in (pr_body_text(), str_trailers):
        cls_match = RE_JUSTIFICATION.search(str_text)
        if cls_match and cls_match.group(1).strip():
            return cls_match.group(1).strip()
    return ""


def apply_root_flag(list_argv: list) -> bool:
    """Parse a leading ``--root <dir>`` flag, updating ``PATH_ROOT`` in place.

    Parameters
    ----------
    list_argv : list of str
        The raw argv tail.

    Returns
    -------
    bool
        ``False`` on bad usage (already reported to stdout); ``True`` otherwise.
    """
    global PATH_ROOT  # noqa: PLW0603
    if list_argv[:1] != ["--root"]:
        return True
    if len(list_argv) < 2:  # noqa: PLR2004
        print("❌ --root needs a directory")
        return False
    PATH_ROOT = pathlib.Path(list_argv[1]).resolve()
    return True


def merge_heads() -> list:
    """Return every incoming commit of a merge in progress (several for an octopus).

    Mid-merge the index already holds the incoming side's files but HEAD is still the
    pre-merge tip, so a base taken from HEAD alone charges the incoming delta to this branch.
    ``rev-parse MERGE_HEAD`` resolves only the first line, so the file itself is read.

    Returns
    -------
    list of str
        One commit hash per incoming head; empty when no merge is in progress.
    """
    str_path = _git(["rev-parse", "--git-path", "MERGE_HEAD"]).strip()
    path_file = pathlib.Path(str_path) if str_path else None
    if path_file is None:
        return []
    if not path_file.is_absolute():
        path_file = PATH_ROOT / path_file
    return path_file.read_text(encoding="utf-8").split() if path_file.is_file() else []


def resolve_base() -> str | None:
    """Resolve the merge-base to diff against.

    Returns
    -------
    str or None
        ``None`` means a real skip: HEAD already IS the resolved ref. An empty string means
        no ref could be resolved at all, and is never treated as a skip — ``main()`` fails
        the run on it instead of passing it silently (mirrors blueprintx#313).
    """
    str_ref = default_branch()
    str_base = _git(["merge-base", str_ref, "HEAD", *merge_heads()]).strip()
    if not str_base:
        print(f"❌ could not resolve a merge-base against {str_ref!r} — refusing to pass blind.")
        return ""
    str_head = _git(["rev-parse", "HEAD"]).strip()
    if str_base == str_head:
        print("✅ assertion-weakening check skipped — on the default branch (nothing to diff).")
        return None
    return str_base


def _dump(node: ast.AST) -> str:
    """Return a location-independent structural fingerprint of an AST node.

    Parameters
    ----------
    node : ast.AST
        Any expression node.

    Returns
    -------
    str
        ``ast.dump`` output with no line/column noise, so two structurally identical
        expressions compare equal regardless of where they sit in the file.
    """
    return ast.dump(node, annotate_fields=False, include_attributes=False)


def _is_trivial_assert_test(node_test: ast.expr) -> bool:
    """Return whether an ``assert`` test is a bare truthy constant (``assert True``, ``1``).

    Parameters
    ----------
    node_test : ast.expr
        The expression after ``assert``.

    Returns
    -------
    bool
        ``True`` only for a truthy ``ast.Constant`` — an assertion that can never fail.
    """
    return isinstance(node_test, ast.Constant) and bool(node_test.value)


def _call_attr(node_call: ast.Call) -> str | None:
    """Return a call's method name when it is an attribute call (``self.assertX(...)``).

    Parameters
    ----------
    node_call : ast.Call
        The call node.

    Returns
    -------
    str or None
        The attribute name, or ``None`` for a bare-name call.
    """
    func = node_call.func
    return func.attr if isinstance(func, ast.Attribute) else None


def _is_assert_call(node_call: ast.Call) -> bool:
    """Return whether a call is a unittest-style ``self.assertX(...)`` assertion.

    Parameters
    ----------
    node_call : ast.Call
        The call node.

    Returns
    -------
    bool
        ``True`` when the attribute name starts with ``assert``.
    """
    str_attr = _call_attr(node_call)
    return str_attr is not None and str_attr.startswith("assert")


def _raises_func_name(node_call: ast.Call) -> str | None:
    """Return the callable name of a context-manager call (``pytest.raises`` / ``raises``).

    Parameters
    ----------
    node_call : ast.Call
        A ``with`` item's context expression.

    Returns
    -------
    str or None
        ``"raises"`` when matched, else ``None``.
    """
    func = node_call.func
    if isinstance(func, ast.Attribute):
        return func.attr
    if isinstance(func, ast.Name):
        return func.id
    return None


def _is_raises_with(node_with: ast.With) -> bool:
    """Return whether a ``with`` block is a ``pytest.raises(...)`` context.

    Parameters
    ----------
    node_with : ast.With
        The ``with`` statement.

    Returns
    -------
    bool
        ``True`` when any item's context expression calls ``raises``.
    """
    for item in node_with.items:
        expr = item.context_expr
        if isinstance(expr, ast.Call) and _raises_func_name(expr) == "raises":
            return True
    return False


def _raises_exception_name(node_with: ast.With) -> str | None:
    """Return the exception type name a ``pytest.raises(...)`` block declares.

    Parameters
    ----------
    node_with : ast.With
        A ``with`` statement already known to be a ``raises`` context.

    Returns
    -------
    str or None
        The exception name (``"tuple"`` for a multi-type tuple), or ``None`` when
        ``raises`` was called with no positional exception type.
    """
    for item in node_with.items:
        expr = item.context_expr
        if not (isinstance(expr, ast.Call) and _raises_func_name(expr) == "raises"):
            continue
        if not expr.args:
            return None
        arg0 = expr.args[0]
        if isinstance(arg0, ast.Name):
            return arg0.id
        if isinstance(arg0, ast.Attribute):
            return arg0.attr
        if isinstance(arg0, ast.Tuple):
            return "tuple"
        return None
    return None


def _function_checks(node_fn: ast.FunctionDef) -> list:
    """Return the ordered ``(kind, node)`` assertion-like checks inside a function.

    Parameters
    ----------
    node_fn : ast.FunctionDef
        The test function (or method).

    Returns
    -------
    list of tuple
        ``("assert" | "call" | "raises", ast.AST)``, in source order. Does not descend
        into nested function/lambda definitions — those are their own unit.
    """
    list_checks: list = []

    def _walk(node: ast.AST) -> None:
        for child in ast.iter_child_nodes(node):
            if isinstance(child, ast.FunctionDef | ast.AsyncFunctionDef | ast.Lambda):
                continue
            if isinstance(child, ast.Assert):
                list_checks.append(("assert", child))
            elif isinstance(child, ast.With) and _is_raises_with(child):
                list_checks.append(("raises", child))
            elif (
                isinstance(child, ast.Expr)
                and isinstance(child.value, ast.Call)
                and _is_assert_call(child.value)
            ):
                list_checks.append(("call", child.value))
            _walk(child)

    _walk(node_fn)
    return list_checks


def _skip_or_xfail_markers(node_fn: ast.FunctionDef) -> set:
    """Return the ``skip``/``xfail`` marker names decorating a test function.

    Parameters
    ----------
    node_fn : ast.FunctionDef
        The test function.

    Returns
    -------
    set of str
        Subset of ``{"skip", "xfail"}`` present as ``@pytest.mark.<name>`` decorators.
    """
    set_out = set()
    for dec in node_fn.decorator_list:
        target = dec.func if isinstance(dec, ast.Call) else dec
        if isinstance(target, ast.Attribute) and target.attr in {"skip", "xfail"}:
            set_out.add(target.attr)
    return set_out


def _is_literal_ish(node: ast.expr) -> bool:
    """Return whether a node is a literal, or a plain aggregate/call of literals.

    Parameters
    ----------
    node : ast.expr
        An expression to classify.

    Returns
    -------
    bool
        ``True`` for ``ast.Constant``, a signed constant, a tuple/list/set of literals,
        or a call (``Decimal("1.99")``, ``date(2026, 6, 8)``) whose every argument is
        itself literal-ish. ``False`` for anything referencing a name, attribute value,
        or subscript — those are CODE, not an expected value, and conflating the two is
        a measured false positive (a rewritten call-under-test wrongly read as a
        tampered expectation; see the module docstring's PR history note).
    """
    if isinstance(node, ast.Constant):
        return True
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.UAdd | ast.USub):
        return _is_literal_ish(node.operand)
    if isinstance(node, ast.Tuple | ast.List | ast.Set):
        return all(_is_literal_ish(elt) for elt in node.elts)
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name | ast.Attribute):
        return all(_is_literal_ish(a) for a in node.args) and all(
            _is_literal_ish(kw.value) for kw in node.keywords
        )
    return False


def _value_side_changed(cmp_old: ast.Compare, cmp_new: ast.Compare) -> bool:
    """Return whether a LITERAL side of an ``==`` comparison changed, the other unchanged.

    Parameters
    ----------
    cmp_old : ast.Compare
        The comparison at the merge-base.
    cmp_new : ast.Compare
        The comparison in this change.

    Returns
    -------
    bool
        ``True`` only when one side is unchanged CODE and the other side is a literal
        in both versions with a different value — an expected-value edit, never a
        rewrite of the call/expression under test (measured: ``dict_calls["n"]`` ->
        ``cls_call.call_count`` on an unchanged ``== 1`` must NOT fire; ``Decimal("1.99")``
        -> ``Decimal("2.00")`` on an unchanged left side MUST).
    """
    str_ol, str_nl = _dump(cmp_old.left), _dump(cmp_new.left)
    str_or, str_nr = _dump(cmp_old.comparators[0]), _dump(cmp_new.comparators[0])
    if str_ol == str_nl and str_or != str_nr:
        return _is_literal_ish(cmp_old.comparators[0]) and _is_literal_ish(cmp_new.comparators[0])
    if str_or == str_nr and str_ol != str_nl:
        return _is_literal_ish(cmp_old.left) and _is_literal_ish(cmp_new.left)
    return False


def _compare_assert(old_node: ast.Assert, new_node: ast.Assert, bool_prod_changed: bool) -> str:
    """Return a weakening message for an ``assert``-to-``assert`` pair, or ``""``.

    Parameters
    ----------
    old_node : ast.Assert
        The assertion at the merge-base.
    new_node : ast.Assert
        The assertion in this change.
    bool_prod_changed : bool
        Whether a non-test file also changed in this diff — gates the value-changed rule.

    Returns
    -------
    str
        A human-readable finding, or ``""`` when nothing decidable weakened.
    """
    cmp_old, cmp_new = old_node.test, new_node.test
    if _is_trivial_assert_test(cmp_new) and not _is_trivial_assert_test(cmp_old):
        return "trivialised to a bare truthy constant (assert True)"
    if not (isinstance(cmp_old, ast.Compare) and isinstance(cmp_new, ast.Compare)):
        return ""
    if len(cmp_old.ops) != 1 or len(cmp_new.ops) != 1:
        return ""
    str_old_op, str_new_op = type(cmp_old.ops[0]).__name__, type(cmp_new.ops[0]).__name__
    if str_old_op == "Eq" and str_new_op in _WEAK_FROM_EQ:
        return f"operator weakened from == to {_OP_SYMBOLS.get(str_new_op, str_new_op)}"
    bool_value_edit = str_old_op == "Eq" and str_new_op == "Eq" and bool_prod_changed
    if bool_value_edit and _value_side_changed(cmp_old, cmp_new):
        return "expected value changed while production code changed in the same diff"
    return ""


def _compare_call(old_node: ast.Call, new_node: ast.Call, bool_prod_changed: bool) -> str:
    """Return a weakening message for a unittest-style call pair, or ``""``.

    Parameters
    ----------
    old_node : ast.Call
        The ``self.assertX(...)`` call at the merge-base.
    new_node : ast.Call
        The call in this change.
    bool_prod_changed : bool
        Whether a non-test file also changed in this diff.

    Returns
    -------
    str
        A human-readable finding, or ``""``.
    """
    str_old_attr, str_new_attr = _call_attr(old_node), _call_attr(new_node)
    if str_old_attr is None or str_new_attr is None:
        return ""
    if str_new_attr in _WEAKER_ASSERT_CALLS.get(str_old_attr, frozenset()):
        return f"{str_old_attr}() weakened to {str_new_attr}()"
    if (
        str_old_attr == str_new_attr == "assertEqual"
        and bool_prod_changed
        and len(old_node.args) >= _MIN_EQ_ARGS
        and len(new_node.args) >= _MIN_EQ_ARGS
    ):
        str_oa0, str_na0 = _dump(old_node.args[0]), _dump(new_node.args[0])
        str_oa1, str_na1 = _dump(old_node.args[1]), _dump(new_node.args[1])
        bool_a1_is_the_edit = (
            str_oa0 == str_na0
            and str_oa1 != str_na1
            and _is_literal_ish(old_node.args[1])
            and _is_literal_ish(new_node.args[1])
        )
        bool_a0_is_the_edit = (
            str_oa1 == str_na1
            and str_oa0 != str_na0
            and _is_literal_ish(old_node.args[0])
            and _is_literal_ish(new_node.args[0])
        )
        if bool_a1_is_the_edit or bool_a0_is_the_edit:
            return "expected value changed while production code changed in the same diff"
    return ""


def _compare_raises(old_node: ast.With, new_node: ast.With) -> str:
    """Return a weakening message for a ``pytest.raises`` pair, or ``""``.

    Parameters
    ----------
    old_node : ast.With
        The ``raises`` block at the merge-base.
    new_node : ast.With
        The ``raises`` block in this change.

    Returns
    -------
    str
        A human-readable finding, or ``""``.
    """
    str_old_exc = _raises_exception_name(old_node)
    str_new_exc = _raises_exception_name(new_node)
    set_broad = {None, "Exception", "BaseException"}
    if str_old_exc and str_old_exc not in set_broad and str_new_exc in set_broad:
        str_shown_new = str_new_exc or "no exception type"
        return f"pytest.raises broadened from {str_old_exc} to {str_shown_new}"
    return ""


def _compare_pair(tuple_old: tuple, tuple_new: tuple, bool_prod_changed: bool) -> str:
    """Dispatch a same-position check pair to its comparator by kind.

    Parameters
    ----------
    tuple_old : tuple
        ``(kind, node)`` at the merge-base.
    tuple_new : tuple
        ``(kind, node)`` in this change.
    bool_prod_changed : bool
        Whether a non-test file also changed in this diff.

    Returns
    -------
    str
        A human-readable finding, or ``""`` when the pair carries no decidable weakening
        (including every kind-mismatch other than a ``raises`` block replaced outright).
    """
    old_kind, old_node = tuple_old
    new_kind, new_node = tuple_new
    if old_kind == "raises" and new_kind != "raises":
        return "pytest.raises removed or replaced by a plain assertion"
    if old_kind == "raises" and new_kind == "raises":
        return _compare_raises(old_node, new_node)
    if old_kind == "assert" and new_kind == "assert":
        return _compare_assert(old_node, new_node, bool_prod_changed)
    if old_kind == "call" and new_kind == "call":
        return _compare_call(old_node, new_node, bool_prod_changed)
    if old_kind == "call" and new_kind == "assert":
        return _compare_call_to_assert(old_node, new_node)
    return ""


_CALL_AS_OPERATOR = {
    "assertEqual": "Eq",
    "assertListEqual": "Eq",
    "assertDictEqual": "Eq",
    "assertIn": "In",
    "assertIs": "Is",
    "assertIsNot": "IsNot",
    "assertNotEqual": "NotEq",
}


def _compare_call_to_assert(old_node: ast.Call, new_node: ast.Assert) -> str:
    """Return a weakening message when a unittest call became a weaker bare ``assert``.

    Rewriting ``self.assertEqual(a, b)`` as ``assert a in b`` changes the assertion's kind, so
    a same-kind comparison never sees it and the check count stays identical. Normalising the
    call to the operator it is equivalent to makes the pair comparable.

    Parameters
    ----------
    old_node : ast.Call
        The ``self.assertX(...)`` call at the merge-base.
    new_node : ast.Assert
        The bare ``assert`` statement on the branch. Its ``.test`` carries the comparison --
        the checks list stores the statement, not the expression.

    Returns
    -------
    str
        A human-readable finding, or ``""`` when the rewrite is not a decidable weakening
        (an unlisted call, or a new form that is not a simple comparison).
    """
    if not isinstance(old_node.func, ast.Attribute):
        return ""
    str_old_op = _CALL_AS_OPERATOR.get(old_node.func.attr, "")
    if not str_old_op:
        return ""
    expr_new = new_node.test if isinstance(new_node, ast.Assert) else new_node
    if _is_trivial_assert_test(expr_new):
        return f"{old_node.func.attr} trivialised to a bare truthy constant"
    if not isinstance(expr_new, ast.Compare) or len(expr_new.ops) != 1:
        return ""
    str_new_op = type(expr_new.ops[0]).__name__
    if str_old_op == "Eq" and str_new_op in _WEAK_FROM_EQ:
        str_symbol = _OP_SYMBOLS.get(str_new_op, str_new_op)
        return f"{old_node.func.attr} weakened to a bare assert with {str_symbol}"
    return ""


def parse_functions(str_source: str) -> dict | None:
    """Return every ``test_*`` function/method defined in a source file, by name.

    Parameters
    ----------
    str_source : str
        Full file content.

    Returns
    -------
    dict or None
        ``{name: ast.FunctionDef}``, or ``None`` when the source does not parse — a
        distinct state from "parses clean with zero tests" (three states: flagged /
        clean / could not parse).
    """
    try:
        cls_tree = ast.parse(str_source)
    except SyntaxError:
        return None
    dict_funcs = {}
    _index_tests(cls_tree, "", dict_funcs)
    return dict_funcs


def _index_tests(node_parent: ast.AST, str_prefix: str, dict_funcs: dict) -> None:
    """Index every ``test_*`` function under ``node_parent`` by its qualified name.

    Qualified, not bare: two classes in one module routinely define the same method name, and
    a bare key silently overwrites the first -- so weakening the overwritten one produced no
    finding. See the backlog note.

    Parameters
    ----------
    node_parent : ast.AST
        Module or class body to walk. Only direct children are visited; nested classes
        recurse with an extended prefix.
    str_prefix : str
        Dotted prefix accumulated from enclosing classes, ``""`` at module level.
    dict_funcs : dict
        Accumulator, mutated in place: qualified name to AST node.
    """
    for node in ast.iter_child_nodes(node_parent):
        if isinstance(node, ast.ClassDef):
            _index_tests(node, f"{str_prefix}{node.name}.", dict_funcs)
        elif isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef) and node.name.startswith(
            "test_"
        ):
            dict_funcs[f"{str_prefix}{node.name}"] = node


def _function_findings(
    str_path: str,
    str_name: str,
    node_old: ast.FunctionDef,
    node_new: ast.FunctionDef,
    bool_prod_changed: bool,
) -> list:
    """Return every weakening finding for one test function present in both versions.

    Parameters
    ----------
    str_path : str
        Repository-relative path, for message prefixing.
    str_name : str
        The test function's name.
    node_old : ast.FunctionDef
        The function at the merge-base.
    node_new : ast.FunctionDef
        The function in this change.
    bool_prod_changed : bool
        Whether a non-test file also changed in this diff.

    Returns
    -------
    list of str
        Findings, in the order the underlying checks appear.
    """
    list_problems = []
    set_new_markers = _skip_or_xfail_markers(node_new) - _skip_or_xfail_markers(node_old)
    if set_new_markers:
        str_markers = "/".join(sorted(set_new_markers))
        list_problems.append(f"{str_path}: {str_name}() newly marked {str_markers}")

    list_old_checks = _function_checks(node_old)
    list_new_checks = _function_checks(node_new)
    if len(list_new_checks) < len(list_old_checks):
        list_problems.append(
            f"{str_path}: {str_name}() lost {len(list_old_checks) - len(list_new_checks)} "
            f"assertion(s) (had {len(list_old_checks)}, now {len(list_new_checks)})"
        )
    for tuple_old, tuple_new in zip(list_old_checks, list_new_checks, strict=False):
        str_msg = _compare_pair(tuple_old, tuple_new, bool_prod_changed)
        if str_msg:
            list_problems.append(f"{str_path}: {str_name}() line {tuple_new[1].lineno}: {str_msg}")
    return list_problems


def _file_findings(
    str_path: str, str_old_text: str, str_new_text: str, bool_prod_changed: bool
) -> list:
    """Return every weakening finding for one changed test file.

    Parameters
    ----------
    str_path : str
        Repository-relative path.
    str_old_text : str
        Content at the merge-base.
    str_new_text : str
        Content in this change.
    bool_prod_changed : bool
        Whether a non-test file also changed in this diff.

    Returns
    -------
    list of str
        One ``could not parse`` finding when either version fails to parse (a file not
        checked is a finding in its own right, never read as clean); otherwise the
        combined per-function findings.
    """
    dict_old_funcs = parse_functions(str_old_text)
    dict_new_funcs = parse_functions(str_new_text)
    if dict_old_funcs is None or dict_new_funcs is None:
        return [f"{str_path}: could not parse — not checked"]
    list_problems = []
    for str_name, node_old in dict_old_funcs.items():
        node_new = dict_new_funcs.get(str_name)
        if node_new is None:
            list_problems.append(f"{str_path}: test {str_name!r} deleted")
            continue
        list_problems.extend(
            _function_findings(str_path, str_name, node_old, node_new, bool_prod_changed)
        )
    return list_problems


def _touches_production_code(list_changed: list) -> bool:
    """Return whether the diff touches anything besides tests and docs.

    Parameters
    ----------
    list_changed : list of tuple
        ``(status_letter, source_path, destination_path)`` rows from ``changed_paths``.

    Returns
    -------
    bool
        ``True`` when at least one changed path is neither a test file nor
        documentation — the signal that gates the expected-value-changed rule.
    """
    for str_status, str_src, str_path in list_changed:
        tuple_paths = (str_src, str_path) if str_status == "R" else (str_path,)
        if any(
            not (RE_TEST_PATH.search(str_p) or RE_DOC_PATH.search(str_p)) for str_p in tuple_paths
        ):
            return True
    return False


def _test_file_removed(str_status: str, str_src: str, str_path: str) -> bool:
    """Return whether a row takes a test file out of the suite (deleted, or moved off tests/).

    Parameters
    ----------
    str_status : str
        The row's status letter.
    str_src : str
        The row's source path.
    str_path : str
        The row's destination path.

    Returns
    -------
    bool
        ``True`` for ``D`` on a test path, or ``R`` from a test path to a non-test path.
    """
    if str_status == "D":
        return bool(RE_TEST_PATH.search(str_path))
    moved_off = RE_TEST_PATH.search(str_src) and not RE_TEST_PATH.search(str_path)
    return str_status == "R" and bool(moved_off)


def _removed_findings(str_base: str, str_path: str) -> list:
    """Return the findings for a test file that left the suite.

    Parameters
    ----------
    str_base : str
        The merge-base commit.
    str_path : str
        The test file's path at the base.

    Returns
    -------
    list of str
        One finding when the base file held tests (or cannot be parsed), else empty.
    """
    str_old = show(str_base, str_path)
    dict_old_funcs = parse_functions(str_old) if str_old is not None else {}
    if str_old is not None and dict_old_funcs is None:
        return [f"{str_path}: could not parse the removed test file — not checked"]
    if dict_old_funcs:
        int_n = len(dict_old_funcs)
        return [f"{str_path}: entire test file deleted or moved out of tests/ ({int_n} test(s))"]
    return []


def collect_problems(list_changed: list, str_base: str) -> list:
    """Return every weakening finding across the branch's changed test files.

    Parameters
    ----------
    list_changed : list of tuple
        ``(status_letter, source_path, destination_path)`` rows from ``changed_paths``.
    str_base : str
        The merge-base commit.

    Returns
    -------
    list of str
        Combined findings from deleted test files and modified ones.
    """
    list_problems = []
    bool_prod_changed = _touches_production_code(list_changed)
    for str_status, str_src, str_path in list_changed:
        if _test_file_removed(str_status, str_src, str_path):
            list_problems.extend(_removed_findings(str_base, str_src))
            continue
        if not RE_TEST_PATH.search(str_path):
            continue
        str_new = show(STR_INDEX_REF, str_path)
        str_old = show(str_base, str_src) if RE_TEST_PATH.search(str_src) else None
        if str_new is None or str_old is None:
            continue
        list_problems.extend(_file_findings(str_path, str_old, str_new, bool_prod_changed))
    return list_problems


def report(list_problems: list, str_base: str, int_changed_count: int) -> int:
    """Print findings and the verdict, resolving the justification escape hatch.

    Parameters
    ----------
    list_problems : list of str
        Findings from ``collect_problems``.
    str_base : str
        The merge-base commit — passed through to ``justification_reason``.
    int_changed_count : int
        Total changed-path count, shown on a clean pass.

    Returns
    -------
    int
        0 when clean or justified, 1 on an unjustified weakening.
    """
    if not list_problems:
        print(f"✅ assertion-weakening check OK ({int_changed_count} changed file(s) checked)")
        return 0

    for str_problem in list_problems:
        print(f"⚠️  {str_problem}")

    str_reason = justification_reason(str_base)
    if str_reason:
        print(f"\n✅ justified: test-change-ok: {str_reason}")
        return 0

    print(
        f"\n❌ {len(list_problems)} assertion-weakening change(s) with no justification. Add a "
        f"'test-change-ok: <reason>' line to the PR body or as a commit trailer — the reason "
        f"is required, matching 'gate-change-ok: <reason>' elsewhere in this repo."
    )
    return 1


def main(list_argv: list) -> int:
    """Check the branch's cumulative diff for an unjustified assertion weakening.

    Parameters
    ----------
    list_argv : list of str
        ``["--root", <dir>]`` or empty.

    Returns
    -------
    int
        0 when clean or justified, 1 on an unjustified weakening.
    """
    if not apply_root_flag(list_argv):
        return 1

    str_base = resolve_base()
    if str_base is None:
        return 0
    if not str_base:
        return 1

    list_changed = changed_paths(str_base)
    list_problems = collect_problems(list_changed, str_base)
    return report(list_problems, str_base, len(list_changed))


if __name__ == "__main__":
    for cls_stream in (sys.stdout, sys.stderr):
        if hasattr(cls_stream, "reconfigure"):
            cls_stream.reconfigure(encoding="utf-8", errors="replace")

    sys.exit(main(sys.argv[1:]))
