"""Unit tests for the Informe Quadrimestral FIP reader.

``InfQuadrimestralFipReader`` reads ``inf_quadrimestral_fip_AAAA.csv`` — a plain CSV (not a ZIP),
partitioned by **year**, the post-RCVM 175 four-monthly FIP report. It is column-identical to the
quarterly form except the first two columns (``TP_FUNDO_CLASSE`` + ``CNPJ_FUNDO_CLASSE`` replace
``CNPJ_FUNDO``). ``DT_COMPTC`` is coerced to a ``date``; money and quota amounts stay exact source
text. Mock the single I/O boundary (``download_file``); no network (the autouse guard in
``conftest.py`` also blocks any real socket).
"""

from datetime import date
from pathlib import Path

import pytest

from filings_cvm import InfQuadrimestralFipReader, RetryPolicy
from filings_cvm._internal.config.contracts import INF_QUADRIMESTRAL_FIP
from filings_cvm._internal.utils.tabular_reader import ContractError


VALID_CNPJ = "11.222.333/0001-81"
REF = date(2024, 8, 15)
YEAR = "2024"


def _value_for(str_col: str) -> str:
	"""Return a plausible value for one column, by name, in the CVM source shape."""
	if str_col == "CNPJ_FUNDO_CLASSE":
		return VALID_CNPJ
	if str_col == "TP_FUNDO_CLASSE":
		return "CLASSES - FIP"
	if str_col == "DT_COMPTC":
		return "2024-12-31"
	if str_col == "DENOM_SOCIAL":
		return "FUNDO DE INVESTIMENTO EM PARTICIPACOES EXEMPLO"
	if str_col == "PUBLICO_ALVO":
		return "Investidores qualificados"
	if str_col == "CLASSE_COTA":
		return "1"
	if str_col in ("ENTID_INVEST", "DIREITO_POLIT_CLASSE", "DIREITO_ECON_CLASSE"):
		return "N"
	# Every remaining column is a numeric amount in the source, kept as text by the reader.
	return "0.00000000"


def _valid_row() -> list[str]:
	"""One valid row, in the contract's column order."""
	return [_value_for(str_col) for str_col in INF_QUADRIMESTRAL_FIP.tuple_required]


def _csv(list_cols: list[str], list_rows: list[list[str]]) -> str:
	"""Serialise a header + rows into the CVM ``;``-separated CSV shape."""
	lines = [";".join(list_cols)] + [";".join(r) for r in list_rows]
	return "\n".join(lines) + "\n"


def _default_csv() -> str:
	"""Header + one valid row for the contract."""
	return _csv(list(INF_QUADRIMESTRAL_FIP.tuple_required), [_valid_row()])


def _patch_download(monkeypatch: pytest.MonkeyPatch, str_text: str) -> list[str]:
	"""Patch the reader's download_file boundary to drop ``str_text``; capture requested URLs."""
	list_urls: list[str] = []

	def _fake_download(
		str_url: str, path_dest: Path, int_timeout_s: int = 60, retry_policy: object = None
	) -> Path:
		list_urls.append(str_url)
		path_dest.parent.mkdir(parents=True, exist_ok=True)
		path_dest.write_bytes(str_text.encode("ISO-8859-1"))
		return path_dest

	monkeypatch.setattr(
		"filings_cvm.ingestion.fip.doc.inf_quadrimestral.inf_quadrimestral.download_file",
		_fake_download,
	)
	return list_urls


def test_read_returns_all_contract_columns(monkeypatch: pytest.MonkeyPatch) -> None:
	"""The frame carries exactly the contract's columns (plus provenance).

	Parameters
	----------
	monkeypatch : pytest.MonkeyPatch
		Fixture used to replace the download boundary.
	"""
	_patch_download(monkeypatch, _default_csv())

	df_ = InfQuadrimestralFipReader(date_ref=REF).read()

	assert len(df_) == 1
	assert list(df_.columns) == list(INF_QUADRIMESTRAL_FIP.output_columns)


def test_read_carries_the_rcvm175_class_key_columns(monkeypatch: pytest.MonkeyPatch) -> None:
	"""The post-175 fund/class identifier columns are present and exact source text.

	Parameters
	----------
	monkeypatch : pytest.MonkeyPatch
		Fixture used to replace the download boundary.
	"""
	_patch_download(monkeypatch, _default_csv())

	df_ = InfQuadrimestralFipReader(date_ref=REF).read()

	assert df_["TP_FUNDO_CLASSE"].iloc[0] == "CLASSES - FIP"
	assert df_["CNPJ_FUNDO_CLASSE"].iloc[0] == VALID_CNPJ
	assert "CNPJ_FUNDO" not in df_.columns


