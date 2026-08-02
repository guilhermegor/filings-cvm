"""Unit tests for the EVENTUAL FI index reader.

``EventualFiReader`` reads ``eventual_fi_AAAA.csv`` — a plain CSV (not a ZIP), partitioned by
**year**, indexing the eventual documents a fund or class delivered. The reader returns
``LINK_ARQ`` as text and must **not** follow it.

Three things carry the weight here:

1. the contract is compared against the **verbatim header bytes CVM publishes** — every other test
   builds its input from ``tuple_required`` and is therefore a tautology;
2. this dataset and ``DFIN_FII`` are the same *kind* of artifact (a yearly plain-CSV index of
   documents delivered by a fund) and share **not one column name**, so semantic parallelism is
   pinned as *not* a naming rule;
3. ``ID_DOC`` is declared ``int`` by the dataset's META and is deliberately typed as **text**.

Mock the single I/O boundary (``download_file``); no network (the autouse guard in ``conftest.py``
also blocks any real socket).
"""

from datetime import date
from pathlib import Path

import pandas as pd
import pytest

from filings_cvm import RetryPolicy
from filings_cvm._internal.config.contracts import DFIN_FII, EVENTUAL_FI
from filings_cvm._internal.utils.tabular_reader import ContractError
from filings_cvm.ingestion.fi import EventualFiReader, MetaEventualFiReader


VALID_CNPJ = "11.222.333/0001-81"
REF = date(2025, 6, 15)
YEAR = "2025"
URL = "https://dados.cvm.gov.br/dados/FI/DOC/EVENTUAL/DADOS/eventual_fi_2025.csv"
PATH_FIXTURES = Path(__file__).resolve().parents[1] / "fixtures" / "eventual_fi"

_LINK = "https://web.cvm.gov.br/app/fundosweb/classes/documentos/download/19543"

# Columns a filing may legitimately leave blank — measured on the 2025 artifact, where each is
# empty for a large share of rows because it depends on the kind of document.
OPTIONAL_COLS = ("ID_SUBCLASSE", "NM_ARQ", "ID_DOC", "RESULTADO_AUDITORIA")


def _csv(list_cols: list[str], list_rows: list[list[str]]) -> str:
	"""Serialise a header + rows into the CVM ``;``-separated, ISO-8859-1 CSV shape."""
	lines = [";".join(list_cols)] + [";".join(r) for r in list_rows]
	return "\n".join(lines) + "\n"


def _valid_row() -> list[str]:
	"""One valid EVENTUAL row, in the contract's column order."""
	return [
		"CLASSE FIF/FAPI",  # TP_FUNDO_CLASSE
		VALID_CNPJ,  # CNPJ_FUNDO_CLASSE
		"BB FAPI FUNDO DE APOSENTADORIA PROGRAMADA INDIVIDUAL",  # DENOM_SOCIAL
		"OUBWU1765543823",  # ID_SUBCLASSE
		"2025-06-27",  # DT_COMPTC
		"2025-07-04",  # DT_RECEB
		"SGF ANEXO",  # TP_DOC
		"DOC_ANEXO_35799_19543_2025_07.pdf",  # NM_ARQ
		"0001209504",  # ID_DOC — leading zero on purpose; see the typing test
		_LINK,  # LINK_ARQ
		"Sem Ressalva",  # RESULTADO_AUDITORIA
	]


def _default_csv() -> str:
	"""Header + one valid row for the EVENTUAL contract."""
	return _csv(list(EVENTUAL_FI.tuple_required), [_valid_row()])


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
		"filings_cvm.ingestion.fi.doc.eventual.eventual.download_file", _fake_download
	)
	return list_urls


def test_contract_matches_the_published_header() -> None:
	"""The contract equals the verbatim header CVM publishes — the only non-tautological check.

	Every other test in this file builds its input from ``tuple_required``, so it can only ever
	agree with whatever was written there. This one compares against bytes we did not author.
	"""
	str_line = (PATH_FIXTURES / "eventual_fi_header.csv").read_text(encoding="iso-8859-1")

	assert EVENTUAL_FI.tuple_required == tuple(str_line.strip().split(";"))
	assert len(EVENTUAL_FI.tuple_required) == 11


