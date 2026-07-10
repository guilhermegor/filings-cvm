"""Unit tests for the Registro de Fundo (RCVM 175) ingestion reader.

Mock the single I/O boundary (``download_file``) with a fixture ZIP holding all three
members of ``registro_fundo_classe.zip``, then exercise exact member selection, the
``FileContract`` validation, and dtype application for real — no network.

Two properties are pinned because both look like defects and are not: the reader takes **no
reference month** (the archive is a current-state snapshot) and ``ID_Registro_Fundo`` is not
strictly unique (a fund is re-registered across regime migrations).
"""

from datetime import date
import io
from pathlib import Path
import zipfile

import pandas as pd
import pytest

from filings_cvm._internal.config.contracts.registro_classe import REGISTRO_CLASSE
from filings_cvm._internal.config.contracts.registro_fundo import REGISTRO_FUNDO
from filings_cvm._internal.config.contracts.registro_subclasse import REGISTRO_SUBCLASSE
from filings_cvm._internal.utils.tabular_reader import ContractError
from filings_cvm.ingestion import RegistroFundoReader


# Bare-digit CNPJs (CVM ships them unmasked here) valid under the repo's ASCII-48 mod-11 routine.
VALID_CNPJ = "11222333000181"
OTHER_CNPJ = "11444777000161"
VALID_CPF = "11144477735"

_HEADER = ";".join(REGISTRO_FUNDO.tuple_required)


def _row(
	str_cnpj: str,
	str_tipo: str = "FIF",
	str_situacao: str = "Em Funcionamento Normal",
	str_data_registro: str = "1994-06-06",
	str_data_cancel: str = "",
	str_tipo_pessoa_gestor: str = "PJ",
	str_gestor_id: str = OTHER_CNPJ,
) -> str:
	"""Build one 21-field fund row, overriding only the fields a test cares about."""
	dict_over = {
		"ID_Registro_Fundo": "1",
		"CNPJ_Fundo": str_cnpj,
		"Denominacao_Social": "FUNDO ALFA",
		"Tipo_Fundo": str_tipo,
		"Situacao": str_situacao,
		"Data_Registro": str_data_registro,
		"Data_Constituicao": "1994-06-06",
		"Data_Cancelamento": str_data_cancel,
		"Data_Inicio_Situacao": "1995-03-31",
		"Data_Adaptacao_RCVM175": "2024-12-16",
		"Data_Inicio_Exercicio_Social": "",
		"Data_Fim_Exercicio_Social": "",
		"Data_Patrimonio_Liquido": "1994-12-31",
		"Patrimonio_Liquido": "50000.00",
		"Tipo_Pessoa_Gestor": str_tipo_pessoa_gestor,
		"CPF_CNPJ_Gestor": str_gestor_id,
	}
	return ";".join(dict_over.get(str_col, "x") for str_col in REGISTRO_FUNDO.tuple_required)


def _sibling(contract: object, str_cnpj_col: str, str_cnpj: str) -> str:
	"""Build a one-row CSV for a sibling member so the archive holds all three."""
	list_cols = list(contract.tuple_required)  # type: ignore[attr-defined]
	dict_over = {str_cnpj_col: str_cnpj, "Data_Inicio_Situacao": "2025-06-27"}
	str_row = ";".join(dict_over.get(c, "x") for c in list_cols)
	return ";".join(list_cols) + "\n" + str_row + "\n"


def _default_members() -> dict[str, str]:
	"""Build the member-name → CSV-text map of a well-formed fixture archive."""
	return {
		"registro_fundo.csv": f"{_HEADER}\n{_row(VALID_CNPJ)}\n",
		"registro_classe.csv": _sibling(REGISTRO_CLASSE, "CNPJ_Classe", VALID_CNPJ),
		"registro_subclasse.csv": _sibling(REGISTRO_SUBCLASSE, "ID_Subclasse", "1"),
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
		"filings_cvm.ingestion.cad.registro.registro_fundo.download_file", _fake_download
	)


def _read_default(monkeypatch: pytest.MonkeyPatch) -> pd.DataFrame:
	"""Read the well-formed fixture archive."""
	_patch_download(monkeypatch, _zip_bytes(_default_members()))
	return RegistroFundoReader().read()


