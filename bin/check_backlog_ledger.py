#!/usr/bin/env python
"""Enforce the per-branch work ledger deterministically, not by memory.

``docs/CLAUDE.md`` requires that every non-trivial branch keep a **per-branch work ledger** at
``docs/backlog/<kebab-topic>_YYYYMMDD_HHMMSS.md`` (timestamped at creation, never renamed), each
item a Markdown checkbox (``- [ ]`` open, ``- [x]`` done). That was the last rule of the flow that
lived only in prose — a repo that already makes every other convention structural
(``bin/check_typing.py``, ``bin/check_provenance.py``, ``tests/unit/test_reader_retry_policy.py``).
This hook closes it.

**"Non-trivial" is made deterministic by PATH** — the same axis ``bin/pr_gate.py`` classifies a
PR by, reused here rather than re-listed (the two must never drift). A branch whose cumulative
diff touches any ``src`` or ``ci`` path (source, or ``bin/`` / ``.github/`` / build config) must
add or edit at least one ``docs/backlog`` ledger. Every other class — a docs-only edit, a ``deps``
bump (``poetry.lock`` / ``pyproject.toml``), a tests-only tweak — is exempt.

``pr_gate.classify_risk`` collapses a whole diff to its *single most dangerous* class (and ranks
``tests`` above ``ci``), which is the right question for auto-merge but the wrong one here: a
branch touching both ``bin/`` and ``tests/`` would collapse to ``tests`` and wrongly escape the
ledger requirement. So the classifier is reused **per path** — the question is set-membership
("does *any* changed path fall in a ledger class?"), not "what is the diff's worst class".

The check is **diff-based, not per-commit**: the ledger is a per-*branch* artifact, so a later
source-only commit on a branch that already carries a ledger must pass. It compares the branch to
its merge-base with ``main`` and asks whether a ledger rides along in that cumulative diff. On
``main`` itself (or a tag build) the merge-base is ``HEAD``, the diff is empty, and the check is a
no-op — so it only ever fires on a feature branch / PR, which is exactly where a ledger is owed.

Failures (each a hard error, exit 1):

- the branch touches a ``src``/``ci`` path but no ``docs/backlog/*.md`` is part of its diff;
- a touched ledger's filename does not match ``<kebab-topic>_YYYYMMDD_HHMMSS.md``;
- a touched ledger carries no ``- [ ]`` / ``- [x]`` checkbox item (to-dos as bare bullets).
"""

from __future__ import annotations

from collections.abc import Callable
import os
import pathlib
import re
import shutil
import subprocess
import sys


# Reuse the PR gate's path->risk classifier instead of re-listing the risk paths here, so the two
# can never drift on what "src" or "ci" means. ``bin/`` is this file's own directory; put it on
# the path first so the sibling import resolves regardless of the caller's cwd (pre-commit and CI
# both invoke this as ``python bin/check_backlog_ledger.py``).
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import pr_gate  # noqa: E402  (deliberate: import follows the sys.path bootstrap above)


# Risk classes whose changes are "non-trivial" enough to demand a work ledger — the same path axis
# ``pr_gate`` computes: ``src`` = source, ``ci`` = bin/CI/workflows/build config. ``deps`` /
# ``docs`` / ``tests`` / ``other`` are exempt (a lockfile bump, a docs typo, a test-only tweak).
LEDGER_CLASSES: frozenset[str] = frozenset({"src", "ci"})

# Where a per-branch ledger lives (docs/CLAUDE.md). Not published (mkdocs ``exclude_docs``).
LEDGER_DIR = "docs/backlog/"

# ``<kebab-topic>_YYYYMMDD_HHMMSS.md`` — the topic is kebab-case (no underscores of its own), then
# an 8-digit date and 6-digit time. Fixed at creation, never renamed.
_NAME_RE = re.compile(r"^[a-z0-9-]+_\d{8}_\d{6}\.md$")

# At least one Markdown task checkbox: ``- [ ]`` open, or ``- [x]`` / ``- [X]`` done. A bare ``-``
# bullet does not count — the rule is that ledger items are trackable checkboxes.
_CHECKBOX_RE = re.compile(r"^\s*[-*] \[[ xX]\]", re.MULTILINE)


def requires_ledger(list_paths: list[str]) -> bool:
    """Say whether a diff's paths oblige the branch to carry a work ledger.

    Reuses :func:`pr_gate.classify_risk` **per path** (set-membership), not on the whole list: the
    whole-list call returns only the single most-dangerous class and ranks ``tests`` above ``ci``,
    so a branch touching both ``bin/`` and ``tests/`` would collapse to ``tests`` and wrongly
    escape the requirement. Asking each path keeps "any src/ci path present?" honest.

    Parameters
    ----------
    list_paths : list of str
        Repo-relative paths in the branch's cumulative diff.

    Returns
    -------
    bool
        True when at least one path classifies as a ledger class (``src`` or ``ci``).
    """
    return any(pr_gate.classify_risk([str_path]) in LEDGER_CLASSES for str_path in list_paths)


def ledger_paths(list_paths: list[str]) -> list[str]:
    """Filter a diff's paths down to the ``docs/backlog`` Markdown ledgers.

    Parameters
    ----------
    list_paths : list of str
        Repo-relative paths in the branch's cumulative diff.

    Returns
    -------
    list of str
        The paths under ``docs/backlog/`` ending in ``.md``.
    """
    return [p for p in list_paths if p.startswith(LEDGER_DIR) and p.endswith(".md")]


