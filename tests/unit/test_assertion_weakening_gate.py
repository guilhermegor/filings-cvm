"""Unit tests for the assertion-weakening gate (no network; uses a local git).

**The negative control is the point** (blueprintx#324). A gate that claims to catch a PR
turning a red test green by weakening its assertion is worthless unless something in this
suite actually FAILS it. Every test below either proves a rule FIRES on the exact shape the
issue names, or pins a measured reason it must NOT fire — the should-fail witnesses from the
issue body, plus the literal-ish narrowing that measurement against real history required
(a rewritten left-hand expression, e.g. ``dict_calls["n"]`` -> ``cls_call.call_count``, on an
unchanged RHS constant must not be read as an edited expected value).
"""

import importlib.util
from pathlib import Path
import subprocess
import sys
from types import ModuleType

import pytest


_PATH_BIN = Path(__file__).resolve().parents[2] / "bin"


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
	cls_spec = importlib.util.spec_from_file_location(str_name, _PATH_BIN / f"{str_name}.py")
	assert cls_spec is not None and cls_spec.loader is not None
	cls_module = importlib.util.module_from_spec(cls_spec)
	sys.modules[str_name] = cls_module
	cls_spec.loader.exec_module(cls_module)
	return cls_module


cls_gate = _load("check_assertion_weakening")


def _findings(str_old: str, str_new: str, *, bool_prod_changed: bool = False) -> list[str]:
	"""Run the file-level comparator over two versions of one test file's source.

	Parameters
	----------
	str_old : str
		Content at the merge-base.
	str_new : str
		Content in this change.
	bool_prod_changed : bool
		Whether a non-test file also changed in this diff.

	Returns
	-------
	list of str
		Findings from ``cls_gate._file_findings``.
	"""
	return cls_gate._file_findings(
		"tests/unit/test_sample.py", str_old, str_new, bool_prod_changed
	)


def _sole_finding(str_old: str, str_new: str, *, bool_prod_changed: bool = False) -> str:
	"""Run the comparator and return its single finding, asserting there is exactly one.

	Every fixture in this file is a two-line diff built to trip exactly one rule, so "one
	finding, not a cascade" is a precondition of the fixture rather than a per-test
	behaviour (blueprintx#544). Hoisting it here keeps each test at one assertion AND makes
	the callers that use it check the count; tests that need several findings use
	``_findings`` directly.

	Parameters
	----------
	str_old : str
		Content at the merge-base.
	str_new : str
		Content in this change.
	bool_prod_changed : bool
		Whether a non-test file also changed in this diff.

	Returns
	-------
	str
		The one finding.
	"""
	list_problems = _findings(str_old, str_new, bool_prod_changed=bool_prod_changed)
	assert len(list_problems) == 1, list_problems
	return list_problems[0]


@pytest.mark.parametrize("str_fragment", ["test_x", "deleted"])
def test_a_deleted_test_function_is_reported(str_fragment: str) -> None:
	"""A test present at the merge-base but absent now is a finding."""
	assert str_fragment in _sole_finding(
		"def test_x() -> None:\n\tassert 1 == 1\n",
		"def test_other() -> None:\n\tassert 1 == 1\n",
	)


def test_an_unrelated_new_test_alongside_the_old_one_is_clean() -> None:
	"""Adding a sibling test while keeping the original one intact is not a finding."""
	str_old = "def test_x() -> None:\n\tassert 1 == 1\n"
	str_new = (
		"def test_x() -> None:\n\tassert 1 == 1\n\n\ndef test_y() -> None:\n\tassert 2 == 2\n"
	)

	assert _findings(str_old, str_new) == []


@pytest.mark.parametrize("str_fragment", ["test_x", "lost 1 assertion"])
def test_an_assertion_removed_is_reported(str_fragment: str) -> None:
	"""A test that had two assertions and now has one is a finding, count-based."""
	assert str_fragment in _sole_finding(
		"def test_x() -> None:\n\tassert 1 == 1\n\tassert 2 == 2\n",
		"def test_x() -> None:\n\tassert 1 == 1\n",
	)


