"""Unit tests for the Registro de Subclasse (RCVM 175) ingestion reader.

Mock the single I/O boundary (``download_file``) with a fixture ZIP holding all three members
of ``registro_fundo_classe.zip``, then exercise member selection, contract validation (with an
**empty** CNPJ tuple — a subclass has no CNPJ), and dtype application for real — no network.
"""

from datetime import date
import io
from pathlib import Path
import zipfile

import pytest

from filings_cvm._internal.config.contracts.registro_classe import REGISTRO_CLASSE
from filings_cvm._internal.config.contracts.registro_fundo import REGISTRO_FUNDO
from filings_cvm._internal.config.contracts.registro_subclasse import REGISTRO_SUBCLASSE
from filings_cvm._internal.utils.tabular_reader import ContractError
from filings_cvm.ingestion import RegistroSubclasseReader


VALID_CNPJ = "11222333000181"
_HEADER = ";".join(REGISTRO_SUBCLASSE.tuple_required)


def _row(str_id_subclasse: str = "1", str_id_classe: str = "10") -> str:
	"""Build one 14-field subclass row, overriding only the fields a test cares about."""
	dict_over = {
		"ID_Registro_Classe": str_id_classe,
		"ID_Subclasse": str_id_subclasse,
		"Denominacao_Social": "SUBCLASSE ALFA",
		"Situacao": "Em Funcionamento Normal",
		"Data_Constituicao": "2025-05-15",
		"Data_Inicio": "2025-05-14",
		"Data_Inicio_Situacao": "2025-05-15",
		"Exclusivo": "N",
		"Previdenciario": "N",
	}
	return ";".join(dict_over.get(str_col, "x") for str_col in REGISTRO_SUBCLASSE.tuple_required)


def _sibling(contract: object, str_key_col: str, str_val: str) -> str:
	"""Build a one-row CSV for a sibling member so the archive holds all three."""
	list_cols = list(contract.tuple_required)  # type: ignore[attr-defined]
	dict_over = {str_key_col: str_val, "Data_Inicio_Situacao": "2025-06-27"}
	return ";".join(list_cols) + "\n" + ";".join(dict_over.get(c, "x") for c in list_cols) + "\n"


def _default_members() -> dict[str, str]:
	"""Build the member-name → CSV-text map of a well-formed fixture archive."""
	return {
		"registro_fundo.csv": _sibling(REGISTRO_FUNDO, "CNPJ_Fundo", VALID_CNPJ),
		"registro_classe.csv": _sibling(REGISTRO_CLASSE, "CNPJ_Classe", VALID_CNPJ),
		"registro_subclasse.csv": f"{_HEADER}\n{_row()}\n",
	}


def _zip_bytes(dict_members: dict[str, str]) -> bytes:
	"""Build an in-memory ZIP holding each ``name → csv text`` member."""
	buffer = io.BytesIO()
	with zipfile.ZipFile(buffer, "w") as cls_zip:
		for str_name, str_text in dict_members.items():
			cls_zip.writestr(str_name, str_text.encode("ISO-8859-1"))
	return buffer.getvalue()


def _patch_download(monkeypatch: pytest.MonkeyPatch, payload: bytes) -> None:
	"""Patch the reader's download_file boundary to drop ``payload`` at the destination."""

	def _fake_download(str_url: str, path_dest: Path, int_timeout_s: int = 60) -> Path:
		path_dest.parent.mkdir(parents=True, exist_ok=True)
		path_dest.write_bytes(payload)
		return path_dest

	monkeypatch.setattr(
		"filings_cvm.ingestion.cad.registro.registro_subclasse.download_file", _fake_download
	)


def _read_default(monkeypatch: pytest.MonkeyPatch):  # noqa: ANN202 - pandas DataFrame
	"""Read the well-formed fixture archive."""
	_patch_download(monkeypatch, _zip_bytes(_default_members()))
	return RegistroSubclasseReader().read()


def test_read_returns_the_subclass_member_with_all_columns(
	monkeypatch: pytest.MonkeyPatch,
) -> None:
	"""The subclass member's rows come back with all 14 columns, keyed by the class FK.

	Parameters
	----------
	monkeypatch : pytest.MonkeyPatch
		Fixture used to replace the download boundary.
	"""
	df_ = _read_default(monkeypatch)

	assert len(df_) == 1
	assert list(df_.columns) == list(REGISTRO_SUBCLASSE.output_columns)
	assert df_["ID_Registro_Classe"].iloc[0] == "10"


def test_contract_declares_no_cnpj_column() -> None:
	"""A subclass has no CNPJ of its own, so the contract's CNPJ tuple is empty."""
	assert REGISTRO_SUBCLASSE.tuple_cnpj_cols == ()


