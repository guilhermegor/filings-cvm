"""Unit tests for the PR quality gate's classification logic.

Only the **pure** functions are tested — classification, sizing, the auto-merge decision and the
comment rendering. Every GitHub call lives behind `main()`/`_api()` and is never exercised here, so
these tests need no network (the autouse guard in `conftest.py` blocks sockets anyway).

The rule that matters most: **`src/` is never auto-mergeable, at any size** — a one-character
change to a `FileContract` is tiny *and* catastrophic, and every test still passes because the
tests assert the contract that was written.
"""

import importlib.util
from pathlib import Path

import pytest


# bin/ is not an importable package; load the module straight from its path.
_PATH = Path(__file__).resolve().parents[2] / "bin" / "pr_gate.py"
_SPEC = importlib.util.spec_from_file_location("pr_gate", _PATH)
assert _SPEC is not None and _SPEC.loader is not None
pr_gate = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(pr_gate)


@pytest.mark.parametrize(
	("list_paths", "str_expected"),
	[
		(["docs/api.md"], "docs"),
		(["README.md"], "docs"),
		(["mkdocs.yml"], "docs"),
		([".github/workflows/tests.yaml"], "ci"),
		(["bin/pr_gate.py"], "ci"),
		(["Makefile"], "ci"),
		(["poetry.lock"], "deps"),
		(["pyproject.toml"], "deps"),
		(["tests/unit/test_cda_ingestion.py"], "tests"),
		(["src/filings_cvm/ingestion/fip/doc/inf_trimestral.py"], "src"),
		(["some/unknown/path.txt"], "other"),
	],
)
def test_classify_risk_maps_each_path_family(list_paths: list[str], str_expected: str) -> None:
	"""Each path family maps to its risk class.

	Parameters
	----------
	list_paths : list of str
		Changed paths.
	str_expected : str
		Expected risk class.
	"""
	assert pr_gate.classify_risk(list_paths) == str_expected


def test_classify_risk_takes_the_most_dangerous_class() -> None:
	"""A PR touching both docs and src is classified `src`, never the safer of the two."""
	assert pr_gate.classify_risk(["docs/api.md", "src/filings_cvm/__init__.py"]) == "src"


def test_classify_risk_of_no_files_is_not_auto_mergeable() -> None:
	"""An empty diff falls to `other`, which is deliberately outside AUTO_MERGEABLE."""
	assert pr_gate.classify_risk([]) == "other"
	assert "other" not in pr_gate.AUTO_MERGEABLE


@pytest.mark.parametrize(
	("int_add", "int_del", "str_expected"),
	[
		(1, 0, "XS"),
		(5, 4, "XS"),
		(10, 0, "S"),
		(30, 19, "S"),
		(100, 99, "M"),
		(300, 100, "L"),
		(600, 0, "XL"),
	],
)
def test_size_bucket_maps_diff_volume(int_add: int, int_del: int, str_expected: str) -> None:
	"""The bucket follows additions + deletions.

	Parameters
	----------
	int_add : int
		Lines added.
	int_del : int
		Lines removed.
	str_expected : str
		Expected bucket.
	"""
	assert pr_gate.size_bucket(int_add, int_del) == str_expected


def test_src_is_never_auto_mergeable_even_when_tiny() -> None:
	"""THE core safety rule: a one-line `src/` change still needs a human — no label can arm it."""
	assert pr_gate.is_auto_mergeable("src", "XS", []) is False


def test_tests_class_is_not_auto_mergeable() -> None:
	"""Test-only changes also wait for review — they define what "passing" means."""
	assert pr_gate.is_auto_mergeable("tests", "S", []) is False


def test_safe_class_auto_merges_without_a_label() -> None:
	"""Opt-out model: classification IS the consent — a safe class merges with no label."""
	assert pr_gate.is_auto_mergeable("docs", "S", []) is True


def test_do_not_merge_label_opts_out() -> None:
	"""`do-not-merge` is the escape hatch — it holds an otherwise-eligible PR back."""
	assert pr_gate.is_auto_mergeable("docs", "S", [pr_gate.BLOCK_LABEL]) is False


def test_xl_diff_is_never_auto_merged() -> None:
	"""A huge docs/CI diff still deserves a look, no matter the class."""
	assert pr_gate.is_auto_mergeable("docs", "XL", []) is False


