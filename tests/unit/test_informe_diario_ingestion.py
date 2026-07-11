"""Unit tests for the Informe Diário FIF ingestion reader.

Mock the single I/O boundary (``download_file``) with a fixture ZIP, then exercise
extraction, the ``FileContract`` validation, and dtype application for real — no network.
"""

from datetime import date
import io
from pathlib import Path
import zipfile

import pytest

from filings_cvm._internal.utils.retry import RetryPolicy
from filings_cvm._internal.utils.tabular_reader import ContractError, FileContract
from filings_cvm.ingestion import InformeDiarioReader


# A CNPJ whose check digits are valid under the repo's ASCII-48 mod-11 routine.
VALID_CNPJ = "11222333000181"

_COLUMNS = [
	"TP_FUNDO_CLASSE",
	"CNPJ_FUNDO_CLASSE",
	"ID_SUBCLASSE",
	"DT_COMPTC",
	"VL_TOTAL",
	"VL_QUOTA",
	"VL_PATRIM_LIQ",
	"CAPTC_DIA",
	"RESG_DIA",
	"NR_COTST",
]
_HEADER = ";".join(_COLUMNS)
_ROW = f"FI;{VALID_CNPJ};;2025-01-02;1000.50;1.234567;950.25;100.00;50.00;42"


def _zip_bytes(csv_text: str, member: str = "inf_diario_fi_202501.csv") -> bytes:
	"""Build an in-memory ZIP holding one CSV member with the given text."""
	buffer = io.BytesIO()
	with zipfile.ZipFile(buffer, "w") as cls_zip:
		cls_zip.writestr(member, csv_text.encode("ISO-8859-1"))
	return buffer.getvalue()


def _patch_download(monkeypatch: pytest.MonkeyPatch, payload: bytes) -> None:
	"""Patch the reader's download_file boundary to drop ``payload`` at the destination."""

	def _fake_download(
		str_url: str, path_dest: Path, int_timeout_s: int = 30, retry_policy: object = None
	) -> Path:
		path_dest.parent.mkdir(parents=True, exist_ok=True)
		path_dest.write_bytes(payload)
		return path_dest

	monkeypatch.setattr(
		"filings_cvm.ingestion.fi.doc.informe_diario.download_file", _fake_download
	)


def test_read_forwards_retry_policy_to_download(monkeypatch: pytest.MonkeyPatch) -> None:
	"""The reader hands its ``retry_policy`` through to the ``download_file`` seam.

	Guards the wiring end to end: a construction-time policy must reach the single network
	boundary, or per-source retry tuning would be silently ignored.

	Parameters
	----------
	monkeypatch : pytest.MonkeyPatch
		Fixture used to capture the download boundary's arguments.
	"""
	dict_seen: dict[str, object] = {}

	def _capturing_download(
		str_url: str, path_dest: Path, int_timeout_s: int = 30, retry_policy: object = None
	) -> Path:
		dict_seen["retry_policy"] = retry_policy
		path_dest.parent.mkdir(parents=True, exist_ok=True)
		path_dest.write_bytes(_zip_bytes(f"{_HEADER}\n{_ROW}\n"))
		return path_dest

	monkeypatch.setattr(
		"filings_cvm.ingestion.fi.doc.informe_diario.download_file", _capturing_download
	)
	cls_policy = RetryPolicy(int_max_attempts=7, str_strategy="linear")

	InformeDiarioReader(date_ref=date(2025, 1, 15), retry_policy=cls_policy).read()

	assert dict_seen["retry_policy"] is cls_policy


