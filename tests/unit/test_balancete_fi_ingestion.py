"""Unit tests for the FI/DOC/BALANCETE readers.

``balancete_fi_AAAAMM.zip`` is a single-member ZIP partitioned by month. Two schemas share the
filename pattern: 5 columns (``CNPJ_FUNDO``) through ``202310``, 6 columns
(``TP_FUNDO_CLASSE`` + ``CNPJ_FUNDO_CLASSE``) from ``202311`` -- a cut measured over the published
headers, one month before the Perfil Mensal's.

The oracle is the verbatim header bytes CVM publishes (``tests/fixtures/balancete_fi``); every
other test builds input from the contract and is a tautology by construction.
"""

from datetime import date
from pathlib import Path
import zipfile

import pytest

from filings_cvm._internal.config.contracts import (
	BALANCETE_FI,
	BALANCETE_FI_PRE202311,
	BALANCETE_FIE,
)
from filings_cvm._internal.utils.tabular_reader import ContractError, FileContract
from filings_cvm.ingestion.fi import (
	BalanceteFiPre202311Reader,
	BalanceteFiReader,
	MetaBalanceteFiReader,
)


VALID_CNPJ = "11.222.333/0001-81"
REF_NEW = date(2025, 6, 15)
REF_OLD = date(2020, 1, 15)
URL_NEW = "https://dados.cvm.gov.br/dados/FI/DOC/BALANCETE/DADOS/balancete_fi_202506.zip"
PATH_FIXTURES = Path(__file__).resolve().parents[1] / "fixtures" / "balancete_fi"


def _row(tuple_cols: tuple[str, ...], dict_over: dict[str, str] | None = None) -> list[str]:
	"""Build one plausible measured row for ``tuple_cols``."""
	dict_values = {
		"TP_FUNDO_CLASSE": "CLASSES - FIF",
		"CNPJ_FUNDO_CLASSE": VALID_CNPJ,
		"CNPJ_FUNDO": VALID_CNPJ,
		"DT_COMPTC": "2025-06-30",
		"PLANO_CONTA_BALCTE": "COFI",
		"CD_CONTA_BALCTE": "10000007",
		# Both a trailing zero and a negative sign die in a float.
		"VL_SALDO_BALCTE": "-1984223115.40",
	}
	dict_values.update(dict_over or {})
	return [dict_values[str_col] for str_col in tuple_cols]


def _csv(tuple_cols: tuple[str, ...], list_rows: list[list[str]]) -> str:
	"""Serialise header + rows in CVM's ``;`` / CRLF shape."""
	return "\r\n".join([";".join(tuple_cols), *(";".join(r) for r in list_rows)]) + "\r\n"


def _patch_download(
	monkeypatch: pytest.MonkeyPatch, str_text: str, str_member: str = "balancete_fi_202506.csv"
) -> list[str]:
	"""Patch the shared base's download boundary to write a real one-member ZIP."""
	list_urls: list[str] = []

	def _fake(
		str_url: str, path_dest: Path, int_timeout_s: int = 60, retry_policy: object = None
	) -> Path:
		list_urls.append(str_url)
		path_dest.parent.mkdir(parents=True, exist_ok=True)
		with zipfile.ZipFile(path_dest, "w") as zf:
			zf.writestr(str_member, str_text.encode("ISO-8859-1"))
		return path_dest

	monkeypatch.setattr(
		"filings_cvm.ingestion.fi.doc.balancete._base_balancete_reader.download_file", _fake
	)
	return list_urls


# ---- the pinned oracle ---------------------------------------------------------------------


@pytest.mark.parametrize(
	("contract", "str_file", "int_cols"),
	[
		(BALANCETE_FI, "balancete_fi_header.csv", 6),
		(BALANCETE_FI_PRE202311, "balancete_fi_pre202311_header.csv", 5),
	],
)
def test_contract_matches_the_published_header(
	contract: FileContract, str_file: str, int_cols: int
) -> None:
	"""Each contract equals the verbatim header CVM publishes for its regime."""
	str_line = (PATH_FIXTURES / str_file).read_text(encoding="iso-8859-1")

	assert contract.tuple_required == tuple(str_line.strip().split(";"))
	assert len(contract.tuple_required) == int_cols


def test_regimes_differ_exactly_in_the_key_block() -> None:
	"""Everything after the key block matches position for position, and nothing else differs."""
	tuple_new = BALANCETE_FI.tuple_required
	tuple_old = BALANCETE_FI_PRE202311.tuple_required

	assert tuple_new[:2] == ("TP_FUNDO_CLASSE", "CNPJ_FUNDO_CLASSE")
	assert tuple_old[:1] == ("CNPJ_FUNDO",)
	assert tuple_new[2:] == tuple_old[1:]
	assert BALANCETE_FI.tuple_cnpj_cols == ("CNPJ_FUNDO_CLASSE",)
	assert BALANCETE_FI_PRE202311.tuple_cnpj_cols == ("CNPJ_FUNDO",)


def test_fund_class_contract_is_distinct_from_the_fie_one_by_source_key() -> None:
	"""Same six names as the FIE balancete, but a different dataset: provenance must differ."""
	assert BALANCETE_FI.tuple_required == BALANCETE_FIE.tuple_required
	assert BALANCETE_FI.str_source_key != BALANCETE_FIE.str_source_key


# ---- month window --------------------------------------------------------------------------


@pytest.mark.parametrize(
	("cls_reader", "date_bad", "str_sibling"),
	[
		(BalanceteFiReader, date(2023, 10, 31), "BalanceteFiPre202311Reader"),
		(BalanceteFiPre202311Reader, date(2023, 11, 1), "BalanceteFiReader"),
	],
)
def test_a_month_outside_the_regime_names_the_sibling(
	cls_reader: type, date_bad: date, str_sibling: str
) -> None:
	"""Asking for the other regime's month fails fast, pointing at the right reader."""
	with pytest.raises(ValueError, match=str_sibling):
		cls_reader(date_bad)


