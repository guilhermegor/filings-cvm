"""Unit tests for the 8 Informe Mensal OTS section readers.

One parameterized module covers the whole uniform family: a single in-memory fixture ZIP holds all
8 members for one reference **year** (the dump is year-partitioned despite the monthly report), and
each reader is asserted to select **its own** member, coerce its date columns, and honour the
shared base behaviour (`path_raw` persistence, contract validation, per-module retry policy).

Three dedicated regressions lock the traps found in the real bytes:

1. ``cedente_devedor.CNPJ`` is **not** a CNPJ column (it holds CPFs) — a CPF there must not fail
   the contract.
2. ``Indice_Subordinacao_Data_Base`` is **not** a date — it stays exact text.
3. The CVM typo ``Outras_Contigencias_Relevantes`` survives verbatim.

Mock the single I/O boundary (``download_file``); no network.
"""

from datetime import date
import io
from pathlib import Path
import zipfile

import pytest

from filings_cvm import (
	InfMensalOtsAtivoPassivoReader,
	InfMensalOtsCedenteDevedorReader,
	InfMensalOtsClasseReader,
	InfMensalOtsDerivativosReader,
	InfMensalOtsDesembolsoReader,
	InfMensalOtsDireitosCreditoriosReader,
	InfMensalOtsFluxoCaixaReader,
	InfMensalOtsGeralReader,
	RetryPolicy,
)
from filings_cvm._internal.config.ports.ingestion_reader import IngestionReader
from filings_cvm._internal.utils.tabular_reader import ContractError
from filings_cvm.ingestion.securit.doc.inf_mensal_ots._base_inf_mensal_ots_reader import (
	_DEFAULT_RETRY_POLICY,
)


# CNPJ valid under the repo's ASCII-48 mod-11 routine; the contract's CNPJ check accepts it.
VALID_CNPJ = "11.222.333/0001-81"

# Fixed reference YEAR for the fixture; the member names embed it (``…_2025.csv``).
REF = date(2025, 6, 15)
YEAR = "2025"

# The whole family. Introspection off the class attributes keeps this list from re-stating the 8
# members/contracts that the readers already declare.
ALL_READERS: tuple[type[IngestionReader], ...] = (
	InfMensalOtsGeralReader,
	InfMensalOtsAtivoPassivoReader,
	InfMensalOtsClasseReader,
	InfMensalOtsDireitosCreditoriosReader,
	InfMensalOtsDesembolsoReader,
	InfMensalOtsFluxoCaixaReader,
	InfMensalOtsDerivativosReader,
	InfMensalOtsCedenteDevedorReader,
)


def _member_name(cls: type[IngestionReader]) -> str:
	"""Return the archive member name for ``cls`` in the fixture reference year."""
	return f"{cls._MEMBER_STEM}_{YEAR}.csv"  # type: ignore[attr-defined]


def _value_for(cls: type[IngestionReader], str_col: str) -> str:
	"""Return a plausible source value for one column of ``cls``'s member."""
	if str_col == "CNPJ_Securitizadora":
		return VALID_CNPJ
	if str_col in cls._DATE_COLS:  # type: ignore[attr-defined]
		return "2025-01-31"
	return "x"


def _member_csv(cls: type[IngestionReader]) -> str:
	"""Header + one valid row for ``cls``'s member."""
	list_cols = list(cls._CONTRACT.tuple_required)  # type: ignore[attr-defined]
	list_row = [_value_for(cls, c) for c in list_cols]
	return ";".join(list_cols) + "\n" + ";".join(list_row) + "\n"


def _all_members() -> dict[str, str]:
	"""Build the full 8-member fixture archive, one valid row each."""
	return {_member_name(cls): _member_csv(cls) for cls in ALL_READERS}


def _zip_bytes(dict_members: dict[str, str]) -> bytes:
	"""Build an in-memory ZIP holding each ``name → csv text`` member."""
	buffer = io.BytesIO()
	with zipfile.ZipFile(buffer, "w") as cls_zip:
		for str_name, str_text in dict_members.items():
			cls_zip.writestr(str_name, str_text.encode("ISO-8859-1"))
	return buffer.getvalue()


def _patch_download(monkeypatch: pytest.MonkeyPatch, payload: bytes) -> list[str]:
	"""Patch the shared base reader's download_file boundary to drop ``payload``."""
	list_urls: list[str] = []

	def _fake_download(
		str_url: str, path_dest: Path, int_timeout_s: int = 60, retry_policy: object = None
	) -> Path:
		list_urls.append(str_url)
		path_dest.parent.mkdir(parents=True, exist_ok=True)
		path_dest.write_bytes(payload)
		return path_dest

	monkeypatch.setattr(
		"filings_cvm.ingestion.securit.doc.inf_mensal_ots."
		"_base_inf_mensal_ots_reader.download_file",
		_fake_download,
	)
	return list_urls