def test_trivialised_to_assert_true_is_reported() -> None:
	"""A real assertion collapsed to a bare truthy constant is a finding."""
	str_old = "def test_x() -> None:\n\tassert compute() == 5\n"
	str_new = "def test_x() -> None:\n\tassert True\n"

	list_problems = _findings(str_old, str_new)

	assert any("trivialised" in str_p for str_p in list_problems)


@pytest.mark.parametrize("str_fragment", ["operator weakened from == to in", "line 2"])
def test_equality_weakened_to_membership_is_reported(str_fragment: str) -> None:
	"""``==`` narrowed to ``in`` is exactly the defect blueprintx#289's review caught."""
	assert str_fragment in _sole_finding(
		'def test_x() -> None:\n\tassert resolve_intent(x) == "send"\n',
		'def test_x() -> None:\n\tassert resolve_intent(x) in {"send", "reconcile"}\n',
	)


def test_an_operator_swap_to_an_inequality_is_not_flagged() -> None:
	"""An operator swap is out of the decidable core, by design (no safety claim made)."""
	str_old = "def test_x() -> None:\n\tassert compute() == 5\n"
	str_new = "def test_x() -> None:\n\tassert compute() > 5\n"

	assert _findings(str_old, str_new) == []


def test_assert_equal_weakened_to_assert_true_is_reported() -> None:
	"""``assertEqual`` downgraded to ``assertTrue`` loses the value it pinned."""
	str_old = "class T:\n\tdef test_x(self) -> None:\n\t\tself.assertEqual(compute(), 5)\n"
	str_new = "class T:\n\tdef test_x(self) -> None:\n\t\tself.assertTrue(compute())\n"

	list_problems = _findings(str_old, str_new)

	assert any("assertEqual() weakened to assertTrue()" in str_p for str_p in list_problems)


def test_raises_broadened_to_bare_exception_is_reported() -> None:
	"""A specific exception type widened to ``Exception`` loses what it pinned."""
	str_old = "def test_x() -> None:\n\twith pytest.raises(ValueError):\n\t\tf()\n"
	str_new = "def test_x() -> None:\n\twith pytest.raises(Exception):\n\t\tf()\n"

	list_problems = _findings(str_old, str_new)

	str_want = "pytest.raises broadened from ValueError to Exception"
	assert any(str_want in str_p for str_p in list_problems)


def test_raises_replaced_in_place_by_a_plain_assertion_is_reported() -> None:
	"""Dropping the ``raises`` context while keeping the check count is a finding.

	Padded with a second, unchanged assertion on both sides so the two checks stay
	POSITIONALLY paired — otherwise the count-based rule fires first, and this test would
	prove that rule instead of the raises-specific one it targets.
	"""
	str_old = (
		"def test_x() -> None:\n\twith pytest.raises(ValueError):\n\t\tf()\n\tassert 1 == 1\n"
	)
	str_new = "def test_x() -> None:\n\tassert True\n\tassert 1 == 1\n"

	list_problems = _findings(str_old, str_new)

	assert any("pytest.raises removed" in str_p for str_p in list_problems)


def test_raises_kept_at_the_same_specificity_is_clean() -> None:
	"""An unrelated line added around an unchanged ``raises`` block is not a finding."""
	str_old = "def test_x() -> None:\n\twith pytest.raises(ValueError):\n\t\tf()\n"
	str_new = "def test_x() -> None:\n\tprepare()\n\twith pytest.raises(ValueError):\n\t\tf()\n"

	assert _findings(str_old, str_new) == []


def test_a_newly_added_skip_marker_is_reported() -> None:
	"""A test that gained ``@pytest.mark.skip`` without carrying it before is a finding."""
	str_old = "def test_x() -> None:\n\tassert 1 == 1\n"
	str_new = "@pytest.mark.skip(reason='flaky')\ndef test_x() -> None:\n\tassert 1 == 1\n"

	list_problems = _findings(str_old, str_new)

	assert any("newly marked skip" in str_p for str_p in list_problems)


def test_expected_value_changed_alongside_production_code_is_reported() -> None:
	"""The exact blueprintx#323 shape: a literal expectation edited, code changed too."""
	str_old = 'def test_x() -> None:\n\tassert to_decimal_strict("1.999", 2) == Decimal("1.99")\n'
	str_new = 'def test_x() -> None:\n\tassert to_decimal_strict("1.999", 2) == Decimal("2.00")\n'

	assert "expected value changed while production code changed" in _sole_finding(
		str_old, str_new, bool_prod_changed=True
	)


