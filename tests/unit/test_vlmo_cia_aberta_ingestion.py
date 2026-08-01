"""Unit tests for the two CIA_ABERTA/DOC/VLMO readers (`cia_aberta/doc/vlmo/`).

`VlmoCiaAbertaReader` reads the **index** member (12 cols) and `VlmoCiaAbertaConReader` the
**content** member (17 cols) of the same yearly ZIP — ⚠️ not a registry+satellite pair.

Two behaviours carry the weight here and both are pinned below: the money/quantity columns come
back as **exact source text** (10 decimal places preserved, never a float), and
`Data_Movimentacao` is a date column that is **~58% blank** in the real file, so blanks must
become `NaT` rather than raise.

Every test except one builds its input from each contract's `tuple_required`, so it is a
tautology. The exception is :func:`test_contracts_match_the_published_headers`, which compares
both contracts against the **verbatim header bytes CVM publishes** — the only assertion here
whose expected value we did not author. See ``tests/CLAUDE.md``.

Mock the single I/O boundary (``download_file``); no network.
"""

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
import io
from pathlib import Path
import zipfile

import pandas as pd
import pytest

from filings_cvm._internal.config.contracts import (
	VLMO_CIA_ABERTA,
	VLMO_CIA_ABERTA_CON,
	FileContract,
)
from filings_cvm._internal.config.ports.ingestion_reader import IngestionReader
from filings_cvm._internal.utils.tabular_reader import ContractError
from filings_cvm.ingestion.cia_aberta import (
	MetaVlmoCiaAbertaReader,
	VlmoCiaAbertaConReader,
	VlmoCiaAbertaReader,
)


VALID_CNPJ = "11.222.333/0001-81"
DATE_REF = date(2025, 6, 15)
URL = "https://dados.cvm.gov.br/dados/CIA_ABERTA/DOC/VLMO/DADOS/vlmo_cia_aberta_2025.zip"
MODULE = "filings_cvm.ingestion.cia_aberta.doc.vlmo._base_vlmo_reader"
PATH_FIXTURES = Path(__file__).resolve().parents[1] / "fixtures" / "vlmo_cia_aberta"

# A real 2025 value: 10 decimal places whose trailing digits a binary float would destroy.
VOLUME_EXACT = "61961072.9999543100"
PRECO_EXACT = "39.7967995028"


@dataclass(frozen=True)
class VlmoCase:
	"""One reader's spec: how to build it, which member it reads, and its date columns."""

	cls_reader: type[IngestionReader]
	cls_contract: FileContract
	str_stem: str
	tuple_date_cols: tuple[str, ...]


CASES: tuple[VlmoCase, ...] = (
	VlmoCase(
		VlmoCiaAbertaReader,
		VLMO_CIA_ABERTA,
		"vlmo_cia_aberta",
		("Data_Referencia", "Data_Entrega"),
	),
	VlmoCase(
		VlmoCiaAbertaConReader,
		VLMO_CIA_ABERTA_CON,
		"vlmo_cia_aberta_con",
		("Data_Referencia", "Data_Movimentacao"),
	),
)
IDS = [case.cls_reader.__name__ for case in CASES]


def _value_for(str_col: str) -> str:
	"""Return a plausible source value for one column, by name."""
	if str_col == "CNPJ_Companhia":
		return VALID_CNPJ
	if str_col.startswith("Data_"):
		return "2025-08-25"
	if str_col == "Volume":
		return VOLUME_EXACT
	if str_col == "Preco_Unitario":
		return PRECO_EXACT
	if str_col == "Quantidade":
		return "2865417084"
	if str_col == "Versao":
		return "1"
	return "x"


def _row(cls_contract: FileContract) -> list[str]:
	"""One valid row in the contract's column order."""
	return [_value_for(c) for c in cls_contract.tuple_required]


def _csv_text(list_cols: list[str], list_rows: list[list[str]]) -> str:
	"""Serialise a header + rows into the CVM ``;``-separated CSV shape."""
	return "\n".join([";".join(list_cols), *[";".join(r) for r in list_rows]]) + "\n"


def _payload(dict_members: dict[str, str]) -> bytes:
	"""Build the yearly ZIP holding the given ``member name -> csv text`` mapping."""
	buffer = io.BytesIO()
	with zipfile.ZipFile(buffer, "w") as cls_zip:
		for str_name, str_csv in dict_members.items():
			cls_zip.writestr(str_name, str_csv.encode("ISO-8859-1"))
	return buffer.getvalue()


def _both_members(dict_override: dict[str, str] | None = None) -> bytes:
	"""Build the real two-member archive, one valid row per member unless overridden."""
	dict_members = {
		f"{case.str_stem}_2025.csv": _csv_text(
			list(case.cls_contract.tuple_required), [_row(case.cls_contract)]
		)
		for case in CASES
	}
	dict_members.update(dict_override or {})
	return _payload(dict_members)


