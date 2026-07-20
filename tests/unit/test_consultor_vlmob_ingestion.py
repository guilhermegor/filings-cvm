"""Unit tests for the five CONSULTOR_VLMOB/CAD registry readers (`cad_consultor_vlmob.zip`).

One parameterized module covers all five members: a single in-memory fixture ZIP holds every CSV,
and each reader is asserted to select **its own** member, coerce its date columns, and honour the
shared base behaviour (no ``date_ref``, ``path_raw`` persistence, contract validation). The one
non-tautological assertion is ``test_contract_matches_the_published_header``: it compares each
contract against the verbatim header bytes CVM publishes, committed under
``tests/fixtures/cad_consultor_vlmob/`` — the pinned oracle. Mock the single I/O boundary
(``download_file``); no network.
"""

from datetime import date
import io
from pathlib import Path
import zipfile

import pytest

from filings_cvm._internal.config.contracts import (
	CAD_CONSULTOR_VLMOB_DIRETOR,
	CAD_CONSULTOR_VLMOB_PF,
	CAD_CONSULTOR_VLMOB_PJ,
	CAD_CONSULTOR_VLMOB_RESP,
	CAD_CONSULTOR_VLMOB_SOCIOS,
)
from filings_cvm._internal.config.ports.ingestion_reader import IngestionReader
from filings_cvm._internal.utils.tabular_reader import ContractError, FileContract
from filings_cvm.ingestion import (
	ConsultorVlmobDiretorReader,
	ConsultorVlmobPfReader,
	ConsultorVlmobPjReader,
	ConsultorVlmobRespReader,
	ConsultorVlmobSociosReader,
)


# CNPJ valid under the repo's ASCII-48 mod-11 routine; the CNPJ-bearing contracts accept it.
VALID_CNPJ = "11.222.333/0001-81"

# Verbatim published headers — the oracle the contracts are pinned to.
PATH_FIXTURES = Path(__file__).resolve().parents[1] / "fixtures" / "cad_consultor_vlmob"

# The whole family. Introspection off the class attributes keeps this list from re-stating the
# members/contracts/date-columns the readers already declare.
ALL_READERS: tuple[type[IngestionReader], ...] = (
	ConsultorVlmobPfReader,
	ConsultorVlmobPjReader,
	ConsultorVlmobDiretorReader,
	ConsultorVlmobRespReader,
	ConsultorVlmobSociosReader,
)

# (fixture section, reader, contract) for the anti-tautology header check.
SECTIONS: tuple[tuple[str, type[IngestionReader], FileContract], ...] = (
	("pf", ConsultorVlmobPfReader, CAD_CONSULTOR_VLMOB_PF),
	("pj", ConsultorVlmobPjReader, CAD_CONSULTOR_VLMOB_PJ),
	("diretor", ConsultorVlmobDiretorReader, CAD_CONSULTOR_VLMOB_DIRETOR),
	("resp", ConsultorVlmobRespReader, CAD_CONSULTOR_VLMOB_RESP),
	("socios", ConsultorVlmobSociosReader, CAD_CONSULTOR_VLMOB_SOCIOS),
)

# The three members CVM publishes with no date column at all — like ADM_CART.
DATELESS_READERS: tuple[type[IngestionReader], ...] = (
	ConsultorVlmobDiretorReader,
	ConsultorVlmobRespReader,
	ConsultorVlmobSociosReader,
)


def _row_for(cls: type[IngestionReader]) -> str:
	"""Build one valid CSV row for ``cls``'s member from its contract + date columns."""
	list_vals = []
	for str_col in cls._CONTRACT.tuple_required:  # type: ignore[attr-defined]
		if str_col == "CNPJ":
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
	"""Build the full five-member fixture archive, one valid row each."""
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

	def _fake_download(
		str_url: str, path_dest: Path, int_timeout_s: int = 60, retry_policy: object = None
	) -> Path:
		path_dest.parent.mkdir(parents=True, exist_ok=True)
		path_dest.write_bytes(payload)
		return path_dest

	monkeypatch.setattr(
		"filings_cvm.ingestion.consultor_vlmob.cad._base_consultor_vlmob_reader.download_file",
		_fake_download,
	)