def test_eventual_shares_no_column_name_with_the_dfin_index() -> None:
	"""Same kind of artifact, zero shared column names — parallelism is not a naming rule.

	``dfin_fii_AAAA.csv`` and ``eventual_fi_AAAA.csv`` are both yearly plain-CSV indexes of
	documents a fund delivered, and seven of their columns mean the same thing: fund type, CNPJ,
	name, reference date, delivery date, document link, auditor result. **Every one of those is
	spelled differently.** A contract written by analogy with the sibling would be wrong in all
	eleven columns while looking entirely reasonable, so the divergence is asserted rather than
	assumed — in both directions.
	"""
	set_eventual = set(EVENTUAL_FI.tuple_required)
	set_dfin = set(DFIN_FII.tuple_required)

	assert not set_eventual & set_dfin
	# The uppercase-abbreviated style is this dataset's; the CamelCase style is the sibling's.
	assert {"TP_FUNDO_CLASSE", "CNPJ_FUNDO_CLASSE", "DT_COMPTC", "LINK_ARQ"} <= set_eventual
	assert {
		"Tipo_Fundo_Classe",
		"CNPJ_Fundo_Classe",
		"Data_Referencia",
		"Link_Download",
	} <= set_dfin
	assert EVENTUAL_FI.tuple_cnpj_cols == ("CNPJ_FUNDO_CLASSE",)
	assert DFIN_FII.tuple_cnpj_cols == ("CNPJ_Fundo_Classe",)


def test_read_returns_all_contract_columns(monkeypatch: pytest.MonkeyPatch) -> None:
	"""The frame carries exactly the contract's columns (plus provenance).

	Parameters
	----------
	monkeypatch : pytest.MonkeyPatch
		Fixture used to replace the download boundary.
	"""
	_patch_download(monkeypatch, _default_csv())

	df_ = EventualFiReader(date_ref=REF).read()

	assert len(df_) == 1
	assert list(df_.columns) == list(EVENTUAL_FI.output_columns)


def test_read_coerces_both_date_columns(monkeypatch: pytest.MonkeyPatch) -> None:
	"""``DT_COMPTC`` and ``DT_RECEB`` become pure ``date`` objects; they are the only two.

	Parameters
	----------
	monkeypatch : pytest.MonkeyPatch
		Fixture used to replace the download boundary.
	"""
	_patch_download(monkeypatch, _default_csv())

	df_ = EventualFiReader(date_ref=REF).read()

	assert df_["DT_COMPTC"].iloc[0] == date(2025, 6, 27)
	assert df_["DT_RECEB"].iloc[0] == date(2025, 7, 4)


def test_read_keeps_id_doc_as_text_despite_the_meta_declaring_int(
	monkeypatch: pytest.MonkeyPatch,
) -> None:
	"""``ID_DOC`` is an identifier, so it stays source text even though the META types it ``int``.

	Asserted on a value carrying a **leading zero**, because that is what an integer type destroys
	silently: ``int64`` turns ``0001209504`` into ``1209504`` and nothing fails. The repo has met
	this exact case before in the CGVN's ``Codigo_CVM`` (``001023`` as published).

	Parameters
	----------
	monkeypatch : pytest.MonkeyPatch
		Fixture used to replace the download boundary.
	"""
	_patch_download(monkeypatch, _default_csv())

	df_ = EventualFiReader(date_ref=REF).read()

	assert df_["ID_DOC"].iloc[0] == "0001209504"
	assert isinstance(df_["ID_DOC"].iloc[0], str)


def test_read_returns_link_arq_as_text_and_does_not_follow_it(
	monkeypatch: pytest.MonkeyPatch,
) -> None:
	"""``LINK_ARQ`` is exact source text; the only URL fetched is the EVENTUAL CSV itself.

	The reader indexes documents — it must not download the linked files.

	Parameters
	----------
	monkeypatch : pytest.MonkeyPatch
		Fixture used to replace the download boundary.
	"""
	list_urls = _patch_download(monkeypatch, _default_csv())

	df_ = EventualFiReader(date_ref=REF).read()

	assert df_["LINK_ARQ"].iloc[0] == _LINK
	assert isinstance(df_["LINK_ARQ"].iloc[0], str)
	assert list_urls == [URL]
	# The document host is never requested — only the year's index CSV is.
	assert not any("fundosweb" in str_url for str_url in list_urls)


