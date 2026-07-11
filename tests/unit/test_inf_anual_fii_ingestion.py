"""Unit tests for the 12 Informe Anual FII readers.

One parameterized module covers the uniform family: a single in-memory fixture ZIP holds all 12
members for one reference year, and each reader is asserted to select **its own** member (columns
match its contract, not a sibling's), coerce its date columns, and honour the shared base behaviour
(yearly partition, ``path_raw`` persistence, contract validation, the retry standard).

Two dataset-specific guarantees get their own tests: ``complemento``'s ``Link_Download_Anexo`` is
returned as text and **never followed**, and the ``CPF`` on ``diretor_responsavel`` /
``representante_cotista`` stays exact text (never CNPJ-validated). Mock the single I/O boundary
(``download_file``); no network (the autouse guard in ``conftest.py`` also blocks any real socket).
"""

from datetime import date
import io
from pathlib import Path
import zipfile

import pytest

from filings_cvm import RetryPolicy
from filings_cvm._internal.config.ports.ingestion_reader import IngestionReader
from filings_cvm._internal.utils.tabular_reader import ContractError
from filings_cvm.ingestion import (
	InfAnualFiiAtivoAdquiridoReader,
	InfAnualFiiAtivoTransacaoReader,
	InfAnualFiiAtivoValorContabilReader,
	InfAnualFiiComplementoReader,
	InfAnualFiiDiretorResponsavelReader,
	InfAnualFiiDistribuicaoCotistasReader,
	InfAnualFiiExperienciaProfissionalReader,
	InfAnualFiiGeralReader,
	InfAnualFiiPrestadorServicoReader,
	InfAnualFiiProcessoReader,
	InfAnualFiiProcessoSemelhanteReader,
	InfAnualFiiRepresentanteCotistaReader,
)


VALID_CNPJ = "11.222.333/0001-81"
YEAR = "2025"
REF = date(2025, 6, 15)

_ANEXO = "https://fnet.bmfbovespa.com.br/fnet/publico/downloadDocumento?id=999999"
_CPF = "123.456.789-09"

ALL_READERS: tuple[type[IngestionReader], ...] = (
	InfAnualFiiGeralReader,
	InfAnualFiiComplementoReader,
	InfAnualFiiAtivoAdquiridoReader,
	InfAnualFiiAtivoTransacaoReader,
	InfAnualFiiAtivoValorContabilReader,
	InfAnualFiiDistribuicaoCotistasReader,
	InfAnualFiiDiretorResponsavelReader,
	InfAnualFiiExperienciaProfissionalReader,
	InfAnualFiiPrestadorServicoReader,
	InfAnualFiiProcessoReader,
	InfAnualFiiProcessoSemelhanteReader,
	InfAnualFiiRepresentanteCotistaReader,
)


def _member_name(cls: type[IngestionReader], str_year: str = YEAR) -> str:
	"""Return the archive member name for ``cls`` in the given reference year."""
	return f"{cls._MEMBER_STEM}_{str_year}.csv"  # type: ignore[attr-defined]


def _value_for(cls: type[IngestionReader], str_col: str) -> str:
	"""Return the fixture value for one column of ``cls``'s member."""
	if str_col == "CNPJ_Fundo_Classe":
		return VALID_CNPJ
	if str_col in cls._DATE_COLS:  # type: ignore[attr-defined]
		return "2025-12-31"
	if str_col == "Link_Download_Anexo":
		return _ANEXO
	if str_col == "CPF":
		return _CPF
	return "x"


def _member_csv(cls: type[IngestionReader]) -> str:
	"""Header + one valid row for ``cls``'s member, built from its contract."""
	list_cols = list(cls._CONTRACT.tuple_required)  # type: ignore[attr-defined]
	list_vals = [_value_for(cls, str_col) for str_col in list_cols]
	return ";".join(list_cols) + "\n" + ";".join(list_vals) + "\n"


def _all_members(str_year: str = YEAR) -> dict[str, str]:
	"""Build the full 12-member fixture archive for a year, one valid row each."""
	return {_member_name(cls, str_year): _member_csv(cls) for cls in ALL_READERS}


def _zip_bytes(dict_members: dict[str, str]) -> bytes:
	"""Build an in-memory ZIP holding each ``name → csv text`` member."""
	buffer = io.BytesIO()
	with zipfile.ZipFile(buffer, "w") as cls_zip:
		for str_name, str_text in dict_members.items():
			cls_zip.writestr(str_name, str_text.encode("ISO-8859-1"))
	return buffer.getvalue()