@pytest.mark.parametrize("cls", ALL_READERS, ids=lambda c: c.__name__)
def test_read_selects_its_own_member_with_all_columns(
	cls: type[IngestionReader], monkeypatch: pytest.MonkeyPatch
) -> None:
	"""Each reader returns exactly its member's columns from the shared 8-member archive.

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
def test_read_coerces_its_date_columns(
	cls: type[IngestionReader], monkeypatch: pytest.MonkeyPatch
) -> None:
	"""Every declared date column of a member becomes a pure ``date`` object.

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
		assert df_[str_col].iloc[0] == date(2025, 1, 31)


@pytest.mark.parametrize("cls", ALL_READERS, ids=lambda c: c.__name__)
def test_reader_requests_the_yearly_archive(
	cls: type[IngestionReader], monkeypatch: pytest.MonkeyPatch
) -> None:
	"""Only ``date_ref.year`` reaches the URL — the dump is YEAR-partitioned, though monthly.

	Parameters
	----------
	cls : type[IngestionReader]
		The reader under test.
	monkeypatch : pytest.MonkeyPatch
		Fixture used to replace the download boundary.
	"""
	list_urls = _patch_download(monkeypatch, _zip_bytes(_all_members()))

	cls(date_ref=date(2025, 12, 31)).read()

	assert list_urls == [
		"https://dados.cvm.gov.br/dados/SECURIT/DOC/INF_MENSAL_OTS/DADOS/inf_mensal_ots_2025.zip"
	]


@pytest.mark.parametrize("cls", ALL_READERS, ids=lambda c: c.__name__)
def test_reader_defaults_to_its_module_retry_policy(cls: type[IngestionReader]) -> None:
	"""With no ``retry_policy`` argument, a reader uses its own ``_RETRY_POLICY`` class default.

	Parameters
	----------
	cls : type[IngestionReader]
		The reader under test.
	"""
	assert cls._RETRY_POLICY is _DEFAULT_RETRY_POLICY  # type: ignore[attr-defined]
	assert cls(date_ref=REF)._retry_policy is _DEFAULT_RETRY_POLICY  # type: ignore[attr-defined]


def test_cedente_devedor_accepts_a_cpf_in_the_cnpj_column(
	monkeypatch: pytest.MonkeyPatch,
) -> None:
	"""REGRESSION: ``cedente_devedor.CNPJ`` holds CPFs — it must NOT be validated as a CNPJ.

	On the real 2025 file, 257 of 1650 rows carry an 11-digit CPF there (the cedente/devedor may be
	a natural person). Declaring it a CNPJ column would make a valid CVM file fail the contract —
	the ``cad_fi.CPF_CNPJ_GESTOR`` trap. Only ``CNPJ_Securitizadora`` is a CNPJ column.

	Parameters
	----------
	monkeypatch : pytest.MonkeyPatch
		Fixture used to replace the download boundary.
	"""
	cls = InfMensalOtsCedenteDevedorReader
	list_cols = list(cls._CONTRACT.tuple_required)
	list_row = [_value_for(cls, c) for c in list_cols]
	list_row[list_cols.index("CNPJ")] = "529.982.247-25"  # a CPF, not a CNPJ
	dict_members = _all_members()
	dict_members[_member_name(cls)] = ";".join(list_cols) + "\n" + ";".join(list_row) + "\n"
	_patch_download(monkeypatch, _zip_bytes(dict_members))

	df_ = cls(date_ref=REF).read()

	assert df_["CNPJ"].iloc[0] == "529.982.247-25"
	assert "CNPJ" not in cls._CONTRACT.tuple_cnpj_cols
	assert cls._CONTRACT.tuple_cnpj_cols == ("CNPJ_Securitizadora",)


def test_classe_does_not_coerce_indice_subordinacao_data_base(
	monkeypatch: pytest.MonkeyPatch,
) -> None:
	"""REGRESSION: ``Indice_Subordinacao_Data_Base`` is NOT a date, despite its name.

	The real values are numeric (``0.00000000000000000000``); coercing the column by its name would
	corrupt it. It must stay exact source text.

	Parameters
	----------
	monkeypatch : pytest.MonkeyPatch
		Fixture used to replace the download boundary.
	"""
	cls = InfMensalOtsClasseReader
	list_cols = list(cls._CONTRACT.tuple_required)
	list_row = [_value_for(cls, c) for c in list_cols]
	list_row[list_cols.index("Indice_Subordinacao_Data_Base")] = "0.00000000000000000000"
	dict_members = _all_members()
	dict_members[_member_name(cls)] = ";".join(list_cols) + "\n" + ";".join(list_row) + "\n"
	_patch_download(monkeypatch, _zip_bytes(dict_members))

	df_ = cls(date_ref=REF).read()

	assert "Indice_Subordinacao_Data_Base" not in cls._DATE_COLS
	assert df_["Indice_Subordinacao_Data_Base"].iloc[0] == "0.00000000000000000000"
	assert isinstance(df_["Indice_Subordinacao_Data_Base"].iloc[0], str)