def test_read_coerces_dt_comptc(monkeypatch: pytest.MonkeyPatch) -> None:
	"""``DT_COMPTC`` becomes a pure ``date`` object.

	Parameters
	----------
	monkeypatch : pytest.MonkeyPatch
		Fixture used to replace the download boundary.
	"""
	_patch_download(monkeypatch, _default_csv())

	df_ = InfQuadrimestralFipReader(date_ref=REF).read()

	assert df_["DT_COMPTC"].iloc[0] == date(2024, 12, 31)


def test_read_keeps_money_columns_as_text(monkeypatch: pytest.MonkeyPatch) -> None:
	"""Money/quota amounts stay exact source text, never parsed to float.

	Parameters
	----------
	monkeypatch : pytest.MonkeyPatch
		Fixture used to replace the download boundary.
	"""
	list_cols = list(INF_QUADRIMESTRAL_FIP.tuple_required)
	list_row = _valid_row()
	list_row[list_cols.index("VL_PATRIM_LIQ")] = "51024.920000000000"
	_patch_download(monkeypatch, _csv(list_cols, [list_row]))

	df_ = InfQuadrimestralFipReader(date_ref=REF).read()

	assert df_["VL_PATRIM_LIQ"].iloc[0] == "51024.920000000000"
	assert isinstance(df_["VL_PATRIM_LIQ"].iloc[0], str)


def test_date_ref_selects_the_year(monkeypatch: pytest.MonkeyPatch) -> None:
	"""Only ``date_ref.year`` reaches the URL — the dump is year-partitioned.

	Parameters
	----------
	monkeypatch : pytest.MonkeyPatch
		Fixture used to replace the download boundary.
	"""
	list_urls = _patch_download(monkeypatch, _default_csv())

	InfQuadrimestralFipReader(date_ref=date(2025, 2, 28)).read()

	assert list_urls == [
		"https://dados.cvm.gov.br/dados/FIP/DOC/INF_QUADRIMESTRAL/DADOS/"
		"inf_quadrimestral_fip_2025.csv"
	]


def test_read_raises_contract_error_on_missing_required_column(
	monkeypatch: pytest.MonkeyPatch,
) -> None:
	"""Dropping a declared column violates the contract.

	Parameters
	----------
	monkeypatch : pytest.MonkeyPatch
		Fixture used to replace the download boundary.
	"""
	list_cols = [c for c in INF_QUADRIMESTRAL_FIP.tuple_required if c != "TP_FUNDO_CLASSE"]
	list_row = [
		v
		for c, v in zip(INF_QUADRIMESTRAL_FIP.tuple_required, _valid_row(), strict=True)
		if c != "TP_FUNDO_CLASSE"
	]
	_patch_download(monkeypatch, _csv(list_cols, [list_row]))

	with pytest.raises(ContractError):
		InfQuadrimestralFipReader(date_ref=REF).read()


def test_read_persists_csv_when_path_raw_is_given(
	monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
	"""With ``path_raw`` set, the raw CSV survives the read.

	Parameters
	----------
	monkeypatch : pytest.MonkeyPatch
		Fixture used to replace the download boundary.
	tmp_path : pathlib.Path
		Pytest-provided scratch directory standing in for the bronze layer.
	"""
	_patch_download(monkeypatch, _default_csv())
	path_raw = tmp_path / "bronze"

	InfQuadrimestralFipReader(date_ref=REF, path_raw=path_raw).read()

	assert (path_raw / f"inf_quadrimestral_fip_{YEAR}.csv").is_file()


def test_reader_follows_the_retry_policy_standard(monkeypatch: pytest.MonkeyPatch) -> None:
	"""The reader declares its own ``_RETRY_POLICY`` and lets an instance override it.

	Parameters
	----------
	monkeypatch : pytest.MonkeyPatch
		Fixture used to replace the download boundary.
	"""
	cls_custom = RetryPolicy(int_max_attempts=8)

	assert isinstance(InfQuadrimestralFipReader._RETRY_POLICY, RetryPolicy)
	assert (
		InfQuadrimestralFipReader(date_ref=REF)._retry_policy
		is InfQuadrimestralFipReader._RETRY_POLICY
	)
	assert (
		InfQuadrimestralFipReader(date_ref=REF, retry_policy=cls_custom)._retry_policy
		is cls_custom
	)


def test_read_rejects_wrong_argument_type(monkeypatch: pytest.MonkeyPatch) -> None:
	"""The inherited ABCTypeCheckerMeta rejects a mistyped argument at call time.

	Parameters
	----------
	monkeypatch : pytest.MonkeyPatch
		Fixture used to replace the download boundary.
	"""
	_patch_download(monkeypatch, _default_csv())

	with pytest.raises(TypeError):
		InfQuadrimestralFipReader(date_ref=REF).read(int_timeout_s="nope")
