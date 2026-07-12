"""Unit tests for the 2 Informe Mensal FIAGRO member readers.

One parameterized module covers both members: a single in-memory fixture ZIP holds both members
for one reference month, and each reader is asserted to select **its own** member (columns match
its contract, not the sibling's), coerce its date columns, and honour the shared base behaviour
(monthly ``date_ref``, ``path_raw`` persistence, contract validation). Mock the single I/O
boundary (``download_file``); no network.
"""

from datetime import date
import io
from pathlib import Path
import zipfile

import pytest

from filings_cvm import (
	InfMensalFiagroReader,
	InfMensalFiagroSubclasseReader,
	RetryPolicy,
)
from filings_cvm._internal.config.ports.ingestion_reader import IngestionReader
from filings_cvm._internal.utils.tabular_reader import ContractError
from filings_cvm.ingestion.fiagro.doc.inf_mensal._base_inf_mensal_fiagro_reader import (
	_DEFAULT_RETRY_POLICY,
)


# CNPJ valid under the repo's ASCII-48 mod-11 routine; the contract's CNPJ check accepts it.
VALID_CNPJ = "11.222.333/0001-81"

# Fixed reference month for the fixture; the member names embed it (``…_202506.csv``).
REF = date(2025, 6, 1)
YM = "202506"

# Both members. Introspection off the class attributes keeps this list from re-stating the
# members/contracts that the readers already declare.
ALL_READERS: tuple[type[IngestionReader], ...] = (
	InfMensalFiagroReader,
	InfMensalFiagroSubclasseReader,
)


def _member_name(cls: type[IngestionReader]) -> str:
	"""Return the archive member name for ``cls`` in the fixture reference month."""
	return f"{cls._MEMBER_STEM}_{YM}.csv"  # type: ignore[attr-defined]


def _row_for(cls: type[IngestionReader]) -> str:
	"""Build one valid CSV row for ``cls``'s member from its contract + date columns."""
	list_vals = []
	for str_col in cls._CONTRACT.tuple_required:  # type: ignore[attr-defined]
		if str_col == "CNPJ_Classe":
			list_vals.append(VALID_CNPJ)
		elif str_col in cls._DATE_COLS:  # type: ignore[attr-defined]
			list_vals.append("2025-06-15")
		else:
			list_vals.append("x")
	return ";".join(list_vals)


def _member_csv(cls: type[IngestionReader]) -> str:
	"""Header + one valid row for ``cls``'s member."""
	str_header = ";".join(cls._CONTRACT.tuple_required)  # type: ignore[attr-defined]
	return f"{str_header}\n{_row_for(cls)}\n"


def _all_members() -> dict[str, str]:
	"""Build the full 2-member fixture archive, one valid row each."""
	return {_member_name(cls): _member_csv(cls) for cls in ALL_READERS}


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
		"filings_cvm.ingestion.fiagro.doc.inf_mensal._base_inf_mensal_fiagro_reader.download_file",
		_fake_download,
	)


