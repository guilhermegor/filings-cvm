"""Detect a PR that weakens a quality gate without an explicit justification.

THE DEFECT (blueprintx#309). Nothing today distinguishes "fixed the code" from "deleted the
check that failed" — both produce a green PR, and this is the one failure that survives every
other control, because it disarms them. With ``required_approving_review_count`` pinned at 0
(a solo maintainer cannot self-approve, so any human gate is unsatisfiable — see
``enable_repo_rules.sh``), this has to be a deterministic gate, not a reviewer's judgement call.

WHY DIFF-SCOPED, NOT WHOLE-TREE — the one deliberate departure from this file's siblings.
``check_function_length.py`` / ``check_complexity.sh`` audit a PROPERTY of the current tree, so
whole-tree is the right shape for them. This gate audits a DELTA — a hook that was never added
is not a violation, but one that WAS there and got REMOVED is — so it has to compare against
something. It diffs the index (staged content locally; equal to HEAD on a clean CI checkout)
against ``merge-base(HEAD, <default-branch>)``, the same shape as ``check_backlog_ledger.py``.

WHAT COUNTS AS WEAKENING (every one of these is a delta, read straight off the five config
files a change touches — never off arbitrary source):

- a pre-commit hook (``- id: <x>``) removed from a changed ``.pre-commit-config.yaml``
- a rule removed from a changed ``ruff.toml``'s ``[lint] select``
- a rule ADDED to ``ignore`` or ``per-file-ignores`` — RULE level, in either config file
- a path ADDED to ``ruff.toml``'s ``exclude`` or ``mypy.ini``'s ``[mypy] exclude``
- a ``[mypy-<module>] ignore_errors = True`` section ADDED, or an EXISTING section flipped
  from ``False``/absent to ``True`` — compared by effective value, not by section presence
- an ``error:``-escalated ``filterwarnings`` entry removed from ``pytest.ini``
- a ``bin/ci/*`` file, or a ``bin/check_*``/``bin/lint_*`` gate script, DELETED
- any watched config (``.pre-commit-config.yaml``, ``ruff.toml``, ``mypy.ini``, ``pytest.ini``)
  or workflow file DELETED outright — the most complete form of every weakening above
- a job key removed from a changed workflow's ``jobs:`` block
- a required status-check context removed from ``enable_repo_rules.sh``'s
  ``REQUIRED_CHECKS`` array (the single reviewable source that WRITES the ruleset — this gate
  reads its diff rather than calling the GitHub API, the same "one implementation" reasoning
  the script itself is built on)

THE ESCAPE HATCH mirrors the precedent already in this file family (``# complexity-ok:
<reason>``): a ``gate-change-ok: <reason>`` line, with a non-empty reason, in the PR body (read
from ``GITHUB_EVENT_PATH``) or as a trailer on any commit since the merge-base — the latter
covers a local run before a PR exists, and a squash-merge that drops the PR body. A bare marker
with no reason does not count, matching ``check_complexity.sh``'s "the reason is required" rule.

⚠️ NEITHER of those two sources is reachable at the moment this gate actually FIRES locally
(blueprintx#354). The PR body needs ``GITHUB_EVENT_PATH``, live only inside a GitHub Actions
run. The trailer is read from ``git log <base>..HEAD``, and the commit this pre-commit run is
guarding is never in ``HEAD`` yet — it does not exist until the hook exits 0. The obvious third
candidate, reading the message the author is CURRENTLY typing, was measured and does not work
either: this hook runs at git's own ``pre-commit`` stage (``default_stages`` in
``.pre-commit-config.yaml``), and at that stage ``.git/COMMIT_EDITMSG`` still holds the
PREVIOUS commit's message — git does not (re)write it until AFTER the pre-commit hooks pass —
and neither ``COMMIT_EDITMSG`` nor ``PRE_COMMIT_COMMIT_MSG_SOURCE`` is set in the hook's
environment at this stage (both are populated only for ``commit-msg``). So a THIRD source,
the ``GATE_CHANGE_OK`` environment variable, covers exactly that gap: it needs neither a
finished commit nor a PR, so it is live at the one moment the other two are not. ⚠️ It is
IGNORED under CI (``CI`` / ``GITHUB_ACTIONS`` set), and that is enforced rather than assumed:
"CI never reads a contributor's shell environment" is true of a contributor's shell and false
of a workflow ``env:`` line or a repo/org variable, either of which would let a weakening merge
with no justification a reviewer can read. So the PR-body/trailer path stays the one a PR must
satisfy before it can merge. Read directly (no ``gate-change-ok:`` prefix — the variable name
already says what it is), it carries the same non-empty-reason rule, so it cannot become a
quieter ``--no-verify``.

⚠️ LINE-LEVEL SUPPRESSIONS (``# noqa: X``, ``# complexity-ok: <reason>``, ``# type: ignore``,
``# pragma: no cover``, ``# shellcheck disable`` — ~250 in this tree) MUST NEVER TRIP THIS GATE,
and structurally cannot: for the config-file checks above it only ever reads the five files
named above, never a ``.py``/``.sh`` source file; for the assertion checks below it only ever
reads ``tests/{unit,integration}/test_*.py``, never an arbitrary source file where such a
suppression would live. PR #306 suppressed S608 per LINE for exactly this reason — a rule-level
ignore would have silenced every future S608 finding, not just the one reviewed. A gate that
blocked line-level suppressions would be worse than no gate: it teaches people to route around
it, and then they route around it for the real findings too.

THE SHARPER HALF (blueprintx#324): the cheapest way to turn a red build green is not a config
file at all, it is editing the assertion:

    - assert to_decimal_strict("1.999", 2) == Decimal("1.99")
    + assert to_decimal_strict("1.999", 2) == Decimal("2.00")

That diff turns a money-truncation BUG into a green suite, and nothing above this section would
object — PR #323 shipped exactly that failure in all six tiers. ⚠️ Whether "2.00" is the WRONG
answer is not decidable from a diff, and a gate that guesses is wrong in both directions. What
IS decidable is the SHAPE of the change, read only from a diff that satisfies BOTH halves of one
combination — either alone is routine, the two together are not:

- a changed ``tests/{unit,integration}/test_*.py`` file, AND
- the same branch also touches a non-test ``.py`` file sharing its module stem
  (``test_decimals.py`` <-> any ``decimals.py``) — the repo's own naming convention doubling
  as the correlation signal, never a claim about which lines are "the code under test".

Inside a file that clears that combination, four shapes count (all pure ``ast``/line-diff, no
semantic judgement):

- a ``test_*`` function present at the merge-base and gone now, or its body collapsed to a bare
  ``pass`` / ``assert True``
- a REPLACED assert line whose left-hand expression is unchanged but whose right-hand (expected)
  value changed — the #323 shape verbatim
- a REPLACED assert line whose operator weakened from ``==`` to ``in``/``>=``/``<=``/``not in``,
  or a ``self.assertEqual(`` replaced by ``self.assertTrue(`` — the #289 shape (``in`` where
  ``==`` belonged, found by a human review because nothing else was watching)
- a ``pytest.raises(<Specific>)`` replaced by a broader ``pytest.raises(Exception)`` /
  ``pytest.raises(BaseException)``, or removed outright on a line that had one
- a ``test_*`` function newly decorated ``@pytest.mark.skip`` / ``@pytest.mark.xfail`` where it
  carried no such mark at the merge-base

A test file touched WITHOUT the matching code file — a correction to a genuinely wrong
expectation, the common and legitimate case — clears none of this and must stay silent; that is
what keeps the gate payable rather than a semantic judge.

THE ESCAPE HATCH is the SAME ``gate-change-ok: <reason>`` marker as the config checks above, not
a second one. Both classes are one question — "is a change that weakens confidence in this PR's
own CI deliberate and explained?" — and a single marker means a reviewer scanning a PR body has
one phrase to look for, not two near-identical ones to tell apart. Splitting it would also
duplicate ``RE_JUSTIFICATION``/``justification_reason``/``report`` for no behavioural gain — the
kind of second implementation ``check_codespell_sync.sh`` exists to police, applied to a hatch
rather than a script.

CI must check out with ``fetch-depth: 0`` — a shallow clone has no common ancestor to resolve.
"""