def _patch(monkeypatch: pytest.MonkeyPatch, bytes_payload: bytes) -> list[str]:
	"""Patch the shared base's download_file to drop ``bytes_payload``; capture requested URLs."""
	list_urls: list[str] = []

	def _fake_download(
		str_url: str, path_dest: Path, int_timeout_s: int = 60, retry_policy: object = None
	) -> Path:
		list_urls.append(str_url)
		path_dest.parent.mkdir(parents=True, exist_ok=True)
		path_dest.write_bytes(bytes_payload)
		return path_dest

	monkeypatch.setattr(f"{MODULE}.download_file", _fake_download)
	return list_urls


def test_contracts_match_the_published_headers() -> None:
	"""Both contracts equal the verbatim headers CVM publishes — the non-tautological oracle."""
	for case in CASES:
		str_line = (PATH_FIXTURES / f"{case.str_stem}_header.csv").read_text(encoding="iso-8859-1")
		assert case.cls_contract.tuple_required == tuple(str_line.strip().split(";"))
	assert len(VLMO_CIA_ABERTA.tuple_required) == 12
	assert len(VLMO_CIA_ABERTA_CON.tuple_required) == 17


def test_the_two_members_are_not_copies_of_each_other() -> None:
	"""Index and content are different tables — anti-copy guard.

	They share the company-identity prefix but the content member carries the movement columns
	and the index carries the document ones. Copying one contract onto the other would ship a
	wrong reader with every other test still green.
	"""
	set_idx = set(VLMO_CIA_ABERTA.tuple_required)
	set_con = set(VLMO_CIA_ABERTA_CON.tuple_required)

	assert set_idx != set_con
	assert {"Link_Download", "Motivo_Reapresentacao", "Data_Entrega"} <= set_idx
	assert {"Quantidade", "Preco_Unitario", "Volume", "Data_Movimentacao"} <= set_con
	assert not {"Quantidade", "Preco_Unitario", "Volume"} & set_idx


@pytest.mark.parametrize("case", CASES, ids=IDS)
def test_read_returns_all_contract_columns(
	case: VlmoCase, monkeypatch: pytest.MonkeyPatch
) -> None:
	"""Each reader's frame carries exactly its contract's columns, plus provenance.

	Parameters
	----------
	case : VlmoCase
		The reader spec under test.
	monkeypatch : pytest.MonkeyPatch
		Fixture used to replace the download boundary.
	"""
	_patch(monkeypatch, _both_members())

	df_ = case.cls_reader(date_ref=DATE_REF).read()

	assert len(df_) == 1
	assert list(df_.columns) == list(case.cls_contract.output_columns)


@pytest.mark.parametrize("case", CASES, ids=IDS)
def test_read_coerces_its_own_date_columns(
	case: VlmoCase, monkeypatch: pytest.MonkeyPatch
) -> None:
	"""Each reader coerces its own date columns — the two members differ in the second one.

	Parameters
	----------
	case : VlmoCase
		The reader spec under test.
	monkeypatch : pytest.MonkeyPatch
		Fixture used to replace the download boundary.
	"""
	_patch(monkeypatch, _both_members())

	df_ = case.cls_reader(date_ref=DATE_REF).read()

	for str_col in case.tuple_date_cols:
		assert isinstance(df_[str_col].iloc[0], date)
		assert df_[str_col].iloc[0] == date(2025, 8, 25)


@pytest.mark.parametrize("case", CASES, ids=IDS)
def test_read_requests_the_yearly_url(case: VlmoCase, monkeypatch: pytest.MonkeyPatch) -> None:
	"""Both readers fetch the same yearly archive, selected by ``date_ref.year`` alone.

	Parameters
	----------
	case : VlmoCase
		The reader spec under test.
	monkeypatch : pytest.MonkeyPatch
		Fixture used to replace the download boundary.
	"""
	list_urls = _patch(monkeypatch, _both_members())

	case.cls_reader(date_ref=date(2025, 1, 1)).read()

	assert list_urls == [URL]


def test_read_preserves_money_and_quantity_as_exact_text(
	monkeypatch: pytest.MonkeyPatch,
) -> None:
	"""``Preco_Unitario`` / ``Volume`` keep all 10 published decimals; ``Quantidade`` stays text.

	This is the #157 rule at its first real consumer in this portal root. The assertion is on the
	**string**, not a numeric comparison: ``float(VOLUME_EXACT)`` compares equal to several
	different decimal strings, so only the text proves nothing was lost. The ``Decimal`` round
	trip shown here is what a consumer does downstream — never a ``float``.

	Parameters
	----------
	monkeypatch : pytest.MonkeyPatch
		Fixture used to replace the download boundary.
	"""
	_patch(monkeypatch, _both_members())

	df_ = VlmoCiaAbertaConReader(date_ref=DATE_REF).read()

	assert df_["Volume"].iloc[0] == VOLUME_EXACT
	assert df_["Preco_Unitario"].iloc[0] == PRECO_EXACT
	assert df_["Quantidade"].iloc[0] == "2865417084"
	assert isinstance(df_["Volume"].iloc[0], str)
	# What a consumer does downstream — the published value survives, digit for digit.
	assert Decimal(df_["Volume"].iloc[0]) == Decimal(VOLUME_EXACT)
	assert str(Decimal(df_["Volume"].iloc[0])) == VOLUME_EXACT
	# The float path this typing exists to exclude loses the trailing digits.
	assert str(float(VOLUME_EXACT)) != VOLUME_EXACT


