"""Unit tests for the 19 CAD/FI histórico change-log readers.

One parameterized module covers the whole uniform family: a single in-memory fixture ZIP
holds all 19 members, and each reader is asserted to select **its own** member (columns match
its contract, not a sibling's), coerce its date columns, and honour the shared base behaviour
(no ``date_ref``, ``path_raw`` persistence, contract validation). Mock the single I/O boundary
(``download_file``); no network.
"""

from datetime import date
import io
from pathlib import Path
import zipfile

import pytest

from filings_cvm._internal.config.ports.ingestion_reader import IngestionReader
from filings_cvm._internal.utils.tabular_reader import ContractError
from filings_cvm.ingestion import (
	CadastroFiHistAdminReader,
	CadastroFiHistAuditorReader,
	CadastroFiHistClasseReader,
	CadastroFiHistCondomReader,
	CadastroFiHistControladorReader,
	CadastroFiHistCustodianteReader,
	CadastroFiHistDenomComercReader,
	CadastroFiHistDenomSocialReader,
	CadastroFiHistDiretorRespReader,
	CadastroFiHistExclusivoReader,
	CadastroFiHistExercSocialReader,
	CadastroFiHistFicReader,
	CadastroFiHistGestorReader,
	CadastroFiHistPublicoAlvoReader,
	CadastroFiHistRentabReader,
	CadastroFiHistSitReader,
	CadastroFiHistTaxaAdmReader,
	CadastroFiHistTaxaPerfmReader,
	CadastroFiHistTribLprazoReader,
)


# CNPJ valid under the repo's ASCII-48 mod-11 routine; the contract's CNPJ check accepts it.
VALID_CNPJ = "11.222.333/0001-81"

# The whole family. Introspection off the class attributes keeps this list from re-stating the
# 19 members/contracts/date-columns that the readers already declare.
ALL_READERS: tuple[type[IngestionReader], ...] = (
	CadastroFiHistAdminReader,
	CadastroFiHistAuditorReader,
	CadastroFiHistClasseReader,
	CadastroFiHistCondomReader,
	CadastroFiHistControladorReader,
	CadastroFiHistCustodianteReader,
	CadastroFiHistDenomComercReader,
	CadastroFiHistDenomSocialReader,
	CadastroFiHistDiretorRespReader,
	CadastroFiHistExclusivoReader,
	CadastroFiHistExercSocialReader,
	CadastroFiHistFicReader,
	CadastroFiHistGestorReader,
	CadastroFiHistPublicoAlvoReader,
	CadastroFiHistRentabReader,
	CadastroFiHistSitReader,
	CadastroFiHistTaxaAdmReader,
	CadastroFiHistTaxaPerfmReader,
	CadastroFiHistTribLprazoReader,
)


def _row_for(cls: type[IngestionReader]) -> str:
	"""Build one valid CSV row for ``cls``'s member from its contract + date columns."""
	list_vals = []
	for str_col in cls._CONTRACT.tuple_required:  # type: ignore[attr-defined]
		if str_col == "CNPJ_FUNDO":
			list_vals.append(VALID_CNPJ)
		elif str_col in cls._DATE_COLS:  # type: ignore[attr-defined]
			list_vals.append("2020-01-15")
		else:
			list_vals.append("x")
	return ";".join(list_vals)


def _member_csv(cls: type[IngestionReader]) -> str:
	"""Header + one valid row for ``cls``'s member."""
	str_header = ";".join(cls._CONTRACT.tuple_required)  # type: ignore[attr-defined]
	return f"{str_header}\n{_row_for(cls)}\n"


def _all_members() -> dict[str, str]:
	"""Build the full 19-member fixture archive, one valid row each."""
	return {cls._MEMBER: _member_csv(cls) for cls in ALL_READERS}  # type: ignore[attr-defined]


def _zip_bytes(dict_members: dict[str, str]) -> bytes:
	"""Build an in-memory ZIP holding each ``name → csv text`` member."""
	buffer = io.BytesIO()
	with zipfile.ZipFile(buffer, "w") as cls_zip:
		for str_name, str_text in dict_members.items():
			cls_zip.writestr(str_name, str_text.encode("ISO-8859-1"))
	return buffer.getvalue()


def _patch_download(monkeypatch: pytest.MonkeyPatch, payload: bytes) -> None:
	"""Patch the shared base reader's download_file boundary to drop ``payload``."""

	def _fake_download(str_url: str, path_dest: Path, int_timeout_s: int = 60) -> Path:
		path_dest.parent.mkdir(parents=True, exist_ok=True)
		path_dest.write_bytes(payload)
		return path_dest

	monkeypatch.setattr(
		"filings_cvm.ingestion._base_cad_fi_hist_reader.download_file", _fake_download
	)


@pytest.mark.parametrize("cls", ALL_READERS, ids=lambda c: c.__name__)
def test_read_selects_its_own_member_with_all_columns(
	cls: type[IngestionReader], monkeypatch: pytest.MonkeyPatch
) -> None:
	"""Each reader returns exactly its member's columns from the shared 19-member archive.

	Parameters
	----------
	cls : type[IngestionReader]
		The reader under test.
	monkeypatch : pytest.MonkeyPatch
		Fixture used to replace the download boundary.
	"""
	_patch_download(monkeypatch, _zip_bytes(_all_members()))

	df_ = cls().read()

	assert len(df_) == 1
	assert list(df_.columns) == list(cls._CONTRACT.tuple_required)  # type: ignore[attr-defined]