def is_valid_ledger_name(str_name: str) -> bool:
    """Report whether a ledger's basename matches ``<kebab-topic>_YYYYMMDD_HHMMSS.md``.

    Parameters
    ----------
    str_name : str
        The file's basename (no directory).

    Returns
    -------
    bool
        True when the name matches the required timestamped pattern.
    """
    return bool(_NAME_RE.match(str_name))


def has_checkbox_item(str_text: str) -> bool:
    """Report whether a ledger's text carries at least one Markdown task checkbox.

    Parameters
    ----------
    str_text : str
        The ledger's full text.

    Returns
    -------
    bool
        True when a ``- [ ]`` / ``- [x]`` / ``- [X]`` item is present.
    """
    return bool(_CHECKBOX_RE.search(str_text))


def check(list_paths: list[str], read_text: Callable[[str], str | None]) -> list[str]:
    """Return every ledger violation for a branch's cumulative diff (empty list = clean).

    Pure: all filesystem and git access is injected via ``read_text`` and supplied by the caller,
    so the rule is unit-testable without a working tree.

    Parameters
    ----------
    list_paths : list of str
        Repo-relative paths in the branch's cumulative diff.
    read_text : callable
        Maps a repo-relative path to its text, or ``None`` when the file is absent (e.g. a ledger
        that the diff *deletes* — its content cannot be judged, only its name).

    Returns
    -------
    list of str
        Human-readable error lines; empty when the branch satisfies the ledger rule.
    """
    if not requires_ledger(list_paths):
        return []
    list_ledgers = ledger_paths(list_paths)
    if not list_ledgers:
        return [
            "❌ branch touches a src/ci path but its diff adds no "
            "docs/backlog/<kebab-topic>_YYYYMMDD_HHMMSS.md work ledger — every non-trivial "
            "branch keeps one (docs/CLAUDE.md). Create it, tracking each to-do as a `- [ ]` box."
        ]
    list_errors: list[str] = []
    for str_path in list_ledgers:
        str_name = str_path.rsplit("/", 1)[-1]
        if not is_valid_ledger_name(str_name):
            list_errors.append(
                f"❌ {str_path}: ledger filename must match <kebab-topic>_YYYYMMDD_HHMMSS.md "
                "(kebab topic, then an 8-digit date and 6-digit time)."
            )
        str_text = read_text(str_path)
        if str_text is not None and not has_checkbox_item(str_text):
            list_errors.append(
                f"❌ {str_path}: no `- [ ]`/`- [x]` checkbox item — ledger to-dos must be "
                "checkboxes, not bare `-` bullets."
            )
    return list_errors


def _git(*args: str) -> subprocess.CompletedProcess[str]:
    """Run a git command with a trusted, constant argv and capture its output.

    Parameters
    ----------
    *args : str
        Arguments after the ``git`` executable.

    Returns
    -------
    subprocess.CompletedProcess of str
        The completed process (``check=False``; callers inspect ``returncode``).
    """
    str_git = shutil.which("git") or "git"
    # Trusted, constant argv; git is resolved to an absolute path via shutil.which (bandit S603).
    return subprocess.run([str_git, *args], capture_output=True, text=True, check=False)  # noqa: S603


def _base_ref() -> str | None:
    """Resolve the commit to diff the branch against (its merge-base with main).

    Honours a ``LEDGER_BASE_REF`` override first (CI passes the PR base), then the merge-base with
    ``origin/main`` and finally with ``main``. Returns ``None`` when none resolves — e.g. on
    ``main`` itself, where there is no branch to enforce.

    Returns
    -------
    str or None
        A commit-ish to diff against, or ``None`` when the check should be a no-op.
    """
    str_override = os.environ.get("LEDGER_BASE_REF")
    if str_override:
        return str_override
    for str_ref in ("origin/main", "main"):
        cls_proc = _git("merge-base", "HEAD", str_ref)
        if cls_proc.returncode == 0 and cls_proc.stdout.strip():
            return cls_proc.stdout.strip()
    return None


def _changed_paths() -> list[str]:
    """Return the branch's cumulative changed paths (merge-base with main -> the index).

    Diffs the **index** (``--cached``), not the working tree: pre-commit runs against *staged*
    content, and ``git diff`` ignores untracked files — a brand-new ledger not yet staged would be
    invisible, so the gate would demand a ledger that is right there but not added. The index holds
    both the branch's earlier commits (matched by ``HEAD``) and the files staged for this commit,
    so ``--cached`` captures exactly what the branch is about to contribute. In CI the tree is
    clean (index == HEAD), so it reduces to the branch's cumulative diff against its base.

    Diffing from the merge-base (not two-dot against the branch tip) yields exactly the branch's
    own changes and excludes commits that landed on ``main`` in the meantime, matching three-dot
    semantics without needing them.

    Returns
    -------
    list of str
        Repo-relative changed paths; empty when there is no base to compare against.
    """
    str_base = _base_ref()
    if str_base is None:
        return []
    cls_proc = _git("diff", "--cached", "--name-only", str_base)
    cls_proc.check_returncode()
    return [line for line in cls_proc.stdout.splitlines() if line]


def _read_text(str_path: str) -> str | None:
    """Read a repo-relative file's text, or ``None`` when it does not exist.

    Parameters
    ----------
    str_path : str
        Repo-relative path.

    Returns
    -------
    str or None
        The file's text, or ``None`` when absent.
    """
    cls_path = pathlib.Path(str_path)
    if not cls_path.is_file():
        return None
    return cls_path.read_text(encoding="utf-8")


if __name__ == "__main__":
    list_found = check(_changed_paths(), _read_text)
    for str_line in list_found:
        print(str_line)
    sys.exit(1 if list_found else 0)
