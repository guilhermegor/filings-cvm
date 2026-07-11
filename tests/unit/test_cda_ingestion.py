"""Unit tests for the CDA FIF ingestion reader.

Mock the single I/O boundary (``download_file``) with a fixture ZIP, then exercise block
consolidation, the ``PL`` left-join, the ``FileContract`` validation, and dtype application
for real — no network.

The fixture mirrors the real ``cda_fi_AAAAMM.zip``: two blocks with *different* layouts
(so the union-of-columns concat is genuinely tested rather than a homogeneous stack), a
``PL`` member at the coarser fund grain, and a ``cda_fie`` member that must be ignored.
"""

from datetime import date
import io
from pathlib import Path
import zipfile

import pandas as pd
import pytest

from filings_cvm._internal.utils.retry import LogEmitter
from filings_cvm._internal.utils.tabular_reader import ContractError
from filings_cvm.ingestion import CdaReader


class _SpyLogger(LogEmitter):
	"""Injected LogEmitter capturing every (message, level) pair instead of emitting it."""

	def __init__(self) -> None:
		"""Start with an empty capture list (no stdlib logger is built)."""
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

	def warnings(self) -> list[str]:
		"""Return only the messages emitted at ``warning`` level."""
		return [msg for msg, level in self.list_calls if level == "warning"]


# CNPJs whose check digits are valid under the repo's ASCII-48 mod-11 routine. CVM ships
# them masked, as here, so the contract's unmasking path is exercised too.
VALID_CNPJ = "11.222.333/0001-81"
OTHER_CNPJ = "11.444.777/0001-61"

# BLC_1 (títulos públicos) — carries CD_SELIC, which BLC_4 does not.
_BLC_1_HEADER = (
	"TP_FUNDO_CLASSE;CNPJ_FUNDO_CLASSE;DENOM_SOCIAL;DT_COMPTC;"
	"TP_APLIC;QT_POS_FINAL;VL_MERC_POS_FINAL;CD_SELIC"
)
_BLC_1_ROW = f"FI;{VALID_CNPJ};FUNDO ALFA;2025-04-30;Títulos públicos;10;1000.50;100000"

# BLC_4 (ações) — carries CD_ATIVO, which BLC_1 does not.
_BLC_4_HEADER = (
	"TP_FUNDO_CLASSE;CNPJ_FUNDO_CLASSE;DENOM_SOCIAL;DT_COMPTC;"
	"TP_APLIC;QT_POS_FINAL;VL_MERC_POS_FINAL;CD_ATIVO"
)
_BLC_4_ROW = f"FI;{VALID_CNPJ};FUNDO ALFA;2025-04-30;Ações;5;2500.25;PETR4"

# PL — the coarser grain: one row per fund per date.
_PL_HEADER = "TP_FUNDO_CLASSE;CNPJ_FUNDO_CLASSE;DENOM_SOCIAL;DT_COMPTC;VL_PATRIM_LIQ"
_PL_ROW = f"FI;{VALID_CNPJ};FUNDO ALFA;2025-04-30;50000.00"

# A member with a wholly different layout that the reader must skip.
_FIE_HEADER = "TP_FUNDO_CLASSE;CNPJ_FUNDO_CLASSE;DENOM_SOCIAL;DT_COMPTC;ID_DOC;VL_PATRIM_LIQ"
_FIE_ROW = f"FI;{OTHER_CNPJ};FUNDO EXTERIOR;2025-04-30;99;123.45"


