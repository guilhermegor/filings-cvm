"""Unit tests for the Lâmina carteira FIF ingestion reader.

Mock the single I/O boundary (``download_file``) with a fixture ZIP, then exercise member
selection, the ``FileContract`` validation, and dtype application for real — no network.

The fixture mirrors the real ``lamina_fi_AAAAMM.zip``: the ``carteira`` member alongside
the three siblings (the lâmina proper and two ``rentab_*`` series) that share its
``lamina_fi_`` prefix and must not be mistaken for it.
"""

from datetime import date
import io
from pathlib import Path
import zipfile

import pandas as pd
import pytest

from filings_cvm._internal.utils.retry import LogEmitter
from filings_cvm._internal.utils.tabular_reader import ContractError, FileContract
from filings_cvm.ingestion import LaminaCarteiraReader


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


# CNPJs whose check digits are valid under the repo's ASCII-48 mod-11 routine. CVM ships
# them masked, as here, so the contract's unmasking path is exercised too.
VALID_CNPJ = "11.222.333/0001-81"
OTHER_CNPJ = "11.444.777/0001-61"

_HEADER = (
	"TP_FUNDO_CLASSE;CNPJ_FUNDO_CLASSE;ID_SUBCLASSE;DENOM_SOCIAL;DT_COMPTC;TP_ATIVO;PR_PL_ATIVO"
)
# ID_SUBCLASSE is empty on every real 2025-04 row; keep it so here.
_ROW_COTAS = f"CLASSES - FIF;{VALID_CNPJ};;FUNDO ALFA;2025-04-30;Cotas de fundos 409;69.58"
_ROW_DEPOSITOS = f"CLASSES - FIF;{VALID_CNPJ};;FUNDO ALFA;2025-04-30;Depósitos a prazo;5.26"
# A leveraged fund's short exposure: PR_PL_ATIVO is signed and totals may exceed 100.
_ROW_SHORT = f"CLASSES - FIF;{OTHER_CNPJ};;FUNDO BETA;2025-04-30;Mercado futuro;-37.08"


