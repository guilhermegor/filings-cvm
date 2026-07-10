"""Unit tests for the Lâmina FIF (fact sheet) ingestion reader.

Mock the single I/O boundary (``download_file``) with a fixture ZIP, then exercise exact
member selection, the ``FileContract`` validation, quoting, and dtype application for real —
no network.

The fixture mirrors the real ``lamina_fi_AAAAMM.zip``: the lâmina member alongside the three
siblings whose names it *prefixes*, and a free-text field carrying the stray unbalanced ``"``
that makes default CSV quoting merge two records.
"""

from datetime import date
import io
from pathlib import Path
import zipfile

import pandas as pd
import pytest

from filings_cvm._internal.config.contracts.lamina_fif import LAMINA_FIF
from filings_cvm._internal.utils.tabular_reader import ContractError
from filings_cvm.ingestion import LaminaReader


# CNPJs whose check digits are valid under the repo's ASCII-48 mod-11 routine. CVM ships
# them masked, as here, so the contract's unmasking path is exercised too.
VALID_CNPJ = "11.222.333/0001-81"
OTHER_CNPJ = "11.444.777/0001-61"

_HEADER = ";".join(LAMINA_FIF.tuple_required)


def _row(str_cnpj: str, str_objetivo: str = "Rendimento", str_dt_ini_despesa: str = "") -> str:
	"""Build one 78-field row, overriding only the fields a test cares about."""
	dict_over = {
		"TP_FUNDO_CLASSE": "FI",
		"CNPJ_FUNDO_CLASSE": str_cnpj,
		"ID_SUBCLASSE": "",
		"DENOM_SOCIAL": "FUNDO ALFA",
		"DT_COMPTC": "2025-04-30",
		"OBJETIVO": str_objetivo,
		"DT_INI_DESPESA": str_dt_ini_despesa,
		"DT_FIM_DESPESA": "",
		"DT_INI_ATIV_5ANO": "2005-04-08",
		"VL_PATRIM_LIQ": "50000.00",
		"TAXA_ADM": "1.50",
	}
	return ";".join(dict_over.get(str_col, "x") for str_col in LAMINA_FIF.tuple_required)


def _default_members() -> dict[str, str]:
	"""Build the member-name → CSV-text map of a well-formed fixture archive."""
	return {
		"lamina_fi_202504.csv": f"{_HEADER}\n{_row(VALID_CNPJ)}\n{_row(OTHER_CNPJ)}\n",
		# Siblings that ``lamina_fi_202504.csv`` is a strict prefix of.
		"lamina_fi_carteira_202504.csv": f"CNPJ_FUNDO_CLASSE;TP_ATIVO\n{VALID_CNPJ};Acoes\n",
		"lamina_fi_rentab_ano_202504.csv": f"CNPJ_FUNDO_CLASSE;ANO\n{VALID_CNPJ};2025\n",
		"lamina_fi_rentab_mes_202504.csv": f"CNPJ_FUNDO_CLASSE;MES\n{VALID_CNPJ};4\n",
	}


def _zip_bytes(dict_members: dict[str, str]) -> bytes:
	"""Build an in-memory ZIP holding each ``name → csv text`` member."""
	buffer = io.BytesIO()
	with zipfile.ZipFile(buffer, "w") as cls_zip:
		for str_name, str_text in dict_members.items():
			cls_zip.writestr(str_name, str_text.encode("ISO-8859-1"))
	return buffer.getvalue()


def _patch_download(monkeypatch: pytest.MonkeyPatch, payload: bytes) -> None:
	"""Patch the reader's download_file boundary to drop ``payload`` at the destination."""

	def _fake_download(str_url: str, path_dest: Path, int_timeout_s: int = 30) -> Path:
		path_dest.parent.mkdir(parents=True, exist_ok=True)
		path_dest.write_bytes(payload)
		return path_dest

	monkeypatch.setattr("filings_cvm.ingestion.fi.doc.lamina.lamina.download_file", _fake_download)


def _read_default(monkeypatch: pytest.MonkeyPatch) -> pd.DataFrame:
	"""Read the well-formed fixture archive."""
	_patch_download(monkeypatch, _zip_bytes(_default_members()))
	return LaminaReader(date_ref=date(2025, 4, 15)).read()