def _patch_download(monkeypatch: pytest.MonkeyPatch, payload: bytes) -> list[str]:
	"""Patch the base reader's download_file boundary; return a list capturing requested URLs."""
	list_urls: list[str] = []

	def _fake_download(
		str_url: str, path_dest: Path, int_timeout_s: int = 60, retry_policy: object = None
	) -> Path:
		list_urls.append(str_url)
		path_dest.parent.mkdir(parents=True, exist_ok=True)
		path_dest.write_bytes(payload)
		return path_dest

	monkeypatch.setattr(
		"filings_cvm.ingestion.fii.doc.inf_anual._base_inf_anual_fii_reader.download_file",
		_fake_download,
	)
	return list_urls


@pytest.mark.parametrize("cls", ALL_READERS, ids=lambda c: c.__name__)
def test_read_selects_its_own_member_with_all_columns(
	cls: type[IngestionReader], monkeypatch: pytest.MonkeyPatch
) -> None:
	"""Each reader returns exactly its member's columns from the shared 12-member archive.

	Parameters
	----------
	cls : type[IngestionReader]
		The reader under test.
	monkeypatch : pytest.MonkeyPatch
		Fixture used to replace the download boundary.
	"""
	_patch_download(monkeypatch, _zip_bytes(_all_members()))

	df_ = cls(date_ref=REF).read()

	assert len(df_) == 1
	assert list(df_.columns) == list(cls._CONTRACT.output_columns)  # type: ignore[attr-defined]


@pytest.mark.parametrize("cls", ALL_READERS, ids=lambda c: c.__name__)
def test_read_coerces_every_declared_date_column(
	cls: type[IngestionReader], monkeypatch: pytest.MonkeyPatch
) -> None:
	"""Every declared date column becomes a pure ``date`` object.

	Parameters
	----------
	cls : type[IngestionReader]
		The reader under test.
	monkeypatch : pytest.MonkeyPatch
		Fixture used to replace the download boundary.
	"""
	_patch_download(monkeypatch, _zip_bytes(_all_members()))

	df_ = cls(date_ref=REF).read()

	for str_col in cls._DATE_COLS:  # type: ignore[attr-defined]
		assert df_[str_col].iloc[0] == date(2025, 12, 31)


@pytest.mark.parametrize("cls", ALL_READERS, ids=lambda c: c.__name__)
def test_date_ref_selects_the_year(
	cls: type[IngestionReader], monkeypatch: pytest.MonkeyPatch
) -> None:
	"""Only ``date_ref.year`` reaches the URL — the dump is one archive per year.

	Parameters
	----------
	cls : type[IngestionReader]
		The reader under test.
	monkeypatch : pytest.MonkeyPatch
		Fixture used to replace the download boundary.
	"""
	list_urls = _patch_download(monkeypatch, _zip_bytes(_all_members()))

	cls(date_ref=date(2025, 1, 2)).read()

	assert list_urls == [
		"https://dados.cvm.gov.br/dados/FII/DOC/INF_ANUAL/DADOS/inf_anual_fii_2025.zip"
	]


def test_complemento_returns_the_anexo_link_as_text_and_does_not_follow_it(
	monkeypatch: pytest.MonkeyPatch,
) -> None:
	"""``Link_Download_Anexo`` is exact text; the only URL fetched is the yearly ZIP itself.

	The reader parses the filing — it must not download the linked annex.

	Parameters
	----------
	monkeypatch : pytest.MonkeyPatch
		Fixture used to replace the download boundary.
	"""
	list_urls = _patch_download(monkeypatch, _zip_bytes(_all_members()))

	df_ = InfAnualFiiComplementoReader(date_ref=REF).read()

	assert df_["Link_Download_Anexo"].iloc[0] == _ANEXO
	assert isinstance(df_["Link_Download_Anexo"].iloc[0], str)
	assert not any("fnet" in str_url for str_url in list_urls)


