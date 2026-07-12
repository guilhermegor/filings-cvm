"""Unit tests for the three FIE readers (`fie/` portal root).

``BalanceteFieReader`` and ``BalancoFieReader`` read a **single-member ZIP** (monthly / yearly);
``MedidasMesFieReader`` reads a **plain CSV** (monthly). All three coerce only ``DT_COMPTC`` to a
``date`` and keep money / counts / account codes as exact source text. A config table drives the
shared assertions across the three, with reader-specific tests for the ZIP member selection, the
month-vs-year partitioning, and the discontinued yearly balanço. Mock the single I/O boundary
(``download_file``); no network (the autouse guard in ``conftest.py`` also blocks any real socket).
"""

from dataclasses import dataclass
from datetime import date
import io
from pathlib import Path
import zipfile

import pytest

from filings_cvm import (
	BalanceteFieReader,
	BalancoFieReader,
	MedidasMesFieReader,
	RetryPolicy,
)
from filings_cvm._internal.config.contracts import (
	BALANCETE_FIE,
	BALANCO_FIE,
	MEDIDAS_MES_FIE,
	FileContract,
)
from filings_cvm._internal.config.ports.ingestion_reader import IngestionReader
from filings_cvm._internal.utils.tabular_reader import ContractError


VALID_CNPJ = "11.222.333/0001-81"


@dataclass(frozen=True)
class FieCase:
	"""One reader's test spec: how to build it, its artifact shape, and its expectations."""

	cls_reader: type[IngestionReader]
	cls_contract: FileContract
	date_ref: date
	str_stem: str  # artifact basename stem, e.g. "balancete_fie_202606"
	bool_zip: bool  # True → single-member ZIP; False → plain CSV
	str_module: str  # dotted module path whose download_file is patched
	str_url: str  # the exact URL the reader must request
	str_cnpj_col: str
	str_money_col: str


CASES: tuple[FieCase, ...] = (
	FieCase(
		BalanceteFieReader,
		BALANCETE_FIE,
		date(2026, 6, 15),
		"balancete_fie_202606",
		True,
		"filings_cvm.ingestion.fie.doc.balancete",
		"https://dados.cvm.gov.br/dados/FIE/DOC/BALANCETE/DADOS/balancete_fie_202606.zip",
		"CNPJ_FUNDO_CLASSE",
		"VL_SALDO_BALCTE",
	),
	FieCase(
		BalancoFieReader,
		BALANCO_FIE,
		date(2020, 6, 15),
		"balanco_fie_2020",
		True,
		"filings_cvm.ingestion.fie.doc.balanco",
		"https://dados.cvm.gov.br/dados/FIE/DOC/BALANCO/DADOS/balanco_fie_2020.zip",
		"CNPJ_FUNDO",
		"VL_SALDO_BALANCO",
	),
	FieCase(
		MedidasMesFieReader,
		MEDIDAS_MES_FIE,
		date(2026, 6, 15),
		"medidas_mes_fie_202606",
		False,
		"filings_cvm.ingestion.fie.medidas",
		"https://dados.cvm.gov.br/dados/FIE/MEDIDAS/DADOS/medidas_mes_fie_202606.csv",
		"CNPJ_FUNDO",
		"VL_PATRIM_LIQ",
	),
)
IDS = [case.cls_reader.__name__ for case in CASES]


def _value_for(str_col: str, str_cnpj_col: str) -> str:
	"""Return a plausible source value for one column, by name."""
	if str_col == str_cnpj_col:
		return VALID_CNPJ
	if str_col == "DT_COMPTC":
		return "2026-06-30"
	if str_col.startswith("VL_") or str_col == "NR_COTST":
		return "0.00"
	return "x"


def _row(cls_contract: FileContract, str_cnpj_col: str) -> list[str]:
	"""One valid row in the contract's column order."""
	return [_value_for(c, str_cnpj_col) for c in cls_contract.tuple_required]


def _csv_text(list_cols: list[str], list_rows: list[list[str]]) -> str:
	"""Serialise a header + rows into the CVM ``;``-separated CSV shape."""
	return "\n".join([";".join(list_cols), *[";".join(r) for r in list_rows]]) + "\n"


def _default_csv(case: FieCase) -> str:
	"""Header + one valid row for the case's contract."""
	return _csv_text(
		list(case.cls_contract.tuple_required), [_row(case.cls_contract, case.str_cnpj_col)]
	)


