"""Unit tests for ``bin/check_type_prefix.py`` — the type-prefix naming gate.

Loaded by path (``bin/`` is not an importable package). Each case writes a tiny module to
``tmp_path`` and asserts the flagged names. Every exemption has a negative control: the same
source with the exemption withdrawn is reported.
"""

import importlib.util
from pathlib import Path

import pytest


_PATH_SCRIPT = Path(__file__).resolve().parents[2] / "bin" / "check_type_prefix.py"
_SPEC = importlib.util.spec_from_file_location("check_type_prefix", _PATH_SCRIPT)
assert _SPEC is not None and _SPEC.loader is not None
ctp = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(ctp)

TUPLE_PREFIXES = ctp.table_prefixes()


def _names(
	path_tmp: Path,
	str_src: str,
	tuple_fixtures: tuple = (),
	str_filename: str = "mod.py",
) -> list:
	"""Write ``str_src`` under ``path_tmp`` and return the flagged names."""
	path_file = path_tmp / str_filename
	path_file.parent.mkdir(parents=True, exist_ok=True)
	path_file.write_text(str_src, encoding="utf-8")
	list_found = ctp.file_findings(path_file, TUPLE_PREFIXES, tuple_fixtures)
	return [tuple_item[1] for tuple_item in list_found]


def test_table_prefixes_reads_the_claude_md_table() -> None:
	"""The vocabulary comes from the table, including the bool aliases."""
	assert {"str", "df", "fn", "is", "has", "can"} <= set(TUPLE_PREFIXES)


def test_table_prefixes_missing_section_raises(tmp_path: Path) -> None:
	"""A file without the section cannot make the gate pass vacuously."""
	path_md = tmp_path / "CLAUDE.md"
	path_md.write_text("# nothing here\n", encoding="utf-8")
	with pytest.raises(ValueError, match="no prefix table"):
		ctp.table_prefixes(path_md)


def test_prefixed_assignment_passes(tmp_path: Path) -> None:
	"""A prefixed module-level name is clean."""
	assert _names(tmp_path, "str_name = 'a'\n") == []


def test_bare_assignment_is_flagged(tmp_path: Path) -> None:
	"""A bare name is reported."""
	assert _names(tmp_path, "name = 'a'\n") == ["name"]


def test_leading_underscores_are_stripped(tmp_path: Path) -> None:
	"""``_PATH_BIN`` passes: underscores and case are ignored."""
	assert _names(tmp_path, "_PATH_BIN = 1\n") == []


def test_prefix_must_be_the_first_token(tmp_path: Path) -> None:
	"""``_BIN`` fails: the stripped name has no prefix."""
	assert _names(tmp_path, "_BIN = 1\n") == ["_BIN"]


def test_prefix_without_underscore_is_flagged(tmp_path: Path) -> None:
	"""``string`` is not ``str_``."""
	assert _names(tmp_path, "string = 'a'\n") == ["string"]


def test_loop_target_is_flagged(tmp_path: Path) -> None:
	"""A ``for`` target is covered."""
	assert _names(tmp_path, "for x in []:\n\tpass\n") == ["x"]


def test_comprehension_target_is_flagged(tmp_path: Path) -> None:
	"""A comprehension target is covered."""
	assert _names(tmp_path, "list_a = [x for x in []]\n") == ["x"]


def test_with_target_is_flagged(tmp_path: Path) -> None:
	"""A ``with ... as`` target is covered."""
	assert _names(tmp_path, "with open('f') as h:\n\tpass\n") == ["h"]


def test_except_target_is_flagged(tmp_path: Path) -> None:
	"""An ``except ... as`` target is covered."""
	assert _names(tmp_path, "try:\n\tpass\nexcept OSError as e:\n\tpass\n") == ["e"]


def test_walrus_target_is_flagged(tmp_path: Path) -> None:
	"""A walrus target is covered."""
	assert _names(tmp_path, "if (n := 1):\n\tpass\n") == ["n"]


def test_class_attribute_is_flagged(tmp_path: Path) -> None:
	"""A class-body assignment is covered."""
	assert _names(tmp_path, "class A:\n\tx = 1\n") == ["x"]


def test_parameter_is_flagged(tmp_path: Path) -> None:
	"""A plain parameter is covered."""
	assert _names(tmp_path, "def f(a):\n\tpass\n") == ["a"]


def test_keyword_only_parameter_is_flagged(tmp_path: Path) -> None:
	"""A keyword-only parameter is covered."""
	assert _names(tmp_path, "def f(*, a):\n\tpass\n") == ["a"]


def test_variadic_parameters_are_flagged(tmp_path: Path) -> None:
	"""``*args`` and ``**kwargs`` are chosen by the code, so they are covered."""
	assert _names(tmp_path, "def f(*args, **kwargs):\n\tpass\n") == ["args", "kwargs"]


def test_lambda_parameter_is_flagged(tmp_path: Path) -> None:
	"""A lambda parameter is covered."""
	assert _names(tmp_path, "fn_a = lambda x: x\n") == ["x"]


def test_self_is_exempt(tmp_path: Path) -> None:
	"""The receiver ``self`` is not chosen by the code."""
	assert _names(tmp_path, "class A:\n\tdef m(self):\n\t\tpass\n") == []