@pytest.mark.parametrize(
	"cls",
	(InfAnualFiiDiretorResponsavelReader, InfAnualFiiRepresentanteCotistaReader),
	ids=lambda c: c.__name__,
)
def test_cpf_is_kept_as_exact_text_and_never_cnpj_validated(
	cls: type[IngestionReader], monkeypatch: pytest.MonkeyPatch
) -> None:
	"""``CPF`` is a natural person's id: exact text, and never in the contract's CNPJ columns.

	Parameters
	----------
	cls : type[IngestionReader]
		The reader under test.
	monkeypatch : pytest.MonkeyPatch
		Fixture used to replace the download boundary.
	"""
	_patch_download(monkeypatch, _zip_bytes(_all_members()))

	df_ = cls(date_ref=REF).read()

	assert df_["CPF"].iloc[0] == _CPF
	assert isinstance(df_["CPF"].iloc[0], str)
	assert "CPF" not in cls._CONTRACT.tuple_cnpj_cols  # type: ignore[attr-defined]


def test_read_raises_value_error_for_a_year_absent_from_the_archive(
	monkeypatch: pytest.MonkeyPatch,
) -> None:
	"""A reader built for a year whose member is absent raises a clear ValueError.

	Parameters
	----------
	monkeypatch : pytest.MonkeyPatch
		Fixture used to replace the download boundary.
	"""
	_patch_download(monkeypatch, _zip_bytes(_all_members()))

	with pytest.raises(ValueError, match="inf_anual_fii_geral_2024.csv"):
		InfAnualFiiGeralReader(date_ref=date(2024, 3, 1)).read()


def test_read_raises_contract_error_on_missing_required_column(
	monkeypatch: pytest.MonkeyPatch,
) -> None:
	"""Dropping a declared column from a member violates its contract.

	Parameters
	----------
	monkeypatch : pytest.MonkeyPatch
		Fixture used to replace the download boundary.
	"""
	dict_members = _all_members()
	cls = InfAnualFiiAtivoValorContabilReader
	list_cols = [c for c in cls._CONTRACT.tuple_required if c != "Valor_Justo"]
	dict_members[_member_name(cls)] = (
		";".join(list_cols) + "\n" + ";".join("x" for _ in list_cols) + "\n"
	)
	_patch_download(monkeypatch, _zip_bytes(dict_members))

	with pytest.raises(ContractError):
		cls(date_ref=REF).read()


def test_read_persists_whole_archive_when_path_raw_is_given(
	monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
	"""With ``path_raw`` set, the ZIP and all 12 members survive a single reader's read.

	Parameters
	----------
	monkeypatch : pytest.MonkeyPatch
		Fixture used to replace the download boundary.
	tmp_path : pathlib.Path
		Pytest-provided scratch directory standing in for the bronze layer.
	"""
	_patch_download(monkeypatch, _zip_bytes(_all_members()))
	path_raw = tmp_path / "bronze"

	InfAnualFiiGeralReader(date_ref=REF, path_raw=path_raw).read()

	assert (path_raw / f"inf_anual_fii_{YEAR}.zip").is_file()
	assert {p.name for p in path_raw.glob("*.csv")} == set(_all_members())


def test_read_keeps_money_column_as_exact_source_text(monkeypatch: pytest.MonkeyPatch) -> None:
	"""A money column (``Valor``) keeps its exact CVM text, never a lossy float.

	Parameters
	----------
	monkeypatch : pytest.MonkeyPatch
		Fixture used to replace the download boundary.
	"""
	dict_members = _all_members()
	cls = InfAnualFiiAtivoValorContabilReader
	list_cols = list(cls._CONTRACT.tuple_required)
	list_vals = ["1234567.89" if c == "Valor" else _value_for(cls, c) for c in list_cols]
	dict_members[_member_name(cls)] = ";".join(list_cols) + "\n" + ";".join(list_vals) + "\n"
	_patch_download(monkeypatch, _zip_bytes(dict_members))

	df_ = cls(date_ref=REF).read()

	assert df_["Valor"].iloc[0] == "1234567.89"
	assert isinstance(df_["Valor"].iloc[0], str)


@pytest.mark.parametrize("cls", ALL_READERS, ids=lambda c: c.__name__)
def test_reader_follows_the_retry_policy_standard(cls: type[IngestionReader]) -> None:
	"""Each reader declares its own ``_RETRY_POLICY`` and lets an instance override it.

	Parameters
	----------
	cls : type[IngestionReader]
		The reader under test.
	"""
	cls_custom = RetryPolicy(int_max_attempts=8)

	assert isinstance(cls._RETRY_POLICY, RetryPolicy)  # type: ignore[attr-defined]
	assert cls(date_ref=REF)._retry_policy is cls._RETRY_POLICY  # type: ignore[attr-defined]
	assert cls(date_ref=REF, retry_policy=cls_custom)._retry_policy is cls_custom