def test_read_returns_typed_contract_valid_dataframe(monkeypatch: pytest.MonkeyPatch) -> None:
	"""Parse the CSV into a typed frame: date, nullable int, and str-kept money.

	Parameters
	----------
	monkeypatch : pytest.MonkeyPatch
		Fixture used to replace the download boundary.
	"""
	_patch_download(monkeypatch, _zip_bytes(f"{_HEADER}\n{_ROW}\n"))

	df_ = InformeDiarioReader(date_ref=date(2025, 1, 15)).read()

	assert list(df_.columns) == [*_COLUMNS, *FileContract.PROVENANCE_COLUMNS]
	assert len(df_) == 1
	# NR_COTST uses the nullable integer dtype so a blank count would not raise.
	assert str(df_["NR_COTST"].dtype) == "Int64"
	# DT_COMPTC is coerced to pure date objects.
	assert df_["DT_COMPTC"].iloc[0] == date(2025, 1, 2)
	# Monetary columns keep their exact source text, never a lossy float.
	assert isinstance(df_["VL_TOTAL"].iloc[0], str)
	assert df_["VL_TOTAL"].iloc[0] == "1000.50"


def test_read_raises_contract_error_on_missing_required_column(
	monkeypatch: pytest.MonkeyPatch,
) -> None:
	"""A CSV missing the CNPJ column violates the contract and raises ContractError.

	Parameters
	----------
	monkeypatch : pytest.MonkeyPatch
		Fixture used to replace the download boundary.
	"""
	columns = [c for c in _COLUMNS if c != "CNPJ_FUNDO_CLASSE"]
	header = ";".join(columns)
	row = "FI;;2025-01-02;1000.50;1.234567;950.25;100.00;50.00;42"
	_patch_download(monkeypatch, _zip_bytes(f"{header}\n{row}\n"))

	with pytest.raises(ContractError):
		InformeDiarioReader(date_ref=date(2025, 1, 15)).read()


def test_read_raises_value_error_when_zip_has_no_csv(monkeypatch: pytest.MonkeyPatch) -> None:
	"""A ZIP with no CSV member raises a clear ValueError.

	Parameters
	----------
	monkeypatch : pytest.MonkeyPatch
		Fixture used to replace the download boundary.
	"""
	buffer = io.BytesIO()
	with zipfile.ZipFile(buffer, "w") as cls_zip:
		cls_zip.writestr("leiame.txt", b"sem csv aqui")
	_patch_download(monkeypatch, buffer.getvalue())

	with pytest.raises(ValueError, match="No CSV member"):
		InformeDiarioReader(date_ref=date(2025, 1, 15)).read()


def test_read_persists_raw_artifact_when_path_raw_is_given(
	monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
	"""With ``path_raw`` set, the downloaded ZIP and its extracted CSV survive the read.

	Parameters
	----------
	monkeypatch : pytest.MonkeyPatch
		Fixture used to replace the download boundary.
	tmp_path : pathlib.Path
		Pytest-provided scratch directory standing in for the bronze layer.
	"""
	_patch_download(monkeypatch, _zip_bytes(f"{_HEADER}\n{_ROW}\n"))
	path_raw = tmp_path / "bronze" / "informe_diario" / "202501"

	InformeDiarioReader(date_ref=date(2025, 1, 15), path_raw=path_raw).read()

	assert (path_raw / "inf_diario_fi_202501.zip").is_file()
	assert (path_raw / "inf_diario_fi_202501.csv").is_file()


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
	_patch_download(monkeypatch, _zip_bytes(f"{_HEADER}\n{_ROW}\n"))
	monkeypatch.chdir(tmp_path)

	InformeDiarioReader(date_ref=date(2025, 1, 15)).read()

	assert list(tmp_path.iterdir()) == []


def test_url_reflects_reference_month() -> None:
	"""The download URL is built from the reference month (AAAAMM)."""
	reader = InformeDiarioReader(date_ref=date(2025, 3, 9))

	assert reader._str_url.endswith("inf_diario_fi_202503.zip")


def test_read_rejects_wrong_argument_type(monkeypatch: pytest.MonkeyPatch) -> None:
	"""The inherited ABCTypeCheckerMeta rejects a mistyped argument at call time.

	Parameters
	----------
	monkeypatch : pytest.MonkeyPatch
		Fixture used to replace the download boundary.
	"""
	_patch_download(monkeypatch, _zip_bytes(f"{_HEADER}\n{_ROW}\n"))

	with pytest.raises(TypeError):
		InformeDiarioReader(date_ref=date(2025, 1, 15)).read(int_timeout_s="nope")
