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


def test_src_is_never_auto_mergeable_even_when_tiny_and_opted_in() -> None:
	"""THE core safety rule: a one-line `src/` change with the opt-in label still needs a human."""
	assert pr_gate.is_auto_mergeable("src", "XS", [pr_gate.OPT_IN_LABEL]) is False


def test_tests_class_is_not_auto_mergeable() -> None:
	"""Test-only changes also wait for review — they define what "passing" means."""
	assert pr_gate.is_auto_mergeable("tests", "S", [pr_gate.OPT_IN_LABEL]) is False


def test_auto_merge_requires_the_opt_in_label() -> None:
	"""Classification alone is not consent — the label is."""
	assert pr_gate.is_auto_mergeable("docs", "S", []) is False
	assert pr_gate.is_auto_mergeable("docs", "S", [pr_gate.OPT_IN_LABEL]) is True


def test_block_label_overrides_the_opt_in() -> None:
	"""`do-not-merge` wins over `automerge`, whatever the class."""
	assert (
		pr_gate.is_auto_mergeable("docs", "S", [pr_gate.OPT_IN_LABEL, pr_gate.BLOCK_LABEL])
		is False
	)


def test_xl_diff_is_never_auto_merged() -> None:
	"""A huge docs/CI diff still deserves a look."""
	assert pr_gate.is_auto_mergeable("docs", "XL", [pr_gate.OPT_IN_LABEL]) is False


@pytest.mark.parametrize("str_class", sorted(pr_gate.AUTO_MERGEABLE))
def test_every_auto_mergeable_class_merges_when_opted_in(str_class: str) -> None:
	"""Each declared auto-mergeable class does merge once opted in.

	Parameters
	----------
	str_class : str
		A class from AUTO_MERGEABLE.
	"""
	assert pr_gate.is_auto_mergeable(str_class, "M", [pr_gate.OPT_IN_LABEL]) is True


def test_gate_state_pending_is_not_failing() -> None:
	"""A still-running check is `pending`, never `failing`.

	Regression: the gate's own first live run labelled a fresh PR `gate:failing` while its checks
	were still queued. Pending says nothing about the outcome — reporting it as a failure cries
	wolf on every newly-opened PR.
	"""
	list_running = [("Testes", "⏳", "em execução"), ("CodeQL", "✅", "ok")]

	assert pr_gate.gate_state(list_running) == "pending"


def test_gate_state_failing_beats_pending() -> None:
	"""A red axis wins over a pending one — a known failure is not "still deciding"."""
	list_mixed = [("Testes", "❌", "1 falhando"), ("CodeQL", "⏳", "em execução")]

	assert pr_gate.gate_state(list_mixed) == "failing"


def test_gate_state_passing_needs_every_axis_finished_green() -> None:
	"""`passing` is only claimed when every axis actually completed green."""
	assert pr_gate.gate_state([("Testes", "✅", "ok"), ("CodeQL", "✅", "ok")]) == "passing"


def test_gate_state_of_no_axes_is_pending() -> None:
	"""No checks reported yet is pending, not a vacuous pass."""
	assert pr_gate.gate_state([]) == "pending"


def test_render_comment_headline_reflects_the_pending_state() -> None:
	"""The sticky comment says "em execução" while checks run, not "Bloqueado"."""
	str_body = pr_gate.render_comment("docs", "S", [("Testes", "⏳", "em execução")], False)

	assert "Em execução" in str_body
	assert "Bloqueado" not in str_body


def test_render_comment_carries_the_marker_for_in_place_updates() -> None:
	"""The hidden marker is what lets the gate update one comment instead of stacking new ones."""
	str_body = pr_gate.render_comment("docs", "S", [("Testes", "✅", "ok")], False)

	assert pr_gate._MARKER in str_body


def test_render_comment_reports_green_only_when_every_axis_passed() -> None:
	"""One failing axis flips the headline to blocked."""
	list_mixed = [("Testes", "✅", "ok"), ("CodeQL", "❌", "1 falhando")]

	assert "Gate verde" in pr_gate.render_comment("docs", "S", [("Testes", "✅", "ok")], False)
	assert "Bloqueado" in pr_gate.render_comment("docs", "S", list_mixed, False)


def test_render_comment_explains_why_src_is_not_auto_merged() -> None:
	"""A `src` PR's comment states that human review is mandatory, not merely absent."""
	str_body = pr_gate.render_comment("src", "XS", [("Testes", "✅", "ok")], False)

	assert "Revisão humana obrigatória" in str_body


def test_render_comment_invites_the_opt_in_when_eligible_but_unlabelled() -> None:
	"""An eligible class without the label is told how to opt in."""
	str_body = pr_gate.render_comment("docs", "S", [("Testes", "✅", "ok")], False)

	assert pr_gate.OPT_IN_LABEL in str_body


def test_axes_from_checks_folds_matrix_runs_into_one_axis() -> None:
	"""The 3-OS test matrix collapses to a single "Testes" axis."""
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
		{"name": "CodeQL", "status": "completed", "conclusion": "success"},
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
		{"name": "CodeQL", "status": "completed", "conclusion": "success"},
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
