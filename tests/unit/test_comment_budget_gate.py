"""Unit tests for the comment-budget gate (blueprintx#303).

**The calibration is the thing under test**, same rule as
``test_comment_language_gate.py``: a rule that "simplifies" away one class of
false positive or false negative keeps the obvious cases passing while
quietly reopening the exact gap it was written to close. Each test below pins
one measured behaviour by name — the should-fail witness the issue asks for
(``test_a_run_one_line_over_the_ceiling_is_flagged`` /
``test_the_same_run_passes_with_a_pragma_in_the_middle``) is the negative
control: the two tests share the same oversized run, differing only by one
``# noqa`` line, so a change that breaks the "pragma breaks a run" rule fails
the second test while the first stays green.
"""

import importlib.util
from pathlib import Path
import subprocess
import sys
from types import ModuleType

import pytest


_BIN = Path(__file__).resolve().parents[2] / "bin"


def _load(str_name: str) -> ModuleType:
	"""Load a ``bin/`` script by path (``bin/`` is not a package).

	Parameters
	----------
	str_name : str
		Module stem under ``bin/``.

	Returns
	-------
	ModuleType
		The imported module.
	"""
	cls_spec = importlib.util.spec_from_file_location(str_name, _BIN / f"{str_name}.py")
	cls_module = importlib.util.module_from_spec(cls_spec)
	sys.modules[str_name] = cls_module
	cls_spec.loader.exec_module(cls_module)
	return cls_module


gate = _load("check_comment_budget")


def test_a_short_comment_block_is_not_flagged(tmp_path: Path) -> None:
	"""A handful of comment lines, well under the ratchet, is clean.

	Parameters
	----------
	tmp_path : pathlib.Path
		A throwaway directory pytest provides per test.
	"""
	path_file = tmp_path / "probe.sh"
	path_file.write_text("# short\n# rationale\necho hi\n", encoding="utf-8")
	assert gate.file_problems(path_file) == []


def test_a_run_one_line_over_the_ceiling_is_flagged(tmp_path: Path) -> None:
	"""The should-fail witness, part 1: one line past ``INT_MAX_RUN`` fails.

	Parameters
	----------
	tmp_path : pathlib.Path
		A throwaway directory pytest provides per test.
	"""
	path_file = tmp_path / "probe.sh"
	list_lines = ["# filler"] * (gate.INT_MAX_RUN + 1)
	path_file.write_text("\n".join(list_lines) + "\n", encoding="utf-8")
	list_problems = gate.file_problems(path_file)
	assert len(list_problems) == 1


def test_the_same_run_passes_with_a_pragma_in_the_middle(tmp_path: Path) -> None:
	"""The should-fail witness, part 2: a ``# noqa`` in the middle breaks the run.

	Same total line count as the failing case above — the only difference is
	one pragma line splitting it into two runs, each under the ceiling.

	Parameters
	----------
	tmp_path : pathlib.Path
		A throwaway directory pytest provides per test.
	"""
	path_file = tmp_path / "probe.sh"
	int_half = gate.INT_MAX_RUN // 2
	list_lines = ["# filler"] * int_half + ["# noqa"] + ["# filler"] * int_half
	path_file.write_text("\n".join(list_lines) + "\n", encoding="utf-8")
	assert gate.file_problems(path_file) == []


def test_a_qa_pragma_line_is_never_itself_a_finding(tmp_path: Path) -> None:
	"""A lone suppression pragma, nowhere near the ceiling, is clean.

	Parameters
	----------
	tmp_path : pathlib.Path
		A throwaway directory pytest provides per test.
	"""
	path_file = tmp_path / "probe.sh"
	path_file.write_text("# noqa\necho hi\n", encoding="utf-8")
	assert gate.file_problems(path_file) == []


def test_the_escape_hatch_exempts_a_flagged_block() -> None:
	"""``# comment-budget-ok: <reason>`` anywhere in the block exempts it."""
	list_lines = ["filler"] * (gate.INT_MAX_RUN + 1)
	list_lines[0] = " comment-budget-ok: pinned oracle, see docs/decisions/x.md"
	assert gate.has_valid_escape(list_lines) is True


def test_a_bare_escape_marker_with_no_reason_does_not_exempt() -> None:
	"""A marker with nothing after the colon is rejected, like `# complexity-ok:`."""
	assert gate.has_valid_escape([" comment-budget-ok:"]) is False


def test_the_escape_hatch_exempts_a_real_oversized_block(tmp_path: Path) -> None:
	"""A valid marker inside a real over-ceiling block exempts the whole file.

	Should-fail witness for blueprintx#303's own follow-up defect: the marker's
	text must NOT be in ``comment_budget_allowlist.txt``, because a pragma line
	BREAKS a run (``line_breaks_run``) before ``has_valid_escape`` ever sees it —
	so a listed escape hatch could never exempt the block it opens.

	Parameters
	----------
	tmp_path : pathlib.Path
		A throwaway directory pytest provides per test.
	"""
	path_file = tmp_path / "probe.sh"
	list_lines = ["# comment-budget-ok: pinned oracle, see docs/decisions/x.md"]
	list_lines += ["# filler"] * (gate.INT_MAX_RUN + 1)
	path_file.write_text("\n".join(list_lines) + "\n", encoding="utf-8")
	assert gate.file_problems(path_file) == []


