"""Unit tests for ``bin/check_backlog_ledger.py`` — the deterministic work-ledger gate.

Loaded by path (``bin/`` is not an importable package). The script is the BlueprintX template's
version; these tests pin its behaviour: flat ``.specs/backlog`` ledgers, fenced checkboxes,
bot-author exemption keyed on the PR author, and a merge in progress.
"""

import importlib.util
import json
from pathlib import Path

import pytest


_BIN = Path(__file__).resolve().parents[2] / "bin"
_SPEC = importlib.util.spec_from_file_location(
	"check_backlog_ledger", _BIN / "check_backlog_ledger.py"
)
assert _SPEC is not None and _SPEC.loader is not None
clg = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(clg)

_GATE = clg._load_pr_gate()
assert _GATE is not None, "bin/pr_gate.py must exist: the ledger gate classifies paths with it"

_LEDGER = ".specs/backlog/topic_20260717_091038.md"


@pytest.mark.parametrize(
	("list_paths", "bool_expected"),
	[
		(["src/filings_cvm/x.py"], True),
		(["bin/foo.py"], True),
		([".github/workflows/tests.yaml"], True),
		(["bin/foo.py", "tests/test_x.py"], True),  # per-path: tests must not mask bin/
		(["src/filings_cvm/x.py", _LEDGER], True),
		(["docs/api.md"], False),
		(["tests/test_x.py"], False),
		([_LEDGER], False),
		([], False),
	],
)
def test_needs_ledger(list_paths: list[str], bool_expected: bool) -> None:
	"""needs_ledger asks set-membership per path, immune to most-dangerous collapse."""
	assert clg.needs_ledger(list_paths, _GATE) is bool_expected


@pytest.mark.parametrize(
	("str_path", "bool_ok"),
	[
		(".specs/backlog/backlog-ledger-gate_20260717_091038.md", True),
		(".specs/backlog/a_20260101_000000.md", True),
		(".specs/backlog/Bad-Caps_20260717_091038.md", False),
		(".specs/backlog/no-timestamp.md", False),
		(".specs/backlog/under_score_20260717_091038.md", False),
		(".specs/backlog/short_2026071_091038.md", False),
		(".specs/backlog/topic_20260717_091038.txt", False),
		("docs/backlog/topic_20260717_091038.md", False),  # the old home no longer counts
		(".specs/backlog/sub/topic_20260717_091038.md", False),  # flat
	],
)
def test_ledger_name_pattern(str_path: str, bool_ok: bool) -> None:
	"""Only a flat ``.specs/backlog/<kebab-topic>_YYYYMMDD_HHMMSS.md`` is a ledger."""
	assert bool(clg.LEDGER_RE.match(str_path)) is bool_ok


@pytest.mark.parametrize(
	("str_text", "bool_ok"),
	[
		("- [ ] todo\n", True),
		("- [x] done\n", True),
		("- [~] chore/363-specs in progress\n", True),
		("1. [ ] numbered\n", True),
		("- [~] no-branch\n", False),
		("- bare bullet\n", False),
		("prose only\n", False),
		("```\n- [ ] only inside a fence\n```\n", False),
		("```\n- [ ] fenced\n```\n- [ ] real\n", True),
		("", False),
	],
)
def test_checkbox_outside_fences(str_text: str, bool_ok: bool) -> None:
	"""A ledger needs a real checkbox outside a code fence."""
	assert bool(clg.CHECKBOX_RE.search(clg.FENCE_RE.sub("", str_text))) is bool_ok


def test_find_ledger_problems_none_added() -> None:
	"""A src/ci diff with no ledger is one error."""
	assert len(clg.find_ledger_problems(["bin/foo.py"])) == 1


def test_find_ledger_problems_old_location_is_not_a_ledger() -> None:
	"""A ledger under the old docs/backlog home does not satisfy the gate."""
	assert clg.find_ledger_problems(["bin/foo.py", "docs/backlog/t_20260717_091038.md"])


def test_find_ledger_problems_bad_name() -> None:
	"""A mis-named ledger is flagged."""
	list_problems = clg.find_ledger_problems(["src/x.py", ".specs/backlog/Bad_Name.md"])
	assert "name must match" in "".join(list_problems)


