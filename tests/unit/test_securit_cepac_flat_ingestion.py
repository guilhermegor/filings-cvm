"""Unit tests for the Wave 2 flat-CSV readers (SECURIT DFIN CRA/CRI + EMISSOR_CEPAC CAD).

``DfinCraReader`` / ``DfinCriReader`` read a year-partitioned plain CSV index (``date_ref`` selects
the year; ``Link_Download`` returned as text, not followed). ``CadastroEmissorCepacReader`` reads a
fixed-URL registry **snapshot** — it takes **no** ``date_ref``. A config table drives the shared
assertions; a couple of reader-specific tests cover the year selection and the snapshot's absent
``date_ref``. Mock the single I/O boundary (``download_file``); no network (the autouse
``conftest.py`` guard also blocks any real socket).
"""

from dataclasses import dataclass
from datetime import date
from pathlib import Path

import pytest

from filings_cvm import (
	CadastroEmissorCepacReader,
	DfinCraReader,
	DfinCriReader,
	RetryPolicy,
)
from filings_cvm._internal.config.contracts import (
	CAD_EMISSOR_CEPAC,
	DFIN_CRA,
	DFIN_CRI,
	FileContract,
)
from filings_cvm._internal.config.ports.ingestion_reader import IngestionReader
from filings_cvm._internal.utils.tabular_reader import ContractError


VALID_CNPJ = "11.222.333/0001-81"


@dataclass(frozen=True)
class FlatCase:
	"""One flat-CSV reader's test spec."""

	cls_reader: type[IngestionReader]
	cls_contract: FileContract
	str_module: str  # dotted module path whose download_file is patched
	str_url: str  # the exact URL the reader must request
	str_filename: str  # basename persisted under path_raw
	str_cnpj_col: str
	tuple_date_cols: tuple[str, ...]
	bool_year_partitioned: bool  # True → constructor takes date_ref; False → snapshot, no date_ref


REF = date(2025, 6, 15)

CASES: tuple[FlatCase, ...] = (
	FlatCase(
		DfinCraReader,
		DFIN_CRA,
		"filings_cvm.ingestion.securit.doc.dfin_cra.dfin_cra",
		"https://dados.cvm.gov.br/dados/SECURIT/DOC/DFIN_CRA/DADOS/dfin_cra_2025.csv",
		"dfin_cra_2025.csv",
		"CNPJ_Emissora",
		("Data_Referencia", "Data_Entrega"),
		True,
	),
	FlatCase(
		DfinCriReader,
		DFIN_CRI,
		"filings_cvm.ingestion.securit.doc.dfin_cri.dfin_cri",
		"https://dados.cvm.gov.br/dados/SECURIT/DOC/DFIN_CRI/DADOS/dfin_cri_2025.csv",
		"dfin_cri_2025.csv",
		"CNPJ_Emissora",
		("Data_Referencia", "Data_Entrega"),
		True,
	),
	FlatCase(
		CadastroEmissorCepacReader,
		CAD_EMISSOR_CEPAC,
		"filings_cvm.ingestion.emissor_cepac.cad.cadastro.cadastro",
		"https://dados.cvm.gov.br/dados/EMISSOR_CEPAC/CAD/DADOS/cad_emissor_cepac.csv",
		"cad_emissor_cepac.csv",
		"CNPJ",
		("DT_REG", "DT_CANCEL", "DT_INI_SIT"),
		False,
	),
)
IDS = [case.cls_reader.__name__ for case in CASES]


def _value_for(str_col: str, case: FlatCase) -> str:
	"""Return a plausible source value for one column, by name."""
	if str_col == case.str_cnpj_col:
		return VALID_CNPJ
	if str_col in case.tuple_date_cols:
		return "2025-12-31"
	return "x"


def _default_csv(case: FlatCase) -> str:
	"""Header + one valid row for the case's contract."""
	list_cols = list(case.cls_contract.tuple_required)
	list_row = [_value_for(c, case) for c in list_cols]
	return "\n".join([";".join(list_cols), ";".join(list_row)]) + "\n"


def _build(case: FlatCase, **kwargs: object) -> IngestionReader:
	"""Construct the case's reader, passing ``date_ref`` only when it is year-partitioned."""
	if case.bool_year_partitioned:
		return case.cls_reader(date_ref=REF, **kwargs)  # type: ignore[call-arg]
	return case.cls_reader(**kwargs)  # type: ignore[call-arg]


def _patch(monkeypatch: pytest.MonkeyPatch, case: FlatCase, str_csv: str) -> list[str]:
	"""Patch the case reader's download_file to drop ``str_csv``; capture requested URLs."""
	list_urls: list[str] = []

	def _fake_download(
		str_url: str, path_dest: Path, int_timeout_s: int = 60, retry_policy: object = None
	) -> Path:
		list_urls.append(str_url)
		path_dest.parent.mkdir(parents=True, exist_ok=True)
		path_dest.write_bytes(str_csv.encode("ISO-8859-1"))
		return path_dest

	monkeypatch.setattr(f"{case.str_module}.download_file", _fake_download)
	return list_urls


@pytest.mark.parametrize("case", CASES, ids=IDS)
def test_read_returns_all_contract_columns(
	case: FlatCase, monkeypatch: pytest.MonkeyPatch
) -> None:
	"""Each reader's frame carries exactly its contract's columns (plus provenance).

	Parameters
	----------
	case : FlatCase
		The reader spec under test.
	monkeypatch : pytest.MonkeyPatch
		Fixture used to replace the download boundary.
	"""
	_patch(monkeypatch, case, _default_csv(case))

	df_ = _build(case).read()

	assert len(df_) == 1
	assert list(df_.columns) == list(case.cls_contract.output_columns)