def _default_members() -> dict[str, str]:
	"""Build the member-name → CSV-text map of a well-formed fixture archive."""
	return {
		"cda_fi_BLC_1_202504.csv": f"{_BLC_1_HEADER}\n{_BLC_1_ROW}\n",
		"cda_fi_BLC_4_202504.csv": f"{_BLC_4_HEADER}\n{_BLC_4_ROW}\n",
		"cda_fi_PL_202504.csv": f"{_PL_HEADER}\n{_PL_ROW}\n",
		"cda_fie_202504.csv": f"{_FIE_HEADER}\n{_FIE_ROW}\n",
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

	def _fake_download(
		str_url: str, path_dest: Path, int_timeout_s: int = 30, retry_policy: object = None
	) -> Path:
		path_dest.parent.mkdir(parents=True, exist_ok=True)
		path_dest.write_bytes(payload)
		return path_dest

	monkeypatch.setattr("filings_cvm.ingestion.fi.doc.cda.download_file", _fake_download)


def _read_default(monkeypatch: pytest.MonkeyPatch) -> pd.DataFrame:
	"""Read the well-formed fixture archive."""
	_patch_download(monkeypatch, _zip_bytes(_default_members()))
	return CdaReader(date_ref=date(2025, 4, 15)).read()


def test_read_consolidates_blocks_tagged_by_source_block(
	monkeypatch: pytest.MonkeyPatch,
) -> None:
	"""Both BLC_* blocks are stacked and tagged with the block they came from.

	Parameters
	----------
	monkeypatch : pytest.MonkeyPatch
		Fixture used to replace the download boundary.
	"""
	df_ = _read_default(monkeypatch)

	assert len(df_) == 2
	assert sorted(df_["BLOCO"]) == ["BLC_1", "BLC_4"]


def test_read_unions_block_specific_columns(monkeypatch: pytest.MonkeyPatch) -> None:
	"""A column defined by only one block is present, and null on the other block's rows.

	Parameters
	----------
	monkeypatch : pytest.MonkeyPatch
		Fixture used to replace the download boundary.
	"""
	df_ = _read_default(monkeypatch).set_index("BLOCO")

	assert df_.loc["BLC_1", "CD_SELIC"] == "100000"
	assert df_.loc["BLC_4", "CD_ATIVO"] == "PETR4"
	# CD_ATIVO does not exist in the BLC_1 layout, so it is null on that block's row.
	assert pd.isna(df_.loc["BLC_1", "CD_ATIVO"])
	assert pd.isna(df_.loc["BLC_4", "CD_SELIC"])


def test_read_joins_fund_net_worth_onto_every_holdings_row(
	monkeypatch: pytest.MonkeyPatch,
) -> None:
	"""PL's VL_PATRIM_LIQ is broadcast onto each of the fund's asset rows.

	This is what makes the *diversificação* half of CDA computable
	(``VL_MERC_POS_FINAL / VL_PATRIM_LIQ``) without a second read.

	Parameters
	----------
	monkeypatch : pytest.MonkeyPatch
		Fixture used to replace the download boundary.
	"""
	df_ = _read_default(monkeypatch)

	assert list(df_["VL_PATRIM_LIQ"]) == ["50000.00", "50000.00"]
	# The PL member's DENOM_SOCIAL is dropped before the merge, so no _x/_y collision.
	assert "DENOM_SOCIAL" in df_.columns
	assert "DENOM_SOCIAL_x" not in df_.columns


def test_read_keeps_money_columns_as_exact_source_text(
	monkeypatch: pytest.MonkeyPatch,
) -> None:
	"""Monetary and quantity columns keep their exact CVM text, never a lossy float.

	Parameters
	----------
	monkeypatch : pytest.MonkeyPatch
		Fixture used to replace the download boundary.
	"""
	df_ = _read_default(monkeypatch).set_index("BLOCO")

	assert df_.loc["BLC_1", "VL_MERC_POS_FINAL"] == "1000.50"
	assert isinstance(df_.loc["BLC_1", "VL_PATRIM_LIQ"], str)
	assert df_.loc["BLC_4", "VL_MERC_POS_FINAL"] == "2500.25"


def test_read_coerces_reference_date_to_date_objects(monkeypatch: pytest.MonkeyPatch) -> None:
	"""DT_COMPTC is coerced to pure date objects on both sides of the join.

	Parameters
	----------
	monkeypatch : pytest.MonkeyPatch
		Fixture used to replace the download boundary.
	"""
	df_ = _read_default(monkeypatch)

	assert df_["DT_COMPTC"].iloc[0] == date(2025, 4, 30)


def test_read_ignores_the_fie_member(monkeypatch: pytest.MonkeyPatch) -> None:
	"""The distinct ``cda_fie`` layout is not mistaken for a ninth block.

	Its CNPJ must appear nowhere in the result, and ``ID_DOC`` must not leak into the
	column union.

	Parameters
	----------
	monkeypatch : pytest.MonkeyPatch
		Fixture used to replace the download boundary.
	"""
	df_ = _read_default(monkeypatch)

	assert "ID_DOC" not in df_.columns
	assert OTHER_CNPJ not in set(df_["CNPJ_FUNDO_CLASSE"])


def test_read_raises_contract_error_on_missing_required_column(
	monkeypatch: pytest.MonkeyPatch,
) -> None:
	"""A block missing the shared DENOM_SOCIAL column violates the contract.

	Parameters
	----------
	monkeypatch : pytest.MonkeyPatch
		Fixture used to replace the download boundary.
	"""
	dict_members = _default_members()
	dict_members["cda_fi_BLC_1_202504.csv"] = (
		"TP_FUNDO_CLASSE;CNPJ_FUNDO_CLASSE;DT_COMPTC;TP_APLIC\n"
		f"FI;{VALID_CNPJ};2025-04-30;Títulos públicos\n"
	)
	_patch_download(monkeypatch, _zip_bytes(dict_members))

	with pytest.raises(ContractError):
		CdaReader(date_ref=date(2025, 4, 15)).read()


def test_read_raises_value_error_when_archive_has_no_block(
	monkeypatch: pytest.MonkeyPatch,
) -> None:
	"""An archive with no BLC_* member raises a clear ValueError.

	Parameters
	----------
	monkeypatch : pytest.MonkeyPatch
		Fixture used to replace the download boundary.
	"""
	dict_members = {"cda_fi_PL_202504.csv": f"{_PL_HEADER}\n{_PL_ROW}\n"}
	_patch_download(monkeypatch, _zip_bytes(dict_members))

	with pytest.raises(ValueError, match="No CDA BLC_. block"):
		CdaReader(date_ref=date(2025, 4, 15)).read()


def test_read_raises_value_error_when_archive_has_no_pl(
	monkeypatch: pytest.MonkeyPatch,
) -> None:
	"""An archive with no PL member raises a clear ValueError.

	Parameters
	----------
	monkeypatch : pytest.MonkeyPatch
		Fixture used to replace the download boundary.
	"""
	dict_members = {"cda_fi_BLC_1_202504.csv": f"{_BLC_1_HEADER}\n{_BLC_1_ROW}\n"}
	_patch_download(monkeypatch, _zip_bytes(dict_members))

	with pytest.raises(ValueError, match="No CDA PL member"):
		CdaReader(date_ref=date(2025, 4, 15)).read()


def test_read_raises_when_pl_has_duplicate_fund_rows(monkeypatch: pytest.MonkeyPatch) -> None:
	"""A duplicated fund/date in PL would fan out holdings rows — the merge must refuse.

	Without ``validate="many_to_one"`` this silently doubles every asset position of the
	affected fund, inflating any downstream sum.

	Parameters
	----------
	monkeypatch : pytest.MonkeyPatch
		Fixture used to replace the download boundary.
	"""
	dict_members = _default_members()
	dict_members["cda_fi_PL_202504.csv"] = f"{_PL_HEADER}\n{_PL_ROW}\n{_PL_ROW}\n"
	_patch_download(monkeypatch, _zip_bytes(dict_members))

	with pytest.raises(pd.errors.MergeError):
		CdaReader(date_ref=date(2025, 4, 15)).read()


def test_read_warns_and_returns_frame_when_a_fund_is_absent_from_pl(
	monkeypatch: pytest.MonkeyPatch,
) -> None:
	"""An unmatched fund yields a null net worth, a warning naming it, and a usable frame.

	The reader deliberately warns rather than raises: one fund missing from PL must not
	cost the caller the month's other good rows.

	Parameters
	----------
	monkeypatch : pytest.MonkeyPatch
		Fixture used to replace the download boundary.
	"""
	dict_members = _default_members()
	# BLC_4 now holds a *second* fund that the PL member never mentions.
	dict_members["cda_fi_BLC_4_202504.csv"] = (
		f"{_BLC_4_HEADER}\n{_BLC_4_ROW}\n"
		f"FI;{OTHER_CNPJ};FUNDO BETA;2025-04-30;Ações;7;700.00;VALE3\n"
	)
	_patch_download(monkeypatch, _zip_bytes(dict_members))
	spy = _SpyLogger()

	df_ = CdaReader(date_ref=date(2025, 4, 15), cls_logger=spy).read()

	# The whole frame comes back; the two matched rows keep their net worth.
	assert len(df_) == 3
	sr_beta = df_["CNPJ_FUNDO_CLASSE"] == OTHER_CNPJ
	assert pd.isna(df_.loc[sr_beta, "VL_PATRIM_LIQ"].iloc[0])
	assert set(df_.loc[~sr_beta, "VL_PATRIM_LIQ"]) == {"50000.00"}

	# ...and exactly one warning names the offending fund.
	list_warnings = spy.warnings()
	assert len(list_warnings) == 1
	assert OTHER_CNPJ in list_warnings[0]
	assert "1 fund(s)" in list_warnings[0]


def test_read_does_not_warn_when_pl_covers_every_fund(monkeypatch: pytest.MonkeyPatch) -> None:
	"""A total join emits no coverage warning — the common case must stay quiet.

	Parameters
	----------
	monkeypatch : pytest.MonkeyPatch
		Fixture used to replace the download boundary.
	"""
	_patch_download(monkeypatch, _zip_bytes(_default_members()))
	spy = _SpyLogger()

	CdaReader(date_ref=date(2025, 4, 15), cls_logger=spy).read()

	assert spy.warnings() == []


def test_read_persists_raw_artifact_when_path_raw_is_given(
	monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
	"""With ``path_raw`` set, the downloaded ZIP and its extracted CSVs survive the read.

	This is what makes a datalake's bronze layer authoritative: the exact bytes that a
	failing transform saw remain on disk, replayable.

	Parameters
	----------
	monkeypatch : pytest.MonkeyPatch
		Fixture used to replace the download boundary.
	tmp_path : pathlib.Path
		Pytest-provided scratch directory standing in for the bronze layer.
	"""
	_patch_download(monkeypatch, _zip_bytes(_default_members()))
	path_raw = tmp_path / "bronze" / "cda" / "202504"

	CdaReader(date_ref=date(2025, 4, 15), path_raw=path_raw).read()

	# The directory is created together with its parents, and holds the untouched artifact
	assert (path_raw / "cda_fi_202504.zip").is_file()
	# alongside everything extracted from it, including the skipped fie member.
	set_names = {p.name for p in path_raw.glob("*.csv")}
	assert set_names == set(_default_members())


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

	CdaReader(date_ref=date(2025, 4, 15)).read()

	assert list(tmp_path.iterdir()) == []


def test_url_reflects_reference_month() -> None:
	"""The download URL is built from the reference month (AAAAMM)."""
	reader = CdaReader(date_ref=date(2025, 3, 9))

	assert reader._str_url.endswith("cda_fi_202503.zip")


def test_read_rejects_wrong_argument_type(monkeypatch: pytest.MonkeyPatch) -> None:
	"""The inherited ABCTypeCheckerMeta rejects a mistyped argument at call time.

	Parameters
	----------
	monkeypatch : pytest.MonkeyPatch
		Fixture used to replace the download boundary.
	"""
	_patch_download(monkeypatch, _zip_bytes(_default_members()))

	with pytest.raises(TypeError):
		CdaReader(date_ref=date(2025, 4, 15)).read(int_timeout_s="nope")
