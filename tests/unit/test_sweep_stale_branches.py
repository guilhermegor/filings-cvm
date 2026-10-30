"""Unit tests for ``bin/sweep_stale_branches.py`` — decision logic and the ``main()`` seam."""

from __future__ import annotations

import importlib.util
import io
from pathlib import Path
from typing import Any
import urllib.error
import urllib.parse

import pytest


_PATH = Path(__file__).resolve().parents[2] / "bin" / "sweep_stale_branches.py"
_SPEC = importlib.util.spec_from_file_location("sweep_stale_branches", _PATH)
assert _SPEC is not None and _SPEC.loader is not None
mod = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(mod)


@pytest.mark.parametrize(
	("list_states", "str_expected"),
	[
		(["MERGED"], "delete"),
		(["merged"], "delete"),
		(["CLOSED", "MERGED"], "delete"),
		(["OPEN"], "keep-open-pr"),
		(["MERGED", "OPEN"], "keep-open-pr"),
		(["CLOSED"], "keep-no-merged-pr"),
		([], "keep-no-merged-pr"),
	],
)
def test_branch_verdict_classifies_pr_states(list_states: list[str], str_expected: str) -> None:
	"""Only a merged PR with no open PR earns deletion."""
	assert mod.branch_verdict(list_states) == str_expected


def test_negative_control_only_merged_branch_is_deleted() -> None:
	"""Open-PR and no-PR branches survive; the merged one is the only target."""
	dict_in = {"feat/open": ["OPEN"], "feat/wip": [], "feat/done": ["MERGED"]}
	assert mod.branches_to_delete(dict_in, "main") == ["feat/done"]


def test_never_deletes_branch_with_open_pr_even_if_also_merged() -> None:
	"""A reused branch (older PR merged, newer open) is kept."""
	assert mod.branches_to_delete({"feat/x": ["MERGED", "OPEN"]}, "main") == []


def test_never_deletes_default_or_protected_branch() -> None:
	"""The default branch and gh-pages are skipped even with a merged PR against them."""
	dict_in = {"main": ["MERGED"], "trunk": ["MERGED"], "gh-pages": ["MERGED"]}
	assert mod.branches_to_delete(dict_in, "trunk") == []


@pytest.mark.parametrize(
	("str_raw", "bool_expected"),
	[
		(None, True),
		("", True),
		("true", True),
		("garbage", True),
		("false", False),
		("FALSE", False),
		("0", False),
		("no", False),
	],
)
def test_is_dry_run_defaults_to_true(str_raw: str | None, bool_expected: bool) -> None:
	"""Only an explicit false disables dry run."""
	assert mod.is_dry_run(str_raw) is bool_expected


def _fake_api(list_calls: list[str], dict_prs: dict[str, list[dict]]) -> Any:  # noqa: ANN401
	"""Build an ``_api`` stand-in serving a fixed repo and recording DELETEs."""

	def _api(str_method: str, str_url: str) -> Any:  # noqa: ANN401
		if str_method == "DELETE":
			list_calls.append(urllib.parse.unquote(str_url))
			return {}
		if "/branches" in str_url:
			return [
				{"name": str_n, "commit": {"sha": f"tip-{str_n}"}, "protected": False}
				for str_n in ["main", "gh-pages", *dict_prs]
			]
		if "state=open" in str_url:
			return []
		if "/pulls" in str_url:
			str_head = urllib.parse.unquote(str_url.split("head=")[1].split("&")[0])
			str_branch = str_head.split(":")[1]
			return dict_prs[str_branch]
		return {"default_branch": "main"}

	return _api


def _merged(str_head_sha: str, str_base: str = "main") -> dict[str, Any]:
	"""Build a merged PR payload whose head is the given commit."""
	return {
		"state": "closed",
		"merged_at": "2026-01-01T00:00:00Z",
		"head": {"sha": str_head_sha},
		"base": {"ref": str_base},
	}


_PRS = {
	"feat/open": [{"state": "open", "merged_at": None, "head": {"sha": "tip-feat/open"}}],
	"feat/wip": [],
	"feat/closed": [{"state": "closed", "merged_at": None, "head": {"sha": "tip-feat/closed"}}],
	"feat/done": [_merged("tip-feat/done")],
}


