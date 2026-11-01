"""Unit tests for the FI/DOC/ENTREGA readers.

``fi_entrega_documento_AAAAMM.zip`` is a two-member ZIP partitioned by month (series ``202501``
onward). Both members share one 11-column header in every month measured, so there is one regime
and no ``Pre*`` reader; each member has its own reader and contract.

The oracle is the verbatim header bytes CVM publishes (``tests/fixtures/entrega_fi``); every other
test builds input from the contract and is a tautology by construction.
"""

from datetime import date
from pathlib import Path
import zipfile

import pytest

from filings_cvm._internal.config.contracts import ENTREGA_FI, ENTREGA_FI_DIARIO
from filings_cvm._internal.utils.tabular_reader import ContractError, FileContract
from filings_cvm.ingestion.fi import (
	EntregaFiDiarioReader,
	EntregaFiReader,
	MetaEntregaFiReader,
)


VALID_CNPJ = "11222333000181"
REF = date(2025, 6, 15)
URL = "https://dados.cvm.gov.br/dados/FI/DOC/ENTREGA/DADOS/fi_entrega_documento_202506.zip"
PATH_FIXTURES = Path(__file__).resolve().parents[1] / "fixtures" / "entrega_fi"
STR_MEMBER = "fi_entrega_documento_202506.csv"
STR_MEMBER_DIARIO = "fi_entrega_documento_diario_202506.csv"

DICT_ROW = {
	"Tipo_Fundo_Classe": "CLASSES - FIF",
	"CNPJ_Fundo_Classe": VALID_CNPJ,
	"ID_Subclasse": "",
	"Tipo_Documento": "DIÁRIO FUNDOS",
	"Data_Inicio_Competencia": "2025-06-02",
	"Data_Fim_Competencia": "2025-06-02",
	"ID_Documento": "00168398969",
	"Data_Hora_Entrega": "2025-06-03 14:57:33.537",
	"Tipo_Apresentacao": "Apresentação",
	"Ativo": "N",
	"Sistema_Origem": "CVMWEB",
}


def _csv(tuple_cols: tuple[str, ...]) -> str:
	"""Serialise header + one row in CVM's ``;`` / CRLF shape."""
	return "\r\n".join([";".join(tuple_cols), ";".join(DICT_ROW[c] for c in tuple_cols)]) + "\r\n"


def _patch_download(monkeypatch: pytest.MonkeyPatch, dict_members: dict[str, str]) -> list[str]:
	"""Patch the shared base's download boundary to write a real ZIP of ``dict_members``."""
	list_urls: list[str] = []

	def _fake(
		str_url: str, path_dest: Path, int_timeout_s: int = 60, retry_policy: object = None
	) -> Path:
		list_urls.append(str_url)
		path_dest.parent.mkdir(parents=True, exist_ok=True)
		with zipfile.ZipFile(path_dest, "w") as zf:
			for str_name, str_text in dict_members.items():
				zf.writestr(str_name, str_text.encode("ISO-8859-1"))
		return path_dest

	monkeypatch.setattr(
		"filings_cvm.ingestion.fi.doc.entrega._base_entrega_reader.download_file", _fake
	)
	return list_urls


def _both(monkeypatch: pytest.MonkeyPatch, **dict_over: str) -> list[str]:
	"""Patch a ZIP whose two members are told apart by ``Tipo_Documento``."""
	tuple_cols = ENTREGA_FI.tuple_required
	DICT_ROW_BAK = dict(DICT_ROW)
	try:
		DICT_ROW["Tipo_Documento"] = "BALANCETE"
		str_all = _csv(tuple_cols)
		DICT_ROW["Tipo_Documento"] = "DIÁRIO FUNDOS"
		str_daily = _csv(tuple_cols)
	finally:
		DICT_ROW.update(DICT_ROW_BAK)
	return _patch_download(monkeypatch, {STR_MEMBER: str_all, STR_MEMBER_DIARIO: str_daily})