def test_cls_receiver_is_exempt(tmp_path: Path) -> None:
	"""The receiver ``cls`` is not chosen by the code."""
	assert _names(tmp_path, "class A:\n\t@classmethod\n\tdef m(cls):\n\t\tpass\n") == []


def test_underscore_is_exempt(tmp_path: Path) -> None:
	"""``_`` is the discard name."""
	assert _names(tmp_path, "_ = 1\n") == []


def test_dunder_is_exempt(tmp_path: Path) -> None:
	"""Dunder module names are fixed by Python."""
	assert _names(tmp_path, "__all__ = []\n") == []


def test_receiver_exemption_has_a_negative_control(tmp_path: Path) -> None:
	"""A parameter merely named like a receiver, outside the set, is flagged."""
	assert _names(tmp_path, "def f(this):\n\tpass\n") == ["this"]


_STR_FIXTURE_TEST = "def test_a(monkeypatch):\n\tpass\n"


def test_injected_fixture_in_a_test_is_exempt(tmp_path: Path) -> None:
	"""A registry fixture requested by a ``test_*`` function is not chosen by the code."""
	assert _names(tmp_path, _STR_FIXTURE_TEST, ("monkeypatch",), "tests/t.py") == []


def test_injected_fixture_without_registry_is_flagged(tmp_path: Path) -> None:
	"""Negative control: withdraw the registry and the same parameter is reported."""
	assert _names(tmp_path, _STR_FIXTURE_TEST, (), "tests/t.py") == ["monkeypatch"]


def test_fixture_name_outside_tests_is_flagged(tmp_path: Path) -> None:
	"""Negative control: the same test function under ``src`` is not fixture-injected."""
	assert _names(tmp_path, _STR_FIXTURE_TEST, ("monkeypatch",), "src/t.py") == ["monkeypatch"]


def test_fixture_name_in_a_helper_is_flagged(tmp_path: Path) -> None:
	"""Negative control: a non-test helper passes the argument itself, so it chose the name."""
	assert _names(tmp_path, "def helper(tmp_path):\n\tpass\n", ("tmp_path",), "tests/t.py") == [
		"tmp_path"
	]


def test_fixture_function_param_is_exempt(tmp_path: Path) -> None:
	"""A ``@pytest.fixture`` function may request other registry fixtures."""
	str_src = "import pytest\n@pytest.fixture\ndef str_a(tmp_path):\n\treturn 1\n"
	assert _names(tmp_path, str_src, ("tmp_path",), "tests/t.py") == []


def test_overridden_third_party_param_is_exempt(tmp_path: Path) -> None:
	"""A parameter of a method overriding an imported base's method is not chosen."""
	str_src = (
		"from json import JSONEncoder\n"
		"class E(JSONEncoder):\n\tdef default(self, o):\n\t\treturn 1\n"
	)
	assert _names(tmp_path, str_src) == []


def test_new_method_on_third_party_subclass_is_flagged(tmp_path: Path) -> None:
	"""Negative control: a method the base does not declare is the code's own."""
	str_src = (
		"from json import JSONEncoder\nclass E(JSONEncoder):\n\tdef mine(self, o):\n\t\treturn 1\n"
	)
	assert _names(tmp_path, str_src) == ["o"]


def test_local_base_override_is_flagged(tmp_path: Path) -> None:
	"""Negative control: an override of a repository class keeps the repository's naming rule."""
	str_src = (
		"from filings_cvm import RetryPolicy\n"
		"class E(RetryPolicy):\n\tdef default(self, o):\n\t\treturn 1\n"
	)
	assert _names(tmp_path, str_src) == ["o"]


def test_fixture_registry_contains_pytest_builtins() -> None:
	"""The registry is built from the installed pytest, not a hand list."""
	assert {"monkeypatch", "tmp_path", "capsys", "request"} <= set(ctp.pytest_fixture_registry())


def test_mismatch_is_reported(tmp_path: Path) -> None:
	"""``int_x: str`` is measured by ``mismatch_findings``."""
	path_file = tmp_path / "m.py"
	path_file.write_text("def f(int_x: str):\n\tpass\n", encoding="utf-8")
	assert ctp.mismatch_findings(path_file, TUPLE_PREFIXES)[0][1] == "int_x"


def test_variadic_annotation_is_not_a_mismatch(tmp_path: Path) -> None:
	"""``*tuple_args: str`` annotates the element type, so it agrees."""
	path_file = tmp_path / "m.py"
	path_file.write_text("def f(*tuple_args: str):\n\tpass\n", encoding="utf-8")
	assert ctp.mismatch_findings(path_file, TUPLE_PREFIXES) == []


def test_main_exit_code_on_finding(tmp_path: Path) -> None:
	"""``main`` exits 1 for an unprefixed file."""
	path_file = tmp_path / "m.py"
	path_file.write_text("x = 1\n", encoding="utf-8")
	assert ctp.main([str(path_file)]) == 1


def test_main_exit_code_when_clean(tmp_path: Path) -> None:
	"""``main`` exits 0 for a clean file."""
	path_file = tmp_path / "m.py"
	path_file.write_text("int_x = 1\n", encoding="utf-8")
	assert ctp.main([str(path_file)]) == 0


def test_report_never_fails(tmp_path: Path) -> None:
	"""``--report`` exits 0 even on a dirty file."""
	path_file = tmp_path / "m.py"
	path_file.write_text("x = 1\n", encoding="utf-8")
	assert ctp.main(["--report", str(path_file)]) == 0