def test_read_returns_one_row_per_fund_class(monkeypatch: pytest.MonkeyPatch) -> None:
	"""The lâmina member's rows come back at the fund-class grain, all 78 columns.

	Parameters
	----------
	monkeypatch : pytest.MonkeyPatch
		Fixture used to replace the download boundary.
	"""
	df_ = _read_default(monkeypatch)

	assert len(df_) == 2
	assert len(df_.columns) == 78 + len(LAMINA_FIF.PROVENANCE_COLUMNS)
	assert list(df_.columns) == list(LAMINA_FIF.output_columns)


def test_read_selects_the_lamina_member_not_its_prefix_siblings(
	monkeypatch: pytest.MonkeyPatch,
) -> None:
	"""``lamina_fi_202504.csv`` is a strict prefix of three siblings; exact match wins.

	A ``startswith`` selection would return whichever member the archive listed first.

	Parameters
	----------
	monkeypatch : pytest.MonkeyPatch
		Fixture used to replace the download boundary.
	"""
	df_ = _read_default(monkeypatch)

	assert "TP_ATIVO" not in df_.columns
	assert "ANO" not in df_.columns
	assert "MES" not in df_.columns


def test_read_survives_stray_quote_in_free_text(monkeypatch: pytest.MonkeyPatch) -> None:
	"""An unbalanced ``"`` in OBJETIVO must not merge two records into one.

	This is why the reader parses with ``QUOTE_NONE``. Under pandas' default quoting the
	stray quote opens a field that swallows the row terminator, and the real 2025-04 dump
	raises ``ParserError`` (78 fields expected, 142 seen).

	Parameters
	----------
	monkeypatch : pytest.MonkeyPatch
		Fixture used to replace the download boundary.
	"""
	dict_members = _default_members()
	dict_members["lamina_fi_202504.csv"] = (
		f"{_HEADER}\n{_row(VALID_CNPJ, str_objetivo=chr(34) + 'renda fixa')}\n{_row(OTHER_CNPJ)}\n"
	)
	_patch_download(monkeypatch, _zip_bytes(dict_members))

	df_ = LaminaReader(date_ref=date(2025, 4, 15)).read()

	# Both records survive as separate rows, and the quote is kept as literal source text.
	assert len(df_) == 2
	assert df_["OBJETIVO"].iloc[0] == '"renda fixa'


def test_read_coerces_every_date_column(monkeypatch: pytest.MonkeyPatch) -> None:
	"""All four ``DT_*`` columns become pure date objects; a blank becomes NaT.

	Parameters
	----------
	monkeypatch : pytest.MonkeyPatch
		Fixture used to replace the download boundary.
	"""
	dict_members = _default_members()
	dict_members["lamina_fi_202504.csv"] = (
		f"{_HEADER}\n{_row(VALID_CNPJ, str_dt_ini_despesa='2024-05-01')}\n"
	)
	_patch_download(monkeypatch, _zip_bytes(dict_members))

	df_ = LaminaReader(date_ref=date(2025, 4, 15)).read()

	assert df_["DT_COMPTC"].iloc[0] == date(2025, 4, 30)
	assert df_["DT_INI_DESPESA"].iloc[0] == date(2024, 5, 1)
	assert df_["DT_INI_ATIV_5ANO"].iloc[0] == date(2005, 4, 8)
	assert pd.isna(df_["DT_FIM_DESPESA"].iloc[0])


def test_read_keeps_money_columns_as_exact_source_text(
	monkeypatch: pytest.MonkeyPatch,
) -> None:
	"""Monetary and fee columns keep their exact CVM text, never a lossy float.

	Parameters
	----------
	monkeypatch : pytest.MonkeyPatch
		Fixture used to replace the download boundary.
	"""
	df_ = _read_default(monkeypatch)

	assert df_["VL_PATRIM_LIQ"].iloc[0] == "50000.00"
	assert df_["TAXA_ADM"].iloc[0] == "1.50"
	assert isinstance(df_["VL_PATRIM_LIQ"].iloc[0], str)


def test_read_keeps_empty_id_subclasse_missing(monkeypatch: pytest.MonkeyPatch) -> None:
	"""A blank ID_SUBCLASSE stays NA — never the literal string "nan".

	Parameters
	----------
	monkeypatch : pytest.MonkeyPatch
		Fixture used to replace the download boundary.
	"""
	df_ = _read_default(monkeypatch)

	assert df_["ID_SUBCLASSE"].isna().all()