@pytest.mark.parametrize(
	("contract", "str_file"),
	[
		(ENTREGA_FI, "entrega_fi_header.csv"),
		(ENTREGA_FI_DIARIO, "entrega_fi_diario_header.csv"),
	],
)
def test_contract_matches_the_published_header(contract: FileContract, str_file: str) -> None:
	"""Each contract equals the verbatim header CVM publishes for its member."""
	str_line = (PATH_FIXTURES / str_file).read_text(encoding="iso-8859-1")

	assert contract.tuple_required == tuple(str_line.strip().split(";"))
	assert len(contract.tuple_required) == 11


def test_members_share_a_header_but_not_provenance() -> None:
	"""Same 11 names (measured), distinct ``source_key``; only the CNPJ column is declared."""
	assert ENTREGA_FI.tuple_required == ENTREGA_FI_DIARIO.tuple_required
	assert ENTREGA_FI.str_source_key != ENTREGA_FI_DIARIO.str_source_key
	assert ENTREGA_FI.tuple_cnpj_cols == ("CNPJ_Fundo_Classe",)


def test_a_month_before_the_series_is_refused() -> None:
	"""202412 predates the series; fail before downloading 20 MB."""
	with pytest.raises(ValueError, match="no file before 202501"):
		EntregaFiReader(date(2024, 12, 31))


def test_the_first_month_is_accepted() -> None:
	"""202501 is the first published month."""
	assert EntregaFiDiarioReader(date(2025, 1, 1)) is not None


def test_each_reader_reads_its_own_member(monkeypatch: pytest.MonkeyPatch) -> None:
	"""The all-documents reader never returns the daily member, and vice versa."""
	list_urls = _both(monkeypatch)

	df_all = EntregaFiReader(REF).read()
	df_daily = EntregaFiDiarioReader(REF).read()

	assert list_urls == [URL, URL]
	assert df_all["Tipo_Documento"].iloc[0] == "BALANCETE"
	assert df_daily["Tipo_Documento"].iloc[0] == "DIÁRIO FUNDOS"
	assert df_all["source_key"].iloc[0] == "entrega_fi"
	assert df_daily["source_key"].iloc[0] == "entrega_fi_diario"


def test_types_dates_are_dates_and_the_rest_is_exact_text(
	monkeypatch: pytest.MonkeyPatch,
) -> None:
	"""Competency dates become ``date``; id (zero-padded), timestamp and empty cell stay text."""
	_both(monkeypatch)

	df_ = EntregaFiDiarioReader(REF).read()

	assert df_["Data_Inicio_Competencia"].iloc[0] == date(2025, 6, 2)
	assert df_["ID_Documento"].iloc[0] == "00168398969"
	assert df_["Data_Hora_Entrega"].iloc[0] == "2025-06-03 14:57:33.537"
	assert df_["CNPJ_Fundo_Classe"].iloc[0] == VALID_CNPJ
	assert df_["ID_Subclasse"].isna().iloc[0]


def test_path_raw_keeps_the_zip(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
	"""``path_raw`` persists the untouched ZIP."""
	_both(monkeypatch)

	EntregaFiReader(REF, path_raw=tmp_path).read()

	assert (tmp_path / "fi_entrega_documento_202506.zip").exists()


def test_a_missing_member_raises(monkeypatch: pytest.MonkeyPatch) -> None:
	"""A ZIP lacking the daily member is refused by the daily reader."""
	_patch_download(monkeypatch, {STR_MEMBER: _csv(ENTREGA_FI.tuple_required)})

	with pytest.raises(ValueError):
		EntregaFiDiarioReader(REF).read()


def test_a_header_violating_the_contract_raises(monkeypatch: pytest.MonkeyPatch) -> None:
	"""A member missing a contract column fails loudly."""
	_patch_download(monkeypatch, {STR_MEMBER: _csv(ENTREGA_FI.tuple_required[:-1])})

	with pytest.raises(ContractError):
		EntregaFiReader(REF).read()


def test_the_meta_url_is_the_flat_txt() -> None:
	"""The META is the flat ``meta_fi_entrega_documento.txt``, pinned and never derived."""
	assert MetaEntregaFiReader._META_URL.endswith("/ENTREGA/META/meta_fi_entrega_documento.txt")
	assert MetaEntregaFiReader._CONTRACT.str_source_key == "meta_entrega_fi"