def test_geral_preserves_the_cvm_typo_verbatim() -> None:
	"""REGRESSION: the CVM typo ``Outras_Contigencias_Relevantes`` survives verbatim.

	It is missing the *n* of *Contingências* — while ``Contingencias_Principais_Fatos``, in the
	same file, is spelled correctly. Reproduce names as published, never as they "should" be.
	"""
	tuple_cols = InfMensalOtsGeralReader._CONTRACT.tuple_required

	assert "Outras_Contigencias_Relevantes" in tuple_cols
	assert "Contingencias_Principais_Fatos" in tuple_cols
	assert "Outras_Contingencias_Relevantes" not in tuple_cols


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
	cls = InfMensalOtsAtivoPassivoReader
	list_cols = [c for c in cls._CONTRACT.tuple_required if c != "Ativo"]
	dict_members[_member_name(cls)] = (
		";".join(list_cols) + "\n" + ";".join("x" for _ in list_cols) + "\n"
	)
	_patch_download(monkeypatch, _zip_bytes(dict_members))

	with pytest.raises(ContractError):
		cls(date_ref=REF).read()


def test_read_raises_value_error_when_member_absent(monkeypatch: pytest.MonkeyPatch) -> None:
	"""A reader whose member is missing from the archive raises a clear ValueError.

	Parameters
	----------
	monkeypatch : pytest.MonkeyPatch
		Fixture used to replace the download boundary.
	"""
	dict_members = _all_members()
	del dict_members[_member_name(InfMensalOtsGeralReader)]
	_patch_download(monkeypatch, _zip_bytes(dict_members))

	with pytest.raises(ValueError, match="inf_mensal_ots_geral_2025.csv"):
		InfMensalOtsGeralReader(date_ref=REF).read()


def test_read_persists_whole_archive_when_path_raw_is_given(
	monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
	"""With ``path_raw`` set, the ZIP and all 8 members survive a single reader's read.

	The whole archive is kept, so the other 7 readers replay the same bytes.

	Parameters
	----------
	monkeypatch : pytest.MonkeyPatch
		Fixture used to replace the download boundary.
	tmp_path : pathlib.Path
		Pytest-provided scratch directory standing in for the bronze layer.
	"""
	_patch_download(monkeypatch, _zip_bytes(_all_members()))
	path_raw = tmp_path / "bronze"

	InfMensalOtsGeralReader(date_ref=REF, path_raw=path_raw).read()

	assert (path_raw / f"inf_mensal_ots_{YEAR}.zip").is_file()
	assert {p.name for p in path_raw.glob("*.csv")} == set(_all_members())


def test_read_keeps_money_column_as_exact_source_text(monkeypatch: pytest.MonkeyPatch) -> None:
	"""A money column keeps its exact CVM text, never a lossy float.

	Parameters
	----------
	monkeypatch : pytest.MonkeyPatch
		Fixture used to replace the download boundary.
	"""
	cls = InfMensalOtsAtivoPassivoReader
	list_cols = list(cls._CONTRACT.tuple_required)
	list_row = [_value_for(cls, c) for c in list_cols]
	list_row[list_cols.index("Ativo")] = "1234567.89"
	dict_members = _all_members()
	dict_members[_member_name(cls)] = ";".join(list_cols) + "\n" + ";".join(list_row) + "\n"
	_patch_download(monkeypatch, _zip_bytes(dict_members))

	df_ = cls(date_ref=REF).read()

	assert df_["Ativo"].iloc[0] == "1234567.89"
	assert isinstance(df_["Ativo"].iloc[0], str)


def test_per_instance_retry_policy_overrides_module_default() -> None:
	"""A ``retry_policy`` passed to the constructor wins over the reader's module default."""
	custom = RetryPolicy(int_max_attempts=8, float_base_wait_s=1.0)

	cls_reader = InfMensalOtsGeralReader(date_ref=REF, retry_policy=custom)

	assert cls_reader._retry_policy is custom


def test_read_rejects_wrong_argument_type(monkeypatch: pytest.MonkeyPatch) -> None:
	"""The inherited ABCTypeCheckerMeta rejects a mistyped argument at call time.

	Parameters
	----------
	monkeypatch : pytest.MonkeyPatch
		Fixture used to replace the download boundary.
	"""
	_patch_download(monkeypatch, _zip_bytes(_all_members()))

	with pytest.raises(TypeError):
		InfMensalOtsGeralReader(date_ref=REF).read(int_timeout_s="nope")