def test_read_leaves_an_unpopulated_column_empty(monkeypatch: pytest.MonkeyPatch) -> None:
	"""A column the filing does not populate comes back empty, never filled with a placeholder.

	Four columns are partially empty in the real 2025 file, because each depends on the kind of
	document: a link-only filing has no ``NM_ARQ`` or ``ID_DOC``, a fund with no subclass has no
	``ID_SUBCLASSE``, and only an audited document carries a ``RESULTADO_AUDITORIA``. Substituting
	an empty string or a zero would invent a fact the source never stated.

	Parameters
	----------
	monkeypatch : pytest.MonkeyPatch
		Fixture used to replace the download boundary.
	"""
	list_cols = list(EVENTUAL_FI.tuple_required)
	list_blank = [
		"" if c in OPTIONAL_COLS else v for c, v in zip(list_cols, _valid_row(), strict=True)
	]
	_patch_download(monkeypatch, _csv(list_cols, [_valid_row(), list_blank]))

	df_ = EventualFiReader(date_ref=REF).read()

	assert len(df_) == 2
	for str_col in OPTIONAL_COLS:
		assert pd.isna(df_[str_col].iloc[1]), str_col
	# The row is still a valid row — its non-optional columns survive intact.
	assert df_["CNPJ_FUNDO_CLASSE"].iloc[1] == VALID_CNPJ
	assert df_["DT_COMPTC"].iloc[1] == date(2025, 6, 27)


def test_date_ref_selects_the_year(monkeypatch: pytest.MonkeyPatch) -> None:
	"""Only ``date_ref.year`` reaches the URL — the dump is year-partitioned.

	Parameters
	----------
	monkeypatch : pytest.MonkeyPatch
		Fixture used to replace the download boundary.
	"""
	list_urls = _patch_download(monkeypatch, _default_csv())

	EventualFiReader(date_ref=date(2024, 2, 29)).read()

	assert list_urls == [
		"https://dados.cvm.gov.br/dados/FI/DOC/EVENTUAL/DADOS/eventual_fi_2024.csv"
	]


def test_read_stamps_provenance(monkeypatch: pytest.MonkeyPatch) -> None:
	"""The frame carries this dataset's source key and the URL it came from.

	Parameters
	----------
	monkeypatch : pytest.MonkeyPatch
		Fixture used to replace the download boundary.
	"""
	_patch_download(monkeypatch, _default_csv())

	df_ = EventualFiReader(date_ref=REF).read()

	assert df_["source_key"].iloc[0] == "eventual_fi"
	assert df_["url"].iloc[0] == URL


def test_read_raises_contract_error_on_missing_required_column(
	monkeypatch: pytest.MonkeyPatch,
) -> None:
	"""Dropping a declared column violates the contract.

	Parameters
	----------
	monkeypatch : pytest.MonkeyPatch
		Fixture used to replace the download boundary.
	"""
	list_cols = [c for c in EVENTUAL_FI.tuple_required if c != "LINK_ARQ"]
	list_row = [
		v for c, v in zip(EVENTUAL_FI.tuple_required, _valid_row(), strict=True) if c != "LINK_ARQ"
	]
	_patch_download(monkeypatch, _csv(list_cols, [list_row]))

	with pytest.raises(ContractError):
		EventualFiReader(date_ref=REF).read()


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

	EventualFiReader(date_ref=REF, path_raw=path_raw).read()

	assert (path_raw / f"eventual_fi_{YEAR}.csv").is_file()


def test_meta_url_is_the_loose_txt() -> None:
	"""EVENTUAL's META is a loose ``.txt``; the other three spellings this portal uses all 404.

	Measured, not derived — the portal spells META four different ways across datasets, so the URL
	is pinned per dataset rather than built from the dataset name.
	"""
	assert MetaEventualFiReader._META_URL == (
		"https://dados.cvm.gov.br/dados/FI/DOC/EVENTUAL/META/meta_eventual_fi.txt"
	)
	assert MetaEventualFiReader._META_URL.endswith(".txt")
	assert MetaEventualFiReader._CONTRACT.str_source_key == "meta_eventual_fi"


def test_reader_follows_the_retry_policy_standard() -> None:
	"""The reader declares its own ``_RETRY_POLICY`` and lets an instance override it."""
	cls_custom = RetryPolicy(int_max_attempts=8)

	assert isinstance(EventualFiReader._RETRY_POLICY, RetryPolicy)
	assert EventualFiReader(date_ref=REF)._retry_policy is EventualFiReader._RETRY_POLICY
	assert EventualFiReader(date_ref=REF, retry_policy=cls_custom)._retry_policy is cls_custom


def test_read_rejects_wrong_argument_type(monkeypatch: pytest.MonkeyPatch) -> None:
	"""The inherited ABCTypeCheckerMeta rejects a mistyped argument at call time.

	Parameters
	----------
	monkeypatch : pytest.MonkeyPatch
		Fixture used to replace the download boundary.
	"""
	_patch_download(monkeypatch, _default_csv())

	with pytest.raises(TypeError):
		EventualFiReader(date_ref=REF).read(int_timeout_s="nope")