def test_expected_value_changed_without_production_code_changing_is_clean() -> None:
	"""Should-fail witness #3: a test-only correction must PASS, never be caught."""
	str_old = 'def test_x() -> None:\n\tassert to_decimal_strict("1.999", 2) == Decimal("1.99")\n'
	str_new = 'def test_x() -> None:\n\tassert to_decimal_strict("1.999", 2) == Decimal("2.00")\n'

	assert _findings(str_old, str_new, bool_prod_changed=False) == []


def test_a_rewritten_left_hand_expression_is_not_read_as_a_changed_value() -> None:
	"""Measured false positive against real history, narrowed away (blueprintx#324's PR body).

	A rewrite from a counter dict to a Mock's call-count attribute
	(``dict_calls["n"]`` -> ``cls_call.call_count``) leaves the RHS literal ``1`` untouched.
	Neither changed side is literal-ish (a Subscript, an Attribute), so this reads as the
	rewrite it is, not an edited expectation — measured on blueprintx's own
	``test_retry.py`` history.
	"""
	str_old = 'def test_x() -> None:\n\tassert dict_calls["n"] == 1\n'
	str_new = "def test_x() -> None:\n\tassert cls_call.call_count == 1\n"

	assert _findings(str_old, str_new, bool_prod_changed=True) == []


def test_an_unparsable_new_version_is_a_finding_not_a_silent_pass() -> None:
	"""A file the gate cannot parse must FAIL, never read as clean.

	Mirrors #324's sibling gates: "cannot be checked" and "is clean" are opposite facts.
	"""
	assert "could not parse" in _sole_finding(
		"def test_x() -> None:\n\tassert 1 == 1\n", "def test_x(:\n"
	)


def test_a_clean_file_with_no_test_changes_reports_nothing() -> None:
	"""Whitespace/comment-only edits with no assertion-shape change produce zero findings."""
	str_old = "def test_x() -> None:\n\tassert 1 == 1\n"
	str_new = "def test_x() -> None:\n\t# a harmless comment\n\tassert 1 == 1\n"

	assert _findings(str_old, str_new) == []


def test_the_report_passes_a_flagged_diff_with_a_justification_trailer(
	monkeypatch: pytest.MonkeyPatch,
) -> None:
	"""``test-change-ok: <reason>`` in the searched text clears an otherwise-failing report.

	Parameters
	----------
	monkeypatch : pytest.MonkeyPatch
		Replaces the gate's git runner so the trailer search reads a fixed commit message.
	"""
	monkeypatch.setattr(cls_gate, "pr_body_text", lambda: "")
	monkeypatch.setattr(
		cls_gate,
		"_git",
		lambda _args: (
			"fix: correct the truncation bug\n\n"
			"test-change-ok: fixing the ROUND_DOWN bug this test pins\n"
		),
	)

	assert cls_gate.report(["some finding"], "base-sha", 1) == 0


def test_the_report_fails_a_flagged_diff_with_no_justification(
	monkeypatch: pytest.MonkeyPatch,
) -> None:
	"""No ``test-change-ok`` trailer anywhere means the weakening blocks the PR."""
	monkeypatch.setattr(cls_gate, "pr_body_text", lambda: "")
	monkeypatch.setattr(cls_gate, "_git", lambda _args: "fix: unrelated commit body\n")

	assert cls_gate.report(["some finding"], "base-sha", 1) == 1


def test_a_bare_marker_with_no_reason_does_not_justify(monkeypatch: pytest.MonkeyPatch) -> None:
	"""The reason is REQUIRED, matching ``gate-change-ok:``'s convention."""
	monkeypatch.setattr(cls_gate, "pr_body_text", lambda: "")
	monkeypatch.setattr(cls_gate, "_git", lambda _args: "test-change-ok:\n")

	assert cls_gate.report(["some finding"], "base-sha", 1) == 1


