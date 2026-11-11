"""Unit tests for the one-assert gate (offline; no git, no network — blueprintx#431/#544).

**The negative control is the point.** A gate claiming to cap assertion sites is worthless
unless something in this suite actually fails it. Every test below either proves a rule FIRES
on the shape it targets, or pins a measured reason it must NOT fire — including the one that
carries the whole design: the cap applies under ``tests/unit/`` and NOT under
``tests/integration/``, decided by path rather than by filename.

Each test carries exactly one assertion site, which is the rule this gate enforces. Where a
single arrange backs several claims, the claims are ``parametrize`` cases rather than extra
asserts — the pattern ``tests/CLAUDE.md`` prescribes for exactly this split.
"""

import ast
import importlib.util
from pathlib import Path
import sys
from types import ModuleType

import pytest


_BIN = Path(__file__).resolve().parents[2] / "bin"

_SRC_ZERO_ASSERT = "def test_x() -> None:\n\tpass\n"
_SRC_ONE_ASSERT = "def test_x() -> None:\n\tassert 1 == 1\n"
_SRC_TWO_ASSERTS = "def test_x() -> None:\n\tassert 1 == 1\n\tassert 2 == 2\n"


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
	assert cls_spec is not None and cls_spec.loader is not None
	cls_module = importlib.util.module_from_spec(cls_spec)
	sys.modules[str_name] = cls_module
	cls_spec.loader.exec_module(cls_module)
	return cls_module


gate = _load("check_one_assert")


def _write_test_file(path_root: Path, str_content: str, str_suite: str = "tests/unit") -> None:
	"""Write one fixture test file under ``<path_root>/<str_suite>/test_sample.py``.

	Parameters
	----------
	path_root : pathlib.Path
		The fixture tree root.
	str_content : str
		The fixture file's full source text.
	str_suite : str
		Root-relative suite directory to write into — ``tests/unit`` by default, since that
		is the suite the cap applies to.
	"""
	path_suite = path_root / str_suite
	path_suite.mkdir(parents=True, exist_ok=True)
	(path_suite / "test_sample.py").write_text(str_content, encoding="utf-8")


def _run(path_root: Path, list_extra_args: list[str]) -> int:
	"""Run the gate's ``main()`` against a fixture root.

	Parameters
	----------
	path_root : pathlib.Path
		The fixture tree root.
	list_extra_args : list of str
		Extra argv tokens after ``--root <path_root>``.

	Returns
	-------
	int
		The gate's exit code.
	"""
	return gate.main(["--root", str(path_root), *list_extra_args])


def _count_sites(str_src: str) -> int:
	"""Count the assertion sites of ``test_x`` in a source string.

	Parameters
	----------
	str_src : str
		Source text defining ``test_x``.

	Returns
	-------
	int
		The number of assertion sites the gate discovers in ``test_x``.
	"""
	return len(gate._assertion_sites(gate._index_test_functions(ast.parse(str_src))["test_x"]))


def test_a_zero_assertion_unit_test_is_flagged(tmp_path: Path) -> None:
	"""A ``test_*`` function with no assert, call, or raises/warns block is a finding."""
	_write_test_file(tmp_path, _SRC_ZERO_ASSERT)

	assert _run(tmp_path, []) == 1


def test_a_zero_assertion_integration_test_is_flagged_too(tmp_path: Path) -> None:
	"""The zero rule is unconditional — the loose integration cap does not excuse it."""
	_write_test_file(tmp_path, _SRC_ZERO_ASSERT, str_suite="tests/integration")

	assert _run(tmp_path, []) == 1


@pytest.mark.parametrize("str_fragment", ["test_x", "asserts nothing"])
def test_a_zero_assertion_finding_names_the_function_and_the_reason(
	tmp_path: Path, capsys: pytest.CaptureFixture[str], str_fragment: str
) -> None:
	"""The message must identify the offending function, not merely report a count."""
	_write_test_file(tmp_path, _SRC_ZERO_ASSERT)
	_run(tmp_path, [])

	assert str_fragment in capsys.readouterr().err