@pytest.mark.parametrize("str_class", sorted(pr_gate.AUTO_MERGEABLE))
def test_every_auto_mergeable_class_merges_without_a_label(str_class: str) -> None:
	"""Each declared auto-mergeable class merges by default — no label required.

	Parameters
	----------
	str_class : str
		A class from AUTO_MERGEABLE.
	"""
	assert pr_gate.is_auto_mergeable(str_class, "M", []) is True


def test_gate_state_pending_is_not_failing() -> None:
	"""A still-running check is `pending`, never `failing`.

	Regression: the gate's own first live run labelled a fresh PR `gate:failing` while its checks
	were still queued. Pending says nothing about the outcome — reporting it as a failure cries
	wolf on every newly-opened PR.
	"""
	list_running = [("Tests", "⏳", "running"), ("CodeQL", "✅", "ok")]

	assert pr_gate.gate_state(list_running) == "pending"


def test_gate_state_failing_beats_pending() -> None:
	"""A red axis wins over a pending one — a known failure is not "still deciding"."""
	list_mixed = [("Tests", "❌", "1 failing"), ("CodeQL", "⏳", "running")]

	assert pr_gate.gate_state(list_mixed) == "failing"


def test_gate_state_passing_needs_every_axis_finished_green() -> None:
	"""`passing` is only claimed when every axis actually completed green."""
	assert pr_gate.gate_state([("Tests", "✅", "ok"), ("CodeQL", "✅", "ok")]) == "passing"


def test_gate_state_of_no_axes_is_pending() -> None:
	"""No checks reported yet is pending, not a vacuous pass."""
	assert pr_gate.gate_state([]) == "pending"


def test_render_comment_headline_reflects_the_pending_state() -> None:
	"""The sticky comment says "Running" while checks run, not "Blocked"."""
	str_body = pr_gate.render_comment("docs", "S", [("Tests", "⏳", "running")], False)

	assert "Running" in str_body
	assert "Blocked" not in str_body


def test_render_comment_carries_the_marker_for_in_place_updates() -> None:
	"""The hidden marker is what lets the gate update one comment instead of stacking new ones."""
	str_body = pr_gate.render_comment("docs", "S", [("Tests", "✅", "ok")], False)

	assert pr_gate._MARKER in str_body


def test_render_comment_reports_green_only_when_every_axis_passed() -> None:
	"""One failing axis flips the headline to blocked."""
	list_mixed = [("Tests", "✅", "ok"), ("CodeQL", "❌", "1 failing")]

	assert "Gate green" in pr_gate.render_comment("docs", "S", [("Tests", "✅", "ok")], False)
	assert "Blocked" in pr_gate.render_comment("docs", "S", list_mixed, False)


def test_render_comment_explains_why_src_is_not_auto_merged() -> None:
	"""A `src` PR's comment states that human review is mandatory, not merely absent."""
	str_body = pr_gate.render_comment("src", "XS", [("Tests", "✅", "ok")], False)

	assert "Human review required" in str_body


def test_render_comment_says_enabled_when_auto_merge_is_on() -> None:
	"""An armed PR's comment states auto-merge is enabled (the default for a safe class)."""
	str_body = pr_gate.render_comment("docs", "S", [("Tests", "✅", "ok")], True)

	assert "Auto-merge enabled" in str_body


def test_render_comment_explains_an_xl_hold() -> None:
	"""An auto-mergeable class held only by an `XL` diff says a human must look."""
	str_body = pr_gate.render_comment("docs", "XL", [("Tests", "✅", "ok")], False)

	assert "Human review required" in str_body


def test_render_comment_explains_a_do_not_merge_hold() -> None:
	"""A non-XL auto-mergeable class with auto-merge off is held by the opt-out label."""
	str_body = pr_gate.render_comment("docs", "S", [("Tests", "✅", "ok")], False)

	assert "Auto-merge held" in str_body
	assert pr_gate.BLOCK_LABEL in str_body


def test_axes_from_checks_folds_matrix_runs_into_one_axis() -> None:
	"""The 3-OS test matrix collapses to a single "Tests" axis."""
	list_runs = [
		{
			"name": "Run Automated Tests (ubuntu-latest)",
			"status": "completed",
			"conclusion": "success",
		},
		{
			"name": "Run Automated Tests (macos-latest)",
			"status": "completed",
			"conclusion": "success",
		},
		{"name": "build", "status": "completed", "conclusion": "success"},
		{"name": "Analyze (python)", "status": "completed", "conclusion": "success"},
	]

	list_axes = pr_gate._axes_from_checks(list_runs)

	assert [icon for _, icon, _ in list_axes] == ["✅", "✅", "✅"]