@pytest.mark.parametrize("cls", ALL_READERS, ids=lambda c: c.__name__)
def test_read_selects_its_own_member_with_all_columns(
	cls: type[IngestionReader], monkeypatch: pytest.MonkeyPatch
) -> None:
	"""Each reader returns exactly its member's columns from the shared 2-member archive.

	The informe stem ``inf_mensal_fiagro`` is a strict prefix of the subclasse member's name, so
	this also confirms member selection is by **exact** name, not prefix.

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
		assert df_[str_col].iloc[0] == date(2025, 6, 15)


def test_informe_reader_coerces_three_date_columns() -> None:
	"""The informe proper carries three date columns; the subclasse member only one."""
	assert InfMensalFiagroReader._DATE_COLS == (
		"Data_Referencia",
		"Data_Entrega",
		"Data_Registro",
	)
	assert InfMensalFiagroSubclasseReader._DATE_COLS == ("Data_Referencia",)


@pytest.mark.parametrize("cls", ALL_READERS, ids=lambda c: c.__name__)
def test_reader_takes_reference_month(cls: type[IngestionReader]) -> None:
	"""The monthly dump is partitioned, so every reader exposes ``date_ref``.

	Parameters
	----------
	cls : type[IngestionReader]
		The reader under test.
	"""
	import inspect

	assert "date_ref" in set(inspect.signature(cls.__init__).parameters)


def test_read_uses_reference_month_in_member_name(monkeypatch: pytest.MonkeyPatch) -> None:
	"""A reader built for a month whose member is absent raises a clear ValueError.

	Confirms the ``AAAAMM`` in the requested ``date_ref`` — not the fixture's — drives member
	selection.

	Parameters
	----------
	monkeypatch : pytest.MonkeyPatch
		Fixture used to replace the download boundary.
	"""
	_patch_download(monkeypatch, _zip_bytes(_all_members()))

	with pytest.raises(ValueError, match="inf_mensal_fiagro_202505.csv"):
		InfMensalFiagroReader(date_ref=date(2025, 5, 1)).read()


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
	cls = InfMensalFiagroReader
	list_cols = [c for c in cls._CONTRACT.tuple_required if c != "Patrimonio_Liquido"]
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
	del dict_members[_member_name(InfMensalFiagroSubclasseReader)]
	_patch_download(monkeypatch, _zip_bytes(dict_members))

	with pytest.raises(ValueError, match="inf_mensal_fiagro_subclasse_202506.csv"):
		InfMensalFiagroSubclasseReader(date_ref=REF).read()


def test_read_persists_whole_archive_when_path_raw_is_given(
	monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
	"""With ``path_raw`` set, the ZIP and both members survive a single reader's read.

	The whole archive is kept, so the other reader replays the same bytes.

	Parameters
	----------
	monkeypatch : pytest.MonkeyPatch
		Fixture used to replace the download boundary.
	tmp_path : pathlib.Path
		Pytest-provided scratch directory standing in for the bronze layer.
	"""
	_patch_download(monkeypatch, _zip_bytes(_all_members()))
	path_raw = tmp_path / "bronze"

	InfMensalFiagroReader(date_ref=REF, path_raw=path_raw).read()

	assert (path_raw / f"inf_mensal_fiagro_{YM}.zip").is_file()
	assert {p.name for p in path_raw.glob("*.csv")} == set(_all_members())


def test_read_keeps_money_column_as_exact_source_text(monkeypatch: pytest.MonkeyPatch) -> None:
	"""A money column (``Patrimonio_Liquido``) keeps its exact CVM text, never a lossy float.

	Parameters
	----------
	monkeypatch : pytest.MonkeyPatch
		Fixture used to replace the download boundary.
	"""
	dict_members = _all_members()
	cls = InfMensalFiagroReader
	list_cols = list(cls._CONTRACT.tuple_required)
	list_vals = [
		VALID_CNPJ
		if c == "CNPJ_Classe"
		else "2025-06-15"
		if c in cls._DATE_COLS
		else ("655460450.13" if c == "Patrimonio_Liquido" else "x")
		for c in list_cols
	]
	dict_members[_member_name(cls)] = ";".join(list_cols) + "\n" + ";".join(list_vals) + "\n"
	_patch_download(monkeypatch, _zip_bytes(dict_members))

	df_ = cls(date_ref=REF).read()

	assert df_["Patrimonio_Liquido"].iloc[0] == "655460450.13"
	assert isinstance(df_["Patrimonio_Liquido"].iloc[0], str)


def test_read_rejects_wrong_argument_type(monkeypatch: pytest.MonkeyPatch) -> None:
	"""The inherited ABCTypeCheckerMeta rejects a mistyped argument at call time.

	Parameters
	----------
	monkeypatch : pytest.MonkeyPatch
		Fixture used to replace the download boundary.
	"""
	_patch_download(monkeypatch, _zip_bytes(_all_members()))

	with pytest.raises(TypeError):
		InfMensalFiagroReader(date_ref=REF).read(int_timeout_s="nope")


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


def test_per_instance_retry_policy_overrides_module_default() -> None:
	"""A ``retry_policy`` passed to the constructor wins over the reader's module default."""
	custom = RetryPolicy(int_max_attempts=8, float_base_wait_s=1.0)

	cls_reader = InfMensalFiagroReader(date_ref=REF, retry_policy=custom)

	assert cls_reader._retry_policy is custom