def test_main_apply_deletes_only_merged_and_reports_count(
	monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
	"""End to end through ``main()``: one DELETE, and the examined count is printed."""
	list_calls: list[str] = []
	monkeypatch.setenv("GITHUB_REPOSITORY", "o/r")
	monkeypatch.setenv("SWEEP_DRY_RUN", "false")
	monkeypatch.setattr(mod, "_api", _fake_api(list_calls, _PRS))
	assert mod.main() == 0
	assert len(list_calls) == 1
	assert list_calls[0].endswith("/git/refs/heads/feat/done")
	assert "examined 6 branch(es)" in capsys.readouterr().out


def test_main_default_is_dry_run_and_deletes_nothing(
	monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
	"""Without SWEEP_DRY_RUN the sweep names the target but never calls DELETE."""
	list_calls: list[str] = []
	monkeypatch.setenv("GITHUB_REPOSITORY", "o/r")
	monkeypatch.delenv("SWEEP_DRY_RUN", raising=False)
	monkeypatch.setattr(mod, "_api", _fake_api(list_calls, _PRS))
	assert mod.main() == 0
	assert list_calls == []
	str_out = capsys.readouterr().out
	assert "would delete (dry run)" in str_out
	assert "1 stale (dry run)" in str_out


def test_main_keeps_branch_with_commits_pushed_after_merge(
	monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
	"""A merged PR whose head is not the tip proves nothing about the tip: no DELETE."""
	list_calls: list[str] = []
	monkeypatch.setenv("GITHUB_REPOSITORY", "o/r")
	monkeypatch.setenv("SWEEP_DRY_RUN", "false")
	dict_prs = {"feat/reused": [_merged("older-sha")]}
	monkeypatch.setattr(mod, "_api", _fake_api(list_calls, dict_prs))
	assert mod.main() == 0
	assert list_calls == []
	str_out = capsys.readouterr().out
	assert "1 with PR lookup" in str_out
	assert "0 stale" in str_out


def test_main_keeps_merged_branch_that_is_the_base_of_an_open_pr(
	monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
	"""Deleting a stacked PR's base closes that PR, so the base stays while its siblings go."""
	list_calls: list[str] = []
	dict_prs = {"feat/base": [_merged("tip-feat/base")], "feat/x": [_merged("tip-feat/x")]}
	fn_fake = _fake_api(list_calls, dict_prs)

	def _api(str_method: str, str_url: str) -> Any:  # noqa: ANN401
		if "state=open" in str_url:
			return [{"base": {"ref": "feat/base"}}]
		return fn_fake(str_method, str_url)

	monkeypatch.setenv("GITHUB_REPOSITORY", "o/r")
	monkeypatch.setenv("SWEEP_DRY_RUN", "false")
	monkeypatch.setattr(mod, "_api", _api)
	assert mod.main() == 0
	assert len(list_calls) == 1
	assert list_calls[0].endswith("feat/x")
	assert "branch=feat/base kept: base of an open PR" in capsys.readouterr().out


def test_main_keeps_branch_merged_into_a_non_default_base(
	monkeypatch: pytest.MonkeyPatch,
) -> None:
	"""A PR merged into a feature branch never reached the default branch: no DELETE."""
	list_calls: list[str] = []
	dict_prs = {"feat/a": [_merged("tip-feat/a", "feat/other")]}
	monkeypatch.setenv("GITHUB_REPOSITORY", "o/r")
	monkeypatch.setenv("SWEEP_DRY_RUN", "false")
	monkeypatch.setattr(mod, "_api", _fake_api(list_calls, dict_prs))
	assert mod.main() == 0
	assert list_calls == []


def test_list_branches_skips_protected_branches(monkeypatch: pytest.MonkeyPatch) -> None:
	"""GitHub's own ``protected`` flag excludes a branch from the sweep."""
	list_page = [
		{"name": "release", "commit": {"sha": "tip-r"}, "protected": True},
		{"name": "feat/a", "commit": {"sha": "tip-a"}, "protected": False},
	]
	monkeypatch.setattr(mod, "_api", lambda _m, _u: list_page)
	assert mod._list_branches("u") == {"feat/a": "tip-a"}


def test_main_open_pr_read_failure_deletes_nothing(monkeypatch: pytest.MonkeyPatch) -> None:
	"""Without the open-PR list no deletion is safe, so the run ends before any DELETE."""
	list_calls: list[str] = []
	fn_fake = _fake_api(list_calls, {"feat/a": [_merged("tip-feat/a")]})

	def _api(str_method: str, str_url: str) -> Any:  # noqa: ANN401
		if "state=open" in str_url:
			raise urllib.error.URLError("timed out")
		return fn_fake(str_method, str_url)

	monkeypatch.setenv("GITHUB_REPOSITORY", "o/r")
	monkeypatch.setenv("SWEEP_DRY_RUN", "false")
	monkeypatch.setattr(mod, "_api", _api)
	with pytest.raises(urllib.error.URLError):
		mod.main()
	assert list_calls == []


@pytest.mark.parametrize(
	"cls_exc",
	[
		urllib.error.HTTPError("u", 500, "boom", {}, None),  # type: ignore[arg-type]
		urllib.error.URLError("timed out"),
	],
)
def test_main_delete_failure_skips_branch_and_still_reports(
	monkeypatch: pytest.MonkeyPatch,
	capsys: pytest.CaptureFixture[str],
	cls_exc: Exception,
) -> None:
	"""A failed DELETE is counted, the next branch is still tried, and the summary prints."""
	list_calls: list[str] = []
	dict_prs = {"feat/a": [_merged("tip-feat/a")], "feat/b": [_merged("tip-feat/b")]}
	fn_fake = _fake_api(list_calls, dict_prs)

	def _api(str_method: str, str_url: str) -> Any:  # noqa: ANN401
		if str_method == "DELETE" and str_url.endswith("feat/a"):
			raise cls_exc
		return fn_fake(str_method, str_url)

	monkeypatch.setenv("GITHUB_REPOSITORY", "o/r")
	monkeypatch.setenv("SWEEP_DRY_RUN", "false")
	monkeypatch.setattr(mod, "_api", _api)
	assert mod.main() == 1
	assert len(list_calls) == 1
	assert list_calls[0].endswith("feat/b")
	assert "1 delete failure(s)" in capsys.readouterr().out


def test_main_lookup_failure_keeps_branch_and_fails_the_run(
	monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
	"""A failed PR lookup deletes nothing, still reports, and exits non-zero."""
	list_calls: list[str] = []
	dict_prs = {"feat/a": [_merged("tip-feat/a")]}
	fn_fake = _fake_api(list_calls, dict_prs)

	def _api(str_method: str, str_url: str) -> Any:  # noqa: ANN401
		if "head=" in str_url:
			raise urllib.error.URLError("timed out")
		return fn_fake(str_method, str_url)

	monkeypatch.setenv("GITHUB_REPOSITORY", "o/r")
	monkeypatch.setenv("SWEEP_DRY_RUN", "false")
	monkeypatch.setattr(mod, "_api", _api)
	assert mod.main() == 1
	assert list_calls == []
	assert "1 lookup failure(s)" in capsys.readouterr().out


def _http_error(int_code: int, bytes_body: bytes) -> urllib.error.HTTPError:
	"""Build an HTTP error whose body can be read, as a real response's can."""
	return urllib.error.HTTPError("u", int_code, "x", {}, io.BytesIO(bytes_body))  # type: ignore[arg-type]


@pytest.mark.parametrize(
	("int_code", "bytes_body"), [(404, b""), (422, b'{"message":"Reference does not exist"}')]
)
def test_main_already_gone_branch_is_not_a_failure(
	monkeypatch: pytest.MonkeyPatch,
	capsys: pytest.CaptureFixture[str],
	int_code: int,
	bytes_body: bytes,
) -> None:
	"""A 404, or a 422 naming the missing ref, means gone: exit 0, no failure counted."""
	list_calls: list[str] = []
	fn_fake = _fake_api(list_calls, {"feat/a": [_merged("tip-feat/a")]})

	def _api(str_method: str, str_url: str) -> Any:  # noqa: ANN401
		if str_method == "DELETE":
			raise _http_error(int_code, bytes_body)
		return fn_fake(str_method, str_url)

	monkeypatch.setenv("GITHUB_REPOSITORY", "o/r")
	monkeypatch.setenv("SWEEP_DRY_RUN", "false")
	monkeypatch.setattr(mod, "_api", _api)
	assert mod.main() == 0
	assert "0 delete failure(s)" in capsys.readouterr().out


def test_main_422_refusal_is_a_failure_not_already_gone(
	monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
	"""A ruleset's 422 leaves the branch in place, so it must fail the run."""
	list_calls: list[str] = []
	fn_fake = _fake_api(list_calls, {"feat/a": [_merged("tip-feat/a")]})

	def _api(str_method: str, str_url: str) -> Any:  # noqa: ANN401
		if str_method == "DELETE":
			raise _http_error(422, b'{"message":"Repository rule violations found"}')
		return fn_fake(str_method, str_url)

	monkeypatch.setenv("GITHUB_REPOSITORY", "o/r")
	monkeypatch.setenv("SWEEP_DRY_RUN", "false")
	monkeypatch.setattr(mod, "_api", _api)
	assert mod.main() == 1
	assert "1 delete failure(s)" in capsys.readouterr().out


def test_list_branches_follows_pagination_to_the_last_short_page(
	monkeypatch: pytest.MonkeyPatch,
) -> None:
	"""A full page means more may follow, so a branch on page two is still found."""
	monkeypatch.setattr(mod, "_PER_PAGE", 2)
	dict_pages = {
		"1": [
			{"name": "a", "commit": {"sha": "tip-a"}, "protected": False},
			{"name": "b", "commit": {"sha": "tip-b"}, "protected": False},
		],
		"2": [{"name": "c", "commit": {"sha": "tip-c"}, "protected": False}],
	}

	def _api(str_method: str, str_url: str) -> Any:  # noqa: ANN401
		return dict_pages[str_url.rsplit("page=", 1)[1]]

	monkeypatch.setattr(mod, "_api", _api)
	assert mod._list_branches("api") == {"a": "tip-a", "b": "tip-b", "c": "tip-c"}
