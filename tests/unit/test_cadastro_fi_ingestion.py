"""Unit tests for the CAD/FI (Cadastro de Fundos) ingestion reader.

Mock the single I/O boundary (``download_file``) with a fixture CSV, then exercise the
``FileContract`` validation and dtype application for real — no network.

Two properties of the real artifact are pinned here because both look like defects and are
not: the reader takes **no reference month** (the file is a current-state snapshot), and
``CNPJ_FUNDO`` is **not unique** (a fund keeps its CNPJ across regime migrations).
"""

from datetime import date
from pathlib import Path

import pytest

from filings_cvm._internal.config.contracts.cad_fi import CAD_FI
from filings_cvm._internal.utils.retry import LogEmitter
from filings_cvm._internal.utils.tabular_reader import ContractError
from filings_cvm.ingestion import CadastroFiReader


# CNPJs whose check digits are valid under the repo's ASCII-48 mod-11 routine. CVM ships
# them masked, as here, so the contract's unmasking path is exercised too.
VALID_CNPJ = "11.222.333/0001-81"
OTHER_CNPJ = "11.444.777/0001-61"
# A CPF, which is what CPF_CNPJ_GESTOR holds when PF_PJ_GESTOR == "PF".
VALID_CPF = "111.444.777-35"

_HEADER = ";".join(CAD_FI.tuple_required)


def _row(
	str_cnpj: str,
	str_tp_fundo: str = "FI",
	str_sit: str = "EM FUNCIONAMENTO NORMAL",
	str_dt_reg: str = "2005-03-31",
	str_dt_cancel: str = "",
	str_pf_pj: str = "PJ",
	str_gestor_id: str = OTHER_CNPJ,
) -> str:
	"""Build one 41-field row, overriding only the fields a test cares about."""
	dict_over = {
		"TP_FUNDO": str_tp_fundo,
		"CNPJ_FUNDO": str_cnpj,
		"DENOM_SOCIAL": "FUNDO ALFA",
		"DT_REG": str_dt_reg,
		"DT_CONST": "",
		"DT_CANCEL": str_dt_cancel,
		"SIT": str_sit,
		"DT_INI_SIT": "2008-07-18",
		"DT_INI_ATIV": "",
		"DT_INI_EXERC": "",
		"DT_FIM_EXERC": "",
		"DT_INI_CLASSE": "",
		"DT_PATRIM_LIQ": "2025-04-30",
		"VL_PATRIM_LIQ": "50000.00",
		"TAXA_ADM": "1.50",
		"PF_PJ_GESTOR": str_pf_pj,
		"CPF_CNPJ_GESTOR": str_gestor_id,
	}
	return ";".join(dict_over.get(str_col, "x") for str_col in CAD_FI.tuple_required)


def _default_csv() -> str:
	"""Build a well-formed fixture: one fund re-registered, plus a PF-managed fund."""
	# Same CNPJ under two regimes — the real registry's shape.
	str_old = _row(
		VALID_CNPJ,
		str_tp_fundo="FIF",
		str_sit="CANCELADA",
		str_dt_reg="2003-04-30",
		str_dt_cancel="2005-03-31",
	)
	str_new = _row(VALID_CNPJ, str_tp_fundo="FI")
	str_pf = _row(OTHER_CNPJ, str_pf_pj="PF", str_gestor_id=VALID_CPF)
	return f"{_HEADER}\n{str_old}\n{str_new}\n{str_pf}\n"


def _patch_download(monkeypatch: pytest.MonkeyPatch, str_csv: str) -> None:
	"""Patch the reader's download_file boundary to drop ``str_csv`` at the destination."""

	def _fake_download(str_url: str, path_dest: Path, int_timeout_s: int = 60) -> Path:
		path_dest.parent.mkdir(parents=True, exist_ok=True)
		path_dest.write_bytes(str_csv.encode("ISO-8859-1"))
		return path_dest

	monkeypatch.setattr("filings_cvm.ingestion.cadastro_fi.download_file", _fake_download)


def _read_default(monkeypatch: pytest.MonkeyPatch):  # noqa: ANN202 - pandas DataFrame
	"""Read the well-formed fixture CSV."""
	_patch_download(monkeypatch, _default_csv())
	return CadastroFiReader().read()