def test_a_single_bare_assert_is_clean(tmp_path: Path) -> None:
	"""One ``assert`` statement is the ordinary, unflagged case."""
	_write_test_file(tmp_path, _SRC_ONE_ASSERT)

	assert _run(tmp_path, []) == 0


@pytest.mark.parametrize(
	"str_body",
	[
		"\twith pytest.raises(ValueError):\n\t\tf()\n",
		"\twith pytest.warns(UserWarning):\n\t\tf()\n",
		"\tmock_obj.assert_called_once()\n",
		"\tpd.testing.assert_frame_equal(df_a, df_b)\n",
	],
	ids=["raises", "warns", "mock-assert-call", "pandas-assert-call"],
)
def test_a_non_assert_statement_check_counts_as_one_assertion_site(
	tmp_path: Path, str_body: str
) -> None:
	"""A context-manager or ``assert_*()`` check is the assertion — not its absence."""
	_write_test_file(tmp_path, f"def test_x() -> None:\n{str_body}")

	assert _run(tmp_path, []) == 0


def test_an_async_raises_block_alone_counts_as_one_site_not_zero() -> None:
	"""``async with pytest.raises`` is one site; exit 0 alone cannot tell it from "never seen"."""
	str_src = "async def test_x() -> None:\n\tasync with pytest.raises(E):\n\t\tawait f()\n"

	assert _count_sites(str_src) == 1


def test_a_nested_async_helper_assert_is_not_charged_to_the_outer_test() -> None:
	"""A nested ``async def`` is its own unit; its assert must not inflate the outer count."""
	str_src = (
		"def test_x() -> None:\n\tassert 1 == 1\n"
		"\tasync def helper() -> None:\n\t\tassert 2 == 2\n"
	)

	assert _count_sites(str_src) == 1


def test_a_plain_assert_plus_an_async_raises_block_is_two_sites_and_flagged(
	tmp_path: Path,
) -> None:
	"""The async block must be counted, or this under-counts at one and passes silently (#643)."""
	_write_test_file(
		tmp_path,
		"async def test_x() -> None:\n\tassert 1 == 1\n"
		"\tasync with pytest.raises(ValueError):\n\t\tawait f()\n",
	)

	assert _run(tmp_path, []) == 1


def test_two_assertion_sites_in_a_unit_test_are_flagged_by_default(tmp_path: Path) -> None:
	"""The cap of one is the DEFAULT for the unit suite — no flag needed to arm it."""
	_write_test_file(tmp_path, _SRC_TWO_ASSERTS)

	assert _run(tmp_path, []) == 1


def test_two_assertion_sites_in_an_integration_test_are_clean(tmp_path: Path) -> None:
	"""One call with several observable consequences is one integration behaviour.

	This is the whole reason the rule is scoped by path. Splitting these re-runs the
	expensive arrange to prove no new fact — measured 76% of the integration suite.
	"""
	_write_test_file(tmp_path, _SRC_TWO_ASSERTS, str_suite="tests/integration")

	assert _run(tmp_path, []) == 0


def test_the_suite_is_decided_by_path_not_by_filename(tmp_path: Path) -> None:
	"""The same ``test_sample.py`` name is capped or not purely by where it sits."""
	_write_test_file(tmp_path, _SRC_TWO_ASSERTS, str_suite="tests/integration/deep/nested")

	assert _run(tmp_path, []) == 0


def test_a_custom_unit_dir_moves_the_cap(tmp_path: Path) -> None:
	"""``--unit-dir`` re-points the cap for a project that renames its suite."""
	_write_test_file(tmp_path, _SRC_TWO_ASSERTS, str_suite="tests/fast")

	assert _run(tmp_path, ["--unit-dir", "tests/fast"]) == 1


@pytest.mark.parametrize("str_fragment", ["test_x", "2 assertion sites", "parametrize"])
def test_a_cap_finding_names_the_test_the_count_and_the_remedy(
	tmp_path: Path, capsys: pytest.CaptureFixture[str], str_fragment: str
) -> None:
	"""A finding that does not say how to fix it is a finding people route around."""
	_write_test_file(tmp_path, _SRC_TWO_ASSERTS)
	_run(tmp_path, [])

	assert str_fragment in capsys.readouterr().err