def test_read_returns_the_fund_member_with_all_columns(monkeypatch: pytest.MonkeyPatch) -> None:
	"""The fund member's rows come back with all 21 columns.

	Parameters
	----------
	monkeypatch : pytest.MonkeyPatch
		Fixture used to replace the download boundary.
	"""
	df_ = _read_default(monkeypatch)

	assert len(df_) == 1
	assert list(df_.columns) == list(REGISTRO_FUNDO.output_columns)


def test_read_selects_the_fund_member_not_its_siblings(monkeypatch: pytest.MonkeyPatch) -> None:
	"""The class and subclass members of the same archive must not be read here.

	Parameters
	----------
	monkeypatch : pytest.MonkeyPatch
		Fixture used to replace the download boundary.
	"""
	df_ = _read_default(monkeypatch)

	# ``Tipo_Classe`` / ``ID_Subclasse`` belong to the siblings, never the fund frame.
	assert "Tipo_Classe" not in df_.columns
	assert "ID_Subclasse" not in df_.columns


def test_reader_takes_no_reference_month() -> None:
	"""The registry is a snapshot, so the constructor exposes no ``date_ref``.

	Passing one must fail rather than be silently ignored.
	"""
	import inspect

	set_params = set(inspect.signature(RegistroFundoReader.__init__).parameters)

	assert "date_ref" not in set_params
	with pytest.raises(TypeError):
		RegistroFundoReader(date_ref=date(2025, 4, 1))


def test_read_keeps_a_fund_re_registered_across_regimes(
	monkeypatch: pytest.MonkeyPatch,
) -> None:
	"""``ID_Registro_Fundo`` is not strictly unique and the reader must not de-duplicate.

	Parameters
	----------
	monkeypatch : pytest.MonkeyPatch
		Fixture used to replace the download boundary.
	"""
	dict_members = _default_members()
	str_cancelled = _row(
		VALID_CNPJ, str_tipo="FIF", str_situacao="Cancelado", str_data_cancel="2005-03-31"
	)
	str_active = _row(VALID_CNPJ, str_tipo="FI")
	dict_members["registro_fundo.csv"] = f"{_HEADER}\n{str_cancelled}\n{str_active}\n"
	_patch_download(monkeypatch, _zip_bytes(dict_members))

	df_ = RegistroFundoReader().read()

	assert len(df_) == 2
	assert sorted(df_["Tipo_Fundo"]) == ["FI", "FIF"]


def test_read_coerces_every_date_column(monkeypatch: pytest.MonkeyPatch) -> None:
	"""The eight ``Data_*`` columns become pure date objects; a blank becomes NaT.

	Parameters
	----------
	monkeypatch : pytest.MonkeyPatch
		Fixture used to replace the download boundary.
	"""
	df_ = _read_default(monkeypatch)

	assert df_["Data_Registro"].iloc[0] == date(1994, 6, 6)
	assert df_["Data_Adaptacao_RCVM175"].iloc[0] == date(2024, 12, 16)
	assert pd.isna(df_["Data_Cancelamento"].iloc[0])


def test_read_accepts_a_cpf_in_the_manager_identifier_column(
	monkeypatch: pytest.MonkeyPatch,
) -> None:
	"""``CPF_CNPJ_Gestor`` holds a CPF when the manager is a natural person.

	It is read as text and never validated as a CNPJ.

	Parameters
	----------
	monkeypatch : pytest.MonkeyPatch
		Fixture used to replace the download boundary.
	"""
	dict_members = _default_members()
	dict_members["registro_fundo.csv"] = (
		f"{_HEADER}\n{_row(VALID_CNPJ, str_tipo_pessoa_gestor='PF', str_gestor_id=VALID_CPF)}\n"
	)
	_patch_download(monkeypatch, _zip_bytes(dict_members))

	df_ = RegistroFundoReader().read()

	assert df_["CPF_CNPJ_Gestor"].iloc[0] == VALID_CPF
	assert "CPF_CNPJ_Gestor" not in REGISTRO_FUNDO.tuple_cnpj_cols