@pytest.mark.parametrize(("str_section", "cls", "contract"), SECTIONS, ids=lambda v: str(v))
def test_contract_matches_the_published_header(
	str_section: str, cls: type[IngestionReader], contract: FileContract
) -> None:
	"""Each contract equals the verbatim header CVM publishes — the one non-tautological check.

	Parameters
	----------
	str_section : str
		The member section (``pf`` / ``pj`` / ``diretor`` / ``resp`` / ``socios``).
	cls : type[IngestionReader]
		The reader whose contract is pinned (kept for symmetry with ``ids``).
	contract : FileContract
		The contract under test.
	"""
	str_line = (
		(PATH_FIXTURES / f"cad_consultor_vlmob_{str_section}_header.csv")
		.read_text("utf-8")
		.strip()
	)
	assert contract.tuple_required == tuple(str_line.split(";"))


@pytest.mark.parametrize("cls", ALL_READERS, ids=lambda c: c.__name__)
def test_read_selects_its_own_member_with_all_columns(
	cls: type[IngestionReader], monkeypatch: pytest.MonkeyPatch
) -> None:
	"""Each reader returns exactly its member's columns from the shared archive.

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
	assert list(df_.columns) == list(cls._CONTRACT.output_columns)  # type: ignore[attr-defined]


@pytest.mark.parametrize("cls", ALL_READERS, ids=lambda c: c.__name__)
def test_read_coerces_date_columns(
	cls: type[IngestionReader], monkeypatch: pytest.MonkeyPatch
) -> None:
	"""Every declared date column becomes a pure ``date`` object.

	Vacuous for the three dateless members — their behaviour is pinned by
	``test_dateless_members_read_every_column_as_text``.

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


@pytest.mark.parametrize("cls", DATELESS_READERS, ids=lambda c: c.__name__)
def test_dateless_members_read_every_column_as_text(
	cls: type[IngestionReader], monkeypatch: pytest.MonkeyPatch
) -> None:
	"""``diretor``/``resp``/``socios`` declare no date column, so every column stays source text.

	Parameters
	----------
	cls : type[IngestionReader]
		The dateless reader under test.
	monkeypatch : pytest.MonkeyPatch
		Fixture used to replace the download boundary.
	"""
	assert cls._DATE_COLS == ()  # type: ignore[attr-defined]
	_patch_download(monkeypatch, _zip_bytes(_all_members()))

	df_ = cls().read()

	for str_col in cls._CONTRACT.tuple_required:  # type: ignore[attr-defined]
		assert isinstance(df_[str_col].iloc[0], str)


def test_pj_has_three_date_columns_not_four() -> None:
	"""Unlike ADM_CART's ``pj``, this ``pj`` has no ``DT_PATRIM_LIQ`` — three date columns."""
	assert ConsultorVlmobPjReader._DATE_COLS == ("DT_REG", "DT_CANCEL", "DT_INI_SIT")
	assert "DT_PATRIM_LIQ" not in CAD_CONSULTOR_VLMOB_PJ.tuple_required
	assert "VL_PATRIM_LIQ" not in CAD_CONSULTOR_VLMOB_PJ.tuple_required


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
	set_text = set_required - set_dates
	assert set_text and not (set_text & set_dates)


@pytest.mark.parametrize("cls", ALL_READERS, ids=lambda c: c.__name__)
def test_reader_takes_no_reference_month(cls: type[IngestionReader]) -> None:
	"""The registry is a snapshot, so no reader exposes ``date_ref``.

	Parameters
	----------
	cls : type[IngestionReader]
		The reader under test.
	"""
	import inspect

	assert "date_ref" not in set(inspect.signature(cls.__init__).parameters)
	with pytest.raises(TypeError):
		cls(date_ref=date(2025, 4, 1))  # type: ignore[call-arg]


def test_pf_contract_declares_no_cnpj_column() -> None:
	"""The natural-person member has neither CNPJ nor CPF, so its contract constrains none."""
	assert CAD_CONSULTOR_VLMOB_PF.tuple_cnpj_cols == ()
	assert "CNPJ" not in CAD_CONSULTOR_VLMOB_PF.tuple_required
	assert "CPF" not in CAD_CONSULTOR_VLMOB_PF.tuple_required