def test_read_validates_despite_having_no_cnpj_column(monkeypatch: pytest.MonkeyPatch) -> None:
	"""The read succeeds even though no column is CNPJ-checked.

	Parameters
	----------
	monkeypatch : pytest.MonkeyPatch
		Fixture used to replace the download boundary.
	"""
	df_ = _read_default(monkeypatch)

	assert not df_.empty


def test_read_selects_the_subclass_member_not_its_siblings(
	monkeypatch: pytest.MonkeyPatch,
) -> None:
	"""The fund and class members must not be read here.

	Parameters
	----------
	monkeypatch : pytest.MonkeyPatch
		Fixture used to replace the download boundary.
	"""
	df_ = _read_default(monkeypatch)

	assert "Tipo_Fundo" not in df_.columns
	assert "Tipo_Classe" not in df_.columns


def test_reader_takes_no_reference_month() -> None:
	"""The registry is a snapshot, so the constructor exposes no ``date_ref``."""
	import inspect

	assert "date_ref" not in set(inspect.signature(RegistroSubclasseReader.__init__).parameters)
	with pytest.raises(TypeError):
		RegistroSubclasseReader(date_ref=date(2025, 4, 1))


def test_read_coerces_every_date_column(monkeypatch: pytest.MonkeyPatch) -> None:
	"""The three ``Data_*`` columns become pure date objects.

	Parameters
	----------
	monkeypatch : pytest.MonkeyPatch
		Fixture used to replace the download boundary.
	"""
	df_ = _read_default(monkeypatch)

	assert df_["Data_Constituicao"].iloc[0] == date(2025, 5, 15)
	assert df_["Data_Inicio"].iloc[0] == date(2025, 5, 14)


def test_dtype_map_covers_every_non_date_column() -> None:
	"""The derived dtype map and the date columns together span the whole contract."""
	from filings_cvm.ingestion.cad.registro.registro_subclasse import _DATE_COLS, _DTYPES

	assert set(_DTYPES) | set(_DATE_COLS) == set(REGISTRO_SUBCLASSE.tuple_required)
	assert not set(_DTYPES) & set(_DATE_COLS)


def test_read_raises_contract_error_on_missing_required_column(
	monkeypatch: pytest.MonkeyPatch,
) -> None:
	"""Dropping any of the 14 declared columns violates the contract.

	Parameters
	----------
	monkeypatch : pytest.MonkeyPatch
		Fixture used to replace the download boundary.
	"""
	list_cols = [c for c in REGISTRO_SUBCLASSE.tuple_required if c != "Publico_Alvo"]
	dict_members = _default_members()
	dict_members["registro_subclasse.csv"] = (
		";".join(list_cols) + "\n" + ";".join("x" for _ in list_cols) + "\n"
	)
	_patch_download(monkeypatch, _zip_bytes(dict_members))

	with pytest.raises(ContractError):
		RegistroSubclasseReader().read()


def test_read_raises_value_error_when_archive_has_no_subclass_member(
	monkeypatch: pytest.MonkeyPatch,
) -> None:
	"""An archive without the subclass member raises a clear ValueError naming it.

	Parameters
	----------
	monkeypatch : pytest.MonkeyPatch
		Fixture used to replace the download boundary.
	"""
	dict_members = _default_members()
	del dict_members["registro_subclasse.csv"]
	_patch_download(monkeypatch, _zip_bytes(dict_members))

	with pytest.raises(ValueError, match="registro_subclasse.csv"):
		RegistroSubclasseReader().read()


def test_read_persists_whole_archive_when_path_raw_is_given(
	monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
	"""With ``path_raw`` set, the ZIP and all three members survive the read.

	Parameters
	----------
	monkeypatch : pytest.MonkeyPatch
		Fixture used to replace the download boundary.
	tmp_path : pathlib.Path
		Pytest-provided scratch directory standing in for the bronze layer.
	"""
	_patch_download(monkeypatch, _zip_bytes(_default_members()))
	path_raw = tmp_path / "bronze"

	RegistroSubclasseReader(path_raw=path_raw).read()

	assert (path_raw / "registro_fundo_classe.zip").is_file()
	assert {p.name for p in path_raw.glob("*.csv")} == set(_default_members())


def test_read_rejects_wrong_argument_type(monkeypatch: pytest.MonkeyPatch) -> None:
	"""The inherited ABCTypeCheckerMeta rejects a mistyped argument at call time.

	Parameters
	----------
	monkeypatch : pytest.MonkeyPatch
		Fixture used to replace the download boundary.
	"""
	_patch_download(monkeypatch, _zip_bytes(_default_members()))

	with pytest.raises(TypeError):
		RegistroSubclasseReader().read(int_timeout_s="nope")