import ast
import configparser
import difflib
import json
import os
import pathlib
import re
import subprocess
import sys


PATH_ROOT = pathlib.Path(__file__).resolve().parent.parent

RE_JUSTIFICATION = re.compile(r"^\s*gate-change-ok:\s*(\S.*)$", re.I | re.M)
RE_HOOK_ID = re.compile(r"^\s*-\s*id:\s*(\S+)\s*$", re.M)
RE_REQUIRED_CHECKS = re.compile(r"REQUIRED_CHECKS=\((.*?)\)", re.S)
RE_CI_SCRIPT = re.compile(r"(^|/)bin/ci/[^/]+$")
RE_GATE_SCRIPT = re.compile(r"(^|/)bin/(check|lint)_[^/]+\.(py|sh)$")
RE_WORKFLOW_PATH = re.compile(r"\.github/workflows/.*\.ya?ml$")
RE_TEST_PATH = re.compile(r"(^|/)tests/(unit|integration)/test_[A-Za-z0-9_]+\.py$")
RE_ASSERT_CMP = re.compile(r"^(\s*assert\s+)(.+?)\s(==|!=|>=|<=|<|>|not in|in)\s(.+?)\s*$")
RE_ASSERT_METHOD = re.compile(r"\bself\.(assertEqual|assertTrue)\(")
RE_PYTEST_RAISES = re.compile(r"pytest\.raises\(\s*([A-Za-z_][\w.]*)")
_SET_WEAKER_THAN_EQ = frozenset({"in", "not in", ">=", "<=", "!="})
_SET_BROAD_EXCEPTIONS = frozenset({"Exception", "BaseException"})

STR_INDEX_REF = ""

_INT_MIN_FIELDS = 2


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
        )
    except OSError:
        return ""
    return cls_proc.stdout


def default_branch() -> str:
    """Return a resolvable ref for the repository's default branch.

    Returns
    -------
    str
        ``origin/<name>`` when only the remote-tracking branch exists — the common CI shape,
        a checkout with no local ``main`` — else a local ``<name>``. Previously this stripped
        the remote prefix (``origin/main`` -> ``main``), which is unresolvable by itself when
        no local branch backs it; ``git merge-base`` then failed silently and ``resolve_base``
        read that as "nothing to diff" instead of "could not check" (blueprintx#313). Falls
        back to the literal ``"main"`` only when nothing resolves at all, so ``resolve_base``
        can tell a real skip apart from an unresolvable baseline.
    """
    str_ref = _git(["symbolic-ref", "--quiet", "--short", "refs/remotes/origin/HEAD"]).strip()
    if str_ref:
        return str_ref
    for str_candidate in ("main", "master"):
        for str_full in (f"origin/{str_candidate}", str_candidate):
            if _git(["rev-parse", "--verify", "--quiet", str_full]).strip():
                return str_full
    return "main"


