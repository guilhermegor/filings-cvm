"""Unit tests for the CIA_ABERTA/DOC/IPE reader (`cia_aberta/doc/ipe/`).

``IpeCiaAbertaReader`` reads a **single-member ZIP** partitioned by **year** and returns the index
of the *Informações Periódicas e Eventuais* a listed company filed with CVM. Only
``Data_Referencia`` and ``Data_Entrega`` become ``date``; everything else — ``Codigo_CVM``,
``Versao``, ``Link_Download`` — stays exact source text.

Every test below except one builds its input from ``IPE_CIA_ABERTA.tuple_required``, so it is a
tautology: it asserts the contract we wrote. The exception is
:func:`test_contract_matches_the_published_header`, which compares the contract against the
**verbatim header bytes CVM publishes** (``tests/fixtures/ipe_cia_aberta/``) — the one assertion
here whose expected value we did not author. See ``tests/CLAUDE.md``.

Mock the single I/O boundary (``download_file``); no network (the autouse guard in ``conftest.py``
also blocks any real socket).
"""

from datetime import date
import io
from pathlib import Path
import zipfile

import pandas as pd
import pytest

from filings_cvm._internal.config.contracts import IPE_CIA_ABERTA
from filings_cvm._internal.utils.tabular_reader import ContractError
from filings_cvm.ingestion.cia_aberta import IpeCiaAbertaReader, MetaIpeCiaAbertaReader


VALID_CNPJ = "11.222.333/0001-81"
# CVM's own placeholder for a foreign issuer with no Brazilian CNPJ (44 rows of 49,277 in 2025).
PLACEHOLDER_CNPJ = "00.000.000/0000-00"

DATE_REF = date(2025, 6, 15)
STEM = "ipe_cia_aberta_2025"
MODULE = "filings_cvm.ingestion.cia_aberta.doc.ipe.ipe"
URL = "https://dados.cvm.gov.br/dados/CIA_ABERTA/DOC/IPE/DADOS/ipe_cia_aberta_2025.zip"
LINK = (
	"https://www.rad.cvm.gov.br/ENET/frmDownloadDocumento.aspx"
	"?Tela=ext&descTipo=IPE&CodigoInstituicao=1&numProtocolo=1417971"
)
PATH_FIXTURES = Path(__file__).resolve().parents[1] / "fixtures" / "ipe_cia_aberta"


def _value_for(str_col: str, str_cnpj: str = VALID_CNPJ) -> str:
	"""Return a plausible source value for one column, by name."""
	if str_col == "CNPJ_Companhia":
		return str_cnpj
	if str_col in ("Data_Referencia", "Data_Entrega"):
		return "2025-08-25"
	if str_col == "Codigo_CVM":
		return "027030"
	if str_col == "Versao":
		return "1"
	if str_col == "Link_Download":
		return LINK
	return "x"


def _row(str_cnpj: str = VALID_CNPJ) -> list[str]:
	"""One valid row in the contract's column order."""
	return [_value_for(c, str_cnpj) for c in IPE_CIA_ABERTA.tuple_required]


def _csv_text(list_cols: list[str], list_rows: list[list[str]]) -> str:
	"""Serialise a header + rows into the CVM ``;``-separated CSV shape."""
	return "\n".join([";".join(list_cols), *[";".join(r) for r in list_rows]]) + "\n"


def _default_csv() -> str:
	"""Header + one valid row."""
	return _csv_text(list(IPE_CIA_ABERTA.tuple_required), [_row()])


def _payload(str_csv: str, str_member: str = f"{STEM}.csv") -> bytes:
	"""Wrap the CSV text as the real artifact: a single-member ZIP in the source's encoding."""
	buffer = io.BytesIO()
	with zipfile.ZipFile(buffer, "w") as cls_zip:
		cls_zip.writestr(str_member, str_csv.encode("ISO-8859-1"))
	return buffer.getvalue()


def _patch(monkeypatch: pytest.MonkeyPatch, bytes_payload: bytes) -> list[str]:
	"""Patch the reader's download_file to drop ``bytes_payload``; capture requested URLs."""
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


def test_contract_matches_the_published_header() -> None:
	"""The contract equals the verbatim header CVM publishes — the non-tautological oracle.

	The fixture holds the real 2025 header bytes in the source's own ISO-8859-1 encoding. If CVM
	renames, reorders, adds or drops a column, this is the assertion that fails.
	"""
	str_line = (PATH_FIXTURES / "ipe_cia_aberta_header.csv").read_text(encoding="iso-8859-1")

	assert IPE_CIA_ABERTA.tuple_required == tuple(str_line.strip().split(";"))
	assert len(IPE_CIA_ABERTA.tuple_required) == 13