def test_max_per_test_zero_disables_the_cap_leaving_the_zero_check(tmp_path: Path) -> None:
	"""Measurement mode: ``--max-per-test 0`` cannot mean "cap at zero"."""
	_write_test_file(tmp_path, _SRC_TWO_ASSERTS)

	assert _run(tmp_path, ["--max-per-test", "0"]) == 0


def test_max_per_test_zero_still_flags_a_zero_assertion_test(tmp_path: Path) -> None:
	"""Disabling the cap must not disable the rule the cap was layered on top of."""
	_write_test_file(tmp_path, _SRC_ZERO_ASSERT)

	assert _run(tmp_path, ["--max-per-test", "0"]) == 1


def test_a_raised_cap_admits_a_two_assert_unit_test(tmp_path: Path) -> None:
	"""``--max-per-test`` overrides the default rather than only tightening it."""
	_write_test_file(tmp_path, _SRC_TWO_ASSERTS)

	assert _run(tmp_path, ["--max-per-test", "2"]) == 0


@pytest.mark.parametrize("str_value", ["not-a-number", "-1", "1.5"])
def test_a_non_integer_max_per_test_value_is_rejected(
	tmp_path: Path, capsys: pytest.CaptureFixture[str], str_value: str
) -> None:
	"""Bad usage is refused, not silently coerced; the message names the rejected flag."""
	int_code = _run(tmp_path, ["--max-per-test", str_value])

	assert (
		int_code,
		"--max-per-test needs a non-negative integer" in capsys.readouterr().out,
	) == (
		1,
		True,
	)


