"""Unit tests for the 3 Informe Mensal FII readers.

One parameterized module covers the uniform family: a single in-memory fixture ZIP holds all 3
members for one reference **year**, and each reader is asserted to select **its own** member
(columns match its contract, not a sibling's), coerce its date columns, and honour the shared base
behaviour (year partition, ``path_raw`` persistence, contract validation).

The year partition gets its own tests: the dump is ``inf_mensal_fii_AAAA.zip`` even though it is
the *monthly* report, so ``date_ref`` selects the **year** and the month/day are ignored — the trap
this dataset invites. Mock the single I/O boundary (``download_file``); no network.
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
	InfMensalFiiAtivoPassivoReader,
	InfMensalFiiComplementoReader,
	InfMensalFiiGeralReader,
)


# CNPJ valid under the repo's ASCII-48 mod-11 routine; the contract's CNPJ check accepts it.
VALID_CNPJ = "11.222.333/0001-81"

# Fixed reference year for the fixture; the member names embed it (``…_2025.csv``).
YEAR = "2025"
REF = date(2025, 6, 15)

ALL_READERS: tuple[type[IngestionReader], ...] = (
	InfMensalFiiGeralReader,
	InfMensalFiiAtivoPassivoReader,
	InfMensalFiiComplementoReader,
)


def _member_name(cls: type[IngestionReader], str_year: str = YEAR) -> str:
	"""Return the archive member name for ``cls`` in the given reference year."""
	return f"{cls._MEMBER_STEM}_{str_year}.csv"  # type: ignore[attr-defined]


def _member_csv(cls: type[IngestionReader]) -> str:
	"""Header + one valid row for ``cls``'s member, built from its contract."""
	list_cols = list(cls._CONTRACT.tuple_required)  # type: ignore[attr-defined]
	list_vals = [
		VALID_CNPJ
		if str_col == "CNPJ_Fundo_Classe"
		else "2025-06-01"
		if str_col in cls._DATE_COLS  # type: ignore[attr-defined]
		else "x"
		for str_col in list_cols
	]
	return ";".join(list_cols) + "\n" + ";".join(list_vals) + "\n"


def _all_members(str_year: str = YEAR) -> dict[str, str]:
	"""Build the full 3-member fixture archive for a year, one valid row each."""
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
		"filings_cvm.ingestion.fii.doc.inf_mensal._base_inf_mensal_fii_reader.download_file",
		_fake_download,
	)
	return list_urls


@pytest.mark.parametrize("cls", ALL_READERS, ids=lambda c: c.__name__)
def test_read_selects_its_own_member_with_all_columns(
	cls: type[IngestionReader], monkeypatch: pytest.MonkeyPatch
) -> None:
	"""Each reader returns exactly its member's columns from the shared 3-member archive.

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
		assert df_[str_col].iloc[0] == date(2025, 6, 1)


@pytest.mark.parametrize("cls", ALL_READERS, ids=lambda c: c.__name__)
def test_date_ref_selects_the_year_not_the_month(
	cls: type[IngestionReader], monkeypatch: pytest.MonkeyPatch
) -> None:
	"""The dump is partitioned by **year**: only ``date_ref.year`` reaches the URL and the member.

	Two ``date_ref`` values in different months of the same year must resolve to the *same* yearly
	archive — the trap this dataset invites, since it is the *monthly* report.

	Parameters
	----------
	cls : type[IngestionReader]
		The reader under test.
	monkeypatch : pytest.MonkeyPatch
		Fixture used to replace the download boundary.
	"""
	list_urls = _patch_download(monkeypatch, _zip_bytes(_all_members()))

	cls(date_ref=date(2025, 1, 31)).read()
	cls(date_ref=date(2025, 12, 1)).read()

	assert list_urls == [
		"https://dados.cvm.gov.br/dados/FII/DOC/INF_MENSAL/DADOS/inf_mensal_fii_2025.zip",
		"https://dados.cvm.gov.br/dados/FII/DOC/INF_MENSAL/DADOS/inf_mensal_fii_2025.zip",
	]


def test_read_raises_value_error_for_a_year_absent_from_the_archive(
	monkeypatch: pytest.MonkeyPatch,
) -> None:
	"""A reader built for a year whose member is absent raises a clear ValueError.

	Confirms the year in ``date_ref`` — not the fixture's — drives member selection.

	Parameters
	----------
	monkeypatch : pytest.MonkeyPatch
		Fixture used to replace the download boundary.
	"""
	_patch_download(monkeypatch, _zip_bytes(_all_members()))

	with pytest.raises(ValueError, match="inf_mensal_fii_geral_2024.csv"):
		InfMensalFiiGeralReader(date_ref=date(2024, 3, 1)).read()


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
	cls = InfMensalFiiComplementoReader
	list_cols = [c for c in cls._CONTRACT.tuple_required if c != "Patrimonio_Liquido"]
	dict_members[_member_name(cls)] = (
		";".join(list_cols) + "\n" + ";".join("x" for _ in list_cols) + "\n"
	)
	_patch_download(monkeypatch, _zip_bytes(dict_members))

	with pytest.raises(ContractError):
		cls(date_ref=REF).read()


def test_read_persists_whole_archive_when_path_raw_is_given(
	monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
	"""With ``path_raw`` set, the ZIP and all 3 members survive a single reader's read.

	Parameters
	----------
	monkeypatch : pytest.MonkeyPatch
		Fixture used to replace the download boundary.
	tmp_path : pathlib.Path
		Pytest-provided scratch directory standing in for the bronze layer.
	"""
	_patch_download(monkeypatch, _zip_bytes(_all_members()))
	path_raw = tmp_path / "bronze"

	InfMensalFiiGeralReader(date_ref=REF, path_raw=path_raw).read()

	assert (path_raw / f"inf_mensal_fii_{YEAR}.zip").is_file()
	assert {p.name for p in path_raw.glob("*.csv")} == set(_all_members())


def test_read_keeps_money_column_as_exact_source_text(monkeypatch: pytest.MonkeyPatch) -> None:
	"""A money column (``Patrimonio_Liquido``) keeps its exact CVM text, never a lossy float.

	Parameters
	----------
	monkeypatch : pytest.MonkeyPatch
		Fixture used to replace the download boundary.
	"""
	dict_members = _all_members()
	cls = InfMensalFiiComplementoReader
	list_cols = list(cls._CONTRACT.tuple_required)
	list_vals = [
		VALID_CNPJ
		if c == "CNPJ_Fundo_Classe"
		else "2025-06-01"
		if c in cls._DATE_COLS
		else ("1234567.89" if c == "Patrimonio_Liquido" else "x")
		for c in list_cols
	]
	dict_members[_member_name(cls)] = ";".join(list_cols) + "\n" + ";".join(list_vals) + "\n"
	_patch_download(monkeypatch, _zip_bytes(dict_members))

	df_ = cls(date_ref=REF).read()

	assert df_["Patrimonio_Liquido"].iloc[0] == "1234567.89"
	assert isinstance(df_["Patrimonio_Liquido"].iloc[0], str)


def test_contract_preserves_cvm_column_quirks_verbatim() -> None:
	"""CVM's own accent and misspellings are reproduced exactly — "fixing" them breaks the read."""
	tuple_ap = InfMensalFiiAtivoPassivoReader._CONTRACT.tuple_required
	tuple_comp = InfMensalFiiComplementoReader._CONTRACT.tuple_required

	assert "Outros_Valores_Mobliarios" in tuple_ap
	assert "Provisoes_Contigencias" in tuple_ap
	assert "Numero_Cotistas_Entidade_Fechada_Previdência_Complementar" in tuple_comp


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