def test_a_month_before_the_series_does_not_point_at_a_sibling() -> None:
	"""2014-12 predates the series: no reader serves it, so none may be suggested."""
	with pytest.raises(ValueError, match="publishes no file before 201501") as exc:
		BalanceteFiPre202311Reader(date(2014, 12, 31))

	assert "BalanceteFiReader" not in str(exc.value)


@pytest.mark.parametrize(
	("cls_reader", "date_ok"),
	[
		(BalanceteFiReader, date(2023, 11, 1)),
		(BalanceteFiPre202311Reader, date(2023, 10, 31)),
		(BalanceteFiPre202311Reader, date(2015, 1, 31)),
	],
)
def test_the_boundary_months_are_inclusive(cls_reader: type, date_ok: date) -> None:
	"""``202310``/``202311`` are the measured cutover pair."""
	assert cls_reader(date_ok) is not None


def test_the_closed_regime_defaults_to_its_last_month() -> None:
	"""No-argument construction of the legacy reader must not raise."""
	assert BalanceteFiPre202311Reader()._date_ref == date(2023, 10, 1)


# ---- read path -----------------------------------------------------------------------------


def test_read_builds_the_url_and_keeps_money_as_exact_text(
	monkeypatch: pytest.MonkeyPatch,
) -> None:
	"""``date_ref`` picks the month; balance and account code stay text, date becomes a date."""
	tuple_cols = BALANCETE_FI.tuple_required
	list_urls = _patch_download(monkeypatch, _csv(tuple_cols, [_row(tuple_cols)]))

	df_ = BalanceteFiReader(REF_NEW).read()

	assert list_urls == [URL_NEW]
	assert df_["VL_SALDO_BALCTE"].iloc[0] == "-1984223115.40"
	assert df_["CD_CONTA_BALCTE"].iloc[0] == "10000007"
	assert df_["DT_COMPTC"].iloc[0] == date(2025, 6, 30)
	assert df_["url"].iloc[0] == URL_NEW
	assert df_["source_key"].iloc[0] == "balancete_fi"


def test_the_legacy_reader_reads_its_own_five_column_artifact(
	monkeypatch: pytest.MonkeyPatch,
) -> None:
	"""The legacy reader keys on ``CNPJ_FUNDO`` and has no ``TP_FUNDO_CLASSE``."""
	tuple_cols = BALANCETE_FI_PRE202311.tuple_required
	_patch_download(monkeypatch, _csv(tuple_cols, [_row(tuple_cols)]), "balancete_fi_202001.csv")

	df_ = BalanceteFiPre202311Reader(REF_OLD).read()

	assert df_["CNPJ_FUNDO"].iloc[0] == VALID_CNPJ
	assert "TP_FUNDO_CLASSE" not in df_.columns


def test_the_wrong_regimes_artifact_raises_contract_error(
	monkeypatch: pytest.MonkeyPatch,
) -> None:
	"""A 5-column file served for a 6-column month violates the contract."""
	tuple_cols = BALANCETE_FI_PRE202311.tuple_required
	_patch_download(monkeypatch, _csv(tuple_cols, [_row(tuple_cols)]))

	with pytest.raises(ContractError):
		BalanceteFiReader(REF_NEW).read()


def test_the_source_empty_cells_of_201501_come_back_empty(
	monkeypatch: pytest.MonkeyPatch,
) -> None:
	"""22 rows of 201501 carry an empty account code and balance; empty stays empty."""
	tuple_cols = BALANCETE_FI_PRE202311.tuple_required
	_patch_download(
		monkeypatch,
		_csv(
			tuple_cols,
			[
				_row(tuple_cols, {"CD_CONTA_BALCTE": "", "VL_SALDO_BALCTE": ""}),
				_row(tuple_cols),
			],
		),
		"balancete_fi_201501.csv",
	)

	df_ = BalanceteFiPre202311Reader(date(2015, 1, 31)).read()

	assert len(df_) == 2
	assert df_["VL_SALDO_BALCTE"].isna().iloc[0]
	assert df_["VL_SALDO_BALCTE"].iloc[1] == "-1984223115.40"


def test_path_raw_keeps_the_zip(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
	"""``path_raw`` persists the untouched ZIP."""
	tuple_cols = BALANCETE_FI.tuple_required
	_patch_download(monkeypatch, _csv(tuple_cols, [_row(tuple_cols)]))

	BalanceteFiReader(REF_NEW, path_raw=tmp_path).read()

	assert (tmp_path / "balancete_fi_202506.zip").exists()


def test_a_missing_member_raises(monkeypatch: pytest.MonkeyPatch) -> None:
	"""An archive without ``balancete_fi_AAAAMM.csv`` is refused."""
	tuple_cols = BALANCETE_FI.tuple_required
	_patch_download(monkeypatch, _csv(tuple_cols, [_row(tuple_cols)]), "other.csv")

	with pytest.raises(ValueError):
		BalanceteFiReader(REF_NEW).read()


# ---- META ----------------------------------------------------------------------------------


def test_the_meta_url_is_the_flat_txt() -> None:
	"""The META is the flat ``meta_balancete_fi.txt``, pinned and never derived."""
	assert MetaBalanceteFiReader._META_URL.endswith("/BALANCETE/META/meta_balancete_fi.txt")
	assert MetaBalanceteFiReader._CONTRACT.str_source_key == "meta_balancete_fi"
