"""Unit tests for ``AtoDeclrReader`` (ATO_DECLR/INTERMED) and its META reader.

The download boundary is mocked; no network. The data rows below are synthetic (the real file
carries natural persons' names and CPFs, so only its header is committed as a fixture).
"""

from datetime import date
from pathlib import Path

import pytest

from filings_cvm import RetryPolicy
from filings_cvm._internal.config.contracts import ATO_DECLR, META_ATO_DECLR
from filings_cvm._internal.utils.tabular_reader import ContractError
from filings_cvm.ingestion.ato_declr import AtoDeclrReader, MetaAtoDeclrReader


_MODULE = "filings_cvm.ingestion.ato_declr.intermed.ato_declr"
_PATH_FIXTURE = (
	Path(__file__).resolve().parents[1] / "fixtures" / "ato_declr" / "ato_declr_header.csv"
)
_HEADER = ";".join(ATO_DECLR.tuple_required)

# A CNPJ row, a CPF row, an unmasked 13-digit value, a blank, and a Latin-1 accent.
_ROWS = (
	"07004;2002-10-29;HOTÉIS LTDA;2002-10-31;64.186.679/0001-38;https://x/a.doc;",
	"07005;2002-10-30;PESSOA FISICA;2002-10-31;195.018.446-87;https://x/b.doc;"
	"EXCLUÍDO PELO ATO DECLARATÓRIO CVM N. 9415",
	"07006;2002-10-30;SEM MASCARA;2002-11-05;2846424000105;https://x/c.doc;",
	"25210;2026-05-12;ONIL;2026-05-14;;https://x/d.pdf;",
)


def _patch(monkeypatch: pytest.MonkeyPatch, str_csv: str) -> list[str]:
	"""Replace the download boundary with a write of ``str_csv``; return requested URLs."""
	list_urls: list[str] = []

	def _fake(
		str_url: str, path_dest: Path, int_timeout_s: int = 60, retry_policy: object = None
	) -> Path:
		list_urls.append(str_url)
		path_dest.parent.mkdir(parents=True, exist_ok=True)
		path_dest.write_bytes(str_csv.encode("ISO-8859-1"))
		return path_dest

	monkeypatch.setattr(f"{_MODULE}.download_file", _fake)
	return list_urls


def _csv() -> str:
	return "\n".join((_HEADER, *_ROWS)) + "\n"


def test_contract_matches_the_published_header() -> None:
	"""The contract equals the verbatim header CVM published (the pinned oracle)."""
	str_line = _PATH_FIXTURE.read_text(encoding="ISO-8859-1").strip()

	assert ATO_DECLR.tuple_required == tuple(str_line.split(";"))


def test_read_types_dates_and_keeps_identifiers_as_text(monkeypatch: pytest.MonkeyPatch) -> None:
	"""Dates become ``date``; the act number keeps its leading zero; blanks stay blank."""
	list_urls = _patch(monkeypatch, _csv())

	df_ = AtoDeclrReader().read()

	assert list_urls == ["https://dados.cvm.gov.br/dados/ATO_DECLR/INTERMED/DADOS/ato_declr.csv"]
	assert list(df_.columns) == list(ATO_DECLR.output_columns)
	assert df_["Data_Ato_Declaratorio"].iloc[0] == date(2002, 10, 29)
	assert df_["Data_Publicacao_DOU"].iloc[3] == date(2026, 5, 14)
	assert df_["Numero_Ato_Declaratorio"].iloc[0] == "07004"
	assert df_["Denominacao"].iloc[0] == "HOTÉIS LTDA"
	assert df_["CNPJ_CPF"].iloc[1] == "195.018.446-87"
	assert df_["CNPJ_CPF"].iloc[2] == "2846424000105"
	assert df_["CNPJ_CPF"].isna().iloc[3]


def test_cnpj_cpf_is_not_a_cnpj_column() -> None:
	"""The column mixes CPFs, so it must stay out of ``tuple_cnpj_cols``."""
	assert ATO_DECLR.tuple_cnpj_cols == ()


def test_read_raises_on_missing_column(monkeypatch: pytest.MonkeyPatch) -> None:
	"""Dropping a declared column violates the contract."""
	list_cols = list(ATO_DECLR.tuple_required[:-1])
	_patch(monkeypatch, ";".join(list_cols) + "\n" + ";".join("x" for _ in list_cols) + "\n")

	with pytest.raises(ContractError):
		AtoDeclrReader().read()


def test_read_persists_raw_csv(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
	"""With ``path_raw`` the raw CSV survives the read."""
	_patch(monkeypatch, _csv())

	AtoDeclrReader(path_raw=tmp_path / "bronze").read()

	assert (tmp_path / "bronze" / "ato_declr.csv").is_file()


def test_retry_policy_default_and_override() -> None:
	"""The reader declares its own policy and lets an instance override it."""
	cls_custom = RetryPolicy(int_max_attempts=8)

	assert isinstance(AtoDeclrReader._RETRY_POLICY, RetryPolicy)
	assert AtoDeclrReader()._retry_policy is AtoDeclrReader._RETRY_POLICY
	assert AtoDeclrReader(retry_policy=cls_custom)._retry_policy is cls_custom


def test_meta_reader_points_at_the_fixed_txt() -> None:
	"""META is a flat ``.txt`` at a constant URL under the same portal root."""
	assert MetaAtoDeclrReader._META_URL == (
		"https://dados.cvm.gov.br/dados/ATO_DECLR/INTERMED/META/meta_ato_declr.txt"
	)
	assert MetaAtoDeclrReader._CONTRACT is META_ATO_DECLR
