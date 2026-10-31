"""Unit tests for the tabular-reader seam's read-as-text contract.

The seam must never trust pandas' inference: it reads files as raw text and only then
coerces via the declared dtypes. These tests pin the lossless behaviour (a zero-padded
code and a money decimal survive the read) and that declared types still coerce from text.
The shared ``EXAMPLE_SOURCE`` contract (columns ``code``/``amount``) is reused because a
``FileContract`` may only be constructed under ``config/contracts/`` (ruff TID251).
"""

from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from filings_cvm._internal.config.contracts import EXAMPLE_SOURCE
from filings_cvm._internal.config.contracts.compl_fi import COMPL_FI
from filings_cvm._internal.config.contracts.dfp_cia_aberta import (
	DFP_CIA_ABERTA_DFC_MD_CON,
	DFP_CIA_ABERTA_DFC_MD_IND,
)
from filings_cvm._internal.config.contracts.itr_cia_aberta import (
	ITR_CIA_ABERTA_DFC_MD_CON,
	ITR_CIA_ABERTA_DFC_MD_IND,
)
from filings_cvm._internal.utils.tabular_reader import (
	FileContract,
	find_contract_problems,
	read_table,
)


VALID_CNPJ = "11.222.333/0001-81"


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


def test_read_table_json_does_not_round_a_number_through_a_binary_float(
	tmp_path: Path,
) -> None:
	"""A JSON number survives the read exactly, digit for digit.

	``pd.read_json`` parses every number into a binary float *before* any dtype is applied,
	so the later ``astype("str")`` faithfully stringifies the already-corrupted value —
	``1984223115.42`` comes back as ``"1984223115.4200001"``. Parsing with
	``parse_float=Decimal`` is what makes the JSON branch as text-first as the CSV one.

	Parameters
	----------
	tmp_path : pathlib.Path
		Pytest-provided throwaway directory for the JSON fixture.
	"""
	path_json = tmp_path / "source.json"
	path_json.write_text(
		'[{"code": "007", "amount": 1984223115.42}]',
		encoding="utf-8",
	)

	df_ = read_table(path_json, "", {"code": "str", "amount": "str"}, EXAMPLE_SOURCE)

	assert df_["code"].iloc[0] == "007"
	assert df_["amount"].iloc[0] == "1984223115.42"


def test_read_table_json_yields_decimals_for_declared_decimal_columns(
	tmp_path: Path,
) -> None:
	"""The JSON branch feeds the decimal seam without ever creating a float in between.

	The scale is asserted through ``str``, not through ``==``: ``Decimal`` equality compares
	numeric value and ignores trailing zeros, so ``Decimal("10.5") == Decimal("10.50")`` is
	``True`` and an equality-only assertion would pass on the lossy ``pd.read_json`` path
	this test exists to exclude.

	Parameters
	----------
	tmp_path : pathlib.Path
		Pytest-provided throwaway directory for the JSON fixture.
	"""
	path_json = tmp_path / "source.json"
	path_json.write_text('[{"code": "007", "amount": 10.50}]', encoding="utf-8")

	df_ = read_table(
		path_json,
		"",
		{"code": "str"},
		EXAMPLE_SOURCE,
		list_decimal_cols=("amount",),
	)

	assert str(df_["amount"].iloc[0]) == "10.50"


@pytest.mark.parametrize(
	"cls_contract",
	[
		DFP_CIA_ABERTA_DFC_MD_CON,
		DFP_CIA_ABERTA_DFC_MD_IND,
		ITR_CIA_ABERTA_DFC_MD_CON,
		ITR_CIA_ABERTA_DFC_MD_IND,
	],
	ids=lambda c: c.str_source_key,
)
def test_cnpj_check_passes_a_header_only_partition(cls_contract: FileContract) -> None:
	"""A member CVM ships with a header and no rows has no CNPJ to check, so it passes (#317).

	``DFC_MD_con``/``DFC_MD_ind`` are header-only in ``dfp_cia_aberta_2026.zip``; ITR shares
	the shape. Both declare ``CNPJ_CIA`` because the member is full in other years.

	Parameters
	----------
	cls_contract : FileContract
		A contract that declares a CNPJ column.
	"""
	assert cls_contract.tuple_cnpj_cols
	df_ = pd.DataFrame(columns=list(cls_contract.tuple_required), dtype=str)

	assert find_contract_problems(df_, cls_contract) == []


@pytest.mark.parametrize("empty_value", [np.nan, "", "   "], ids=["nan", "blank", "spaces"])
def test_cnpj_check_passes_a_column_with_no_non_empty_value(empty_value: object) -> None:
	"""A declared CNPJ column whose every cell is empty passes the check (#317).

	``COMPL_FI.CNPJ_AG_RISCO`` is only the vehicle: a second CNPJ column beside a valid
	``CNPJ_FUNDO``, so the frame isolates the all-empty column.

	Parameters
	----------
	empty_value : object
		How an empty cell arrives: NaN from a default read, or blank text.
	"""
	df_ = pd.DataFrame(dict.fromkeys(COMPL_FI.tuple_required, "x"), index=[0, 1])
	df_["CNPJ_FUNDO"] = VALID_CNPJ
	df_["CNPJ_AG_RISCO"] = empty_value

	assert find_contract_problems(df_, COMPL_FI) == []


def test_cnpj_check_still_fails_non_empty_values_with_no_valid_cnpj() -> None:
	"""Present values none of which is a valid CNPJ still fail: that is the check's purpose."""
	df_ = pd.DataFrame(dict.fromkeys(COMPL_FI.tuple_required, "x"), index=[0, 1])
	df_["CNPJ_FUNDO"] = VALID_CNPJ
	df_["CNPJ_AG_RISCO"] = [np.nan, "not-a-cnpj"]

	assert find_contract_problems(df_, COMPL_FI) == [
		"Column 'CNPJ_AG_RISCO' in 'Complemento FI' holds no valid CNPJ (unexpected data type)"
	]