@pytest.mark.parametrize("case", CASES, ids=IDS)
def test_read_coerces_date_columns(case: FlatCase, monkeypatch: pytest.MonkeyPatch) -> None:
	"""Every declared date column becomes a pure ``date`` object.

	Parameters
	----------
	case : FlatCase
		The reader spec under test.
	monkeypatch : pytest.MonkeyPatch
		Fixture used to replace the download boundary.
	"""
	_patch(monkeypatch, case, _default_csv(case))

	df_ = _build(case).read()

	for str_col in case.tuple_date_cols:
		assert df_[str_col].iloc[0] == date(2025, 12, 31)


@pytest.mark.parametrize("case", CASES, ids=IDS)
def test_read_requests_the_expected_url(case: FlatCase, monkeypatch: pytest.MonkeyPatch) -> None:
	"""The reader requests exactly the case's URL.

	Parameters
	----------
	case : FlatCase
		The reader spec under test.
	monkeypatch : pytest.MonkeyPatch
		Fixture used to replace the download boundary.
	"""
	list_urls = _patch(monkeypatch, case, _default_csv(case))

	_build(case).read()

	assert list_urls == [case.str_url]


@pytest.mark.parametrize("case", CASES, ids=IDS)
def test_read_raises_contract_error_on_missing_required_column(
	case: FlatCase, monkeypatch: pytest.MonkeyPatch
) -> None:
	"""Dropping a declared column violates the contract.

	Parameters
	----------
	case : FlatCase
		The reader spec under test.
	monkeypatch : pytest.MonkeyPatch
		Fixture used to replace the download boundary.
	"""
	str_drop = case.cls_contract.tuple_required[-1]
	list_cols = [c for c in case.cls_contract.tuple_required if c != str_drop]
	str_csv = "\n".join([";".join(list_cols), ";".join("x" for _ in list_cols)]) + "\n"
	_patch(monkeypatch, case, str_csv)

	with pytest.raises(ContractError):
		_build(case).read()


@pytest.mark.parametrize("case", CASES, ids=IDS)
def test_read_persists_csv_when_path_raw_is_given(
	case: FlatCase, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
	"""With ``path_raw`` set, the raw CSV survives the read.

	Parameters
	----------
	case : FlatCase
		The reader spec under test.
	monkeypatch : pytest.MonkeyPatch
		Fixture used to replace the download boundary.
	tmp_path : pathlib.Path
		Pytest-provided scratch directory standing in for the bronze layer.
	"""
	_patch(monkeypatch, case, _default_csv(case))
	path_raw = tmp_path / "bronze"

	_build(case, path_raw=path_raw).read()

	assert (path_raw / case.str_filename).is_file()


@pytest.mark.parametrize("case", CASES, ids=IDS)
def test_reader_follows_the_retry_policy_standard(case: FlatCase) -> None:
	"""The reader declares its own ``_RETRY_POLICY`` and lets an instance override it.

	Parameters
	----------
	case : FlatCase
		The reader spec under test.
	"""
	cls_custom = RetryPolicy(int_max_attempts=8)

	assert isinstance(case.cls_reader._RETRY_POLICY, RetryPolicy)  # type: ignore[attr-defined]
	assert _build(case)._retry_policy is case.cls_reader._RETRY_POLICY  # type: ignore[attr-defined]
	assert _build(case, retry_policy=cls_custom)._retry_policy is cls_custom


def test_dfin_keeps_link_download_as_text(monkeypatch: pytest.MonkeyPatch) -> None:
	"""The DFIN index returns ``Link_Download`` as exact text — it is never followed.

	Parameters
	----------
	monkeypatch : pytest.MonkeyPatch
		Fixture used to replace the download boundary.
	"""
	case = CASES[0]
	list_cols = list(case.cls_contract.tuple_required)
	list_row = [_value_for(c, case) for c in list_cols]
	str_link = "https://fnet.bmfbovespa.com.br/fnet/publico/exibirDocumento?id=999"
	list_row[list_cols.index("Link_Download")] = str_link
	str_csv = "\n".join([";".join(list_cols), ";".join(list_row)]) + "\n"
	_patch(monkeypatch, case, str_csv)

	df_ = DfinCraReader(date_ref=REF).read()

	assert df_["Link_Download"].iloc[0] == str_link
	assert isinstance(df_["Link_Download"].iloc[0], str)


def test_dfin_date_ref_selects_the_year(monkeypatch: pytest.MonkeyPatch) -> None:
	"""Only ``date_ref.year`` reaches a DFIN URL — the dump is year-partitioned.

	Parameters
	----------
	monkeypatch : pytest.MonkeyPatch
		Fixture used to replace the download boundary.
	"""
	case = CASES[0]
	list_urls = _patch(monkeypatch, case, _default_csv(case))

	DfinCraReader(date_ref=date(2020, 2, 29)).read()

	assert list_urls == [
		"https://dados.cvm.gov.br/dados/SECURIT/DOC/DFIN_CRA/DADOS/dfin_cra_2020.csv"
	]


def test_cepac_snapshot_takes_no_date_ref() -> None:
	"""The CEPAC registry is a fixed-URL snapshot — its constructor has no ``date_ref``."""
	import inspect

	assert "date_ref" not in set(inspect.signature(CadastroEmissorCepacReader.__init__).parameters)


def test_read_rejects_wrong_argument_type(monkeypatch: pytest.MonkeyPatch) -> None:
	"""The inherited ABCTypeCheckerMeta rejects a mistyped argument at call time.

	Parameters
	----------
	monkeypatch : pytest.MonkeyPatch
		Fixture used to replace the download boundary.
	"""
	case = CASES[2]
	_patch(monkeypatch, case, _default_csv(case))

	with pytest.raises(TypeError):
		CadastroEmissorCepacReader().read(int_timeout_s="nope")