def test_two_classes_sharing_a_method_name_are_tracked_separately() -> None:
	"""A bare method name is not identity: two classes routinely define ``test_value``.

	Keying only on ``node.name`` let the later class overwrite the earlier one, so weakening
	the overwritten method produced no finding at all — a silent miss, and the worst kind for
	a gate whose whole job is to notice a check that got weaker.
	"""
	str_old = (
		'class TestOne:\n\tdef test_v(self) -> None:\n\t\tassert a() == "send"\n\n\n'
		'class TestTwo:\n\tdef test_v(self) -> None:\n\t\tassert b() == "x"\n'
	)
	str_new = (
		'class TestOne:\n\tdef test_v(self) -> None:\n\t\tassert a() in {"send", "recon"}\n\n\n'
		'class TestTwo:\n\tdef test_v(self) -> None:\n\t\tassert b() == "x"\n'
	)
	assert "TestOne.test_v" in _sole_finding(str_old, str_new)


def test_a_unittest_call_rewritten_as_a_weaker_bare_assert_is_reported() -> None:
	"""Changing the assertion's KIND must not hide the weakening.

	``self.assertEqual(a, b)`` rewritten as ``assert a in b`` keeps the check count identical,
	so a same-kind comparison never sees it. The call is normalised to the operator it is
	equivalent to before the pair is compared.
	"""
	assert "bare assert with in" in _sole_finding(
		'class T:\n\tdef test_v(self) -> None:\n\t\tself.assertEqual(a(), "send")\n',
		'class T:\n\tdef test_v(self) -> None:\n\t\tassert a() in {"send", "recon"}\n',
	)


def test_a_unittest_call_rewritten_as_an_equivalent_bare_assert_is_clean() -> None:
	"""⚠️ The other direction: the cross-kind rule must not fire on an ordinary refactor.

	Dropping ``unittest`` for a bare ``assert`` with the SAME operator asserts exactly as much.
	Without this case the rule above would also be satisfied by one that flags every rewrite,
	which is how a gate earns its way into everyone's escape hatch.
	"""
	str_old = 'class T:\n\tdef test_v(self) -> None:\n\t\tself.assertEqual(a(), "send")\n'
	str_new = 'class T:\n\tdef test_v(self) -> None:\n\t\tassert a() == "send"\n'
	assert _findings(str_old, str_new) == []


def test_a_unittest_call_rewritten_with_a_swapped_operator_is_not_flagged() -> None:
	"""A swapped operator after the rewrite is outside the decidable core, by design."""
	str_old = "class T:\n\tdef test_v(self) -> None:\n\t\tself.assertEqual(a(), 5)\n"
	str_new = "class T:\n\tdef test_v(self) -> None:\n\t\tassert a() > 5\n"
	assert _findings(str_old, str_new) == []


@pytest.mark.parametrize("str_new_assert", ["assert True", "assert 1", 'assert "x"'])
def test_a_call_trivialised_to_any_truthy_constant_is_reported(str_new_assert: str) -> None:
	"""``assert True`` is not the only assertion that can never fail.

	The cross-kind rule first checked ``value is True`` literally, so ``assert 1`` and
	``assert "x"`` — equally unfailable — slipped through. It now reuses
	``_is_trivial_assert_test()``, the same predicate the same-kind path already used, rather
	than carrying a second, narrower notion of "trivial".

	Parameters
	----------
	str_new_assert : str
		The trivialised assertion replacing the unittest call.
	"""
	assert "truthy constant" in _sole_finding(
		"class T:\n\tdef test_v(self) -> None:\n\t\tself.assertEqual(a(), 5)\n",
		f"class T:\n\tdef test_v(self) -> None:\n\t\t{str_new_assert}\n",
	)


@pytest.mark.parametrize("str_new_assert", ["assert 0", "assert None"])
def test_a_call_replaced_by_a_falsy_constant_is_not_a_weakening(str_new_assert: str) -> None:
	"""⚠️ The other direction: a falsy constant always FAILS, so it is not weaker.

	Without this case the rule above would also be satisfied by one that flags every constant,
	which would fire on a test deliberately pinned red — and a gate that cannot tell those
	apart gets an escape hatch instead of a fix.

	Parameters
	----------
	str_new_assert : str
		The falsy assertion replacing the unittest call.
	"""
	str_old = "class T:\n\tdef test_v(self) -> None:\n\t\tself.assertEqual(a(), 5)\n"
	str_new = f"class T:\n\tdef test_v(self) -> None:\n\t\t{str_new_assert}\n"
	assert _findings(str_old, str_new) == []