def test_find_ledger_problems_one_valid_ledger_is_enough(
	tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
	"""One good ledger clears the branch even beside a ledger without a checkbox."""
	monkeypatch.chdir(tmp_path)
	(tmp_path / ".specs/backlog").mkdir(parents=True)
	(tmp_path / ".specs/backlog/a_20260101_000000.md").write_text("- [ ] x\n", encoding="utf-8")
	(tmp_path / ".specs/backlog/b_20260101_000000.md").write_text("prose\n", encoding="utf-8")

	assert (
		clg.find_ledger_problems(
			[
				"src/x.py",
				".specs/backlog/a_20260101_000000.md",
				".specs/backlog/b_20260101_000000.md",
			]
		)
		== []
	)


def test_find_ledger_problems_checkbox_missing(
	tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
	"""A lone ledger with no checkbox outside a fence is flagged."""
	monkeypatch.chdir(tmp_path)
	(tmp_path / ".specs/backlog").mkdir(parents=True)
	(tmp_path / _LEDGER).write_text("```\n- [ ] fenced\n```\n", encoding="utf-8")

	list_problems = clg.find_ledger_problems(["src/x.py", _LEDGER])

	assert "checkbox" in "".join(list_problems)


@pytest.mark.parametrize(
	("str_login", "bool_is_bot"),
	[
		("dependabot[bot]", True),
		("github-actions[bot]", True),
		("guilhermegor", False),
		("robotics-dev", False),
		("someone[bot]x", False),
		("", False),
	],
)
def test_is_bot_author(str_login: str, bool_is_bot: bool) -> None:
	"""Only GitHub's ``[bot]`` suffix exempts an author; an unresolved one fails closed."""
	assert clg.is_bot_author(str_login) is bool_is_bot


def _write_event(path: Path, str_login: str) -> None:
	path.write_text(json.dumps({"pull_request": {"user": {"login": str_login}}}), encoding="utf-8")


def test_pr_author_comes_from_the_event_payload_not_the_actor(
	tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
	"""A human re-running a bot's PR keeps the bot as author (PR #167)."""
	path_event = tmp_path / "event.json"
	_write_event(path_event, "dependabot[bot]")
	monkeypatch.setenv("GITHUB_EVENT_PATH", str(path_event))
	monkeypatch.setenv("GITHUB_ACTOR", "guilhermegor")

	assert clg.pr_author_login() == "dependabot[bot]"


def test_a_bot_triggered_rerun_of_a_human_pr_is_not_exempt(
	tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
	"""The inverse must not leak: the actor being a bot does not exempt a human's PR."""
	path_event = tmp_path / "event.json"
	_write_event(path_event, "guilhermegor")
	monkeypatch.setenv("GITHUB_EVENT_PATH", str(path_event))
	monkeypatch.setenv("GITHUB_ACTOR", "github-actions[bot]")

	assert clg.is_bot_author(clg.pr_author_login()) is False


@pytest.mark.parametrize("str_content", ["not json", ""])
def test_unreadable_event_fails_closed(
	tmp_path: Path, monkeypatch: pytest.MonkeyPatch, str_content: str
) -> None:
	"""A payload that cannot be parsed yields no author, so nobody is exempted."""
	path_event = tmp_path / "event.json"
	path_event.write_text(str_content, encoding="utf-8")
	monkeypatch.setenv("GITHUB_EVENT_PATH", str(path_event))
	monkeypatch.setenv("GITHUB_ACTOR", "dependabot[bot]")

	assert clg.pr_author_login() == ""


def test_missing_event_file_fails_closed(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
	"""A GITHUB_EVENT_PATH that points nowhere yields no author."""
	monkeypatch.setenv("GITHUB_EVENT_PATH", str(tmp_path / "nope.json"))

	assert clg.pr_author_login() == ""


def test_actor_is_only_the_fallback_without_a_payload(monkeypatch: pytest.MonkeyPatch) -> None:
	"""With no event path (push run, local hook) GITHUB_ACTOR is consulted."""
	monkeypatch.delenv("GITHUB_EVENT_PATH", raising=False)
	monkeypatch.setenv("GITHUB_ACTOR", "guilhermegor")

	assert clg.pr_author_login() == "guilhermegor"


def test_merge_heads_reads_every_incoming_commit(
	monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
	"""An octopus merge lists several heads in MERGE_HEAD; all are returned."""
	path_head = tmp_path / "MERGE_HEAD"
	path_head.write_text("aaa\nbbb\n", encoding="utf-8")
	monkeypatch.setattr(clg, "_git", lambda _args: str(path_head))

	assert clg.merge_heads() == ["aaa", "bbb"]


def test_merge_heads_empty_without_a_merge(
	monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
	"""No MERGE_HEAD file means no merge in progress."""
	monkeypatch.setattr(clg, "_git", lambda _args: str(tmp_path / "MERGE_HEAD"))

	assert clg.merge_heads() == []


def test_resolve_base_counts_the_merge_in_progress(monkeypatch: pytest.MonkeyPatch) -> None:
	"""Mid-merge the merge-base is taken against HEAD and every incoming head."""
	list_calls: list[list[str]] = []
	monkeypatch.setattr(clg, "default_branch", lambda: "main")
	monkeypatch.setattr(clg, "merge_heads", lambda: ["aaa", "bbb"])
	monkeypatch.setattr(clg, "_git", lambda args: list_calls.append(args) or "base")

	assert (clg.resolve_base(), list_calls) == (
		"base",
		[["merge-base", "main", "HEAD", "aaa", "bbb"]],
	)
