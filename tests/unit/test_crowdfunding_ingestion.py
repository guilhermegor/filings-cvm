"""Unit tests for the three CROWDFUNDING/CAD registry readers (`cad_crowdfunding.zip`).

One parameterized module covers all members: a single in-memory fixture ZIP holds the registry and
its two satellite CSVs, and each reader is asserted to select **its own** member, coerce its date
columns, and honour the shared base behaviour (no ``date_ref``, ``path_raw`` persistence, contract
validation). The one non-tautological assertion is
``test_contract_matches_the_published_header``: it compares each contract against the verbatim
header bytes CVM publishes, committed under ``tests/fixtures/cad_crowdfunding/`` — the pinned
oracle. Mock the single I/O boundary (``download_file``); no network.
"""

from datetime import date
import io
from pathlib import Path
import zipfile

import pytest

from filings_cvm._internal.config.contracts import (
	CAD_CROWDFUNDING,
	CAD_CROWDFUNDING_ADM_RESP,
	CAD_CROWDFUNDING_SOCIOS,
)
from filings_cvm._internal.config.ports.ingestion_reader import IngestionReader
from filings_cvm._internal.utils.tabular_reader import ContractError, FileContract
from filings_cvm.ingestion import (
	CrowdfundingAdmRespReader,
	CrowdfundingReader,
	CrowdfundingSociosReader,
)


# CNPJ valid under the repo's ASCII-48 mod-11 routine; every contract's CNPJ check accepts it.
VALID_CNPJ = "11.222.333/0001-81"

# Verbatim published headers — the oracle the contracts are pinned to.
PATH_FIXTURES = Path(__file__).resolve().parents[1] / "fixtures" / "cad_crowdfunding"

# The whole family. Introspection off the class attributes keeps this list from re-stating the
# members/contracts/date-columns the readers already declare.
ALL_READERS: tuple[type[IngestionReader], ...] = (
	CrowdfundingReader,
	CrowdfundingAdmRespReader,
	CrowdfundingSociosReader,
)

# (fixture section, reader, contract) for the anti-tautology header check.
SECTIONS: tuple[tuple[str, type[IngestionReader], FileContract], ...] = (
	("cad_crowdfunding", CrowdfundingReader, CAD_CROWDFUNDING),
	("cad_crowdfunding_adm_resp", CrowdfundingAdmRespReader, CAD_CROWDFUNDING_ADM_RESP),
	("cad_crowdfunding_socios", CrowdfundingSociosReader, CAD_CROWDFUNDING_SOCIOS),
)