def test_read_keeps_money_as_exact_source_text(monkeypatch: pytest.MonkeyPatch) -> None:
	"""``Patrimonio_Liquido`` keeps its exact CVM text, never a lossy float.

	Parameters
	----------
	monkeypatch : pytest.MonkeyPatch
		Fixture used to replace the download boundary.
	"""
	df_ = _read_default(monkeypatch)

	assert df_["Patrimonio_Liquido"].iloc[0] == "50000.00"
	assert isinstance(df_["Patrimonio_Liquido"].iloc[0], str)


def test_dtype_map_covers_every_non_date_column() -> None:
	"""The derived dtype map and the date columns together span the whole contract."""
	from filings_cvm.ingestion.cad.registro.registro_fundo import _DATE_COLS, _DTYPES

	assert set(_DTYPES) | set(_DATE_COLS) == set(REGISTRO_FUNDO.tuple_required)
	assert not set(_DTYPES) & set(_DATE_COLS)


def test_read_raises_contract_error_on_missing_required_column(
	monkeypatch: pytest.MonkeyPatch,
) -> None:
	"""Dropping any of the 21 declared columns violates the contract.

	Parameters
	----------
	monkeypatch : pytest.MonkeyPatch
		Fixture used to replace the download boundary.
	"""
	list_cols = [c for c in REGISTRO_FUNDO.tuple_required if c != "Gestor"]
	dict_members = _default_members()
	dict_members["registro_fundo.csv"] = (
		";".join(list_cols) + "\n" + ";".join("x" for _ in list_cols) + "\n"
	)
	_patch_download(monkeypatch, _zip_bytes(dict_members))

	with pytest.raises(ContractError):
		RegistroFundoReader().read()


def test_read_raises_value_error_when_archive_has_no_fund_member(
	monkeypatch: pytest.MonkeyPatch,
) -> None:
	"""An archive holding only the siblings raises a clear ValueError naming the member.

	Parameters
	----------
	monkeypatch : pytest.MonkeyPatch
		Fixture used to replace the download boundary.
	"""
	dict_members = _default_members()
	del dict_members["registro_fundo.csv"]
	_patch_download(monkeypatch, _zip_bytes(dict_members))

	with pytest.raises(ValueError, match="registro_fundo.csv"):
		RegistroFundoReader().read()


def test_read_persists_whole_archive_when_path_raw_is_given(
	monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
	"""With ``path_raw`` set, the ZIP and *all three* members survive the read.

	The whole archive is kept so the class and subclass readers replay the same bytes.

	Parameters
	----------
	monkeypatch : pytest.MonkeyPatch
		Fixture used to replace the download boundary.
	tmp_path : pathlib.Path
		Pytest-provided scratch directory standing in for the bronze layer.
	"""
	_patch_download(monkeypatch, _zip_bytes(_default_members()))
	path_raw = tmp_path / "bronze" / "registro" / "20250710"

	RegistroFundoReader(path_raw=path_raw).read()

	assert (path_raw / "registro_fundo_classe.zip").is_file()
	assert {p.name for p in path_raw.glob("*.csv")} == set(_default_members())


def test_read_leaves_no_artifact_on_disk_when_path_raw_is_none(
	monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
	"""Without ``path_raw`` the artifact lands in a temp dir and is discarded.

	Parameters
	----------
	monkeypatch : pytest.MonkeyPatch
		Fixture used to replace the download boundary.
	tmp_path : pathlib.Path
		Scratch directory asserted to stay empty.
	"""
	_patch_download(monkeypatch, _zip_bytes(_default_members()))
	monkeypatch.chdir(tmp_path)

	RegistroFundoReader().read()

	assert list(tmp_path.iterdir()) == []


def test_read_rejects_wrong_argument_type(monkeypatch: pytest.MonkeyPatch) -> None:
	"""The inherited ABCTypeCheckerMeta rejects a mistyped argument at call time.

	Parameters
	----------
	monkeypatch : pytest.MonkeyPatch
		Fixture used to replace the download boundary.
	"""
	_patch_download(monkeypatch, _zip_bytes(_default_members()))

	with pytest.raises(TypeError):
		RegistroFundoReader().read(int_timeout_s="nope")
