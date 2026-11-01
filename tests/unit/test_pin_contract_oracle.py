"""Tests for ``bin/pin_contract_oracle.py``, run against a real published-header fixture."""

import importlib.util
from pathlib import Path
from types import ModuleType

import pytest

from filings_cvm._internal.config.contracts.eventual_fi import EVENTUAL_FI


_ROOT = Path(__file__).resolve().parents[2]
_FIXTURE = _ROOT / "tests" / "fixtures" / "eventual_fi" / "eventual_fi_header.csv"


def _load_tool() -> ModuleType:
	"""Import the ``bin`` script by path (``bin/`` is not a package).

	Returns
	-------
	types.ModuleType
		The loaded ``pin_contract_oracle`` module.
	"""
	spec = importlib.util.spec_from_file_location(
		"pin_contract_oracle", _ROOT / "bin" / "pin_contract_oracle.py"
	)
	module = importlib.util.module_from_spec(spec)
	spec.loader.exec_module(module)
	return module


def test_read_header_of_a_real_fixture_equals_the_contract() -> None:
	"""The generated tuple for CVM's real header is exactly the contract's required columns."""
	tool = _load_tool()
	assert tool.read_header(_FIXTURE, ";", "ISO-8859-1") == EVENTUAL_FI.tuple_required


def test_write_reproduces_the_header_bytes_verbatim(tmp_path: Path) -> None:
	"""``--write`` emits a header-only fixture byte-identical to the real one."""
	path_out = tmp_path / "out" / "header.csv"
	_load_tool().main([str(_FIXTURE), "--write", str(path_out)])
	assert path_out.read_bytes() == _FIXTURE.read_bytes()


def test_read_header_rejects_a_file_without_a_header(tmp_path: Path) -> None:
	"""A blank file has no header to pin, so it fails loudly."""
	path_blank = tmp_path / "blank.csv"
	path_blank.write_text("\n\n", encoding="utf-8")
	with pytest.raises(ValueError, match="no non-empty header line"):
		_load_tool().read_header(path_blank, ";", "utf-8")