def show(str_ref: str, str_path: str) -> str | None:
    """Return a blob's text content at a git ref/path, or ``None`` when it does not exist there.

    Parameters
    ----------
    str_ref : str
        A commit-ish, or ``""`` for the index (``STR_INDEX_REF``).
    str_path : str
        Repository-relative path.

    Returns
    -------
    str or None
        The blob's content, ``None`` when the path does not exist at that ref, and ``None``
        when the blob is not valid UTF-8 — a binary cannot define a gate, so there is nothing
        here to assert about it.
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


def changed_paths(str_base: str) -> list:
    """Return the branch's cumulative changed paths with their status, INDEX included.

    Parameters
    ----------
    str_base : str
        The merge-base commit to diff against.

    Returns
    -------
    list of tuple
        ``(status_letter, path)``, e.g. ``("D", "bin/ci/check_actions.sh")``.
    """
    str_out = _git(["diff", "--cached", "--name-status", str_base])
    list_rows = []
    for str_line in str_out.splitlines():
        list_parts = str_line.split("\t")
        if len(list_parts) >= _INT_MIN_FIELDS:
            list_rows.append((list_parts[0][0], list_parts[-1]))
    return list_rows


def strip_toml_comments(str_text: str) -> str:
    """Remove ``# ...`` end-of-line comments, leaving quoted string content untouched.

    ⚠️ Measured necessary, not defensive: ``ruff.toml``'s own ``[lint.per-file-ignores]``
    section carries a prose comment that itself quotes a phrase (documenting an ``ERA001``
    false positive), and a naive quoted-string scan over the raw text read that phrase as a
    rule code. A ``#`` is only treated as a comment start when reached with an EVEN number of
    ``"`` already seen on the line — i.e. outside any quoted span — which is enough for this
    repo's TOML, where a value never itself contains a bare ``#``.

    Parameters
    ----------
    str_text : str
        Raw file content.

    Returns
    -------
    str
        The same text with every comment's tail removed.
    """
    list_out = []
    for str_line in str_text.splitlines():
        int_quotes = 0
        int_cut = len(str_line)
        for int_i, str_ch in enumerate(str_line):
            if str_ch == '"':
                int_quotes += 1
            elif str_ch == "#" and int_quotes % 2 == 0:
                int_cut = int_i
                break
        list_out.append(str_line[:int_cut])
    return "\n".join(list_out)


def toml_top_array(str_text: str, str_key: str) -> set:
    """Return the quoted string entries of a top-level ``key = [ ... ]`` TOML array.

    Parameters
    ----------
    str_text : str
        Full file content.
    str_key : str
        The array's key, e.g. ``"select"``.

    Returns
    -------
    set of str
        Every quoted entry inside the array.
    """
    str_text = strip_toml_comments(str_text)
    cls_match = re.search(rf"(?m)^{re.escape(str_key)}\s*=\s*\[", str_text)
    if not cls_match:
        return set()
    int_close = str_text.find("]", cls_match.end())
    if int_close == -1:
        return set()
    return set(re.findall(r'"([^"]*)"', str_text[cls_match.end() : int_close]))


def toml_per_file_ignores(str_text: str) -> dict:
    """Return ``{glob: {rule, ...}}`` from a ``[lint.per-file-ignores]`` section.

    Parameters
    ----------
    str_text : str
        Full ``ruff.toml`` content.

    Returns
    -------
    dict
        Glob key to its set of rule codes; empty when the section is absent.
    """
    str_text = strip_toml_comments(str_text)
    cls_section = re.search(r"(?m)^\[lint\.per-file-ignores\]\s*$(.*?)(?=^\[|\Z)", str_text, re.S)
    if not cls_section:
        return {}
    dict_out = {}
    for cls_entry in re.finditer(r'"([^"]+)"\s*=\s*\[(.*?)\]', cls_section.group(1), re.S):
        dict_out[cls_entry.group(1)] = set(re.findall(r'"([^"]*)"', cls_entry.group(2)))
    return dict_out


def ruff_toml_problems(str_old: str, str_new: str, str_shown: str) -> list:
    """Return weakening findings between two versions of a ``ruff.toml``.

    Parameters
    ----------
    str_old : str
        Content at the merge-base.
    str_new : str
        Content in this change.
    str_shown : str
        Path to show in messages.

    Returns
    -------
    list of str
        One message per weakening found.
    """
    list_problems = []
    for str_rule in sorted(toml_top_array(str_old, "select") - toml_top_array(str_new, "select")):
        list_problems.append(f"{str_shown}: rule {str_rule!r} removed from [lint] select")
    set_old_ignore, set_new_ignore = (
        toml_top_array(str_old, "ignore"),
        toml_top_array(str_new, "ignore"),
    )
    for str_rule in sorted(set_new_ignore - set_old_ignore):
        list_problems.append(f"{str_shown}: rule {str_rule!r} added to [lint] ignore")
    set_old_exclude = toml_top_array(str_old, "exclude")
    set_new_exclude = toml_top_array(str_new, "exclude")
    for str_path in sorted(set_new_exclude - set_old_exclude):
        list_problems.append(f"{str_shown}: path {str_path!r} added to exclude")

    dict_old_pfi = toml_per_file_ignores(str_old)
    dict_new_pfi = toml_per_file_ignores(str_new)
    for str_glob, set_new_codes in dict_new_pfi.items():
        for str_rule in sorted(set_new_codes - dict_old_pfi.get(str_glob, set())):
            list_problems.append(
                f"{str_shown}: rule {str_rule!r} added to per-file-ignores[{str_glob!r}]"
            )
    return list_problems


def parsed_ini(str_text: str) -> configparser.ConfigParser | None:
    """Parse INI-style text, returning ``None`` when it does not parse.

    Parameters
    ----------
    str_text : str
        Raw file content (``mypy.ini`` or ``pytest.ini`` shape).

    Returns
    -------
    configparser.ConfigParser or None
        The parsed config, or ``None`` on a syntax error — this gate is not the place to
        validate a config file's syntax, only to compare two versions of a valid one.
    """
    cls_parser = configparser.ConfigParser()
    try:
        cls_parser.read_string(str_text)
    except configparser.Error:
        return None
    return cls_parser


def mypy_ini_problems(str_old: str, str_new: str, str_shown: str) -> list:
    """Return weakening findings between two versions of a ``mypy.ini``.

    Parameters
    ----------
    str_old : str
        Content at the merge-base.
    str_new : str
        Content in this change.
    str_shown : str
        Path to show in messages.

    Returns
    -------
    list of str
        One message per weakening found.
    """
    cls_old = parsed_ini(str_old)
    cls_new = parsed_ini(str_new)
    if cls_old is None or cls_new is None:
        return []

    list_problems = []
    set_old_alts = {
        s.strip() for s in cls_old.get("mypy", "exclude", fallback="").split("|") if s.strip()
    }
    set_new_alts = {
        s.strip() for s in cls_new.get("mypy", "exclude", fallback="").split("|") if s.strip()
    }
    for str_alt in sorted(set_new_alts - set_old_alts):
        list_problems.append(f"{str_shown}: path {str_alt!r} added to [mypy] exclude")

    for str_section in sorted(cls_new.sections()):
        bool_old = cls_old.getboolean(str_section, "ignore_errors", fallback=False)
        bool_new = cls_new.getboolean(str_section, "ignore_errors", fallback=False)
        if bool_new and not bool_old:
            list_problems.append(f"{str_shown}: [{str_section}] ignore_errors = True added")
    return list_problems


def pytest_ini_problems(str_old: str, str_new: str, str_shown: str) -> list:
    """Return weakening findings between two versions of a ``pytest.ini``.

    Parameters
    ----------
    str_old : str
        Content at the merge-base.
    str_new : str
        Content in this change.
    str_shown : str
        Path to show in messages.

    Returns
    -------
    list of str
        One message per ``error:``-escalated ``filterwarnings`` entry that was removed.
    """
    cls_old = parsed_ini(str_old)
    cls_new = parsed_ini(str_new)
    if cls_old is None or cls_new is None:
        return []

    def escalations(cls_parser: configparser.ConfigParser) -> set:
        str_raw = cls_parser.get("pytest", "filterwarnings", fallback="")
        return {
            str_line.strip()
            for str_line in str_raw.splitlines()
            if str_line.strip().startswith("error:")
        }

    return [
        f"{str_shown}: filterwarnings escalation {str_entry!r} removed"
        for str_entry in sorted(escalations(cls_old) - escalations(cls_new))
    ]


def precommit_problems(str_old: str, str_new: str, str_shown: str) -> list:
    """Return hooks present at the merge-base and missing now.

    Parameters
    ----------
    str_old : str
        Content at the merge-base.
    str_new : str
        Content in this change.
    str_shown : str
        Path to show in messages.

    Returns
    -------
    list of str
        One message per removed hook id.
    """
    set_removed = set(RE_HOOK_ID.findall(str_old)) - set(RE_HOOK_ID.findall(str_new))
    return [f"{str_shown}: pre-commit hook {str_id!r} removed" for str_id in sorted(set_removed)]


def workflow_jobs(str_text: str) -> set:
    """Return the top-level job ids under a workflow's ``jobs:`` block.

    Parameters
    ----------
    str_text : str
        Full workflow YAML content.

    Returns
    -------
    set of str
        Job ids, read as 2-space-indented ``name:`` keys directly under ``jobs:`` — the
        indentation this repo's workflows consistently use (avoids a YAML dependency these
        scripts otherwise have no reason to carry; see the module docstring).
    """
    cls_match = re.search(r"(?m)^jobs:\s*$", str_text)
    if not cls_match:
        return set()
    set_jobs = set()
    for str_line in str_text[cls_match.end() :].splitlines():
        if not str_line.strip():
            continue
        if not str_line.startswith(" "):
            break
        cls_job = re.match(r"^ {2}([A-Za-z0-9_-]+):", str_line)
        if cls_job:
            set_jobs.add(cls_job.group(1))
    return set_jobs


def workflow_problems(str_old: str, str_new: str, str_shown: str) -> list:
    """Return job ids present at the merge-base and missing now.

    Parameters
    ----------
    str_old : str
        Content at the merge-base.
    str_new : str
        Content in this change.
    str_shown : str
        Path to show in messages.

    Returns
    -------
    list of str
        One message per removed job.
    """
    set_removed = workflow_jobs(str_old) - workflow_jobs(str_new)
    return [f"{str_shown}: workflow job {str_id!r} removed" for str_id in sorted(set_removed)]


def required_checks_problems(str_old: str, str_new: str, str_shown: str) -> list:
    """Return required status-check contexts removed from ``enable_repo_rules.sh``.

    Parameters
    ----------
    str_old : str
        Content at the merge-base.
    str_new : str
        Content in this change.
    str_shown : str
        Path to show in messages.

    Returns
    -------
    list of str
        One message per removed context.
    """

    def contexts(str_text: str) -> set:
        cls_match = RE_REQUIRED_CHECKS.search(str_text)
        return set(re.findall(r'"([^"]*)"', cls_match.group(1))) if cls_match else set()

    set_removed = contexts(str_old) - contexts(str_new)
    return [
        f"{str_shown}: required status check {str_check!r} removed"
        for str_check in sorted(set_removed)
    ]


def touched_code_stems(list_changed: list) -> frozenset:
    """Return the module stems of every non-test ``.py`` file the branch touches.

    Parameters
    ----------
    list_changed : list of tuple
        ``(status_letter, path)`` rows from ``changed_paths`` — every status counts, including
        a deletion, since removing the implementation is as much "touching" it as editing it.

    Returns
    -------
    frozenset of str
        e.g. ``{"decimals"}`` for a branch that touches ``src/utils/decimals.py``. This is the
        correlation half of blueprintx#324's combination signal.
    """
    return frozenset(
        pathlib.Path(str_path).stem
        for _str_status, str_path in list_changed
        if not RE_TEST_PATH.search(str_path) and pathlib.Path(str_path).suffix == ".py"
    )


def test_module_stem(str_test_path: str) -> str:
    """Return the module stem a ``test_<x>.py`` file names, by the repo's own convention.

    Parameters
    ----------
    str_test_path : str
        A path matching ``RE_TEST_PATH``.

    Returns
    -------
    str
        ``"decimals"`` for ``tests/unit/test_decimals.py``.
    """
    str_stem = pathlib.Path(str_test_path).stem
    return str_stem[len("test_") :] if str_stem.startswith("test_") else str_stem


def test_functions(str_text: str) -> dict:
    """Return ``{name: ast.FunctionDef}`` for every ``test_*`` function, ``{}`` on a parse error.

    Parameters
    ----------
    str_text : str
        Full test-file content.

    Returns
    -------
    dict
        Empty when the text does not parse — this gate compares two versions of valid Python,
        it does not validate syntax.
    """
    try:
        cls_tree = ast.parse(str_text)
    except SyntaxError:
        return {}
    return {
        cls_node.name: cls_node
        for cls_node in ast.walk(cls_tree)
        if isinstance(cls_node, ast.FunctionDef) and cls_node.name.startswith("test_")
    }


def is_gutted_body(cls_node: ast.FunctionDef) -> bool:
    """Return ``True`` when a function's only real statement is ``pass`` / ``assert True``.

    Parameters
    ----------
    cls_node : ast.FunctionDef
        The function to inspect.

    Returns
    -------
    bool
        ``True`` for a body reduced to nothing but a docstring plus ``pass``/``assert True``.
    """
    list_stmts = [
        cls_stmt
        for cls_stmt in cls_node.body
        if not (isinstance(cls_stmt, ast.Expr) and isinstance(cls_stmt.value, ast.Constant))
    ]
    if not list_stmts:
        return True
    cls_only = list_stmts[0]
    if len(list_stmts) > 1:
        return False
    if isinstance(cls_only, ast.Pass):
        return True
    return (
        isinstance(cls_only, ast.Assert)
        and isinstance(cls_only.test, ast.Constant)
        and cls_only.test.value is True
    )


def skip_marks(cls_node: ast.FunctionDef) -> frozenset:
    """Return the ``@pytest.mark.{skip,xfail}`` names decorating a function.

    ⚠️ Deliberately excludes ``skipif``: measured over ``origin/main~100..origin/main``,
    its one hit was a legitimate, well-documented environment-conditional skip (a driver
    that ships to service tiers only), not a hidden failure — flagging it would make the
    gate unpayable on the repo's own history. ``skip``/``xfail`` are unconditional: they
    always disable the test, which is the shape blueprintx#324 is watching for.

    Parameters
    ----------
    cls_node : ast.FunctionDef
        The function to inspect.

    Returns
    -------
    frozenset of str
        e.g. ``{"skip"}``. Empty when undecorated or decorated with something else.
    """
    return frozenset(
        str_mark
        for cls_dec in cls_node.decorator_list
        for str_mark in (_outer_pytest_mark(cls_dec),)
        if str_mark in {"skip", "xfail"}
    )


def _outer_pytest_mark(cls_dec: ast.expr) -> str:
    """Return the mark name of a ``pytest.mark.<name>`` decorator, or ``""``.

    Parameters
    ----------
    cls_dec : ast.expr
        One entry of a ``decorator_list``.

    Returns
    -------
    str
        The mark name for ``@pytest.mark.<name>`` and ``@pytest.mark.<name>(...)``, else ``""``.
    """
    cls_target = cls_dec.func if isinstance(cls_dec, ast.Call) else cls_dec
    if not isinstance(cls_target, ast.Attribute):
        return ""
    cls_owner = cls_target.value
    if isinstance(cls_owner, ast.Attribute) and cls_owner.attr == "mark":
        return cls_target.attr
    return ""


def deleted_or_gutted_tests(str_old: str, str_new: str, str_shown: str) -> list:
    """Return findings for a ``test_*`` function removed, or reduced to a no-op, since base.

    Parameters
    ----------
    str_old : str
        Content at the merge-base.
    str_new : str
        Content in this change.
    str_shown : str
        Path to show in messages.

    Returns
    -------
    list of str
        One message per deleted or gutted test.
    """
    dict_old, dict_new = test_functions(str_old), test_functions(str_new)
    list_problems = [
        f"{str_shown}: test {str_name!r} deleted"
        for str_name in sorted(set(dict_old) - set(dict_new))
    ]
    for str_name, cls_new_node in dict_new.items():
        cls_old_node = dict_old.get(str_name)
        if cls_old_node and not is_gutted_body(cls_old_node) and is_gutted_body(cls_new_node):
            list_problems.append(f"{str_shown}: test {str_name!r} body replaced with a no-op")
    return list_problems


def newly_skipped_tests(str_old: str, str_new: str, str_shown: str) -> list:
    """Return findings for a ``test_*`` function newly marked ``skip``/``xfail`` since base.

    Parameters
    ----------
    str_old : str
        Content at the merge-base.
    str_new : str
        Content in this change.
    str_shown : str
        Path to show in messages.

    Returns
    -------
    list of str
        One message per test newly decorated.
    """
    dict_old, dict_new = test_functions(str_old), test_functions(str_new)
    list_problems = []
    for str_name, cls_new_node in dict_new.items():
        cls_old_node = dict_old.get(str_name)
        if cls_old_node is None:
            continue
        for str_mark in sorted(skip_marks(cls_new_node) - skip_marks(cls_old_node)):
            list_problems.append(
                f"{str_shown}: test {str_name!r} newly decorated @pytest.mark.{str_mark}"
            )
    return list_problems


def diff_replace_pairs(str_old: str, str_new: str) -> list:
    """Return ``(old_line, new_line, new_lineno)`` for every 1:1 replaced source line.

    Parameters
    ----------
    str_old : str
        Content at the merge-base.
    str_new : str
        Content in this change.

    Returns
    -------
    list of tuple
        ``new_lineno`` is 1-based, so it can be matched back against ``ast`` node line numbers.
        Only equal-length replace blocks are read pairwise — an insertion/deletion tangled into
        the same hunk is not a like-for-like replacement and carries no comparable pair.
    """
    list_old, list_new = str_old.splitlines(), str_new.splitlines()
    list_pairs = []
    for str_tag, int_i1, int_i2, int_j1, int_j2 in difflib.SequenceMatcher(
        a=list_old, b=list_new, autojunk=False
    ).get_opcodes():
        if str_tag == "replace" and (int_i2 - int_i1) == (int_j2 - int_j1):
            for int_offset, cls_pair in enumerate(
                zip(list_old[int_i1:int_i2], list_new[int_j1:int_j2], strict=True)
            ):
                list_pairs.append((*cls_pair, int_j1 + int_offset + 1))
    return list_pairs


def assertion_value_or_operator_change(str_old_line: str, str_new_line: str) -> str | None:
    """Return a finding when a replaced line weakens an ``assert``/``assertEqual``, else ``None``.

    Parameters
    ----------
    str_old_line : str
        The line at the merge-base.
    str_new_line : str
        The replacing line.

    Returns
    -------
    str or None
        Describes the weakening (expected-value change, or an operator/method weakened) —
        only when the left-hand expression is unchanged, so an unrelated rewrite of the whole
        line is not mistaken for the same assertion pinned to a new value.
    """
    cls_old, cls_new = RE_ASSERT_CMP.match(str_old_line), RE_ASSERT_CMP.match(str_new_line)
    if cls_old and cls_new and cls_old.group(2).strip() == cls_new.group(2).strip():
        str_old_op, str_new_op = cls_old.group(3), cls_new.group(3)
        str_new_stripped = str_new_line.strip()
        if str_old_op == "==" and str_new_op in _SET_WEAKER_THAN_EQ:
            return f"assertion operator weakened from '==' to {str_new_op!r}: {str_new_stripped!r}"
        if (
            str_old_op == "==" == str_new_op
            and cls_old.group(4).strip() != cls_new.group(4).strip()
        ):
            return (
                f"assertion expected value changed: {str_old_line.strip()!r} -> "
                f"{str_new_stripped!r}"
            )
        return None
    cls_old_m = RE_ASSERT_METHOD.search(str_old_line)
    cls_new_m = RE_ASSERT_METHOD.search(str_new_line)
    if (
        cls_old_m
        and cls_new_m
        and cls_old_m.group(1) == "assertEqual"
        and cls_new_m.group(1) == "assertTrue"
    ):
        return f"assertion weakened: assertEqual() -> assertTrue(): {str_new_line.strip()!r}"
    return None


def raises_broadened_or_removed(str_old_line: str, str_new_line: str) -> str | None:
    """Return a finding when a replaced line broadens or drops a ``pytest.raises(...)``.

    Parameters
    ----------
    str_old_line : str
        The line at the merge-base.
    str_new_line : str
        The replacing line.

    Returns
    -------
    str or None
        Describes the broadening/removal, else ``None``.
    """
    cls_old, cls_new = RE_PYTEST_RAISES.search(str_old_line), RE_PYTEST_RAISES.search(str_new_line)
    if cls_old and not cls_new:
        return f"pytest.raises removed: {str_old_line.strip()!r}"
    if (
        cls_old
        and cls_new
        and cls_old.group(1) != cls_new.group(1)
        and cls_new.group(1) in _SET_BROAD_EXCEPTIONS
        and cls_old.group(1) not in _SET_BROAD_EXCEPTIONS
    ):
        return f"pytest.raises broadened from {cls_old.group(1)!r} to {cls_new.group(1)!r}"
    return None


def raises_count_decreased(str_old: str, str_new: str, str_shown: str) -> list:
    """Return a finding when ``pytest.raises(...)`` wrappers vanish, counted whole-file.

    A wrapper removed alongside its now-unwrapped body reindents every line under it, so it
    never lands in a same-length ``diff_replace_pairs`` block — this checks COUNT, not position,
    which is what makes a plain deletion visible at all.

    Parameters
    ----------
    str_old : str
        Content at the merge-base.
    str_new : str
        Content in this change.
    str_shown : str
        Path to show in messages.

    Returns
    -------
    list of str
        A single finding when the count dropped, else empty.
    """
    int_old = count_pytest_raises_calls(str_old)
    int_new = count_pytest_raises_calls(str_new)
    if int_new < int_old:
        return [f"{str_shown}: pytest.raises(...) count dropped from {int_old} to {int_new}"]
    return []


def count_pytest_raises_calls(str_source: str) -> int:
    """Return how many real ``pytest.raises(...)`` CALLS the source makes.

    Parameters
    ----------
    str_source : str
        Python source to parse.

    Returns
    -------
    int
        The number of call nodes, or the regex count when the source does not parse.

    Notes
    -----
    ⚠️ A regex over source TEXT counts occurrences, not calls — so adding
    ``marker = "pytest.raises(ValueError)"`` restores the count while the real wrapper stays
    removed, and the drop check sees nothing. Measured: the regex finds 1 in that string, the
    AST finds 0 calls. Counting `ast.Call` nodes cannot be fooled by a string literal.

    The regex remains the fallback for unparsable source (a partial diff side), where a rough
    count beats no count at all — but a parse failure means the number is approximate, never
    that there is nothing to find.
    """
    try:
        cls_tree = ast.parse(str_source)
    except SyntaxError:
        return len(RE_PYTEST_RAISES.findall(str_source))
    return sum(
        1
        for cls_node in ast.walk(cls_tree)
        if isinstance(cls_node, ast.Call) and _is_pytest_raises_target(cls_node.func)
    )


def _is_pytest_raises_target(cls_func: ast.expr) -> bool:
    """Return whether a call target is ``pytest.raises`` (or a bare ``raises``).

    Parameters
    ----------
    cls_func : ast.expr
        The ``func`` of an ``ast.Call``.

    Returns
    -------
    bool
        ``True`` for ``pytest.raises`` and for ``raises`` imported directly.
    """
    if isinstance(cls_func, ast.Attribute):
        return cls_func.attr == "raises"
    return isinstance(cls_func, ast.Name) and cls_func.id == "raises"


def enclosing_test_name(str_new: str, int_lineno: int) -> str:
    """Return the innermost ``test_*`` function containing a 1-based line number.

    Parameters
    ----------
    str_new : str
        Content to parse.
    int_lineno : int
        1-based line number.

    Returns
    -------
    str
        The function name, or ``""`` when the line falls outside any ``test_*`` function.
    """
    for str_name, cls_node in test_functions(str_new).items():
        if cls_node.lineno <= int_lineno <= (cls_node.end_lineno or cls_node.lineno):
            return str_name
    return ""


def replaced_assertion_problems(str_old: str, str_new: str, str_shown: str) -> list:
    """Return findings for assertion lines replaced 1:1 between two test-file versions.

    Parameters
    ----------
    str_old : str
        Content at the merge-base.
    str_new : str
        Content in this change.
    str_shown : str
        Path to show in messages.

    Returns
    -------
    list of str
        One message per weakened replaced line, naming its enclosing test where resolvable.
    """
    list_problems = []
    for str_old_line, str_new_line, int_lineno in diff_replace_pairs(str_old, str_new):
        str_finding = assertion_value_or_operator_change(
            str_old_line, str_new_line
        ) or raises_broadened_or_removed(str_old_line, str_new_line)
        if not str_finding:
            continue
        str_test = enclosing_test_name(str_new, int_lineno)
        str_where = f"test {str_test!r}" if str_test else f"{str_shown}:{int_lineno}"
        list_problems.append(f"{str_shown}: {str_where} {str_finding}")
    return list_problems


def test_assertion_problems(str_old: str, str_new: str, str_shown: str) -> list:
    """Return every assertion-integrity finding for one changed test file (blueprintx#324).

    Parameters
    ----------
    str_old : str
        Content at the merge-base.
    str_new : str
        Content in this change.
    str_shown : str
        Path to show in messages.

    Returns
    -------
    list of str
        Combined findings — deleted/gutted tests, newly skipped tests, and weakened
        assertions/``raises`` — for a file already known to clear the correlation signal
        (see ``file_problems``, which is the only caller and gates on ``touched_code_stems``).
    """
    return [
        *deleted_or_gutted_tests(str_old, str_new, str_shown),
        *newly_skipped_tests(str_old, str_new, str_shown),
        *replaced_assertion_problems(str_old, str_new, str_shown),
        *raises_count_decreased(str_old, str_new, str_shown),
    ]


_DICT_DISPATCH = {
    ".pre-commit-config.yaml": precommit_problems,
    "ruff.toml": ruff_toml_problems,
    "mypy.ini": mypy_ini_problems,
    "pytest.ini": pytest_ini_problems,
    "enable_repo_rules.sh": required_checks_problems,
}


def file_problems(
    str_path: str, str_base: str, set_touched_stems: frozenset = frozenset()
) -> list:
    """Return weakening findings for one changed, still-existing path.

    Parameters
    ----------
    str_path : str
        Repository-relative path, as reported by ``changed_paths``.
    str_base : str
        The merge-base commit.
    set_touched_stems : frozenset of str
        Module stems the branch also touches (``touched_code_stems``) — gates the assertion
        checks on blueprintx#324's correlation signal.

    Returns
    -------
    list of str
        Findings for this path; empty when it is not a watched config/test file, is newly
        added (nothing to weaken), or carries no weakening.
    """
    str_new = show(STR_INDEX_REF, str_path)
    str_old = show(str_base, str_path)
    if str_new is None or str_old is None:
        return []

    fn_analyzer = _DICT_DISPATCH.get(pathlib.Path(str_path).name)
    if fn_analyzer is None and RE_WORKFLOW_PATH.search(str_path):
        fn_analyzer = workflow_problems
    list_problems = fn_analyzer(str_old, str_new, str_path) if fn_analyzer else []

    if RE_TEST_PATH.search(str_path) and test_module_stem(str_path) in set_touched_stems:
        list_problems.extend(test_assertion_problems(str_old, str_new, str_path))
    return list_problems


def deletion_problems(list_changed: list, set_touched_stems: frozenset = frozenset()) -> list:
    """Return findings for a deleted gate script, watched config/workflow file, or test file.

    Deleting the whole file is the bluntest form of every weakening ``file_problems`` reads
    line-by-line inside it — a ``ruff.toml`` deleted outright removes every rule at once, and
    that must be at least as loud as removing one rule from it (blueprintx#313). A test file
    deleted alongside the code it tested is the same shape again (blueprintx#324).

    Parameters
    ----------
    list_changed : list of tuple
        ``(status_letter, path)`` rows from ``changed_paths``.
    set_touched_stems : frozenset of str
        Module stems the branch also touches — gates the test-file-deletion finding on the
        same correlation signal as ``file_problems``.

    Returns
    -------
    list of str
        One message per deleted quality-check script, deleted watched config file, or test
        file deleted while its code under test changed.
    """
    list_problems = []
    for str_status, str_path in list_changed:
        if str_status != "D":
            continue
        if RE_CI_SCRIPT.search(str_path) or RE_GATE_SCRIPT.search(str_path):
            list_problems.append(f"{str_path}: quality-check script deleted")
        elif pathlib.Path(str_path).name in _DICT_DISPATCH or RE_WORKFLOW_PATH.search(str_path):
            list_problems.append(f"{str_path}: watched gate configuration deleted")
        elif RE_TEST_PATH.search(str_path) and test_module_stem(str_path) in set_touched_stems:
            list_problems.append(
                f"{str_path}: test file deleted while its code under test changed"
            )
    return list_problems


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


TUPLE_CI_MARKERS = ("CI", "GITHUB_ACTIONS")


def env_reason() -> str:
    """Return the ``GATE_CHANGE_OK`` reason from the environment, or ``""`` (I/O seam).

    Returns
    -------
    str
        The non-empty, stripped value of ``GATE_CHANGE_OK`` — the one escape hatch reachable
        at local ``pre-commit`` time (blueprintx#354); see the module docstring for why the
        PR body and the commit trailer are not. No ``gate-change-ok:`` prefix is expected
        here, unlike the other two sources — the variable name already carries the meaning.
        ``""`` under CI: the hatch is LOCAL-ONLY, so a workflow ``env:`` line or a repo
        variable cannot stand in for a justification a PR reviewer can actually read.
    """
    if any(os.environ.get(str_marker) for str_marker in TUPLE_CI_MARKERS):
        return ""
    return os.environ.get("GATE_CHANGE_OK", "").strip()


def justification_reason(str_base: str) -> str:
    """Return the ``gate-change-ok`` reason from the env, the PR body, or a commit trailer.

    Parameters
    ----------
    str_base : str
        The merge-base commit — commit messages since it are searched for a trailer.

    Returns
    -------
    str
        The non-empty reason text, or ``""`` when no valid justification is present. Checked
        in the order a LOCAL run can actually satisfy them: ``GATE_CHANGE_OK`` first (needs
        neither a finished commit nor a PR), then the PR body, then a commit trailer.
    """
    str_env = env_reason()
    if str_env:
        return str_env
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
        ``False`` on bad usage (already reported to stdout); ``True`` otherwise, including
        when no ``--root`` flag was given at all.
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

    Mid-merge the INDEX already holds the incoming side's files, but HEAD is still the
    pre-merge tip, so a base taken from HEAD alone charges the incoming delta to this branch
    -- main's own gate changes then read as the branch weakening them. ``rev-parse MERGE_HEAD``
    resolves only the first line of the file, so an octopus merge reads the file itself.

    Returns
    -------
    list of str
        One commit hash per incoming head; empty when no merge is in progress.
    """
    str_path = _git(["rev-parse", "--git-path", "MERGE_HEAD"]).strip()
    if not str_path or not pathlib.Path(str_path).is_file():
        return []
    return pathlib.Path(str_path).read_text(encoding="utf-8").split()


def resolve_base() -> str | None:
    """Resolve the merge-base to diff against.

    Returns
    -------
    str or None
        The merge-base commit to diff against. ``None`` means a real skip: a ref resolved
        and HEAD already IS that commit, so there is genuinely nothing to diff. An empty
        string means the OPPOSITE — no ref could be resolved at all — and is deliberately
        never treated as a skip: an absent baseline is not proof of no weakening
        (blueprintx#313); ``main()`` fails the run on it instead of passing it silently.
    """
    str_ref = default_branch()
    str_base = _git(["merge-base", str_ref, "HEAD", *merge_heads()]).strip()
    if not str_base:
        print(f"❌ could not resolve a merge-base against {str_ref!r} — refusing to pass blind.")
        return ""
    str_head = _git(["rev-parse", "HEAD"]).strip()
    if str_base == str_head:
        print("✅ gate-integrity check skipped — on the default branch (nothing to diff).")
        return None
    return str_base


def collect_problems(list_changed: list, str_base: str) -> list:
    """Return every weakening finding across the branch's changed paths.

    Parameters
    ----------
    list_changed : list of tuple
        ``(status_letter, path)`` rows from ``changed_paths``.
    str_base : str
        The merge-base commit.

    Returns
    -------
    list of str
        Combined findings from deletions and from modified watched config/test files.
    """
    set_touched_stems = touched_code_stems(list_changed)
    list_problems = deletion_problems(list_changed, set_touched_stems)
    for str_status, str_path in list_changed:
        if str_status != "D":
            list_problems.extend(file_problems(str_path, str_base, set_touched_stems))
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
        print(f"✅ gate integrity OK ({int_changed_count} changed file(s) checked)")
        return 0

    for str_problem in list_problems:
        print(f"⚠️  {str_problem}")

    str_reason = justification_reason(str_base)
    if str_reason:
        print(f"\n✅ justified: gate-change-ok: {str_reason}")
        return 0

    print(
        f"\n❌ {len(list_problems)} gate-weakening change(s) with no justification. Locally, "
        f"run this commit with GATE_CHANGE_OK='<reason>' set (e.g. `GATE_CHANGE_OK='<reason>' "
        f"git commit -m ...`) — a PR body or commit-trailer 'gate-change-ok: <reason>' line is "
        f"CI-only and cannot be read at commit time. The reason is required either way, "
        f"matching '# complexity-ok: <reason>' elsewhere in this repo."
    )
    return 1


def main(list_argv: list) -> int:
    """Check the branch's cumulative diff for an unjustified gate weakening.

    Parameters
    ----------
    list_argv : list of str
        ``["--root", <dir>]`` or empty. ``--root`` is accepted for interface parity with
        ``check_function_length.py`` / ``check_complexity.sh`` (this repo runs every shared
        gate over BlueprintX via ``--root .``); the diff itself is always repo-wide, since
        ``git diff`` paths are already repository-relative regardless of cwd.

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
