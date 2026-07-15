"""Unit tests for the merged-PR reconciler's pure decision logic.

Only the **pure** functions are exercised — which linked issues to close, whether/which branch to
delete, and the trailing-window filter. Every GitHub call lives behind ``_api``/``_graphql`` and is
never touched here, so these tests need no network (the autouse guard in ``conftest.py`` blocks
sockets anyway).

The invariants that matter most: a **fork** branch and the **default branch** are never deletion
targets, and only a merged PR is ever acted on.
"""

from datetime import datetime, timezone
import importlib.util
from pathlib import Path

import pytest


# bin/ is not an importable package; load the module straight from its path (mirrors test_pr_gate).
_PATH = Path(__file__).resolve().parents[2] / "bin" / "reconcile_merged_prs.py"
_SPEC = importlib.util.spec_from_file_location("reconcile_merged_prs", _PATH)
assert _SPEC is not None and _SPEC.loader is not None
reconcile = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(reconcile)


@pytest.mark.parametrize(
	("list_refs", "list_expected"),
	[
		([], []),
		([{"number": 5, "state": "OPEN"}], [5]),
		([{"number": 5, "state": "CLOSED"}], []),
		(
			[
				{"number": 1, "state": "OPEN"},
				{"number": 2, "state": "CLOSED"},
				{"number": 3, "state": "OPEN"},
			],
			[1, 3],
		),
	],
)
def test_issues_to_close_keeps_only_open(list_refs: list[dict], list_expected: list[int]) -> None:
	"""Only OPEN linked issues are returned — a reopened/hand-closed one is left alone."""
	assert reconcile.issues_to_close(list_refs) == list_expected


def _pr(*, merged: bool = True, fork: bool = False, ref: str = "feat/x") -> dict:
	return {"merged": merged, "isCrossRepository": fork, "headRefName": ref}


def test_branch_to_delete_returns_ref_for_same_repo_merged_pr() -> None:
	"""The normal case: a merged, same-repo, non-default branch is deleted."""
	assert reconcile.branch_to_delete(_pr(ref="fix/pr-reconciler-104"), "main") == (
		"fix/pr-reconciler-104"
	)


def test_branch_to_delete_skips_unmerged() -> None:
	"""An unmerged PR keeps its branch."""
	assert reconcile.branch_to_delete(_pr(merged=False), "main") is None


def test_branch_to_delete_skips_fork() -> None:
	"""A fork's branch is not ours to delete."""
	assert reconcile.branch_to_delete(_pr(fork=True), "main") is None


def test_branch_to_delete_never_deletes_default_branch() -> None:
	"""The repository default branch is never a deletion target."""
	assert reconcile.branch_to_delete(_pr(ref="main"), "main") is None


def test_recently_merged_numbers_filters_by_window_and_merge_state() -> None:
	"""Only PRs merged within the trailing window are returned; unmerged ones are dropped."""
	dt_now = datetime(2026, 7, 15, 12, 0, tzinfo=timezone.utc)
	list_prs = [
		{"number": 1, "merged_at": "2026-07-15T09:00:00Z"},  # today — in
		{"number": 2, "merged_at": None},  # closed unmerged — out
		{"number": 3, "merged_at": "2026-07-01T00:00:00Z"},  # 14 days ago — out
		{"number": 4, "merged_at": "2026-07-10T00:00:00Z"},  # 5 days ago — in
	]
	assert reconcile.recently_merged_numbers(list_prs, dt_now, 7) == [1, 4]


def test_recently_merged_numbers_boundary_is_inclusive() -> None:
	"""A PR merged exactly at the window floor is kept (>=, not >)."""
	dt_now = datetime(2026, 7, 15, 0, 0, tzinfo=timezone.utc)
	list_prs = [{"number": 9, "merged_at": "2026-07-08T00:00:00Z"}]  # exactly 7 days
	assert reconcile.recently_merged_numbers(list_prs, dt_now, 7) == [9]