def test_the_four_cnpj_members_key_on_the_consultant_cnpj() -> None:
	"""Every member except ``pf`` constrains the *consultant's* CNPJ — no personal identifier."""
	for contract in (
		CAD_CONSULTOR_VLMOB_PJ,
		CAD_CONSULTOR_VLMOB_DIRETOR,
		CAD_CONSULTOR_VLMOB_RESP,
		CAD_CONSULTOR_VLMOB_SOCIOS,
	):
		assert contract.tuple_cnpj_cols == ("CNPJ",)
		assert "CPF" not in contract.tuple_required


def test_read_raises_contract_error_on_missing_required_column(
	monkeypatch: pytest.MonkeyPatch,
) -> None:
	"""Dropping a declared column from the pj member violates its contract.

	Parameters
	----------
	monkeypatch : pytest.MonkeyPatch
		Fixture used to replace the download boundary.
	"""
	dict_members = _all_members()
	list_cols = [c for c in ConsultorVlmobPjReader._CONTRACT.tuple_required if c != "DENOM_SOCIAL"]
	dict_members[ConsultorVlmobPjReader._MEMBER] = (
		";".join(list_cols) + "\n" + ";".join("x" for _ in list_cols) + "\n"
	)
	_patch_download(monkeypatch, _zip_bytes(dict_members))

	with pytest.raises(ContractError):
		ConsultorVlmobPjReader().read()


def test_read_raises_value_error_when_member_absent(monkeypatch: pytest.MonkeyPatch) -> None:
	"""A reader whose member is missing from the archive raises a clear ValueError.

	Parameters
	----------
	monkeypatch : pytest.MonkeyPatch
		Fixture used to replace the download boundary.
	"""
	dict_members = _all_members()
	del dict_members[ConsultorVlmobSociosReader._MEMBER]
	_patch_download(monkeypatch, _zip_bytes(dict_members))

	with pytest.raises(ValueError, match="cad_consultor_vlmob_socios.csv"):
		ConsultorVlmobSociosReader().read()


def test_read_persists_whole_archive_when_path_raw_is_given(
	monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
	"""With ``path_raw`` set, the ZIP and all five members survive a single reader's read.

	Parameters
	----------
	monkeypatch : pytest.MonkeyPatch
		Fixture used to replace the download boundary.
	tmp_path : pathlib.Path
		Pytest-provided scratch directory standing in for the bronze layer.
	"""
	_patch_download(monkeypatch, _zip_bytes(_all_members()))
	path_raw = tmp_path / "bronze"

	ConsultorVlmobPfReader(path_raw=path_raw).read()

	assert (path_raw / "cad_consultor_vlmob.zip").is_file()
	assert {p.name for p in path_raw.glob("*.csv")} == set(_all_members())


def test_read_keeps_cep_as_exact_source_text(monkeypatch: pytest.MonkeyPatch) -> None:
	"""``CEP`` keeps its exact CVM text — leading zeros survive, never coerced to a number.

	Parameters
	----------
	monkeypatch : pytest.MonkeyPatch
		Fixture used to replace the download boundary.
	"""
	dict_members = _all_members()
	cls = ConsultorVlmobPjReader
	list_cols = list(cls._CONTRACT.tuple_required)
	list_vals = [
		VALID_CNPJ
		if c == "CNPJ"
		else "2020-01-15"
		if c in cls._DATE_COLS
		else ("01310900" if c == "CEP" else "x")
		for c in list_cols
	]
	dict_members[cls._MEMBER] = ";".join(list_cols) + "\n" + ";".join(list_vals) + "\n"
	_patch_download(monkeypatch, _zip_bytes(dict_members))

	df_ = cls().read()

	assert df_["CEP"].iloc[0] == "01310900"
	assert isinstance(df_["CEP"].iloc[0], str)


def test_read_rejects_wrong_argument_type(monkeypatch: pytest.MonkeyPatch) -> None:
	"""The inherited ABCTypeCheckerMeta rejects a mistyped argument at call time.

	Parameters
	----------
	monkeypatch : pytest.MonkeyPatch
		Fixture used to replace the download boundary.
	"""
	_patch_download(monkeypatch, _zip_bytes(_all_members()))

	with pytest.raises(TypeError):
		ConsultorVlmobPfReader().read(int_timeout_s="nope")