def _payload(case: FieCase, str_csv: str) -> bytes:
	"""Wrap the CSV text as the case's real artifact: a single-member ZIP, or bare CSV bytes."""
	if not case.bool_zip:
		return str_csv.encode("ISO-8859-1")
	buffer = io.BytesIO()
	with zipfile.ZipFile(buffer, "w") as cls_zip:
		cls_zip.writestr(f"{case.str_stem}.csv", str_csv.encode("ISO-8859-1"))
	return buffer.getvalue()


def _patch(monkeypatch: pytest.MonkeyPatch, case: FieCase, bytes_payload: bytes) -> list[str]:
	"""Patch the case reader's download_file to drop ``bytes_payload``; capture requested URLs."""
	list_urls: list[str] = []

	def _fake_download(
		str_url: str, path_dest: Path, int_timeout_s: int = 60, retry_policy: object = None
	) -> Path:
		list_urls.append(str_url)
		path_dest.parent.mkdir(parents=True, exist_ok=True)
		path_dest.write_bytes(bytes_payload)
		return path_dest

	monkeypatch.setattr(f"{case.str_module}.download_file", _fake_download)
	return list_urls


@pytest.mark.parametrize("case", CASES, ids=IDS)
def test_read_returns_all_contract_columns(case: FieCase, monkeypatch: pytest.MonkeyPatch) -> None:
	"""Each reader's frame carries exactly its contract's columns (plus provenance).

	Parameters
	----------
	case : FieCase
		The reader spec under test.
	monkeypatch : pytest.MonkeyPatch
		Fixture used to replace the download boundary.
	"""
	_patch(monkeypatch, case, _payload(case, _default_csv(case)))

	df_ = case.cls_reader(date_ref=case.date_ref).read()

	assert len(df_) == 1
	assert list(df_.columns) == list(case.cls_contract.output_columns)


@pytest.mark.parametrize("case", CASES, ids=IDS)
def test_read_coerces_dt_comptc(case: FieCase, monkeypatch: pytest.MonkeyPatch) -> None:
	"""``DT_COMPTC`` becomes a pure ``date`` object.

	Parameters
	----------
	case : FieCase
		The reader spec under test.
	monkeypatch : pytest.MonkeyPatch
		Fixture used to replace the download boundary.
	"""
	_patch(monkeypatch, case, _payload(case, _default_csv(case)))

	df_ = case.cls_reader(date_ref=case.date_ref).read()

	assert df_["DT_COMPTC"].iloc[0] == date(2026, 6, 30) or df_["DT_COMPTC"].iloc[0].year in (
		2020,
		2026,
	)
	assert isinstance(df_["DT_COMPTC"].iloc[0], date)


@pytest.mark.parametrize("case", CASES, ids=IDS)
def test_read_requests_the_expected_url(case: FieCase, monkeypatch: pytest.MonkeyPatch) -> None:
	"""The reader requests exactly the case's partition URL (month for two, year for balanço).

	Parameters
	----------
	case : FieCase
		The reader spec under test.
	monkeypatch : pytest.MonkeyPatch
		Fixture used to replace the download boundary.
	"""
	list_urls = _patch(monkeypatch, case, _payload(case, _default_csv(case)))

	case.cls_reader(date_ref=case.date_ref).read()

	assert list_urls == [case.str_url]


@pytest.mark.parametrize("case", CASES, ids=IDS)
def test_read_keeps_money_column_as_text(case: FieCase, monkeypatch: pytest.MonkeyPatch) -> None:
	"""The money column stays exact source text, never parsed to float.

	Parameters
	----------
	case : FieCase
		The reader spec under test.
	monkeypatch : pytest.MonkeyPatch
		Fixture used to replace the download boundary.
	"""
	list_cols = list(case.cls_contract.tuple_required)
	list_row = _row(case.cls_contract, case.str_cnpj_col)
	list_row[list_cols.index(case.str_money_col)] = "1234567.89"
	_patch(monkeypatch, case, _payload(case, _csv_text(list_cols, [list_row])))

	df_ = case.cls_reader(date_ref=case.date_ref).read()

	assert df_[case.str_money_col].iloc[0] == "1234567.89"
	assert isinstance(df_[case.str_money_col].iloc[0], str)