def test_read_returns_all_contract_columns(monkeypatch: pytest.MonkeyPatch) -> None:
	"""The frame carries exactly the contract's columns, plus provenance.

	Parameters
	----------
	monkeypatch : pytest.MonkeyPatch
		Fixture used to replace the download boundary.
	"""
	_patch(monkeypatch, _payload(_default_csv()))

	df_ = IpeCiaAbertaReader(date_ref=DATE_REF).read()

	assert len(df_) == 1
	assert list(df_.columns) == list(IPE_CIA_ABERTA.output_columns)


def test_read_coerces_both_date_columns(monkeypatch: pytest.MonkeyPatch) -> None:
	"""``Data_Referencia`` and ``Data_Entrega`` become pure ``date`` objects.

	Parameters
	----------
	monkeypatch : pytest.MonkeyPatch
		Fixture used to replace the download boundary.
	"""
	_patch(monkeypatch, _payload(_default_csv()))

	df_ = IpeCiaAbertaReader(date_ref=DATE_REF).read()

	for str_col in ("Data_Referencia", "Data_Entrega"):
		assert isinstance(df_[str_col].iloc[0], date)
		assert df_[str_col].iloc[0] == date(2025, 8, 25)


def test_read_requests_the_yearly_url(monkeypatch: pytest.MonkeyPatch) -> None:
	"""The dump is partitioned by **year**, so only ``date_ref.year`` selects the artifact.

	Parameters
	----------
	monkeypatch : pytest.MonkeyPatch
		Fixture used to replace the download boundary.
	"""
	list_urls = _patch(monkeypatch, _payload(_default_csv()))

	IpeCiaAbertaReader(date_ref=DATE_REF).read()

	assert list_urls == [URL]
	# A different day of the same year must resolve to the same yearly artifact.
	list_urls.clear()
	IpeCiaAbertaReader(date_ref=date(2025, 1, 1)).read()
	assert list_urls == [URL]


def test_read_returns_link_download_as_text_and_does_not_follow_it(
	monkeypatch: pytest.MonkeyPatch,
) -> None:
	"""``Link_Download`` comes back as the exact source URL string; only the ZIP is fetched.

	The reader stays thin: fetching the linked document is a downstream concern. The captured URL
	list proves the RAD link was never requested.

	Parameters
	----------
	monkeypatch : pytest.MonkeyPatch
		Fixture used to replace the download boundary.
	"""
	list_urls = _patch(monkeypatch, _payload(_default_csv()))

	df_ = IpeCiaAbertaReader(date_ref=DATE_REF).read()

	assert df_["Link_Download"].iloc[0] == LINK
	assert list_urls == [URL]
	assert not any("rad.cvm.gov.br" in str_url for str_url in list_urls)


def test_read_honours_the_all_zeros_placeholder_cnpj(monkeypatch: pytest.MonkeyPatch) -> None:
	"""A foreign issuer's ``00.000.000/0000-00`` is returned as published, never repaired.

	CVM uses that placeholder for issuers with no Brazilian CNPJ (44 of 49,277 rows in 2025). The
	contract still lists ``CNPJ_Companhia`` as a CNPJ column because the check requires *at least
	one* valid CNPJ, not all of them — so a mixed frame is valid and both values survive intact.

	Parameters
	----------
	monkeypatch : pytest.MonkeyPatch
		Fixture used to replace the download boundary.
	"""
	str_csv = _csv_text(list(IPE_CIA_ABERTA.tuple_required), [_row(), _row(PLACEHOLDER_CNPJ)])
	_patch(monkeypatch, _payload(str_csv))

	df_ = IpeCiaAbertaReader(date_ref=DATE_REF).read()

	assert list(df_["CNPJ_Companhia"]) == [VALID_CNPJ, PLACEHOLDER_CNPJ]