def test_a_bare_marker_inside_a_real_oversized_block_still_fails(tmp_path: Path) -> None:
	"""A reasonless marker mid-block must not silently split or exempt the run.

	Same defect from the other side: if the marker were still in the allowlist
	it would BREAK the run in two, each half under the ceiling, so a bare
	marker with no reason would silently pass — exactly the bypass
	``has_valid_escape`` exists to reject.

	Parameters
	----------
	tmp_path : pathlib.Path
		A throwaway directory pytest provides per test.
	"""
	path_file = tmp_path / "probe.sh"
	list_lines = ["# filler"] * (gate.INT_MAX_RUN + 1)
	list_lines.insert(len(list_lines) // 2, "# comment-budget-ok:")
	path_file.write_text("\n".join(list_lines) + "\n", encoding="utf-8")
	assert len(gate.file_problems(path_file)) == 1


def test_a_pragma_line_splits_one_block_into_two() -> None:
	"""Two five-line blocks separated by one pragma are two findings, not one."""
	list_lines = ["# a"] * 5 + ["# noqa"] + ["# b"] * 5
	list_blocks = gate.marker_blocks("\n".join(list_lines), "#")
	assert len(list_blocks) == 2


def test_a_hash_inside_a_python_string_literal_is_not_a_comment() -> None:
	"""``tokenize`` tells a real comment apart from a `#` inside a string."""
	assert gate.python_blocks('x = "# not a comment # not a comment"\n') == []


def test_python_docstrings_are_excluded_from_the_budget(tmp_path: Path) -> None:
	"""A long NumPy docstring is documentation, not the comment volume bounded here.

	Parameters
	----------
	tmp_path : pathlib.Path
		A throwaway directory pytest provides per test.
	"""
	path_file = tmp_path / "probe.py"
	list_docstring_lines = ["    line"] * (gate.INT_MAX_RUN + 1)
	str_source = 'def f() -> None:\n    """\n' + "\n".join(list_docstring_lines) + '\n    """\n'
	path_file.write_text(str_source, encoding="utf-8")
	assert gate.file_problems(path_file) == []


def test_a_decorative_banner_triple_is_flagged() -> None:
	"""A rule / title / rule sandwich is the Makefile's own measured shape."""
	list_findings = gate.banner_findings(1, [" -------", " LINTING", " -------"])
	assert list_findings == [(1, 3)]


def test_a_lone_punctuation_line_is_flagged_as_a_banner() -> None:
	"""A single punctuation-only line, not sandwiching anything, is still a defect."""
	list_findings = gate.banner_findings(1, ["hello", " ----", "world"])
	assert list_findings == [(2, 1)]


def test_a_banner_rule_with_no_closing_rule_is_not_a_triple() -> None:
	"""One rule line with ordinary prose after it is a lone banner, not a sandwich."""
	list_findings = gate.banner_findings(1, [" -------", " a real sentence"])
	assert list_findings == [(1, 1)]


def test_a_section_title_alone_is_not_a_banner() -> None:
	"""Ordinary prose between two non-banner lines is never flagged."""
	assert gate.banner_findings(1, ["a", "b", "c"]) == []


def test_a_shebang_line_is_structurally_exempt() -> None:
	"""Line 1's ``#!`` never counts toward a run."""
	assert gate.line_breaks_run(1, "#!/usr/bin/env bash", "!/usr/bin/env bash", ()) is True


def test_an_encoding_declaration_is_structurally_exempt() -> None:
	"""A PEP 263 encoding declaration on line 2 is metadata, not prose."""
	assert gate.line_breaks_run(2, "# -*- coding: utf-8 -*-", " -*- coding: utf-8 -*-", ()) is True


def test_a_shebang_shaped_line_deeper_in_the_file_is_not_exempt() -> None:
	"""The same text past line 2 is ordinary prose — position, not content, decides."""
	assert gate.line_breaks_run(3, "#!/usr/bin/env bash", "!/usr/bin/env bash", ()) is False


def test_marker_for_recognizes_makefile_by_name() -> None:
	"""``Makefile`` has no suffix, so it must be matched on its exact name."""
	assert gate.marker_for(Path("Makefile")) == "#"


def test_marker_for_recognizes_mk_suffix() -> None:
	"""A ``*.mk`` include file gets the same ``#`` marker."""
	assert gate.marker_for(Path("common.mk")) == "#"


def test_marker_for_recognizes_typescript_suffixes() -> None:
	"""TypeScript files use ``//``, not ``#``."""
	assert gate.marker_for(Path("app.tsx")) == "//"


def test_marker_for_rejects_an_unsupported_extension() -> None:
	"""A binary or otherwise unlisted extension is not budgeted at all."""
	assert gate.marker_for(Path("image.png")) == ""


def test_marker_for_recognizes_python_files() -> None:
	"""``.py`` gets a marker too, even though its blocks are extracted elsewhere.

	``.py`` is deliberately absent from ``DICT_HASH_SUFFIXES`` (its blocks are
	extracted via ``tokenize`` instead) but ``marker_for`` must still return a
	marker for it — should-fail witness for blueprintx#466: without this,
	``file_problems`` returns ``[]`` for every ``.py`` file before ever reaching
	the ``python_blocks`` branch, so ``audit_paths`` reports files "checked"
	that were never actually inspected.
	"""
	assert gate.marker_for(Path("probe.py")) == "#"


def test_audit_discovers_an_extensionless_makefile(
	tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
	"""``audit_paths`` must find ``Makefile`` even though ``rglob("*Makefile")`` would not.

	Parameters
	----------
	tmp_path : pathlib.Path
		A throwaway directory pytest provides per test.
	monkeypatch : pytest.MonkeyPatch
		Used to point the gate's discovery root at ``tmp_path``.
	"""
	(tmp_path / "Makefile").write_text("build:\n\techo hi\n", encoding="utf-8")
	monkeypatch.setattr(gate, "PATH_ROOT", tmp_path)
	assert tmp_path / "Makefile" in gate.audit_paths()


def test_a_python_file_with_a_decorative_banner_is_flagged(tmp_path: Path) -> None:
	"""Should-fail witness: a ``.py`` file's own banner defect must surface.

	Before blueprintx#466, ``marker_for`` never recognized ``.py``, so
	``file_problems`` returned ``[]`` for every Python file regardless of
	content — this is the case that must now fail.

	Parameters
	----------
	tmp_path : pathlib.Path
		A throwaway directory pytest provides per test.
	"""
	path_file = tmp_path / "probe.py"
	str_source = "# -------\n# LINTING\n# -------\ndef f() -> None:\n\tpass\n"
	path_file.write_text(str_source, encoding="utf-8")
	assert len(gate.file_problems(path_file)) == 1


def test_a_python_file_with_an_oversized_comment_run_is_flagged(tmp_path: Path) -> None:
	"""Should-fail witness: a ``.py`` file's long-run defect must surface too.

	Parameters
	----------
	tmp_path : pathlib.Path
		A throwaway directory pytest provides per test.
	"""
	path_file = tmp_path / "probe.py"
	list_lines = ["# filler"] * (gate.INT_MAX_RUN + 1)
	path_file.write_text("\n".join(list_lines) + "\ndef f() -> None:\n\tpass\n", encoding="utf-8")
	assert len(gate.file_problems(path_file)) == 1


def test_a_section_banner_in_a_test_module_is_a_finding(tmp_path: Path) -> None:
	"""Should-fail witness: the old test-section banner is no longer exempt.

	``tests/CLAUDE.md`` once mandated this rule/title/rule triple in every test
	module and the gate exempted it by file type. The convention is gone (the
	suite carries no comments), so the exemption was deleted with it: the same
	three lines in a test module are now the plain decorative banner.

	Parameters
	----------
	tmp_path : pathlib.Path
		A throwaway directory pytest provides per test.
	"""
	path_dir = tmp_path / "tests"
	path_dir.mkdir()
	path_file = path_dir / "test_probe.py"
	str_rule = "# " + "-" * 26 + "\n"
	str_code = "def test_something() -> None:\n\tassert True\n"
	path_file.write_text(str_rule + "# Tests\n" + str_rule + str_code, encoding="utf-8")
	assert len(gate.file_problems(path_file)) == 1


def test_a_production_python_file_banner_is_named_a_decorative_banner(
	tmp_path: Path,
) -> None:
	"""The one finding on a production ``.py`` triple names the banner rule.

	Parameters
	----------
	tmp_path : pathlib.Path
		A throwaway directory pytest provides per test.
	"""
	path_dir = tmp_path / "src"
	path_dir.mkdir()
	path_file = path_dir / "service.py"
	str_rule = "# " + "-" * 26 + "\n"
	str_code = "def run() -> None:\n\treturn None\n"
	path_file.write_text(str_rule + "# Helpers\n" + str_rule + str_code)
	assert "decorative banner (rule/title/rule)" in gate.file_problems(path_file)[0]


def test_a_shell_banner_triple_under_tests_is_a_finding(tmp_path: Path) -> None:
	"""A shell file under ``tests/`` carrying the triple is a banner like any other.

	Parameters
	----------
	tmp_path : pathlib.Path
		A throwaway directory pytest provides per test.
	"""
	path_dir = tmp_path / "tests"
	path_dir.mkdir()
	path_file = path_dir / "probe.sh"
	str_source = (
		"#!/bin/bash\n"
		"# --------------------------\n"
		"# Fixtures\n"
		"# --------------------------\n"
		"echo hi\n"
	)
	path_file.write_text(str_source, encoding="utf-8")
	assert len(gate.file_problems(path_file)) == 1


def test_a_shell_banner_finding_is_named_a_decorative_banner(tmp_path: Path) -> None:
	"""The one finding on a ``tests/`` shell triple names the banner rule.

	Parameters
	----------
	tmp_path : pathlib.Path
		A throwaway directory pytest provides per test.
	"""
	path_dir = tmp_path / "tests"
	path_dir.mkdir()
	path_file = path_dir / "probe.sh"
	str_rule = "# " + "-" * 26 + "\n"
	path_file.write_text("#!/bin/bash\n" + str_rule + "# Fixtures\n" + str_rule + "echo hi\n")
	assert "decorative banner (rule/title/rule)" in gate.file_problems(path_file)[0]


@pytest.fixture
def list_split_run_problems(tmp_path: Path) -> list[str]:
	"""Problems for an 89-line block with one lone rule line in the middle (blueprintx#479).

	``comment_budget_allowlist.txt`` is read by ``is_pragma_line``, and
	``line_breaks_run`` makes a pragma BREAK the current run — correct for a
	QA suppression, wrong for a banner: listing the test-section rule line
	there let one dash line split an 89-line block into two 44-line halves,
	each under ``INT_MAX_RUN``, so the whole file passed clean. A lone rule
	line (no title, no closing rule after it) must both stay IN the run's line
	count and be flagged as its own decorative banner.

	Parameters
	----------
	tmp_path : pathlib.Path
		A throwaway directory pytest provides per test.

	Returns
	-------
	list[str]
		The gate's findings for the probe file.
	"""
	path_file = tmp_path / "probe.py"
	list_lines = ["# filler"] * 44 + ["# --------------------------"] + ["# filler"] * 44
	path_file.write_text("\n".join(list_lines) + "\n", encoding="utf-8")
	return gate.file_problems(path_file)


def test_a_lone_rule_line_does_not_split_an_oversized_run(
	list_split_run_problems: list[str],
) -> None:
	"""Should-fail witness for blueprintx#479: the lone rule line stays in the run's count.

	Parameters
	----------
	list_split_run_problems : list[str]
		The gate's findings for the probe file.
	"""
	assert any("89 lines" in str_problem for str_problem in list_split_run_problems)


def test_a_lone_rule_line_inside_an_oversized_run_is_flagged_as_a_banner(
	list_split_run_problems: list[str],
) -> None:
	"""The lone rule line is also reported as its own decorative banner.

	Parameters
	----------
	list_split_run_problems : list[str]
		The gate's findings for the probe file.
	"""
	assert any("decorative banner" in str_problem for str_problem in list_split_run_problems)


def test_an_oversized_run_split_by_a_rule_line_yields_exactly_two_findings(
	list_split_run_problems: list[str],
) -> None:
	"""One run-length finding and one banner finding, nothing more.

	Parameters
	----------
	list_split_run_problems : list[str]
		The gate's findings for the probe file.
	"""
	assert len(list_split_run_problems) == 2


@pytest.fixture
def list_triple_run_problems(tmp_path: Path) -> list[str]:
	"""Problems for an oversized block wrapped around a rule/title/rule triple.

	Parameters
	----------
	tmp_path : pathlib.Path
		A throwaway directory pytest provides per test.

	Returns
	-------
	list[str]
		The gate's findings for the probe file.
	"""
	path_dir = tmp_path / "tests"
	path_dir.mkdir()
	path_file = path_dir / "probe.py"
	list_lines = (
		["# filler"] * 44
		+ ["# --------------------------", "# Tests", "# --------------------------"]
		+ ["# filler"] * 44
	)
	path_file.write_text("\n".join(list_lines) + "\n", encoding="utf-8")
	return gate.file_problems(path_file)


def test_a_triple_still_counts_toward_an_oversized_run(
	list_triple_run_problems: list[str],
) -> None:
	"""The triple stays in the run's line count.

	Parameters
	----------
	list_triple_run_problems : list[str]
		The gate's findings for the probe file.
	"""
	assert any("91 lines" in str_problem for str_problem in list_triple_run_problems)


def test_a_triple_inside_a_run_is_also_reported_as_a_banner(
	list_triple_run_problems: list[str],
) -> None:
	"""The run-length finding is joined by one banner finding for the triple.

	Parameters
	----------
	list_triple_run_problems : list[str]
		The gate's findings for the probe file.
	"""
	assert any("decorative banner" in str_problem for str_problem in list_triple_run_problems)


def test_audit_mode_fails_when_no_file_matches(
	tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture
) -> None:
	"""A gate that scans nothing must report failure, never a silent pass.

	Parameters
	----------
	tmp_path : pathlib.Path
		An empty throwaway directory — nothing here matches any supported type.
	monkeypatch : pytest.MonkeyPatch
		Used to point the gate's discovery root at ``tmp_path``.
	capsys : pytest.CaptureFixture
		Captures the printed diagnostic.
	"""
	monkeypatch.setattr(gate, "PATH_ROOT", tmp_path)
	assert gate.main([]) == 1


def test_a_clean_tree_reports_the_file_count_on_success(
	tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture
) -> None:
	"""A silent gate is indistinguishable from one that never ran — print the count.

	Parameters
	----------
	tmp_path : pathlib.Path
		A throwaway directory holding one clean file.
	monkeypatch : pytest.MonkeyPatch
		Used to point the gate's discovery root at ``tmp_path``.
	capsys : pytest.CaptureFixture
		Captures the printed success line.
	"""
	(tmp_path / "clean.sh").write_text("#!/bin/bash\necho hi\n", encoding="utf-8")
	monkeypatch.setattr(gate, "PATH_ROOT", tmp_path)
	gate.main([])
	assert "✅ comment budget OK (1 file" in capsys.readouterr().out


_PATH_REPO = Path(__file__).resolve().parents[4]


@pytest.fixture(autouse=True)
def _restore_root(monkeypatch: pytest.MonkeyPatch) -> None:
	"""Undo ``--root``'s change to the module-level ``PATH_ROOT`` after each test.

	Parameters
	----------
	monkeypatch : pytest.MonkeyPatch
		Records the original value and restores it at teardown.
	"""
	monkeypatch.setattr(gate, "PATH_ROOT", gate.PATH_ROOT)


def _run(path_root: Path, capsys: pytest.CaptureFixture, *list_args: str) -> tuple:
	"""Run the gate over ``path_root`` and return ``(exit_code, stdout)``.

	Parameters
	----------
	path_root : pathlib.Path
		The tree to audit.
	capsys : pytest.CaptureFixture
		Captures the gate's report.
	*list_args : str
		Extra flags after ``--root``.

	Returns
	-------
	tuple
		The exit code and everything printed.
	"""
	int_code = gate.main(["--root", str(path_root), *list_args])
	return int_code, capsys.readouterr().out


def _tree(path_root: Path, str_text: str, str_baseline: str = "") -> None:
	"""Write ``a.py`` and a baseline file under ``path_root``.

	Parameters
	----------
	path_root : pathlib.Path
		Tree root.
	str_text : str
		Content of ``a.py``.
	str_baseline : str, optional
		Baseline file text; an empty string still creates the file (ratchet on).
	"""
	(path_root / "a.py").write_text(str_text, encoding="utf-8")
	(path_root / gate.STR_BASELINE_NAME).write_text(str_baseline, encoding="utf-8")


def test_a_new_file_with_one_prose_comment_fails(
	tmp_path: Path, capsys: pytest.CaptureFixture
) -> None:
	"""Should-fail witness: a file absent from the baseline has a baseline of 0.

	Parameters
	----------
	tmp_path : pathlib.Path
		A throwaway directory pytest provides per test.
	capsys : pytest.CaptureFixture
		Captures the gate's report.
	"""
	_tree(tmp_path, "# why this exists\nX = 1\n")
	int_code, str_out = _run(tmp_path, capsys)
	assert (int_code, "a.py: 1 comment line(s), baseline 0" in str_out) == (1, True)


def test_a_file_above_its_baseline_fails(tmp_path: Path, capsys: pytest.CaptureFixture) -> None:
	"""Should-fail witness: one comment more than the recorded count is a finding.

	Parameters
	----------
	tmp_path : pathlib.Path
		A throwaway directory pytest provides per test.
	capsys : pytest.CaptureFixture
		Captures the gate's report.
	"""
	_tree(tmp_path, "# one\n# two\nX = 1\n", "1 a.py\n")
	assert _run(tmp_path, capsys)[0] == 1


def test_a_file_below_its_baseline_is_a_stale_baseline(
	tmp_path: Path, capsys: pytest.CaptureFixture
) -> None:
	"""Should-fail witness: removing a comment without lowering the baseline fails.

	Parameters
	----------
	tmp_path : pathlib.Path
		A throwaway directory pytest provides per test.
	capsys : pytest.CaptureFixture
		Captures the gate's report.
	"""
	_tree(tmp_path, "# one\nX = 1\n", "3 a.py\n")
	int_code, str_out = _run(tmp_path, capsys)
	assert (int_code, "stale baseline" in str_out) == (1, True)


def test_a_vanished_file_with_a_baseline_row_is_stale(
	tmp_path: Path, capsys: pytest.CaptureFixture
) -> None:
	"""A deleted file's row must be removed, or the ratchet would never reach zero.

	Parameters
	----------
	tmp_path : pathlib.Path
		A throwaway directory pytest provides per test.
	capsys : pytest.CaptureFixture
		Captures the gate's report.
	"""
	_tree(tmp_path, "X = 1\n", "2 gone.py\n")
	assert _run(tmp_path, capsys)[0] == 1


def test_a_file_at_its_baseline_passes(tmp_path: Path, capsys: pytest.CaptureFixture) -> None:
	"""Exactly the recorded count is clean.

	Parameters
	----------
	tmp_path : pathlib.Path
		A throwaway directory pytest provides per test.
	capsys : pytest.CaptureFixture
		Captures the gate's report.
	"""
	_tree(tmp_path, "# one\nX = 1\n", "1 a.py\n")
	assert _run(tmp_path, capsys)[0] == 0


def test_without_a_baseline_file_the_ratchet_is_off(
	tmp_path: Path, capsys: pytest.CaptureFixture
) -> None:
	"""A generated project ships no baseline, so a short comment is not a finding yet.

	Parameters
	----------
	tmp_path : pathlib.Path
		A throwaway directory pytest provides per test.
	capsys : pytest.CaptureFixture
		Captures the gate's report.
	"""
	(tmp_path / "a.py").write_text("# one\nX = 1\n", encoding="utf-8")
	assert _run(tmp_path, capsys)[0] == 0


def test_write_baseline_records_counts_and_then_passes(
	tmp_path: Path, capsys: pytest.CaptureFixture
) -> None:
	"""``--write-baseline`` regenerates the file and the next run is green.

	Parameters
	----------
	tmp_path : pathlib.Path
		A throwaway directory pytest provides per test.
	capsys : pytest.CaptureFixture
		Captures the gate's report.
	"""
	(tmp_path / "b.py").write_text("X = 1\n", encoding="utf-8")
	_tree(tmp_path, "# one\n# two\nX = 1\n")
	(tmp_path / gate.STR_BASELINE_NAME).unlink()
	_run(tmp_path, capsys, "--write-baseline")
	str_written = (tmp_path / gate.STR_BASELINE_NAME).read_text(encoding="utf-8")
	assert (str_written, _run(tmp_path, capsys)[0]) == (
		f"{gate.STR_SCOPE_ROW}{gate.INT_SCOPE}\n2 a.py\n",
		0,
	)


def test_docstrings_are_not_counted(tmp_path: Path, capsys: pytest.CaptureFixture) -> None:
	"""A docstring is documentation, so a new file may carry one.

	Parameters
	----------
	tmp_path : pathlib.Path
		A throwaway directory pytest provides per test.
	capsys : pytest.CaptureFixture
		Captures the gate's report.
	"""
	_tree(tmp_path, '"""Module doc."""\n\n\ndef f() -> None:\n\t"""Doc."""\n')
	assert _run(tmp_path, capsys)[0] == 0


def test_a_required_baseline_that_is_missing_fails(
	tmp_path: Path, capsys: pytest.CaptureFixture
) -> None:
	"""Should-fail witness: the root hook must not pass because the baseline was deleted.

	Parameters
	----------
	tmp_path : pathlib.Path
		A throwaway directory pytest provides per test.
	capsys : pytest.CaptureFixture
		Captures the gate's report.
	"""
	(tmp_path / "a.py").write_text("# one\nX = 1\n", encoding="utf-8")
	assert _run(tmp_path, capsys, "--require-baseline")[0] == 1


def test_a_scoped_write_baseline_is_refused(tmp_path: Path, capsys: pytest.CaptureFixture) -> None:
	"""Should-fail witness: naming a file would overwrite every other baseline row.

	Parameters
	----------
	tmp_path : pathlib.Path
		A throwaway directory pytest provides per test.
	capsys : pytest.CaptureFixture
		Captures the gate's report.
	"""
	_tree(tmp_path, "# one\nX = 1\n", "1 a.py\n")
	int_code = gate.main(["--root", str(tmp_path), "--write-baseline", str(tmp_path / "a.py")])
	assert (int_code, (tmp_path / gate.STR_BASELINE_NAME).read_text(encoding="utf-8")) == (
		1,
		"1 a.py\n",
	)


def test_write_baseline_refuses_to_raise_an_existing_row(
	tmp_path: Path, capsys: pytest.CaptureFixture
) -> None:
	"""Should-fail witness: regenerating must not accept a file that gained comments.

	Parameters
	----------
	tmp_path : pathlib.Path
		A throwaway directory pytest provides per test.
	capsys : pytest.CaptureFixture
		Captures the gate's report.
	"""
	_tree(tmp_path, "# one\n# two\nX = 1\n", "1 a.py\n")
	int_code = _run(tmp_path, capsys, "--write-baseline")[0]
	assert (int_code, (tmp_path / gate.STR_BASELINE_NAME).read_text(encoding="utf-8")) == (
		1,
		"1 a.py\n",
	)


def test_write_baseline_lowers_an_existing_row(
	tmp_path: Path, capsys: pytest.CaptureFixture
) -> None:
	"""Regenerating after a sweep records the lower count.

	Parameters
	----------
	tmp_path : pathlib.Path
		A throwaway directory pytest provides per test.
	capsys : pytest.CaptureFixture
		Captures the gate's report.
	"""
	_tree(tmp_path, "# one\nX = 1\n", "3 a.py\n")
	_run(tmp_path, capsys, "--write-baseline")
	assert (tmp_path / gate.STR_BASELINE_NAME).read_text(
		encoding="utf-8"
	) == f"{gate.STR_SCOPE_ROW}{gate.INT_SCOPE}\n1 a.py\n"


def _git(path_root: Path, *list_args: str) -> None:
	"""Run git quietly inside ``path_root`` with a throwaway identity.

	Parameters
	----------
	path_root : pathlib.Path
		The repository.
	*list_args : str
		Git arguments.
	"""
	subprocess.run(  # noqa: S603 -- fixed git argv, no shell
		["git", "-c", "user.name=t", "-c", "user.email=t@t", *list_args],  # noqa: S607
		cwd=path_root,
		check=True,
		capture_output=True,
	)


def test_a_git_detected_rename_regenerates(tmp_path: Path, capsys: pytest.CaptureFixture) -> None:
	"""Should-fail witness: ``git mv`` of a file with comments needs no hand edit.

	Parameters
	----------
	tmp_path : pathlib.Path
		A throwaway directory pytest provides per test.
	capsys : pytest.CaptureFixture
		Captures the gate's report.
	"""
	_git(tmp_path, "init", "-q")
	(tmp_path / "old.py").write_text("# one\nX = 1\n", encoding="utf-8")
	_git(tmp_path, "add", "old.py")
	_git(tmp_path, "commit", "-qm", "x")
	_git(tmp_path, "mv", "old.py", "a.py")
	(tmp_path / gate.STR_BASELINE_NAME).write_text("1 old.py\n", encoding="utf-8")
	_run(tmp_path, capsys, "--write-baseline")
	assert (tmp_path / gate.STR_BASELINE_NAME).read_text(
		encoding="utf-8"
	) == f"{gate.STR_SCOPE_ROW}{gate.INT_SCOPE}\n1 a.py\n"


def test_freed_budget_does_not_transfer_to_a_new_file(
	tmp_path: Path, capsys: pytest.CaptureFixture
) -> None:
	"""Should-fail witness: a comment deleted in one file cannot be spent in a new one.

	Parameters
	----------
	tmp_path : pathlib.Path
		A throwaway directory pytest provides per test.
	capsys : pytest.CaptureFixture
		Captures the gate's report.
	"""
	_tree(tmp_path, "X = 1\n", f"{gate.STR_SCOPE_ROW}{gate.INT_SCOPE}\n1 old.py\n")
	(tmp_path / "old.py").write_text("X = 1\n", encoding="utf-8")
	(tmp_path / "new.py").write_text("# fresh\nX = 1\n", encoding="utf-8")
	assert _run(tmp_path, capsys, "--write-baseline")[0] == 1


def test_prose_that_merely_names_a_directive_is_counted(
	tmp_path: Path, capsys: pytest.CaptureFixture
) -> None:
	"""Should-fail witness: the allowlist matches directive syntax, not a mention.

	Parameters
	----------
	tmp_path : pathlib.Path
		A throwaway directory pytest provides per test.
	capsys : pytest.CaptureFixture
		Captures the gate's report.
	"""
	_tree(tmp_path, "# Avoid noqa in this file\nX = 1\n")
	assert _run(tmp_path, capsys)[0] == 1


def test_a_hand_raised_baseline_fails_the_comparison(
	tmp_path: Path, capsys: pytest.CaptureFixture
) -> None:
	"""Should-fail witness: editing the baseline upward is caught against the base copy.

	Parameters
	----------
	tmp_path : pathlib.Path
		A throwaway directory pytest provides per test.
	capsys : pytest.CaptureFixture
		Captures the gate's report.
	"""
	_tree(tmp_path, "# one\n# two\nX = 1\n", "2 a.py\n")
	path_ref = tmp_path / "ref.txt"
	path_ref.write_text("1 a.py\n", encoding="utf-8")
	assert _run(tmp_path, capsys, "--compare-baseline", str(path_ref))[0] == 1


def test_an_unchanged_baseline_passes_the_comparison(
	tmp_path: Path, capsys: pytest.CaptureFixture
) -> None:
	"""The baseline equal to the base copy is clean.

	Parameters
	----------
	tmp_path : pathlib.Path
		A throwaway directory pytest provides per test.
	capsys : pytest.CaptureFixture
		Captures the gate's report.
	"""
	_tree(tmp_path, "# one\nX = 1\n", "1 a.py\n")
	path_ref = tmp_path / "ref.txt"
	path_ref.write_text("1 a.py\n", encoding="utf-8")
	assert _run(tmp_path, capsys, "--compare-baseline", str(path_ref))[0] == 0


def test_a_malformed_baseline_row_is_a_finding_not_a_traceback(
	tmp_path: Path, capsys: pytest.CaptureFixture
) -> None:
	"""Should-fail witness: a row without a count reports and exits 1.

	Parameters
	----------
	tmp_path : pathlib.Path
		A throwaway directory pytest provides per test.
	capsys : pytest.CaptureFixture
		Captures the gate's report.
	"""
	_tree(tmp_path, "X = 1\n", "garbage\n")
	int_code, str_out = _run(tmp_path, capsys)
	assert (int_code, "malformed baseline row" in str_out) == (1, True)


def test_prose_that_merely_mentions_a_linter_is_counted(
	tmp_path: Path, capsys: pytest.CaptureFixture
) -> None:
	"""Should-fail witness: the allowlist matches directives, not any mention of a tool.

	Parameters
	----------
	tmp_path : pathlib.Path
		A throwaway directory pytest provides per test.
	capsys : pytest.CaptureFixture
		Captures the gate's report.
	"""
	_tree(tmp_path, "# hadolint auto-discovers its config from the cwd\nX = 1\n")
	assert _run(tmp_path, capsys)[0] == 1


def test_a_trailing_comment_in_yaml_is_counted(
	tmp_path: Path, capsys: pytest.CaptureFixture
) -> None:
	"""Should-fail witness: ``key: 1  # why`` is a comment.

	Parameters
	----------
	tmp_path : pathlib.Path
		A throwaway directory pytest provides per test.
	capsys : pytest.CaptureFixture
		Captures the gate's report.
	"""
	(tmp_path / gate.STR_BASELINE_NAME).write_text("", encoding="utf-8")
	(tmp_path / "a.yaml").write_text("key: 1  # why\n", encoding="utf-8")
	assert _run(tmp_path, capsys)[0] == 1


def test_a_hash_inside_a_yaml_string_is_not_a_comment(
	tmp_path: Path, capsys: pytest.CaptureFixture
) -> None:
	"""A ``#`` inside quotes is data.

	Parameters
	----------
	tmp_path : pathlib.Path
		A throwaway directory pytest provides per test.
	capsys : pytest.CaptureFixture
		Captures the gate's report.
	"""
	(tmp_path / gate.STR_BASELINE_NAME).write_text("", encoding="utf-8")
	(tmp_path / "a.yaml").write_text('key: "a # b"\n', encoding="utf-8")
	assert _run(tmp_path, capsys)[0] == 0


def test_a_jsdoc_block_and_trailing_slash_comment_are_counted(
	tmp_path: Path, capsys: pytest.CaptureFixture
) -> None:
	"""Should-fail witness: ``/** */`` and ``x; // y`` in TypeScript count per line.

	Parameters
	----------
	tmp_path : pathlib.Path
		A throwaway directory pytest provides per test.
	capsys : pytest.CaptureFixture
		Captures the gate's report.
	"""
	(tmp_path / gate.STR_BASELINE_NAME).write_text("", encoding="utf-8")
	(tmp_path / "a.ts").write_text("/**\n * Doc.\n */\nconst x = 1; // y\n", encoding="utf-8")
	int_code, str_out = _run(tmp_path, capsys)
	assert (int_code, "a.ts: 4 comment line(s)" in str_out) == (1, True)


def test_a_url_inside_a_ts_string_is_not_a_comment(
	tmp_path: Path, capsys: pytest.CaptureFixture
) -> None:
	"""``"http://x"`` holds no ``//`` comment.

	Parameters
	----------
	tmp_path : pathlib.Path
		A throwaway directory pytest provides per test.
	capsys : pytest.CaptureFixture
		Captures the gate's report.
	"""
	(tmp_path / gate.STR_BASELINE_NAME).write_text("", encoding="utf-8")
	(tmp_path / "a.ts").write_text('const u = "http://x";\n', encoding="utf-8")
	assert _run(tmp_path, capsys)[0] == 0


def test_a_banner_word_outside_the_file_head_is_counted(
	tmp_path: Path, capsys: pytest.CaptureFixture
) -> None:
	"""Should-fail witness: ``~`` entries only exempt a generated-file banner near the top.

	Parameters
	----------
	tmp_path : pathlib.Path
		A throwaway directory pytest provides per test.
	capsys : pytest.CaptureFixture
		Captures the gate's report.
	"""
	(tmp_path / gate.STR_BASELINE_NAME).write_text("", encoding="utf-8")
	str_source = "X = 1\n" * 20 + "# this is not @generated at all\n"
	(tmp_path / "a.py").write_text(str_source, encoding="utf-8")
	assert _run(tmp_path, capsys)[0] == 1


def test_an_empty_allowlist_pattern_is_rejected(
	tmp_path: Path, capsys: pytest.CaptureFixture, monkeypatch: pytest.MonkeyPatch
) -> None:
	"""Should-fail witness: a lone ``~`` would exempt everything, so it is an error.

	Parameters
	----------
	tmp_path : pathlib.Path
		A throwaway directory pytest provides per test.
	capsys : pytest.CaptureFixture
		Captures the gate's report.
	monkeypatch : pytest.MonkeyPatch
		Points the gate at a bad allowlist.
	"""
	(tmp_path / "a.py").write_text("# prose\nX = 1\n", encoding="utf-8")
	path_list = tmp_path / "allow.txt"
	path_list.write_text("~\n", encoding="utf-8")
	monkeypatch.setattr(gate, "PATH_ALLOWLIST", path_list)
	assert _run(tmp_path, capsys)[0] == 1


def test_compare_baseline_without_a_value_is_a_finding(
	tmp_path: Path, capsys: pytest.CaptureFixture
) -> None:
	"""Should-fail witness: no traceback for a missing flag value.

	Parameters
	----------
	tmp_path : pathlib.Path
		A throwaway directory pytest provides per test.
	capsys : pytest.CaptureFixture
		Captures the gate's report.
	"""
	_tree(tmp_path, "X = 1\n")
	assert gate.main(["--root", str(tmp_path), "--compare-baseline"]) == 1


def test_compare_baseline_with_a_missing_file_is_a_finding(
	tmp_path: Path, capsys: pytest.CaptureFixture
) -> None:
	"""Should-fail witness: no traceback for an unreadable reference.

	Parameters
	----------
	tmp_path : pathlib.Path
		A throwaway directory pytest provides per test.
	capsys : pytest.CaptureFixture
		Captures the gate's report.
	"""
	_tree(tmp_path, "X = 1\n")
	assert _run(tmp_path, capsys, "--compare-baseline", str(tmp_path / "nope.txt"))[0] == 1


def test_a_committed_rename_is_still_detected(
	tmp_path: Path, capsys: pytest.CaptureFixture
) -> None:
	"""Should-fail witness: rename detection uses the merge-base, not just ``HEAD``.

	Parameters
	----------
	tmp_path : pathlib.Path
		A throwaway directory pytest provides per test.
	capsys : pytest.CaptureFixture
		Captures the gate's report.
	"""
	_git(tmp_path, "init", "-q", "-b", "main")
	(tmp_path / "old.py").write_text("# one\nX = 1\n", encoding="utf-8")
	_git(tmp_path, "add", "old.py")
	_git(tmp_path, "commit", "-qm", "x")
	_git(tmp_path, "update-ref", "refs/remotes/origin/main", "HEAD")
	_git(tmp_path, "mv", "old.py", "a.py")
	_git(tmp_path, "commit", "-qm", "mv")
	(tmp_path / gate.STR_BASELINE_NAME).write_text("1 old.py\n", encoding="utf-8")
	_run(tmp_path, capsys, "--write-baseline")
	assert (tmp_path / gate.STR_BASELINE_NAME).read_text(
		encoding="utf-8"
	) == f"{gate.STR_SCOPE_ROW}{gate.INT_SCOPE}\n1 a.py\n"


_DICT_ALLOWED = {
	"noqa": "X = 1  # noqa: E501\n",
	"type_ignore": "X = 1  # type: ignore[assignment]\n",
	"pragma": "X = 1  # pragma: no cover\n",
	"pyright": "# pyright: basic\nX = 1\n",
	"mypy": "# mypy: ignore-errors\nX = 1\n",
	"ok_marker": "# complexity-ok: parser branches\nX = 1\n",
	"one_assert_ok": "# one-assert-ok: table-driven\nX = 1\n",
	"pairing": "# pairing:internal\nX = 1\n",
	"pipeline_mode": "# pipeline-mode: single\nX = 1\n",
	"shellcheck_disable": "# shellcheck disable=SC2086\nX=1\n",
	"shellcheck_source": "# shellcheck source=lib/common.sh\nX=1\n",
	"shellcheck_shell": "# shellcheck shell=bash\nX=1\n",
	"codespell": "# codespell:ignore teh\nX=1\n",
	"markdownlint": "# markdownlint-disable MD013\nX=1\n",
	"eslint": "// eslint-disable-next-line no-console\nconst x = 1;\n",
	"stylelint": "// stylelint-disable\nconst x = 1;\n",
	"prettier": "// prettier-ignore\nconst x = 1;\n",
	"ts_expect": "// @ts-expect-error legacy\nconst x = 1;\n",
	"ts_ignore": "// @ts-ignore\nconst x = 1;\n",
	"ts_check": "// @ts-check\nconst x = 1;\n",
	"ts_type": "/** @type {import('jest').Config} */\nconst x = 1;\n",
	"hadolint": "# hadolint ignore=DL3008\nX=1\n",
	"shebang": "#!/usr/bin/env bash\nX=1\n",
	"syntax": "# syntax=docker/dockerfile:1\nX=1\n",
	"coding": "# -*- coding: utf-8 -*-\nX = 1\n",
	"sha_pin_version": "uses: actions/checkout@" + "a" * 40 + " # v7.0.1\n",
	"provenance": "# Written by BlueprintX at scaffold time - do not edit by hand.\nX: 1\n",
}
_DICT_SUFFIX = {
	"eslint": ".ts",
	"stylelint": ".ts",
	"prettier": ".ts",
	"ts_expect": ".ts",
	"ts_ignore": ".ts",
	"ts_check": ".js",
	"ts_type": ".js",
	"sha_pin_version": ".yaml",
	"provenance": ".yaml",
	"shellcheck_disable": ".sh",
	"shellcheck_source": ".sh",
	"shellcheck_shell": ".sh",
	"hadolint": ".sh",
	"shebang": ".sh",
	"syntax": ".sh",
	"markdownlint": ".sh",
	"codespell": ".sh",
	"pairing": ".mk",
}


@pytest.mark.parametrize("str_form", sorted(_DICT_ALLOWED))
def test_each_allowlisted_form_is_not_counted(
	str_form: str, tmp_path: Path, capsys: pytest.CaptureFixture
) -> None:
	"""Every agreed keep-list form passes in a new file against an empty baseline.

	Parameters
	----------
	str_form : str
		Key into ``_DICT_ALLOWED``.
	tmp_path : pathlib.Path
		A throwaway directory pytest provides per test.
	capsys : pytest.CaptureFixture
		Captures the gate's report.
	"""
	str_name = "probe" + _DICT_SUFFIX.get(str_form, ".py")
	_tree(tmp_path, "")
	(tmp_path / str_name).write_text(_DICT_ALLOWED[str_form], encoding="utf-8")
	assert _run(tmp_path, capsys)[0] == 0


@pytest.mark.parametrize(
	"str_source",
	[
		"// see @type {import('x').Y}: this is slow\nconst x = 1;\n",
		"// @type {Foo} is a prose note\nconst x = 1;\n",
	],
)
def test_a_type_mention_in_prose_is_still_counted(
	str_source: str, tmp_path: Path, capsys: pytest.CaptureFixture
) -> None:
	"""Only a comment that starts with the JSDoc import form is exempt, not any mention.

	Parameters
	----------
	str_source : str
		A comment that mentions ``@type {`` without being the annotation.
	tmp_path : pathlib.Path
		A throwaway directory pytest provides per test.
	capsys : pytest.CaptureFixture
		Captures the gate's report.
	"""
	_tree(tmp_path, "")
	(tmp_path / "probe.js").write_text(str_source, encoding="utf-8")
	assert _run(tmp_path, capsys)[0] != 0


@pytest.mark.skipif(
	not (_PATH_REPO / gate.STR_BASELINE_NAME).is_file(), reason="not the BlueprintX root"
)
def test_the_current_tree_passes_against_the_committed_baseline(
	capsys: pytest.CaptureFixture,
) -> None:
	"""The committed baseline matches the tree it was generated from.

	Parameters
	----------
	capsys : pytest.CaptureFixture
		Captures the gate's report.
	"""
	assert _run(_PATH_REPO, capsys)[0] == 0


def test_sha_pin_exemption_survives_a_vertical_tab_earlier_in_the_file() -> None:
	"""A vertical tab breaks ``str.splitlines``; the counter must index by newline only."""
	str_source = "a\x0bb\nuses: actions/checkout@" + "a" * 40 + " # v7.0.1\n"
	assert gate.counted_comments(str_source, "#") == []


LIST_NEWLY_SCANNED = [
	(".env.example", "# note\nKEY=1\n"),
	(".gitignore", "# note\n*.pyc\n"),
	(".dockerignore", "# note\n.git\n"),
	(".gitattributes", "# note\n* text=auto\n"),
	(".codespellrc", "# note\n[codespell]\n"),
	(".editorconfig", "# note\nroot = true\n"),
	(".gitlint", "# note\n[general]\n"),
	(".yamllint", "# note\nrules: {}\n"),
	(".coveragerc", "# note\n[run]\n"),
	("Dockerfile", "# note\nFROM scratch\n"),
	("Dockerfile.dev", "# note\nFROM scratch\n"),
	("nginx.conf", "# note\nuser nginx;\n"),
	("setup.cfg", "# note\n[x]\n"),
	("otel.env.fragment", "# note\nA=1\n"),
	("t.bats", "# note\n@test x {\n}\n"),
	("required-checks.txt", "# note\nlint\n"),
	("requirements.txt", "# note\nrequests\n"),
	(".sqlfluff", "# note\n[sqlfluff]\n"),
	("q.sql", "-- note\nSELECT 1;\n"),
	("s.css", "/* note */\na {}\n"),
]


@pytest.mark.parametrize(("str_name", "str_text"), LIST_NEWLY_SCANNED)
def test_a_comment_in_every_newly_scanned_file_type_fails(
	tmp_path: Path, capsys: pytest.CaptureFixture, str_name: str, str_text: str
) -> None:
	"""Should-fail witness: no file type is left behind (blueprintx#304).

	Parameters
	----------
	tmp_path : pathlib.Path
		A throwaway directory pytest provides per test.
	capsys : pytest.CaptureFixture
		Captures the gate's report.
	str_name : str
		File name that must now be discovered.
	str_text : str
		Content carrying exactly one prose comment.
	"""
	(tmp_path / str_name).write_text(str_text, encoding="utf-8")
	(tmp_path / gate.STR_BASELINE_NAME).write_text("", encoding="utf-8")
	int_code, str_out = _run(tmp_path, capsys)
	assert (int_code, f"{str_name}: 1 comment line(s), baseline 0" in str_out) == (1, True)


def test_the_local_dot_env_working_copy_is_not_scanned(
	tmp_path: Path, capsys: pytest.CaptureFixture
) -> None:
	"""``.env`` is the git-ignored working copy, never ours to budget.

	Parameters
	----------
	tmp_path : pathlib.Path
		A throwaway directory pytest provides per test.
	capsys : pytest.CaptureFixture
		Captures the gate's report.
	"""
	(tmp_path / ".env").write_text("# my own note\nKEY=1\n", encoding="utf-8")
	_tree(tmp_path, "X = 1\n")
	assert _run(tmp_path, capsys)[0] == 0


def test_a_sql_dash_dash_inside_a_string_is_not_a_comment(
	tmp_path: Path, capsys: pytest.CaptureFixture
) -> None:
	"""Should-pass witness: strings are skipped, as for ``#`` and ``//``.

	Parameters
	----------
	tmp_path : pathlib.Path
		A throwaway directory pytest provides per test.
	capsys : pytest.CaptureFixture
		Captures the gate's report.
	"""
	(tmp_path / "q.sql").write_text("SELECT '-- not a comment';\n", encoding="utf-8")
	(tmp_path / gate.STR_BASELINE_NAME).write_text("", encoding="utf-8")
	assert _run(tmp_path, capsys)[0] == 0


def _compare(tmp_path: Path, capsys: pytest.CaptureFixture, str_ref: str, str_head: str) -> int:
	"""Run the base-branch comparison for a tree holding ``a.py`` and ``q.sql``.

	Parameters
	----------
	tmp_path : pathlib.Path
		Tree root.
	capsys : pytest.CaptureFixture
		Captures the gate's report.
	str_ref : str
		Reference (base branch) baseline text.
	str_head : str
		Committed baseline text.

	Returns
	-------
	int
		The gate's exit code.
	"""
	_tree(tmp_path, "# one\nX = 1\n", str_head)
	(tmp_path / "q.sql").write_text("-- one\nSELECT 1;\n", encoding="utf-8")
	path_ref = tmp_path / "ref.txt"
	path_ref.write_text(str_ref, encoding="utf-8")
	return _run(tmp_path, capsys, "--compare-baseline", str(path_ref))[0]


def test_a_widened_scope_admits_rows_for_file_types_the_base_never_scanned(
	tmp_path: Path, capsys: pytest.CaptureFixture
) -> None:
	"""A base written under scope 1 cannot hold rows for ``.sql``; they are not a raise.

	Parameters
	----------
	tmp_path : pathlib.Path
		A throwaway directory pytest provides per test.
	capsys : pytest.CaptureFixture
		Captures the gate's report.
	"""
	str_head = f"{gate.STR_SCOPE_ROW}{gate.INT_SCOPE}\n1 a.py\n1 q.sql\n"
	assert _compare(tmp_path, capsys, "1 a.py\n", str_head) == 0


def test_a_widened_scope_still_blocks_raising_an_existing_row(
	tmp_path: Path, capsys: pytest.CaptureFixture
) -> None:
	"""Should-fail witness: the exemption covers new paths only, never a listed row.

	Parameters
	----------
	tmp_path : pathlib.Path
		A throwaway directory pytest provides per test.
	capsys : pytest.CaptureFixture
		Captures the gate's report.
	"""
	str_head = f"{gate.STR_SCOPE_ROW}{gate.INT_SCOPE}\n1 a.py\n1 q.sql\n"
	assert _compare(tmp_path, capsys, "0 a.py\n", str_head) == 1


def test_a_current_scope_base_blocks_a_new_row(
	tmp_path: Path, capsys: pytest.CaptureFixture
) -> None:
	"""Should-fail witness: once the base is on the current scope, a new row is a raise.

	Parameters
	----------
	tmp_path : pathlib.Path
		A throwaway directory pytest provides per test.
	capsys : pytest.CaptureFixture
		Captures the gate's report.
	"""
	str_scope = f"{gate.STR_SCOPE_ROW}{gate.INT_SCOPE}\n"
	assert _compare(tmp_path, capsys, f"{str_scope}1 a.py\n", f"{str_scope}1 a.py\n1 q.sql\n") == 1


def test_a_new_python_file_is_held_under_a_widened_scope() -> None:
	"""Should-fail witness: row absence is not the exemption, the file type is."""
	assert gate.raised_rows({"src/new_mod.py": 40}, {"a.py": 1}, {}, True) != []


def test_a_rename_with_more_comments_than_its_source_is_held_under_a_widened_scope() -> None:
	"""Should-fail witness: a renamed Python file inherits its source's row, no more."""
	assert gate.raised_rows({"b.py": 5}, {"a.py": 1}, {"b.py": "a.py"}, True) != []


def test_a_new_file_of_a_newly_scanned_type_is_exempt_under_a_widened_scope() -> None:
	"""A ``.gitignore`` row cannot exist in a base that never read ``.gitignore``."""
	assert gate.raised_rows({".gitignore": 9}, {"a.py": 1}, {}, True) == []


def test_a_zero_comment_python_file_gaining_comments_fails_the_comparison(
	tmp_path: Path, capsys: pytest.CaptureFixture
) -> None:
	"""Should-fail witness: the end-to-end form of the new-file hole.

	Parameters
	----------
	tmp_path : pathlib.Path
		A throwaway directory pytest provides per test.
	capsys : pytest.CaptureFixture
		Captures the gate's report.
	"""
	str_head = f"{gate.STR_SCOPE_ROW}{gate.INT_SCOPE}\n1 a.py\n1 q.sql\n"
	assert _compare(tmp_path, capsys, "1 q.sql\n", str_head) == 1


def test_an_untracked_file_is_not_counted(tmp_path: Path, capsys: pytest.CaptureFixture) -> None:
	"""Should-fail witness: a local file git does not track must not change the baseline.

	Parameters
	----------
	tmp_path : pathlib.Path
		A throwaway directory pytest provides per test.
	capsys : pytest.CaptureFixture
		Captures the gate's report.
	"""
	_tree(tmp_path, "# one\nX = 1\n", f"{gate.STR_SCOPE_ROW}{gate.INT_SCOPE}\n1 a.py\n")
	(tmp_path / "local.sh").write_text("# mine\necho hi\n", encoding="utf-8")
	subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)  # noqa: S603, S607
	subprocess.run(["git", "-C", str(tmp_path), "add", "a.py"], check=True)  # noqa: S603, S607
	assert _run(tmp_path, capsys, "--require-baseline")[0] == 0


def test_a_sql_string_spanning_lines_hides_its_dashes(
	tmp_path: Path, capsys: pytest.CaptureFixture
) -> None:
	"""Should-pass witness: ``--`` on a continuation line of a string is data.

	Parameters
	----------
	tmp_path : pathlib.Path
		A throwaway directory pytest provides per test.
	capsys : pytest.CaptureFixture
		Captures the gate's report.
	"""
	(tmp_path / "q.sql").write_text("SELECT 'one\n-- two\nthree';\n", encoding="utf-8")
	_tree(tmp_path, "X = 1\n")
	assert _run(tmp_path, capsys)[0] == 0


def test_a_css_banner_is_flagged(tmp_path: Path, capsys: pytest.CaptureFixture) -> None:
	"""Should-fail witness: ``/* */`` rule / title / rule is a decorative banner.

	Parameters
	----------
	tmp_path : pathlib.Path
		A throwaway directory pytest provides per test.
	capsys : pytest.CaptureFixture
		Captures the gate's report.
	"""
	(tmp_path / "s.css").write_text("/* ------ */\n/* Title */\n/* ------ */\na {}\n", "utf-8")
	_tree(tmp_path, "X = 1\n", "3 s.css\n")
	assert "decorative banner" in _run(tmp_path, capsys)[1]


def test_a_long_css_comment_run_is_flagged(tmp_path: Path, capsys: pytest.CaptureFixture) -> None:
	"""Should-fail witness: a run over the ceiling is caught in CSS too.

	Parameters
	----------
	tmp_path : pathlib.Path
		A throwaway directory pytest provides per test.
	capsys : pytest.CaptureFixture
		Captures the gate's report.
	"""
	int_lines = gate.INT_MAX_RUN + 1
	(tmp_path / "s.css").write_text("/* x */\n" * int_lines + "a {}\n", "utf-8")
	_tree(tmp_path, "X = 1\n", f"{int_lines} s.css\n")
	assert "comment block is" in _run(tmp_path, capsys)[1]


def _count(tmp_path: Path, str_name: str, str_text: str) -> int:
	"""Return the counted comment lines of one scratch file.

	Parameters
	----------
	tmp_path : pathlib.Path
		Scratch directory.
	str_name : str
		File name, which picks the grammar.
	str_text : str
		File content.

	Returns
	-------
	int
		The gate's comment count for the file.
	"""
	path_file = tmp_path / str_name
	path_file.write_text(str_text, encoding="utf-8")
	return gate.comment_line_count(path_file)


@pytest.mark.parametrize(
	"str_open",
	["cat > f << 'EOF'", 'cat > f <<"EOF"', "cat > f <<EOF", "cat > f << EOF"],
)
def test_heredoc_body_is_not_counted_as_comments(tmp_path: Path, str_open: str) -> None:
	"""Should-fail witness: a shebang and a ``# foo`` line inside a heredoc are output.

	Parameters
	----------
	tmp_path : pathlib.Path
		A throwaway directory pytest provides per test.
	str_open : str
		The heredoc opener under test.
	"""
	str_text = f"{str_open}\n#!/usr/bin/env bash\n# foo\nEOF\n"
	assert _count(tmp_path, "s.sh", str_text) == 0


def test_a_comment_right_after_the_terminator_is_counted(tmp_path: Path) -> None:
	"""The skip ends at the terminator, so the next real comment counts.

	Parameters
	----------
	tmp_path : pathlib.Path
		A throwaway directory pytest provides per test.
	"""
	assert _count(tmp_path, "s.sh", "cat <<EOF\n# data\nEOF\n# real\n") == 1


def test_a_dash_heredoc_accepts_a_tab_indented_terminator(tmp_path: Path) -> None:
	"""``<<-`` strips leading tabs from the terminator line.

	Parameters
	----------
	tmp_path : pathlib.Path
		A throwaway directory pytest provides per test.
	"""
	assert _count(tmp_path, "s.sh", "cat <<-EOF\n\t# data\n\tEOF\n# real\n") == 1


def test_a_plain_shell_heredoc_with_only_an_indented_terminator_is_unterminated(
	tmp_path: Path,
) -> None:
	"""Without ``-`` an indented ``EOF`` does not end it, so nothing is skipped.

	Parameters
	----------
	tmp_path : pathlib.Path
		A throwaway directory pytest provides per test.
	"""
	assert _count(tmp_path, "s.sh", "cat <<EOF\n  EOF\n# still data\n") == 1


def test_a_ruby_squiggly_heredoc_is_skipped(tmp_path: Path) -> None:
	"""Should-fail witness: the Formula's ``<<~EOS`` shebang is data.

	Parameters
	----------
	tmp_path : pathlib.Path
		A throwaway directory pytest provides per test.
	"""
	str_text = 'x.write <<~EOS\n  #!/usr/bin/env bash\n  exec "$@"\nEOS\n# real\n'
	assert _count(tmp_path, "f.rb", str_text) == 1


def test_a_yaml_run_block_heredoc_is_skipped(tmp_path: Path) -> None:
	"""Should-fail witness: the apt workflow's indented heredoc shebang is data.

	Parameters
	----------
	tmp_path : pathlib.Path
		A throwaway directory pytest provides per test.
	"""
	str_text = "run: |\n  cat > b << 'EOF'\n  #!/usr/bin/env bash\n  EOF\n  # real\n"
	assert _count(tmp_path, "w.yml", str_text) == 1


def test_a_here_string_and_a_comment_mentioning_a_heredoc_open_nothing(tmp_path: Path) -> None:
	"""``<<<`` and a ``# cat <<EOF`` comment must not swallow the lines below.

	Parameters
	----------
	tmp_path : pathlib.Path
		A throwaway directory pytest provides per test.
	"""
	assert _count(tmp_path, "s.sh", "x <<< y\n# cat <<EOF\n# real\n") == 2


def test_a_docstring_mentioning_a_heredoc_hides_nothing_in_python(tmp_path: Path) -> None:
	"""Should-fail witness: a ``<<'EOF'`` in a docstring must not skip the real comment after it.

	Parameters
	----------
	tmp_path : pathlib.Path
		A throwaway directory pytest provides per test.
	"""
	str_text = '"""Run `python - <<\'EOF\'`."""\n# real\nX = 1\n'
	assert _count(tmp_path, "m.py", str_text) == 1


def test_a_python_shift_is_not_a_heredoc(tmp_path: Path) -> None:
	"""``x << n`` in Python opens nothing.

	Parameters
	----------
	tmp_path : pathlib.Path
		A throwaway directory pytest provides per test.
	"""
	assert _count(tmp_path, "m.py", "X = 1 << SHIFT\n# real\n") == 1


def test_a_toml_string_with_a_heredoc_marker_hides_nothing(tmp_path: Path) -> None:
	"""Should-fail witness: no heredoc scan runs on TOML.

	Parameters
	----------
	tmp_path : pathlib.Path
		A throwaway directory pytest provides per test.
	"""
	assert _count(tmp_path, "c.toml", 'k = "a <<EOF"\n# real\nEOF\n# real2\n') == 2


@pytest.mark.parametrize(
	("str_line", "int_want"),
	[
		('echo "a <<EOF"', 2),
		("echo 'a <<EOF'", 2),
		("foo # see <<EOF", 3),
		("foo;# see <<EOF", 2),
		("foo ;# see <<EOF", 2),
		("x=$(( y << n ))", 2),
		("grep x <<< y", 2),
	],
)
def test_a_false_shell_opener_hides_nothing(tmp_path: Path, str_line: str, int_want: int) -> None:
	"""Should-fail witness: a quoted, commented, arithmetic or here-string ``<<`` is no heredoc.

	Parameters
	----------
	tmp_path : pathlib.Path
		A throwaway directory pytest provides per test.
	str_line : str
		The line carrying the false opener.
	int_want : int
		The exact count: the two real comments below it, plus a trailing comment if the
		line has one the scanner sees.
	"""
	str_text = f"{str_line}\n# real\nEOF\n# real2\n"
	assert _count(tmp_path, "s.sh", str_text) == int_want


def test_a_plain_terminator_must_match_exactly(tmp_path: Path) -> None:
	"""Should-fail witness: ``EOF `` with a trailing space does not end a plain heredoc.

	Parameters
	----------
	tmp_path : pathlib.Path
		A throwaway directory pytest provides per test.
	"""
	assert _count(tmp_path, "s.sh", "cat <<EOF\n# a\nEOF \n# b\nEOF\n# real\n") == 1


def test_a_dash_terminator_strips_only_tabs(tmp_path: Path) -> None:
	"""Should-fail witness: spaces before ``EOF`` do not end a ``<<-`` heredoc.

	Parameters
	----------
	tmp_path : pathlib.Path
		A throwaway directory pytest provides per test.
	"""
	assert _count(tmp_path, "s.sh", "cat <<-EOF\n  EOF\n# x\n") == 1


def test_several_openers_on_one_line_take_their_bodies_in_order(tmp_path: Path) -> None:
	"""Should-fail witness: ``cat <<A <<B`` skips both bodies, not just the first.

	Parameters
	----------
	tmp_path : pathlib.Path
		A throwaway directory pytest provides per test.
	"""
	assert _count(tmp_path, "s.sh", "cat <<A <<B\n# a\nA\n# b\nB\n# real\n") == 1


def test_an_unterminated_opener_counts_its_lines(tmp_path: Path) -> None:
	"""Should-fail witness: no terminator means no heredoc, so the lines are counted.

	Parameters
	----------
	tmp_path : pathlib.Path
		A throwaway directory pytest provides per test.
	"""
	assert _count(tmp_path, "s.sh", "cat <<EOF\n# one\n# two\n") == 2