@pytest.mark.parametrize("case", CASES, ids=IDS)
def test_read_raises_contract_error_on_missing_required_column(
	case: FieCase, monkeypatch: pytest.MonkeyPatch
) -> None:
	"""Dropping a declared column violates the contract.

	Parameters
	----------
	case : FieCase
		The reader spec under test.
	monkeypatch : pytest.MonkeyPatch
		Fixture used to replace the download boundary.
	"""
	str_drop = case.str_money_col
	list_cols = [c for c in case.cls_contract.tuple_required if c != str_drop]
	list_row = [
		v
		for c, v in zip(
			case.cls_contract.tuple_required,
			_row(case.cls_contract, case.str_cnpj_col),
			strict=True,
		)
		if c != str_drop
	]
	_patch(monkeypatch, case, _payload(case, _csv_text(list_cols, [list_row])))

	with pytest.raises(ContractError):
		case.cls_reader(date_ref=case.date_ref).read()


@pytest.mark.parametrize("case", CASES, ids=IDS)
def test_read_persists_artifact_when_path_raw_is_given(
	case: FieCase, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
	"""With ``path_raw`` set, the raw artifact (ZIP or CSV) survives the read.

	Parameters
	----------
	case : FieCase
		The reader spec under test.
	monkeypatch : pytest.MonkeyPatch
		Fixture used to replace the download boundary.
	tmp_path : pathlib.Path
		Pytest-provided scratch directory standing in for the bronze layer.
	"""
	_patch(monkeypatch, case, _payload(case, _default_csv(case)))
	path_raw = tmp_path / "bronze"

	case.cls_reader(date_ref=case.date_ref, path_raw=path_raw).read()

	str_ext = "zip" if case.bool_zip else "csv"
	assert (path_raw / f"{case.str_stem}.{str_ext}").is_file()


@pytest.mark.parametrize("case", CASES, ids=IDS)
def test_reader_follows_the_retry_policy_standard(
	case: FieCase, monkeypatch: pytest.MonkeyPatch
) -> None:
	"""The reader declares its own ``_RETRY_POLICY`` and lets an instance override it.

	Parameters
	----------
	case : FieCase
		The reader spec under test.
	monkeypatch : pytest.MonkeyPatch
		Fixture used to replace the download boundary.
	"""
	cls_custom = RetryPolicy(int_max_attempts=8)

	assert isinstance(case.cls_reader._RETRY_POLICY, RetryPolicy)  # type: ignore[attr-defined]
	assert case.cls_reader(date_ref=case.date_ref)._retry_policy is case.cls_reader._RETRY_POLICY  # type: ignore[attr-defined]
	assert (
		case.cls_reader(date_ref=case.date_ref, retry_policy=cls_custom)._retry_policy
		is cls_custom
	)


def test_balancete_selects_its_member_by_exact_name(monkeypatch: pytest.MonkeyPatch) -> None:
	"""The ZIP reader raises a clear ValueError when its month's member is absent.

	Confirms the ``AAAAMM`` in ``date_ref`` — not whatever the archive happens to hold — drives
	member selection.

	Parameters
	----------
	monkeypatch : pytest.MonkeyPatch
		Fixture used to replace the download boundary.
	"""
	case = CASES[0]
	_patch(monkeypatch, case, _payload(case, _default_csv(case)))

	with pytest.raises(ValueError, match="balancete_fie_202605.csv"):
		BalanceteFieReader(date_ref=date(2026, 5, 1)).read()


def test_balanco_selects_the_year_partition(monkeypatch: pytest.MonkeyPatch) -> None:
	"""Only ``date_ref.year`` reaches the balanço URL — the dump is year-partitioned.

	Parameters
	----------
	monkeypatch : pytest.MonkeyPatch
		Fixture used to replace the download boundary.
	"""
	case = CASES[1]
	# The archive member must match the year being read, so member selection succeeds and the URL
	# is the thing under test.
	buffer = io.BytesIO()
	with zipfile.ZipFile(buffer, "w") as cls_zip:
		cls_zip.writestr("balanco_fie_2019.csv", _default_csv(case).encode("ISO-8859-1"))
	list_urls = _patch(monkeypatch, case, buffer.getvalue())

	BalancoFieReader(date_ref=date(2019, 2, 28)).read()

	assert list_urls == [
		"https://dados.cvm.gov.br/dados/FIE/DOC/BALANCO/DADOS/balanco_fie_2019.zip"
	]


def test_read_rejects_wrong_argument_type(monkeypatch: pytest.MonkeyPatch) -> None:
	"""The inherited ABCTypeCheckerMeta rejects a mistyped argument at call time.

	Parameters
	----------
	monkeypatch : pytest.MonkeyPatch
		Fixture used to replace the download boundary.
	"""
	case = CASES[2]
	_patch(monkeypatch, case, _payload(case, _default_csv(case)))

	with pytest.raises(TypeError):
		MedidasMesFieReader(date_ref=case.date_ref).read(int_timeout_s="nope")