def test_read_rejects_a_partition_of_only_placeholder_cnpjs(
	monkeypatch: pytest.MonkeyPatch,
) -> None:
	"""A frame whose every CNPJ is the placeholder fails the coercible-type check.

	This pins the *boundary* of the "at least one valid CNPJ" rule, and documents a known
	sharp edge: the check is value-presence based, so a hypothetical partition containing
	**only** foreign issuers would raise rather than return rows. Real partitions are nowhere
	near that (2025: 49,233 valid vs 44 placeholders), but the same shape is what bit the CRI
	header-only members — hence pinned rather than left implicit.

	Parameters
	----------
	monkeypatch : pytest.MonkeyPatch
		Fixture used to replace the download boundary.
	"""
	str_csv = _csv_text(list(IPE_CIA_ABERTA.tuple_required), [_row(PLACEHOLDER_CNPJ)])
	_patch(monkeypatch, _payload(str_csv))

	with pytest.raises(ContractError, match="no valid CNPJ"):
		IpeCiaAbertaReader(date_ref=DATE_REF).read()


def test_read_keeps_codigo_cvm_and_versao_as_text(monkeypatch: pytest.MonkeyPatch) -> None:
	"""Identifiers stay text: a leading zero survives and ``Versao`` is not an int.

	``Codigo_CVM`` is ``Domínio: Numérico`` and ``Versao`` is ``smallint`` in the META, but both
	are identifiers/counters rather than quantities — typing them numerically would drop the
	zero-padding this assertion pins.

	Parameters
	----------
	monkeypatch : pytest.MonkeyPatch
		Fixture used to replace the download boundary.
	"""
	_patch(monkeypatch, _payload(_default_csv()))

	df_ = IpeCiaAbertaReader(date_ref=DATE_REF).read()

	assert df_["Codigo_CVM"].iloc[0] == "027030"
	assert df_["Versao"].iloc[0] == "1"
	assert isinstance(df_["Versao"].iloc[0], str)


def test_read_raises_contract_error_on_a_missing_column(
	monkeypatch: pytest.MonkeyPatch,
) -> None:
	"""A dump missing a required column fails before any typing is applied.

	Parameters
	----------
	monkeypatch : pytest.MonkeyPatch
		Fixture used to replace the download boundary.
	"""
	list_cols = [c for c in IPE_CIA_ABERTA.tuple_required if c != "Link_Download"]
	str_csv = _csv_text(list_cols, [[_value_for(c) for c in list_cols]])
	_patch(monkeypatch, _payload(str_csv))

	with pytest.raises(ContractError):
		IpeCiaAbertaReader(date_ref=DATE_REF).read()


def test_read_persists_the_raw_zip_when_path_raw_is_given(
	monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
	"""``path_raw`` keeps the untouched ZIP on disk for a datalake's bronze layer.

	Parameters
	----------
	monkeypatch : pytest.MonkeyPatch
		Fixture used to replace the download boundary.
	tmp_path : pathlib.Path
		Pytest-provided throwaway directory standing in for the bronze landing zone.
	"""
	_patch(monkeypatch, _payload(_default_csv()))
	path_raw = tmp_path / "bronze"

	IpeCiaAbertaReader(date_ref=DATE_REF, path_raw=path_raw).read()

	assert (path_raw / f"{STEM}.zip").exists()


def test_read_stamps_provenance(monkeypatch: pytest.MonkeyPatch) -> None:
	"""The frame carries the six provenance columns, with this reader's source key and URL.

	Parameters
	----------
	monkeypatch : pytest.MonkeyPatch
		Fixture used to replace the download boundary.
	"""
	_patch(monkeypatch, _payload(_default_csv()))

	df_ = IpeCiaAbertaReader(date_ref=DATE_REF).read()

	assert df_["source_key"].iloc[0] == "ipe_cia_aberta"
	assert df_["url"].iloc[0] == URL
	assert pd.notna(df_["content_hash"].iloc[0])


def test_meta_url_is_the_loose_txt_not_a_derived_zip() -> None:
	"""IPE's META is a loose ``.txt``, breaking the ``.zip`` pattern of its six DOC siblings.

	Across ``CIA_ABERTA/DOC`` CVM uses four different META spellings (``meta_<ds>_cia_aberta.zip``,
	``meta_<ds>_cia_aberta_txt.zip``, ``fca_cia_aberta.zip`` with no ``meta_`` prefix, and this
	``.txt``). Pinning the literal URL is what stops a "derive the name" rule from 404-ing or
	silently fetching a different dataset's spec.
	"""
	assert MetaIpeCiaAbertaReader._META_URL == (
		"https://dados.cvm.gov.br/dados/CIA_ABERTA/DOC/IPE/META/meta_ipe_cia_aberta.txt"
	)
	assert MetaIpeCiaAbertaReader._META_URL.endswith(".txt")
	assert MetaIpeCiaAbertaReader._CONTRACT.str_source_key == "meta_ipe_cia_aberta"