# The two satellites declare no date column at all — the ADM_CART shape.
DATELESS_READERS: tuple[type[IngestionReader], ...] = (
	CrowdfundingAdmRespReader,
	CrowdfundingSociosReader,
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
	"""Build the full three-member fixture archive, one valid row each."""
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
		"filings_cvm.ingestion.crowdfunding.cad._base_crowdfunding_reader.download_file",
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
		The member section (``cad_crowdfunding`` / ``…_adm_resp`` / ``…_socios``).
	cls : type[IngestionReader]
		The reader whose contract is pinned (kept for symmetry with ``ids``).
	contract : FileContract
		The contract under test.
	"""
	str_line = (PATH_FIXTURES / f"{str_section}_header.csv").read_text("utf-8").strip()
	assert contract.tuple_required == tuple(str_line.split(";"))


def test_registry_is_leaner_than_its_siblings() -> None:
	"""The registry omits columns every COORD_OFERTA/INTERMED sibling carries.

	It has **no** ``DT_CANCEL`` / ``MOTIVO_CANCEL`` / ``CD_CVM``, and spells the site column
	``WEBSITE`` (not ``SITE_WEB``) and the area code ``DDD`` (not ``DDD_TEL``). Copying a sibling's
	contract would ship the wrong columns with every other test still green, so the difference is
	pinned here.
	"""
	set_cols = set(CAD_CROWDFUNDING.tuple_required)

	assert not ({"DT_CANCEL", "MOTIVO_CANCEL", "CD_CVM", "SITE_WEB", "DDD_TEL"} & set_cols)
	assert {"WEBSITE", "DDD"} <= set_cols


@pytest.mark.parametrize("cls", DATELESS_READERS, ids=lambda c: c.__name__)
def test_satellites_declare_no_date_column(cls: type[IngestionReader]) -> None:
	"""Both satellites carry no date column, so every column stays exact source text.

	Parameters
	----------
	cls : type[IngestionReader]
		The satellite reader under test.
	"""
	assert cls._DATE_COLS == ()  # type: ignore[attr-defined]
	assert len(cls._CONTRACT.tuple_required) == 2  # type: ignore[attr-defined]


@pytest.mark.parametrize("cls", ALL_READERS, ids=lambda c: c.__name__)
def test_read_selects_its_own_member_with_all_columns(
	cls: type[IngestionReader], monkeypatch: pytest.MonkeyPatch
) -> None:
	"""Each reader returns exactly its member's columns from the shared archive.

	This also proves ``find_member`` selects by exact name: ``cad_crowdfunding.csv`` must not match
	the longer ``cad_crowdfunding_adm_resp.csv`` / ``cad_crowdfunding_socios.csv``.

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

	A satellite declares none, so this asserts nothing for it beyond a successful read — which is
	itself the point: the dateless path must not raise.

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


def test_satellite_columns_are_all_text(monkeypatch: pytest.MonkeyPatch) -> None:
	"""A dateless satellite returns every source column as exact text, never coerced.

	Parameters
	----------
	monkeypatch : pytest.MonkeyPatch
		Fixture used to replace the download boundary.
	"""
	_patch_download(monkeypatch, _zip_bytes(_all_members()))

	df_ = CrowdfundingSociosReader().read()

	assert isinstance(df_["SOCIO"].iloc[0], str)
	assert isinstance(df_["CNPJ"].iloc[0], str)


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


def test_meta_url_is_the_zip_not_a_txt() -> None:
	"""The META lives at a ``.zip`` — the sibling-shaped ``.txt`` guess 404s on this dataset.

	Pinned because the URL is a per-dataset constant that must never be derived from another
	dataset's shape: several roots publish a flat ``meta_<dataset>.txt`` while this one ships a
	three-member archive.
	"""
	from filings_cvm.ingestion.crowdfunding.cad.meta import MetaCrowdfundingReader

	assert MetaCrowdfundingReader._META_URL.endswith("/META/meta_cad_crowdfunding.zip")


def test_meta_section_labels_are_asymmetric_by_design() -> None:
	"""The META's three ``section`` labels are the bare stem plus the two suffixes.

	``meta_cad_crowdfunding.txt`` is named with the bare ``_MEMBER_STEM`` and has no ``<stem>_``
	suffix to strip, so the base's ``_section_of`` falls back to the whole stem; the two siblings
	reduce to ``adm_resp`` and ``socios``. The same asymmetry INTERMED and COORD_OFERTA have.
	Pinned so it stays a recorded source fact rather than something a future change silently
	"tidies".
	"""
	from filings_cvm.ingestion.crowdfunding.cad.meta import MetaCrowdfundingReader

	cls_reader = MetaCrowdfundingReader()
	assert cls_reader._section_of("meta_cad_crowdfunding.txt") == "cad_crowdfunding"
	assert cls_reader._section_of("meta_cad_crowdfunding_adm_resp.txt") == "adm_resp"
	assert cls_reader._section_of("meta_cad_crowdfunding_socios.txt") == "socios"


def test_every_member_is_keyed_by_the_platform_cnpj() -> None:
	"""All three members constrain the platform's ``CNPJ`` — no personal identifier is validated.

	The satellites carry people's names (``ADM_RESP``; ``SOCIO`` mixes natural and legal persons)
	but the source publishes **no** CPF column, so nothing person-level is ever CNPJ-validated.
	"""
	for contract in (CAD_CROWDFUNDING, CAD_CROWDFUNDING_ADM_RESP, CAD_CROWDFUNDING_SOCIOS):
		assert contract.tuple_cnpj_cols == ("CNPJ",)
		assert not any("CPF" in c for c in contract.tuple_required)


def test_read_raises_contract_error_on_missing_required_column(
	monkeypatch: pytest.MonkeyPatch,
) -> None:
	"""Dropping a declared column from the registry member violates its contract.

	Parameters
	----------
	monkeypatch : pytest.MonkeyPatch
		Fixture used to replace the download boundary.
	"""
	dict_members = _all_members()
	list_cols = [c for c in CrowdfundingReader._CONTRACT.tuple_required if c != "DENOM_SOCIAL"]
	dict_members[CrowdfundingReader._MEMBER] = (
		";".join(list_cols) + "\n" + ";".join("x" for _ in list_cols) + "\n"
	)
	_patch_download(monkeypatch, _zip_bytes(dict_members))

	with pytest.raises(ContractError):
		CrowdfundingReader().read()


def test_read_raises_value_error_when_member_absent(monkeypatch: pytest.MonkeyPatch) -> None:
	"""A reader whose member is missing from the archive raises a clear ValueError.

	Parameters
	----------
	monkeypatch : pytest.MonkeyPatch
		Fixture used to replace the download boundary.
	"""
	dict_members = _all_members()
	del dict_members[CrowdfundingSociosReader._MEMBER]
	_patch_download(monkeypatch, _zip_bytes(dict_members))

	with pytest.raises(ValueError, match="cad_crowdfunding_socios.csv"):
		CrowdfundingSociosReader().read()


def test_read_persists_whole_archive_when_path_raw_is_given(
	monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
	"""With ``path_raw`` set, the ZIP and all three members survive a single reader's read.

	Parameters
	----------
	monkeypatch : pytest.MonkeyPatch
		Fixture used to replace the download boundary.
	tmp_path : pathlib.Path
		Pytest-provided scratch directory standing in for the bronze layer.
	"""
	_patch_download(monkeypatch, _zip_bytes(_all_members()))
	path_raw = tmp_path / "bronze"

	CrowdfundingReader(path_raw=path_raw).read()

	assert (path_raw / "cad_crowdfunding.zip").is_file()
	assert {p.name for p in path_raw.glob("*.csv")} == set(_all_members())


def test_read_keeps_cep_as_exact_source_text(monkeypatch: pytest.MonkeyPatch) -> None:
	"""``CEP`` keeps its exact CVM text — leading zeros survive, never coerced to a number.

	The META declares ``CEP`` (like ``TEL``/``DDD``) ``numeric``, but it is an identifier: the
	reader keeps it as source text so a leading zero is not lost.

	Parameters
	----------
	monkeypatch : pytest.MonkeyPatch
		Fixture used to replace the download boundary.
	"""
	dict_members = _all_members()
	cls = CrowdfundingReader
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
		CrowdfundingReader().read(int_timeout_s="nope")