def test_read_returns_every_registry_entry(monkeypatch: pytest.MonkeyPatch) -> None:
	"""All rows come back, with all 41 declared columns.

	Parameters
	----------
	monkeypatch : pytest.MonkeyPatch
		Fixture used to replace the download boundary.
	"""
	df_ = _read_default(monkeypatch)

	assert len(df_) == 3
	assert list(df_.columns) == list(CAD_FI.output_columns)


def test_read_keeps_a_cnpj_that_appears_under_two_regimes(
	monkeypatch: pytest.MonkeyPatch,
) -> None:
	"""``CNPJ_FUNDO`` is not unique and the reader must not de-duplicate it.

	A fund keeps its CNPJ across a regulatory-regime migration and is re-registered under a
	new ``TP_FUNDO``. Collapsing those rows would erase the fund's history; keying a merge on
	``CNPJ_FUNDO`` alone would fan rows out. The reader returns what CVM published.

	Parameters
	----------
	monkeypatch : pytest.MonkeyPatch
		Fixture used to replace the download boundary.
	"""
	df_ = _read_default(monkeypatch)

	sr_same = df_["CNPJ_FUNDO"] == VALID_CNPJ
	assert int(sr_same.sum()) == 2
	assert sorted(df_.loc[sr_same, "TP_FUNDO"]) == ["FI", "FIF"]
	assert sorted(df_.loc[sr_same, "SIT"]) == ["CANCELADA", "EM FUNCIONAMENTO NORMAL"]


def test_reader_takes_no_reference_month() -> None:
	"""CAD/FI is a snapshot, so the constructor exposes no ``date_ref``.

	Passing one must fail rather than be silently ignored — a caller who thinks they are
	selecting a month would otherwise get today's registry and never know.
	"""
	import inspect

	set_params = set(inspect.signature(CadastroFiReader.__init__).parameters)

	assert "date_ref" not in set_params
	assert {"path_raw", "cls_logger"} <= set_params
	with pytest.raises(TypeError):
		CadastroFiReader(date_ref=date(2025, 4, 1))


def test_read_coerces_every_date_column(monkeypatch: pytest.MonkeyPatch) -> None:
	"""The nine ``DT_*`` columns become pure date objects; a blank becomes NaT.

	Parameters
	----------
	monkeypatch : pytest.MonkeyPatch
		Fixture used to replace the download boundary.
	"""
	import pandas as pd

	df_ = _read_default(monkeypatch)

	assert df_["DT_REG"].iloc[0] == date(2003, 4, 30)
	assert df_["DT_CANCEL"].iloc[0] == date(2005, 3, 31)
	assert df_["DT_PATRIM_LIQ"].iloc[0] == date(2025, 4, 30)
	# The second row was never cancelled.
	assert pd.isna(df_["DT_CANCEL"].iloc[1])
	assert pd.isna(df_["DT_INI_ATIV"].iloc[0])


def test_read_accepts_a_cpf_in_the_manager_identifier_column(
	monkeypatch: pytest.MonkeyPatch,
) -> None:
	"""``CPF_CNPJ_GESTOR`` holds a CPF when the manager is a natural person.

	It is therefore read as text and never validated as a CNPJ — doing so would reject a
	valid registry.

	Parameters
	----------
	monkeypatch : pytest.MonkeyPatch
		Fixture used to replace the download boundary.
	"""
	df_ = _read_default(monkeypatch)

	sr_pf = df_["PF_PJ_GESTOR"] == "PF"
	assert df_.loc[sr_pf, "CPF_CNPJ_GESTOR"].iloc[0] == VALID_CPF
	assert "CPF_CNPJ_GESTOR" not in CAD_FI.tuple_cnpj_cols


def test_read_keeps_money_columns_as_exact_source_text(
	monkeypatch: pytest.MonkeyPatch,
) -> None:
	"""Monetary and fee columns keep their exact CVM text, never a lossy float.

	Parameters
	----------
	monkeypatch : pytest.MonkeyPatch
		Fixture used to replace the download boundary.
	"""
	df_ = _read_default(monkeypatch)

	assert df_["VL_PATRIM_LIQ"].iloc[0] == "50000.00"
	assert df_["TAXA_ADM"].iloc[0] == "1.50"