def test_read_accepts_a_blank_data_movimentacao(monkeypatch: pytest.MonkeyPatch) -> None:
	"""``Data_Movimentacao`` is ~58% blank in the real file — blanks become ``NaT``, not an error.

	The index member's dates are always present, so this path is only exercised by the content
	member; without it a real read of any year would raise.

	Parameters
	----------
	monkeypatch : pytest.MonkeyPatch
		Fixture used to replace the download boundary.
	"""
	list_cols = list(VLMO_CIA_ABERTA_CON.tuple_required)
	list_blank = ["" if c == "Data_Movimentacao" else _value_for(c) for c in list_cols]
	str_csv = _csv_text(list_cols, [_row(VLMO_CIA_ABERTA_CON), list_blank])
	_patch(monkeypatch, _both_members({"vlmo_cia_aberta_con_2025.csv": str_csv}))

	df_ = VlmoCiaAbertaConReader(date_ref=DATE_REF).read()

	assert len(df_) == 2
	assert df_["Data_Movimentacao"].iloc[0] == date(2025, 8, 25)
	assert pd.isna(df_["Data_Movimentacao"].iloc[1])


@pytest.mark.parametrize("case", CASES, ids=IDS)
def test_read_raises_contract_error_on_a_missing_column(
	case: VlmoCase, monkeypatch: pytest.MonkeyPatch
) -> None:
	"""A member missing a required column fails before any typing is applied.

	Parameters
	----------
	case : VlmoCase
		The reader spec under test.
	monkeypatch : pytest.MonkeyPatch
		Fixture used to replace the download boundary.
	"""
	list_cols = list(case.cls_contract.tuple_required)[:-1]
	str_csv = _csv_text(list_cols, [[_value_for(c) for c in list_cols]])
	_patch(monkeypatch, _both_members({f"{case.str_stem}_2025.csv": str_csv}))

	with pytest.raises(ContractError):
		case.cls_reader(date_ref=DATE_REF).read()


@pytest.mark.parametrize("case", CASES, ids=IDS)
def test_read_stamps_provenance(case: VlmoCase, monkeypatch: pytest.MonkeyPatch) -> None:
	"""Each frame carries its own source key and the shared archive URL.

	Parameters
	----------
	case : VlmoCase
		The reader spec under test.
	monkeypatch : pytest.MonkeyPatch
		Fixture used to replace the download boundary.
	"""
	_patch(monkeypatch, _both_members())

	df_ = case.cls_reader(date_ref=DATE_REF).read()

	assert df_["source_key"].iloc[0] == case.cls_contract.str_source_key
	assert df_["url"].iloc[0] == URL
	assert pd.notna(df_["content_hash"].iloc[0])


def test_read_persists_the_shared_raw_zip(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
	"""``path_raw`` keeps the one archive both readers share.

	Parameters
	----------
	monkeypatch : pytest.MonkeyPatch
		Fixture used to replace the download boundary.
	tmp_path : pathlib.Path
		Pytest-provided throwaway directory standing in for the bronze landing zone.
	"""
	_patch(monkeypatch, _both_members())
	path_raw = tmp_path / "bronze"

	VlmoCiaAbertaReader(date_ref=DATE_REF, path_raw=path_raw).read()

	assert (path_raw / "vlmo_cia_aberta_2025.zip").exists()


def test_meta_url_is_the_zip_and_the_txt_does_not_exist() -> None:
	"""VLMO's META is a ``.zip`` — the exact inverse of sibling IPE's loose ``.txt``.

	Pinning the literal URL is what stops a "derive the name" rule: `meta_vlmo_cia_aberta.txt`
	returns 404, while for IPE the `.txt` is the only form that exists. Four different spellings
	are in use across the seven `CIA_ABERTA/DOC` datasets.
	"""
	assert MetaVlmoCiaAbertaReader._META_URL == (
		"https://dados.cvm.gov.br/dados/CIA_ABERTA/DOC/VLMO/META/meta_vlmo_cia_aberta.zip"
	)
	assert MetaVlmoCiaAbertaReader._META_URL.endswith(".zip")
	assert MetaVlmoCiaAbertaReader._CONTRACT.str_source_key == "meta_vlmo_cia_aberta"