@pytest.mark.parametrize("cls", ALL_READERS, ids=lambda c: c.__name__)
def test_read_coerces_date_columns(
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

	df_ = cls().read()

	for str_col in cls._DATE_COLS:  # type: ignore[attr-defined]
		assert df_[str_col].iloc[0] == date(2020, 1, 15)


@pytest.mark.parametrize("cls", ALL_READERS, ids=lambda c: c.__name__)
def test_dtype_map_and_date_cols_partition_the_contract(cls: type[IngestionReader]) -> None:
	"""The base reader's derived dtype map and the date columns partition the contract.

	Parameters
	----------
	cls : type[IngestionReader]
		The reader under test.
	"""
	set_required = set(cls._CONTRACT.tuple_required)  # type: ignore[attr-defined]
	set_dates = set(cls._DATE_COLS)  # type: ignore[attr-defined]

	assert set_dates <= set_required
	# Every non-date required column would be typed str by the base reader's comprehension.
	set_text = set_required - set_dates
	assert set_text and not (set_text & set_dates)


@pytest.mark.parametrize("cls", ALL_READERS, ids=lambda c: c.__name__)
def test_reader_takes_no_reference_month(cls: type[IngestionReader]) -> None:
	"""The registry history is a snapshot, so no reader exposes ``date_ref``.

	Parameters
	----------
	cls : type[IngestionReader]
		The reader under test.
	"""
	import inspect

	assert "date_ref" not in set(inspect.signature(cls.__init__).parameters)
	with pytest.raises(TypeError):
		cls(date_ref=date(2025, 4, 1))  # type: ignore[call-arg]


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
	# Corrupt the situação member by omitting one of its required columns.
	list_cols = [c for c in CadastroFiHistSitReader._CONTRACT.tuple_required if c != "DT_FIM_SIT"]
	dict_members[CadastroFiHistSitReader._MEMBER] = (
		";".join(list_cols) + "\n" + ";".join("x" for _ in list_cols) + "\n"
	)
	_patch_download(monkeypatch, _zip_bytes(dict_members))

	with pytest.raises(ContractError):
		CadastroFiHistSitReader().read()


def test_read_raises_value_error_when_member_absent(monkeypatch: pytest.MonkeyPatch) -> None:
	"""A reader whose member is missing from the archive raises a clear ValueError.

	Parameters
	----------
	monkeypatch : pytest.MonkeyPatch
		Fixture used to replace the download boundary.
	"""
	dict_members = _all_members()
	del dict_members[CadastroFiHistGestorReader._MEMBER]
	_patch_download(monkeypatch, _zip_bytes(dict_members))

	with pytest.raises(ValueError, match="cad_fi_hist_gestor.csv"):
		CadastroFiHistGestorReader().read()


def test_read_persists_whole_archive_when_path_raw_is_given(
	monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
	"""With ``path_raw`` set, the ZIP and all 19 members survive a single reader's read.

	The whole archive is kept, so the other 18 readers replay the same bytes.

	Parameters
	----------
	monkeypatch : pytest.MonkeyPatch
		Fixture used to replace the download boundary.
	tmp_path : pathlib.Path
		Pytest-provided scratch directory standing in for the bronze layer.
	"""
	_patch_download(monkeypatch, _zip_bytes(_all_members()))
	path_raw = tmp_path / "bronze"

	CadastroFiHistSitReader(path_raw=path_raw).read()

	assert (path_raw / "cad_fi_hist.zip").is_file()
	assert {p.name for p in path_raw.glob("*.csv")} == set(_all_members())


def test_read_keeps_taxa_adm_as_exact_source_text(monkeypatch: pytest.MonkeyPatch) -> None:
	"""A money column (``TAXA_ADM``) keeps its exact CVM text, never a lossy float.

	Parameters
	----------
	monkeypatch : pytest.MonkeyPatch
		Fixture used to replace the download boundary.
	"""
	dict_members = _all_members()
	cls = CadastroFiHistTaxaAdmReader
	list_cols = list(cls._CONTRACT.tuple_required)
	list_vals = [
		VALID_CNPJ
		if c == "CNPJ_FUNDO"
		else "2020-01-15"
		if c in cls._DATE_COLS
		else ("1.50" if c == "TAXA_ADM" else "x")
		for c in list_cols
	]
	dict_members[cls._MEMBER] = ";".join(list_cols) + "\n" + ";".join(list_vals) + "\n"
	_patch_download(monkeypatch, _zip_bytes(dict_members))

	df_ = cls().read()

	assert df_["TAXA_ADM"].iloc[0] == "1.50"
	assert isinstance(df_["TAXA_ADM"].iloc[0], str)


def test_read_rejects_wrong_argument_type(monkeypatch: pytest.MonkeyPatch) -> None:
	"""The inherited ABCTypeCheckerMeta rejects a mistyped argument at call time.

	Parameters
	----------
	monkeypatch : pytest.MonkeyPatch
		Fixture used to replace the download boundary.
	"""
	_patch_download(monkeypatch, _zip_bytes(_all_members()))

	with pytest.raises(TypeError):
		CadastroFiHistSitReader().read(int_timeout_s="nope")