def test_dtype_map_covers_every_non_date_column() -> None:
	"""The derived dtype map and the date columns together span the whole contract."""
	from filings_cvm.ingestion.cadastro_fi import _DATE_COLS, _DTYPES

	assert set(_DTYPES) | set(_DATE_COLS) == set(CAD_FI.tuple_required)
	assert not set(_DTYPES) & set(_DATE_COLS)


def test_read_raises_contract_error_on_missing_required_column(
	monkeypatch: pytest.MonkeyPatch,
) -> None:
	"""Dropping any of the 41 declared columns violates the contract.

	Parameters
	----------
	monkeypatch : pytest.MonkeyPatch
		Fixture used to replace the download boundary.
	"""
	list_cols = [c for c in CAD_FI.tuple_required if c != "CLASSE_ANBIMA"]
	str_csv = ";".join(list_cols) + "\n" + ";".join("x" for _ in list_cols) + "\n"
	_patch_download(monkeypatch, str_csv)

	with pytest.raises(ContractError):
		CadastroFiReader().read()


def test_read_persists_raw_snapshot_when_path_raw_is_given(
	monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
	"""With ``path_raw`` set, the snapshot survives the read.

	CVM overwrites ``cad_fi.csv`` in place, so a persisted snapshot is the only record of
	what the registry said that day — it cannot be re-fetched.

	Parameters
	----------
	monkeypatch : pytest.MonkeyPatch
		Fixture used to replace the download boundary.
	tmp_path : pathlib.Path
		Pytest-provided scratch directory standing in for the bronze layer.
	"""
	_patch_download(monkeypatch, _default_csv())
	path_raw = tmp_path / "bronze" / "cad_fi" / "20250430"

	CadastroFiReader(path_raw=path_raw).read()

	assert (path_raw / "cad_fi.csv").is_file()


def test_read_leaves_no_artifact_on_disk_when_path_raw_is_none(
	monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
	"""Without ``path_raw`` the snapshot lands in a temp dir and is discarded.

	Parameters
	----------
	monkeypatch : pytest.MonkeyPatch
		Fixture used to replace the download boundary.
	tmp_path : pathlib.Path
		Scratch directory asserted to stay empty.
	"""
	_patch_download(monkeypatch, _default_csv())
	monkeypatch.chdir(tmp_path)

	CadastroFiReader().read()

	assert list(tmp_path.iterdir()) == []


def test_read_logs_entry_and_distinct_cnpj_counts(monkeypatch: pytest.MonkeyPatch) -> None:
	"""The summary distinguishes rows from distinct CNPJs — they are not the same number.

	Parameters
	----------
	monkeypatch : pytest.MonkeyPatch
		Fixture used to replace the download boundary.
	"""

	class _SpyLogger(LogEmitter):
		"""Capture emitted messages instead of logging them."""

		def __init__(self) -> None:
			"""Start with an empty capture list."""
			self.list_calls: list[tuple[str, str]] = []

		def log_message(self, str_message: str, str_level: str) -> None:
			"""Record the message and level.

			Parameters
			----------
			str_message : str
				The emitted message.
			str_level : str
				The severity it was emitted at.
			"""
			self.list_calls.append((str_message, str_level))

	_patch_download(monkeypatch, _default_csv())
	spy = _SpyLogger()

	CadastroFiReader(cls_logger=spy).read()

	str_summary = spy.list_calls[-1][0]
	assert "3 registry entries" in str_summary
	assert "2 distinct CNPJs" in str_summary


def test_read_rejects_wrong_argument_type(monkeypatch: pytest.MonkeyPatch) -> None:
	"""The inherited ABCTypeCheckerMeta rejects a mistyped argument at call time.

	Parameters
	----------
	monkeypatch : pytest.MonkeyPatch
		Fixture used to replace the download boundary.
	"""
	_patch_download(monkeypatch, _default_csv())

	with pytest.raises(TypeError):
		CadastroFiReader().read(int_timeout_s="nope")
