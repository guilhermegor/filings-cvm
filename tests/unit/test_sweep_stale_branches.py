"""Unit tests for ``bin/sweep_stale_branches.py`` — decision logic and the ``main()`` seam."""

from __future__ import annotations

import importlib.util
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
				{"name": str_n, "commit": {"sha": f"tip-{str_n}"}}
				for str_n in ["main", "gh-pages", *dict_prs]
			]
		if "/pulls" in str_url:
			str_head = urllib.parse.unquote(str_url.split("head=")[1].split("&")[0])
			str_branch = str_head.split(":")[1]
			return dict_prs[str_branch]
		return {"default_branch": "main"}

	return _api


def _merged(str_head_sha: str) -> dict[str, Any]:
	"""Build a merged PR payload whose head is the given commit."""
	return {
		"state": "closed",
		"merged_at": "2026-01-01T00:00:00Z",
		"head": {"sha": str_head_sha},
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
	monkeypatch: pytest.MonkeyPatch,
) -> None:
	"""A merged PR whose head is not the tip proves nothing about the tip: no DELETE."""
	list_calls: list[str] = []
	monkeypatch.setenv("GITHUB_REPOSITORY", "o/r")
	monkeypatch.setenv("SWEEP_DRY_RUN", "false")
	dict_prs = {"feat/reused": [_merged("older-sha")]}
	monkeypatch.setattr(mod, "_api", _fake_api(list_calls, dict_prs))
	assert mod.main() == 0
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
	assert mod.main() == 0
	assert len(list_calls) == 1
	assert list_calls[0].endswith("feat/b")
	assert "1 delete failure(s)" in capsys.readouterr().out