def _default_members() -> dict[str, str]:
	"""Build the member-name → CSV-text map of a well-formed fixture archive."""
	return {
		"lamina_fi_carteira_202504.csv": (
			f"{_HEADER}\n{_ROW_COTAS}\n{_ROW_DEPOSITOS}\n{_ROW_SHORT}\n"
		),
		# Siblings sharing the ``lamina_fi_`` prefix — none may be read in its place.
		"lamina_fi_202504.csv": f"CNPJ_FUNDO_CLASSE;PR_RENTAB_ANO\n{VALID_CNPJ};1.23\n",
		"lamina_fi_rentab_ano_202504.csv": f"CNPJ_FUNDO_CLASSE;ANO\n{VALID_CNPJ};2025\n",
		"lamina_fi_rentab_mes_202504.csv": f"CNPJ_FUNDO_CLASSE;MES\n{VALID_CNPJ};4\n",
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

	def _fake_download(str_url: str, path_dest: Path, int_timeout_s: int = 30) -> Path:
		path_dest.parent.mkdir(parents=True, exist_ok=True)
		path_dest.write_bytes(payload)
		return path_dest

	monkeypatch.setattr("filings_cvm.ingestion.lamina_carteira.download_file", _fake_download)


def _read_default(monkeypatch: pytest.MonkeyPatch) -> pd.DataFrame:
	"""Read the well-formed fixture archive."""
	_patch_download(monkeypatch, _zip_bytes(_default_members()))
	return LaminaCarteiraReader(date_ref=date(2025, 4, 15)).read()


def test_read_returns_one_row_per_fund_and_asset_type(monkeypatch: pytest.MonkeyPatch) -> None:
	"""The carteira member's rows come back at the fund × asset-type grain.

	Parameters
	----------
	monkeypatch : pytest.MonkeyPatch
		Fixture used to replace the download boundary.
	"""
	df_ = _read_default(monkeypatch)

	assert len(df_) == 3
	assert list(df_.columns) == [
		"TP_FUNDO_CLASSE",
		"CNPJ_FUNDO_CLASSE",
		"ID_SUBCLASSE",
		"DENOM_SOCIAL",
		"DT_COMPTC",
		"TP_ATIVO",
		"PR_PL_ATIVO",
		*FileContract.PROVENANCE_COLUMNS,
	]
	assert sorted(df_["TP_ATIVO"]) == [
		"Cotas de fundos 409",
		"Depósitos a prazo",
		"Mercado futuro",
	]


def test_read_ignores_the_sibling_lamina_members(monkeypatch: pytest.MonkeyPatch) -> None:
	"""``lamina_fi_*`` and ``lamina_fi_rentab_*`` share a prefix but must not be read.

	Their columns would leak in were the member matched on the shorter ``lamina_fi_``.

	Parameters
	----------
	monkeypatch : pytest.MonkeyPatch
		Fixture used to replace the download boundary.
	"""
	df_ = _read_default(monkeypatch)

	assert "PR_RENTAB_ANO" not in df_.columns
	assert "ANO" not in df_.columns
	assert "MES" not in df_.columns


def test_read_keeps_allocation_share_as_exact_source_text(
	monkeypatch: pytest.MonkeyPatch,
) -> None:
	"""PR_PL_ATIVO keeps its exact CVM decimal text, never a lossy float.

	Parameters
	----------
	monkeypatch : pytest.MonkeyPatch
		Fixture used to replace the download boundary.
	"""
	df_ = _read_default(monkeypatch).set_index("TP_ATIVO")

	assert df_.loc["Cotas de fundos 409", "PR_PL_ATIVO"] == "69.58"
	assert isinstance(df_.loc["Depósitos a prazo", "PR_PL_ATIVO"], str)


def test_read_preserves_negative_allocation_shares(monkeypatch: pytest.MonkeyPatch) -> None:
	"""A short/leveraged position's negative share survives the read unaltered.

	The reader asserts no "shares total 100%" invariant: real 2025-04 per-fund totals ran
	from -37.08 to 1123.00, so such a check would reject valid leveraged funds.

	Parameters
	----------
	monkeypatch : pytest.MonkeyPatch
		Fixture used to replace the download boundary.
	"""
	df_ = _read_default(monkeypatch).set_index("TP_ATIVO")

	assert df_.loc["Mercado futuro", "PR_PL_ATIVO"] == "-37.08"


def test_read_coerces_reference_date_to_date_objects(monkeypatch: pytest.MonkeyPatch) -> None:
	"""DT_COMPTC is coerced to pure date objects.

	Parameters
	----------
	monkeypatch : pytest.MonkeyPatch
		Fixture used to replace the download boundary.
	"""
	df_ = _read_default(monkeypatch)

	assert df_["DT_COMPTC"].iloc[0] == date(2025, 4, 30)


def test_read_tolerates_an_empty_id_subclasse(monkeypatch: pytest.MonkeyPatch) -> None:
	"""ID_SUBCLASSE is required as a column but empty on every real row today.

	Parameters
	----------
	monkeypatch : pytest.MonkeyPatch
		Fixture used to replace the download boundary.
	"""
	df_ = _read_default(monkeypatch)

	assert "ID_SUBCLASSE" in df_.columns
	assert df_["ID_SUBCLASSE"].isna().all()


def test_read_raises_contract_error_on_missing_required_column(
	monkeypatch: pytest.MonkeyPatch,
) -> None:
	"""A carteira member missing PR_PL_ATIVO violates the contract.

	Parameters
	----------
	monkeypatch : pytest.MonkeyPatch
		Fixture used to replace the download boundary.
	"""
	dict_members = _default_members()
	dict_members["lamina_fi_carteira_202504.csv"] = (
		"TP_FUNDO_CLASSE;CNPJ_FUNDO_CLASSE;ID_SUBCLASSE;DENOM_SOCIAL;DT_COMPTC;TP_ATIVO\n"
		f"CLASSES - FIF;{VALID_CNPJ};;FUNDO ALFA;2025-04-30;Cotas de fundos 409\n"
	)
	_patch_download(monkeypatch, _zip_bytes(dict_members))

	with pytest.raises(ContractError):
		LaminaCarteiraReader(date_ref=date(2025, 4, 15)).read()


def test_read_raises_value_error_when_archive_has_no_carteira_member(
	monkeypatch: pytest.MonkeyPatch,
) -> None:
	"""An archive holding only the siblings raises a clear ValueError.

	Parameters
	----------
	monkeypatch : pytest.MonkeyPatch
		Fixture used to replace the download boundary.
	"""
	dict_members = _default_members()
	del dict_members["lamina_fi_carteira_202504.csv"]
	_patch_download(monkeypatch, _zip_bytes(dict_members))

	with pytest.raises(ValueError, match="lamina_fi_carteira_202504.csv"):
		LaminaCarteiraReader(date_ref=date(2025, 4, 15)).read()


def test_read_persists_raw_artifact_when_path_raw_is_given(
	monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
	"""With ``path_raw`` set, the ZIP and *every* extracted CSV survive the read.

	Not just the member this reader wants: the bronze layer keeps the whole artifact, so a
	later reader (the lâmina proper) replays the same bytes rather than re-fetching a
	source that may already have changed.

	Parameters
	----------
	monkeypatch : pytest.MonkeyPatch
		Fixture used to replace the download boundary.
	tmp_path : pathlib.Path
		Pytest-provided scratch directory standing in for the bronze layer.
	"""
	_patch_download(monkeypatch, _zip_bytes(_default_members()))
	path_raw = tmp_path / "bronze" / "lamina" / "202504"

	LaminaCarteiraReader(date_ref=date(2025, 4, 15), path_raw=path_raw).read()

	assert (path_raw / "lamina_fi_202504.zip").is_file()
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

	LaminaCarteiraReader(date_ref=date(2025, 4, 15)).read()

	assert list(tmp_path.iterdir()) == []


def test_read_logs_the_asset_type_count(monkeypatch: pytest.MonkeyPatch) -> None:
	"""The summary line reports rows loaded and distinct asset types.

	Parameters
	----------
	monkeypatch : pytest.MonkeyPatch
		Fixture used to replace the download boundary.
	"""
	_patch_download(monkeypatch, _zip_bytes(_default_members()))
	spy = _SpyLogger()

	LaminaCarteiraReader(date_ref=date(2025, 4, 15), cls_logger=spy).read()

	str_summary = spy.list_calls[-1][0]
	assert "3 allocation rows" in str_summary
	assert "3 asset types" in str_summary


def test_url_reflects_reference_month() -> None:
	"""The download URL is built from the reference month (AAAAMM)."""
	reader = LaminaCarteiraReader(date_ref=date(2025, 3, 9))

	assert reader._str_url.endswith("lamina_fi_202503.zip")


def test_read_rejects_wrong_argument_type(monkeypatch: pytest.MonkeyPatch) -> None:
	"""The inherited ABCTypeCheckerMeta rejects a mistyped argument at call time.

	Parameters
	----------
	monkeypatch : pytest.MonkeyPatch
		Fixture used to replace the download boundary.
	"""
	_patch_download(monkeypatch, _zip_bytes(_default_members()))

	with pytest.raises(TypeError):
		LaminaCarteiraReader(date_ref=date(2025, 4, 15)).read(int_timeout_s="nope")