def test_axes_from_checks_reports_a_failing_check() -> None:
	"""A failed matrix leg turns its axis red."""
	list_runs = [
		{
			"name": "Run Automated Tests (ubuntu-latest)",
			"status": "completed",
			"conclusion": "failure",
		},
		{"name": "build", "status": "completed", "conclusion": "success"},
		{"name": "Analyze (python)", "status": "completed", "conclusion": "success"},
	]

	list_axes = pr_gate._axes_from_checks(list_runs)

	assert list_axes[0][1] == "❌"


def test_axes_from_checks_marks_a_pending_check() -> None:
	"""A still-running check shows as pending, not as passing."""
	list_runs = [
		{
			"name": "Run Automated Tests (ubuntu-latest)",
			"status": "in_progress",
			"conclusion": None,
		},
	]

	list_axes = pr_gate._axes_from_checks(list_runs)

	assert list_axes[0][1] == "⏳"


def test_codeql_axis_tracks_the_analyze_runs_not_the_umbrella_check() -> None:
	"""The CodeQL axis reads `Analyze (…)`, never the 2-second `CodeQL` umbrella check.

	Regression (#76): under code-scanning default setup, the check named `CodeQL` completes in ~2
	seconds and flaps while awaiting a result for a new head SHA, long before the real analysis
	finishes. Reading it made the gate report "CodeQL failing" on a PR whose CodeQL went fully
	green seconds later.
	"""
	list_runs = [
		{"name": "CodeQL", "status": "completed", "conclusion": "failure"},
		{"name": "Analyze (python)", "status": "completed", "conclusion": "success"},
		{"name": "Analyze (actions)", "status": "completed", "conclusion": "success"},
	]

	str_label, str_icon, _ = pr_gate._axes_from_checks(list_runs)[2]

	assert str_label == "Security (CodeQL)"
	assert str_icon == "✅"


def test_codeql_axis_is_pending_before_any_analysis_reports() -> None:
	"""No `Analyze (…)` run yet on this head SHA is PENDING, not a failure."""
	list_runs = [{"name": "build", "status": "completed", "conclusion": "success"}]

	_, str_icon, str_detail = pr_gate._axes_from_checks(list_runs)[2]

	assert str_icon == "⏳"
	assert str_detail == "awaiting result"


def test_failing_axis_names_the_failing_checks() -> None:
	"""A red axis says WHICH check failed — the comment must explain itself."""
	list_runs = [
		{"name": "Analyze (python)", "status": "completed", "conclusion": "failure"},
	]

	_, _, str_detail = pr_gate._axes_from_checks(list_runs)[2]

	assert "Analyze (python)" in str_detail
	assert "failure" in str_detail


def test_axes_are_terminal_is_false_while_any_axis_still_runs() -> None:
	"""THE freeze regression (#76): a red axis beside a pending one is NOT terminal.

	`gate_state` reports `failing` here (a red outranks a pending, for display), and the old loop
	broke on `state != "pending"` — freezing the sticky comment on "Blocked" seconds before the
	pending checks went green, with nothing left to revisit it. The loop must keep polling.
	"""
	list_mixed = [("Tests", "⏳", "running"), ("CodeQL", "❌", "1 failing")]

	assert pr_gate.gate_state(list_mixed) == "failing"
	assert pr_gate.axes_are_terminal(list_mixed) is False


def test_axes_are_terminal_when_every_axis_finished() -> None:
	"""All axes done — green or red — is terminal; the loop may stop."""
	list_red = [("Tests", "✅", "ok"), ("CodeQL", "❌", "1 failing")]

	assert pr_gate.axes_are_terminal(list_red) is True
	assert pr_gate.axes_are_terminal([("Tests", "✅", "ok"), ("CodeQL", "✅", "ok")]) is True


def test_axes_are_terminal_is_false_with_no_axes() -> None:
	"""Nothing reported yet is not "finished" — keep polling, never render a vacuous verdict."""
	assert pr_gate.axes_are_terminal([]) is False