def _git_in(path_repo: Path, *args: str) -> str:
	"""Run ``git`` inside a throwaway repo and return its stripped stdout.

	Parameters
	----------
	path_repo : pathlib.Path
		The repository to run in.
	*args : str
		Arguments after ``git``.

	Returns
	-------
	str
		Captured stdout, stripped.
	"""
	cls_proc = subprocess.run(  # noqa: S603
		["git", "-C", str(path_repo), *args],  # noqa: S607
		capture_output=True,
		text=True,
		check=True,
	)
	return cls_proc.stdout.strip()


@pytest.fixture
def path_mid_merge(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
	"""Return a repo whose ``feature`` has a merge of ``main`` in progress.

	``main`` moves on after the fork, so a base resolved from the pre-merge HEAD (the fork
	point) differs from main's tip.

	Parameters
	----------
	tmp_path : pathlib.Path
		Pytest-provided scratch directory.
	monkeypatch : pytest.MonkeyPatch
		Used to run the gate inside the repo.

	Returns
	-------
	pathlib.Path
		The repository, left mid-merge.
	"""
	_git_in(tmp_path, "init", "-q", "--initial-branch=main")
	_git_in(tmp_path, "config", "user.email", "t@example.com")
	_git_in(tmp_path, "config", "user.name", "t")
	_git_in(tmp_path, "config", "commit.gpgsign", "false")
	_git_in(tmp_path, "commit", "-q", "--allow-empty", "-m", "seed")
	_git_in(tmp_path, "checkout", "-q", "-b", "feature")
	(tmp_path / "own").write_text("own", encoding="utf-8")
	_git_in(tmp_path, "add", "own")
	_git_in(tmp_path, "commit", "-q", "-m", "own")
	_git_in(tmp_path, "checkout", "-q", "main")
	(tmp_path / "theirs").write_text("theirs", encoding="utf-8")
	_git_in(tmp_path, "add", "theirs")
	_git_in(tmp_path, "commit", "-q", "-m", "theirs")
	_git_in(tmp_path, "checkout", "-q", "feature")
	_git_in(tmp_path, "merge", "-q", "--no-commit", "--no-ff", "main")
	monkeypatch.chdir(tmp_path)
	monkeypatch.setattr(cls_gate, "PATH_ROOT", tmp_path)
	return tmp_path


def test_resolve_base_mid_merge_is_the_incoming_tip(path_mid_merge: Path) -> None:
	"""Mid-merge the base is main's tip, never the fork point that charges main's delta."""
	assert cls_gate.resolve_base() == _git_in(path_mid_merge, "rev-parse", "main")


_STR_PAD = "".join(
	f"def test_p{int_i}() -> None:\n    assert g({int_i}) == {int_i}\n" for int_i in range(8)
)
_STR_STRONG = _STR_PAD + "def test_v() -> None:\n    assert f() == 1\n"
_STR_WEAK = _STR_PAD + "def test_v() -> None:\n    assert f() in (1, 2)\n"


@pytest.fixture
def path_renamed_repo(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
	"""Return a repo on ``feature`` holding ``tests/test_old.py`` committed on ``main``.

	Parameters
	----------
	tmp_path : pathlib.Path
		Pytest-provided scratch directory.
	monkeypatch : pytest.MonkeyPatch
		Used to run the gate inside the repo.

	Returns
	-------
	pathlib.Path
		The repository, with the base commit on ``main``.
	"""
	_git_in(tmp_path, "init", "-q", "--initial-branch=main")
	_git_in(tmp_path, "config", "user.email", "t@example.com")
	_git_in(tmp_path, "config", "user.name", "t")
	_git_in(tmp_path, "config", "commit.gpgsign", "false")
	_git_in(tmp_path, "config", "diff.renames", "false")
	(tmp_path / "tests").mkdir()
	(tmp_path / "tests" / "test_old.py").write_text(_STR_STRONG, encoding="utf-8")
	_git_in(tmp_path, "add", "-A")
	_git_in(tmp_path, "commit", "-q", "-m", "seed")
	_git_in(tmp_path, "checkout", "-q", "-b", "feature")
	monkeypatch.chdir(tmp_path)
	monkeypatch.setattr(cls_gate, "PATH_ROOT", tmp_path)
	return tmp_path


def _rename_with(path_repo: Path, str_body: str) -> list[str]:
	"""Rename ``test_old.py`` to ``test_new.py`` with ``str_body``, stage, and run the gate.

	Parameters
	----------
	path_repo : pathlib.Path
		The repository from ``path_renamed_repo``.
	str_body : str
		Content of the renamed file.

	Returns
	-------
	list of str
		The gate's findings.
	"""
	_git_in(path_repo, "mv", "tests/test_old.py", "tests/test_new.py")
	(path_repo / "tests" / "test_new.py").write_text(str_body, encoding="utf-8")
	_git_in(path_repo, "add", "-A")
	str_base = _git_in(path_repo, "rev-parse", "main")
	return cls_gate.collect_problems(cls_gate.changed_paths(str_base), str_base)


def test_a_renamed_and_weakened_test_file_is_reported(path_renamed_repo: Path) -> None:
	"""Renaming a test and weakening its assertion in one commit must fail the gate."""
	assert any("test_new.py" in str_f for str_f in _rename_with(path_renamed_repo, _STR_WEAK))


def test_a_merely_renamed_test_file_is_clean(path_renamed_repo: Path) -> None:
	"""A pure rename keeps every assertion, so the gate stays green."""
	assert _rename_with(path_renamed_repo, _STR_STRONG) == []


def test_a_source_file_renamed_into_tests_touches_production_code() -> None:
	"""A rename's SOURCE is removed, so moving ``src/`` into ``tests/`` changes production."""
	assert cls_gate._touches_production_code([("R", "src/app.py", "tests/test_app.py")])


def test_a_test_file_moved_out_of_tests_is_reported(path_renamed_repo: Path) -> None:
	"""Moving ``tests/test_old.py`` to ``src/`` removes its tests, so the gate names it."""
	(path_renamed_repo / "src").mkdir()
	_git_in(path_renamed_repo, "mv", "tests/test_old.py", "src/old.py")
	str_base = _git_in(path_renamed_repo, "rev-parse", "main")
	list_found = cls_gate.collect_problems(cls_gate.changed_paths(str_base), str_base)
	assert any("tests/test_old.py" in str_f for str_f in list_found)


def test_a_source_file_renamed_into_tests_is_not_read_as_an_old_test(
	path_renamed_repo: Path,
) -> None:
	"""A ``src/`` file moved into ``tests/`` has no test baseline, so it is not compared."""
	(path_renamed_repo / "src").mkdir()
	(path_renamed_repo / "src" / "app.py").write_text(_STR_STRONG, encoding="utf-8")
	_git_in(path_renamed_repo, "add", "-A")
	_git_in(path_renamed_repo, "commit", "-q", "-m", "src")
	str_base = _git_in(path_renamed_repo, "rev-parse", "HEAD")
	_git_in(path_renamed_repo, "mv", "src/app.py", "tests/test_app.py")
	(path_renamed_repo / "tests" / "test_app.py").write_text(_STR_WEAK, encoding="utf-8")
	_git_in(path_renamed_repo, "add", "-A")
	assert cls_gate.collect_problems(cls_gate.changed_paths(str_base), str_base) == []


@pytest.mark.parametrize(
	("str_status", "str_src", "str_dst", "bool_expected"),
	[
		("D", "tests/test_a.py", "tests/test_a.py", True),
		("D", "src/a.py", "src/a.py", False),
		("R", "tests/test_a.py", "src/a.py", True),
		("R", "tests/test_a.py", "tests/test_b.py", False),
		("R", "src/a.py", "tests/test_a.py", False),
		("R", "tests/test_a.py", "src/test_a.py", True),
	],
)
def test_test_file_removed_classifies_each_row_shape(
	str_status: str, str_src: str, str_dst: str, bool_expected: bool
) -> None:
	"""Only a deleted test, or one moved to a non-test path, has left the suite."""
	assert cls_gate._test_file_removed(str_status, str_src, str_dst) is bool_expected


def test_moving_a_test_into_src_arms_the_expected_value_rule() -> None:
	"""Intended: a test moved into ``src/`` is a production-path change for the whole diff."""
	assert cls_gate._touches_production_code([("R", "tests/test_a.py", "src/a.py")])
