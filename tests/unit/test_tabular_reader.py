"""Unit tests for the tabular-reader seam's read-as-text contract.

The seam must never trust pandas' inference: it reads files as raw text and only then
coerces via the declared dtypes. These tests pin the lossless behaviour (a zero-padded
code and a money decimal survive the read) and that declared types still coerce from text.
The shared ``EXAMPLE_SOURCE`` contract (columns ``code``/``amount``) is reused because a
``FileContract`` may only be constructed under ``config/contracts/`` (ruff TID251).
"""

from pathlib import Path

from filings_cvm._internal.config.contracts import EXAMPLE_SOURCE
from filings_cvm._internal.utils.tabular_reader import read_table


def test_read_table_preserves_zero_padded_codes_and_decimals(tmp_path: Path) -> None:
	"""Raw text survives the read: leading zeros and trailing decimal zeros are kept.

	Parameters
	----------
	tmp_path : pathlib.Path
		Pytest-provided throwaway directory for the CSV fixture.
	"""
	path_csv = tmp_path / "source.csv"
	path_csv.write_text("code;amount\n007;10.50\n042;1000.00\n", encoding="utf-8")

	df_ = read_table(path_csv, "", {"code": "str", "amount": "str"}, EXAMPLE_SOURCE)

	# Inference would have turned "007" into 7 and "10.50" into 10.5 before typing.
	assert list(df_["code"]) == ["007", "042"]
	assert list(df_["amount"]) == ["10.50", "1000.00"]


def test_read_table_coerces_declared_types_from_text(tmp_path: Path) -> None:
	"""Declared non-text types still coerce cleanly from the text-first read.

	Parameters
	----------
	tmp_path : pathlib.Path
		Pytest-provided throwaway directory for the CSV fixture.
	"""
	path_csv = tmp_path / "source.csv"
	path_csv.write_text("code;amount\n007;42\n", encoding="utf-8")

	df_ = read_table(path_csv, "", {"code": "str", "amount": "Int64"}, EXAMPLE_SOURCE)

	assert df_["code"].iloc[0] == "007"
	assert str(df_["amount"].dtype) == "Int64"
	assert df_["amount"].iloc[0] == 42
