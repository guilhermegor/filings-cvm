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
import io
from pathlib import Path
import urllib.error

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


def _http_error(int_code: int, bytes_body: bytes) -> urllib.error.HTTPError:
	return urllib.error.HTTPError("u", int_code, "x", None, io.BytesIO(bytes_body))  # type: ignore[arg-type]


@pytest.mark.parametrize(
	("int_code", "bytes_body", "bool_expected"),
	[
		(404, b"", True),
		(422, b'{"message":"Reference does not exist"}', True),
		(422, b'{"message":"Cannot delete this branch: ruleset"}', False),
		(500, b"", False),
	],
)
def test_already_gone_counts_a_422_only_when_the_ref_is_missing(
	int_code: int, bytes_body: bytes, bool_expected: bool
) -> None:
	"""A ruleset refusal is also a 422, so only the missing-ref body counts as gone."""
	assert reconcile._already_gone(_http_error(int_code, bytes_body)) is bool_expected


def test_delete_branch_reraises_a_ruleset_422(monkeypatch: pytest.MonkeyPatch) -> None:
	"""A 422 that is not 'Reference does not exist' is a real failure, not a no-op."""

	def _boom(*_args: object, **_kwargs: object) -> None:
		raise _http_error(422, b'{"message":"ruleset"}')

	monkeypatch.setattr(reconcile, "_api", _boom)
	with pytest.raises(urllib.error.HTTPError):
		reconcile._delete_branch("api", "feat/x")


def _graphql_data() -> dict:
	return {
		"repository": {
			"defaultBranchRef": {"name": "main"},
			"pullRequest": {**_pr(ref="feat/parent"), "closingIssuesReferences": {"nodes": []}},
		}
	}


def test_open_pr_bases_collects_every_base(monkeypatch: pytest.MonkeyPatch) -> None:
	"""The set holds the base ref of each open PR."""
	list_open = [{"base": {"ref": "feat/a"}}, {"base": {"ref": "main"}}]
	monkeypatch.setattr(reconcile, "_api", lambda *_a, **_k: list_open)
	assert reconcile._open_pr_bases("api") == {"feat/a", "main"}


def test_open_pr_bases_reads_past_a_full_page(monkeypatch: pytest.MonkeyPatch) -> None:
	"""A full page means more may follow, so a base on page two still counts."""
	list_urls: list[str] = []

	def _fake_api(_str_method: str, str_url: str) -> list[dict]:
		list_urls.append(str_url)
		if str_url.endswith("page=1"):
			return [{"base": {"ref": "main"}}] * 100
		return [{"base": {"ref": "feat/late"}}]

	monkeypatch.setattr(reconcile, "_api", _fake_api)
	assert reconcile._open_pr_bases("api") == {"main", "feat/late"}
	assert [str_url[-6:] for str_url in list_urls] == ["page=1", "page=2"]


def test_reconcile_pr_keeps_a_branch_that_is_the_base_of_an_open_pr(
	monkeypatch: pytest.MonkeyPatch,
) -> None:
	"""Deleting the base of an open PR would close it, so no DELETE is sent."""
	list_calls: list[str] = []
	monkeypatch.setattr(
		reconcile, "_api", lambda str_method, *_a, **_k: list_calls.append(str_method)
	)
	monkeypatch.setattr(reconcile, "_graphql", lambda *_a, **_k: _graphql_data())
	_, str_branch = reconcile.reconcile_pr("api", "o", "n", 1, {"feat/parent"})
	assert str_branch is None
	assert "DELETE" not in list_calls


def test_main_aborts_before_any_delete_when_the_open_pr_read_fails(
	monkeypatch: pytest.MonkeyPatch,
) -> None:
	"""Without the open-PR list no deletion is safe: the run ends before touching anything."""
	list_calls: list[str] = []

	def _api(str_method: str, *_a: object, **_k: object) -> object:
		list_calls.append(str_method)
		raise OSError("boom")

	monkeypatch.setattr(reconcile, "_api", _api)
	monkeypatch.setenv("GITHUB_REPOSITORY", "o/n")
	monkeypatch.setenv("PR_NUMBER", "1")
	with pytest.raises(OSError, match="boom"):
		reconcile.main()
	assert list_calls == ["GET"]


def test_main_sweep_exits_nonzero_when_a_delete_is_refused(
	monkeypatch: pytest.MonkeyPatch,
) -> None:
	"""A ruleset 422 on DELETE fails the sweep instead of being logged as 'already gone'."""

	def _api(str_method: str, str_url: str, *_a: object, **_k: object) -> object:
		if str_method == "DELETE":
			raise _http_error(422, b'{"message":"ruleset"}')
		if "state=open" in str_url:
			return []
		return [{"number": 7, "merged_at": "2999-01-01T00:00:00Z"}]

	monkeypatch.setattr(reconcile, "_api", _api)
	monkeypatch.setattr(reconcile, "_graphql", lambda *_a, **_k: _graphql_data())
	monkeypatch.setenv("GITHUB_REPOSITORY", "o/n")
	monkeypatch.delenv("PR_NUMBER", raising=False)
	assert reconcile.main() == 1
