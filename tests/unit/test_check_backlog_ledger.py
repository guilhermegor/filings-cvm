"""Unit tests for ``bin/check_backlog_ledger.py`` — the deterministic work-ledger gate.

Loaded by path (``bin/`` is not an importable package); the module self-bootstraps its sibling
``pr_gate`` import, so no ``sys.path`` juggling is needed here.
"""

import importlib.util
from pathlib import Path

import pytest


_PATH = Path(__file__).resolve().parents[2] / "bin" / "check_backlog_ledger.py"
_SPEC = importlib.util.spec_from_file_location("check_backlog_ledger", _PATH)
assert _SPEC is not None and _SPEC.loader is not None
clg = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(clg)


@pytest.mark.parametrize(
	("list_paths", "bool_expected"),
	[
		(["src/filings_cvm/x.py"], True),
		(["bin/foo.py"], True),
		([".github/workflows/tests.yaml"], True),
		(["Makefile"], True),
		(["bin/foo.py", "tests/test_x.py"], True),
		(["src/filings_cvm/x.py", "docs/backlog/topic_20260717_091038.md"], True),
		(["docs/api.md"], False),
		(["poetry.lock"], False),
		(["pyproject.toml"], False),
		(["tests/test_x.py"], False),
		(["docs/backlog/topic_20260717_091038.md"], False),
		([], False),
	],
)
def test_requires_ledger(list_paths: list[str], bool_expected: bool) -> None:
	"""requires_ledger asks set-membership per path, immune to most-dangerous collapse."""
	assert clg.requires_ledger(list_paths) is bool_expected


@pytest.mark.parametrize(
	("str_name", "bool_ok"),
	[
		("backlog-ledger-gate_20260717_091038.md", True),
		("a_20260101_000000.md", True),
		("Bad-Caps_20260717_091038.md", False),
		("no-timestamp.md", False),
		("under_score_20260717_091038.md", False),  # topic is kebab: no underscores of its own
		("short_2026071_091038.md", False),  # 7-digit date
		("short_20260717_09103.md", False),  # 5-digit time
		("topic_20260717_091038.txt", False),  # wrong extension
	],
)
def test_is_valid_ledger_name(str_name: str, bool_ok: bool) -> None:
	"""The name gate accepts only ``<kebab-topic>_YYYYMMDD_HHMMSS.md``."""
	assert clg.is_valid_ledger_name(str_name) is bool_ok


@pytest.mark.parametrize(
	("str_text", "bool_ok"),
	[
		("- [ ] todo\n", True),
		("- [x] done\n", True),
		("- [X] done\n", True),
		("  - [ ] indented under a heading\n", True),
		("* [ ] star bullet\n", True),
		("intro\n\n- [ ] later item\n", True),
		("- bare bullet, no box\n", False),
		("-[ ] no space after dash\n", False),
		("prose only, no items\n", False),
		("", False),
	],
)
def test_has_checkbox_item(str_text: str, bool_ok: bool) -> None:
	"""A ledger must carry at least one real Markdown checkbox, not bare bullets."""
	assert clg.has_checkbox_item(str_text) is bool_ok


def test_check_passes_when_no_src_ci_path() -> None:
	"""A docs-only diff owes no ledger."""
	assert clg.check(["docs/api.md"], lambda _p: None) == []


def test_check_fails_when_ci_path_and_no_ledger() -> None:
	"""A ci/src diff with no ledger in it is one hard error."""
	list_errors = clg.check(["bin/foo.py"], lambda _p: None)
	assert len(list_errors) == 1
	assert "work ledger" in list_errors[0]


def test_check_passes_with_valid_ledger() -> None:
	"""A ci diff that carries a well-named ledger with a checkbox is clean."""
	list_paths = ["bin/foo.py", "docs/backlog/topic_20260717_091038.md"]
	assert clg.check(list_paths, lambda _p: "- [ ] do the thing\n") == []


def test_check_flags_bad_ledger_name() -> None:
	"""A ledger whose name misses the timestamp pattern is flagged."""
	list_paths = ["src/x.py", "docs/backlog/Bad_Name.md"]
	list_errors = clg.check(list_paths, lambda _p: "- [ ] x\n")
	assert any("filename" in e for e in list_errors)


def test_check_flags_ledger_without_checkbox() -> None:
	"""A ledger with only bare bullets (no checkbox) is flagged."""
	list_paths = ["src/x.py", "docs/backlog/topic_20260717_091038.md"]
	list_errors = clg.check(list_paths, lambda _p: "- just a bullet\n")
	assert any("checkbox" in e for e in list_errors)


def test_check_skips_content_when_ledger_is_absent() -> None:
	"""A valid-named ledger the diff deletes (reader returns None) passes — no content to judge."""
	list_paths = ["src/x.py", "docs/backlog/topic_20260717_091038.md"]
	assert clg.check(list_paths, lambda _p: None) == []


@pytest.mark.parametrize(
	("str_actor", "bool_is_bot"),
	[
		("dependabot[bot]", True),
		("github-actions[bot]", True),
		("Dependabot[Bot]", True),  # GitHub's casing is not guaranteed
		("  dependabot[bot]  ", True),  # tolerate stray whitespace from the env
		("guilhermegor", False),
		("robotics-dev", False),  # "bot" as a substring is not the marker
		("someone[bot]x", False),  # the suffix must terminate the name
		("", False),
		(None, False),  # a local run has no GITHUB_ACTOR — humans stay bound
	],
)
def test_is_bot_actor(str_actor: str | None, bool_is_bot: bool) -> None:
	"""Only GitHub's own ``[bot]`` suffix marks an actor as exempt.

	Parameters
	----------
	str_actor : str or None
		The candidate actor name.
	bool_is_bot : bool
		Whether it should count as a bot.
	"""
	assert clg.is_bot_actor(str_actor) is bool_is_bot


def test_the_rule_itself_still_binds_a_workflow_change() -> None:
	"""⚠️ Negative control: the exemption must not have disabled the gate.

	``check`` is pure and knows nothing about actors, so a workflow-touching diff with no ledger
	still reports a violation. Without this assertion the bot exemption could silently neuter the
	rule for everyone and every test would stay green.
	"""
	list_found = clg.check([".github/workflows/tests.yaml"], lambda _: None)

	assert list_found
	assert "work ledger" in list_found[0]


def test_a_human_workflow_change_with_a_ledger_passes() -> None:
	"""The ordinary human path is unaffected: workflow + valid ledger = clean."""
	list_paths = [".github/workflows/tests.yaml", "docs/backlog/topic_20260729_101500.md"]

	assert clg.check(list_paths, lambda _: "- [ ] do the thing\n") == []