def test_an_unrecognised_flag_is_rejected(
	tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
	"""A typo'd flag must not be swallowed into a silently narrower run."""
	int_code = _run(tmp_path, ["--max-per-tests", "1"])

	assert (int_code, "unrecognised argument: --max-per-tests" in capsys.readouterr().out) == (
		1,
		True,
	)


def test_a_flag_with_no_value_is_rejected(
	tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
	"""Every flag takes a value; a dangling one is bad usage, not a default."""
	int_code = _run(tmp_path, ["--unit-dir"])

	assert (int_code, "--unit-dir needs a value" in capsys.readouterr().out) == (1, True)


def test_a_justified_multi_assert_test_is_exempted_by_the_hatch(tmp_path: Path) -> None:
	"""``# one-assert-ok: <reason>`` clears a cap violation."""
	_write_test_file(
		tmp_path,
		"def test_x() -> None:\n\tassert 1 == 1\n"
		"\tassert 2 == 2  # one-assert-ok: value and dtype\n",
	)

	assert _run(tmp_path, []) == 0


def test_a_bare_hatch_marker_with_no_reason_does_not_exempt(tmp_path: Path) -> None:
	"""The reason is REQUIRED, matching ``# complexity-ok:``'s convention."""
	_write_test_file(
		tmp_path, "def test_x() -> None:\n\tassert 1 == 1\n\tassert 2 == 2  # one-assert-ok:\n"
	)

	assert _run(tmp_path, []) == 1


def test_a_bare_hatch_marker_mid_function_does_not_exempt(tmp_path: Path) -> None:
	"""A bare marker must not borrow the next line of code as its reason.

	``RE_HATCH``'s whitespace after the marker must stay intra-line, not span a newline —
	otherwise a bare marker on any line but the last lets the reason group capture the
	following line of code, silently exempting the test and breaking the documented
	"a bare marker is rejected" rule.
	"""
	_write_test_file(
		tmp_path, "def test_x() -> None:\n\tassert 1 == 1  # one-assert-ok:\n\tassert 2 == 2\n"
	)

	assert _run(tmp_path, []) == 1


def test_a_hatch_marker_inside_a_string_literal_does_not_exempt(tmp_path: Path) -> None:
	"""Only a real comment is an exemption; the same text in a string is just data."""
	_write_test_file(
		tmp_path,
		"def test_x() -> None:\n\tstr_note = '# one-assert-ok: example'\n"
		"\tassert 1 == 1\n\tassert 2 == 2\n",
	)

	assert _run(tmp_path, []) == 1


def test_two_assertion_contexts_in_one_with_are_two_sites(tmp_path: Path) -> None:
	"""``with pytest.raises(A), pytest.warns(B):`` must not pass the one-site cap."""
	_write_test_file(
		tmp_path,
		"import pytest\n\n\ndef test_x() -> None:\n"
		"\twith pytest.raises(ValueError), pytest.warns(UserWarning):\n\t\tpass\n",
	)

	assert _run(tmp_path, []) == 1


def test_the_two_assertion_contexts_are_counted_as_two_sites() -> None:
	"""The exit status alone could be 1 for another reason; the count itself must be two."""
	cls_tree = ast.parse(
		"import pytest\n\n\ndef test_x() -> None:\n"
		"\twith pytest.raises(ValueError), pytest.warns(UserWarning):\n\t\tpass\n"
	)
	cls_fn = next(n for n in ast.walk(cls_tree) if isinstance(n, ast.FunctionDef))

	assert len(gate._assertion_sites(cls_fn)) == 2


def test_the_hatch_also_exempts_a_zero_assertion_test(tmp_path: Path) -> None:
	"""The same hatch covers the zero-assertion check, not only the cap."""
	_write_test_file(tmp_path, "def test_x() -> None:\n\tpass  # one-assert-ok: smoke test\n")

	assert _run(tmp_path, []) == 0


@pytest.mark.parametrize("str_fragment", ["not valid Python", "not checked"])
def test_an_unparsable_file_is_a_finding_not_a_silent_skip(
	tmp_path: Path, capsys: pytest.CaptureFixture[str], str_fragment: str
) -> None:
	"""A file the gate cannot parse must FAIL, never read as clean."""
	_write_test_file(tmp_path, "def test_x(:\n")
	_run(tmp_path, [])

	assert str_fragment in capsys.readouterr().err


def test_an_unparsable_file_exits_non_zero(tmp_path: Path) -> None:
	"""The message above is only useful if the run actually fails."""
	_write_test_file(tmp_path, "def test_x(:\n")

	assert _run(tmp_path, []) == 1


def test_no_tests_directory_is_a_legitimate_skip(tmp_path: Path) -> None:
	"""A tree with no ``tests/`` at all (like this repo's own root) is a real skip."""
	assert _run(tmp_path, []) == 0


def test_the_skip_says_why_it_skipped(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
	"""A silent skip is indistinguishable from a gate that never ran."""
	_run(tmp_path, [])

	assert "no tests/ directory" in capsys.readouterr().out


def test_a_tests_dir_with_zero_matching_files_is_a_failure_not_a_skip(tmp_path: Path) -> None:
	"""An empty ``tests/`` is the broken-discovery shape, not a legitimate skip."""
	(tmp_path / "tests").mkdir()

	assert _run(tmp_path, []) == 1


def test_broken_discovery_names_the_file_count_it_found(
	tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
	"""The failure has to distinguish "found nothing" from "could not look"."""
	(tmp_path / "tests").mkdir()
	_run(tmp_path, [])

	assert "0 test_*.py files" in capsys.readouterr().err


def test_a_tests_dir_holding_only_non_python_tests_is_a_legitimate_skip(tmp_path: Path) -> None:
	"""A tree testing in another language here is a real skip, not broken discovery.

	BlueprintX's own root ships shell tests under ``tests/``. Mirrors
	``check_complexity.sh``'s own note about this exact repo: "BlueprintX's own tree
	has no src/ or tests/ [in the Python sense]".
	"""
	path_tests = tmp_path / "tests"
	path_tests.mkdir()
	(path_tests / "test_something.sh").write_text("#!/bin/bash\necho ok\n", encoding="utf-8")

	assert _run(tmp_path, []) == 0


@pytest.mark.parametrize(
	"str_expected",
	[
		"0 assertion site(s): 1 test(s)",
		"1 assertion site(s): 2 test(s)",
		"2 assertion site(s): 1 test(s)",
	],
)
def test_the_distribution_table_reports_every_count_found(str_expected: str) -> None:
	"""``distribution_table`` groups counts into a histogram, sorted by count."""
	assert str_expected in gate.distribution_table([0, 1, 1, 2])