def test_dtype_map_covers_every_non_date_column() -> None:
	"""The derived dtype map and the date columns together span the whole contract."""
	from filings_cvm.ingestion.fi.doc.lamina.lamina import _DATE_COLS, _DTYPES

	assert set(_DTYPES) | set(_DATE_COLS) == set(LAMINA_FIF.tuple_required)
	assert not set(_DTYPES) & set(_DATE_COLS)


def test_read_raises_contract_error_on_missing_required_column(
	monkeypatch: pytest.MonkeyPatch,
) -> None:
	"""Dropping any of the 78 declared columns violates the contract.

	Parameters
	----------
	monkeypatch : pytest.MonkeyPatch
		Fixture used to replace the download boundary.
	"""
	list_cols = [c for c in LAMINA_FIF.tuple_required if c != "INF_SAC"]
	dict_members = _default_members()
	dict_members["lamina_fi_202504.csv"] = (
		";".join(list_cols) + "\n" + ";".join("x" for _ in list_cols) + "\n"
	)
	_patch_download(monkeypatch, _zip_bytes(dict_members))

	with pytest.raises(ContractError):
		LaminaReader(date_ref=date(2025, 4, 15)).read()


def test_read_raises_value_error_when_archive_has_no_lamina_member(
	monkeypatch: pytest.MonkeyPatch,
) -> None:
	"""An archive holding only the siblings raises a clear ValueError naming the member.

	Parameters
	----------
	monkeypatch : pytest.MonkeyPatch
		Fixture used to replace the download boundary.
	"""
	dict_members = _default_members()
	del dict_members["lamina_fi_202504.csv"]
	_patch_download(monkeypatch, _zip_bytes(dict_members))

	with pytest.raises(ValueError, match="lamina_fi_202504.csv"):
		LaminaReader(date_ref=date(2025, 4, 15)).read()


def test_read_persists_raw_artifact_when_path_raw_is_given(
	monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
	"""With ``path_raw`` set, the ZIP and *every* extracted CSV survive the read.

	The whole archive is kept, so ``LaminaCarteiraReader`` can replay the same bytes.

	Parameters
	----------
	monkeypatch : pytest.MonkeyPatch
		Fixture used to replace the download boundary.
	tmp_path : pathlib.Path
		Pytest-provided scratch directory standing in for the bronze layer.
	"""
	_patch_download(monkeypatch, _zip_bytes(_default_members()))
	path_raw = tmp_path / "bronze" / "lamina" / "202504"

	LaminaReader(date_ref=date(2025, 4, 15), path_raw=path_raw).read()

	assert (path_raw / "lamina_fi_202504.zip").is_file()
	assert {p.name for p in path_raw.glob("*.csv")} == set(_default_members())


def test_read_leaves_no_artifact_on_disk_when_path_raw_is_none(
	monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
	"""Without ``path_raw`` the artifact lands in a temp dir and is discarded.

	Parameters
	----------
	monkeypatch : pytest.MonkeyPatch
		Fixture used to replace the download boundary.
	tmp_path : pathlib.Path
		Scratch directory asserted to stay empty.
	"""
	_patch_download(monkeypatch, _zip_bytes(_default_members()))
	monkeypatch.chdir(tmp_path)

	LaminaReader(date_ref=date(2025, 4, 15)).read()

	assert list(tmp_path.iterdir()) == []


def test_url_reflects_reference_month() -> None:
	"""The download URL is built from the reference month (AAAAMM)."""
	reader = LaminaReader(date_ref=date(2025, 3, 9))

	assert reader._str_url.endswith("lamina_fi_202503.zip")


def test_read_rejects_wrong_argument_type(monkeypatch: pytest.MonkeyPatch) -> None:
	"""The inherited ABCTypeCheckerMeta rejects a mistyped argument at call time.

	Parameters
	----------
	monkeypatch : pytest.MonkeyPatch
		Fixture used to replace the download boundary.
	"""
	_patch_download(monkeypatch, _zip_bytes(_default_members()))

	with pytest.raises(TypeError):
		LaminaReader(date_ref=date(2025, 4, 15)).read(int_timeout_s="nope")
