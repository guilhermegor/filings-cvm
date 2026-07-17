"""Unit tests for the DFIN FII index reader.

``DfinFiiReader`` reads ``dfin_fii_AAAA.csv`` — a plain CSV (not a ZIP), partitioned by **year**,
that indexes the financial statements a FII delivered. The reader returns the ``Link_Download``
column as text and must **not** follow it. Mock the single I/O boundary (``download_file``); no
network (the autouse guard in ``conftest.py`` also blocks any real socket).
"""

from datetime import date
from pathlib import Path

import pytest

from filings_cvm import DfinFiiReader, RetryPolicy
from filings_cvm._internal.config.contracts import DFIN_FII
from filings_cvm._internal.utils.tabular_reader import ContractError


VALID_CNPJ = "11.222.333/0001-81"
REF = date(2025, 6, 15)
YEAR = "2025"

_LINK = "https://fnet.bmfbovespa.com.br/fnet/publico/downloadDocumento?id=1024849"


def _csv(list_cols: list[str], list_rows: list[list[str]]) -> str:
	"""Serialise a header + rows into the CVM ``;``-separated, ISO-8859-1 CSV shape."""
	lines = [";".join(list_cols)] + [";".join(r) for r in list_rows]
	return "\n".join(lines) + "\n"


def _valid_row() -> list[str]:
	"""One valid DFIN row, in the contract's column order."""
	return [
		"CLASSES - FII",  # Tipo_Fundo_Classe
		VALID_CNPJ,  # CNPJ_Fundo_Classe
		"VIA PARQUE SHOPPING FII",  # Nome_Fundo_Classe
		"2025-07-31",  # Data_Referencia
		"1",  # Versao
		"2025-10-30",  # Data_Entrega
		_LINK,  # Link_Download
		"Sem ressalva e sem ênfase",  # Parecer_Auditor
	]


def _default_csv() -> str:
	"""Header + one valid row for the DFIN contract."""
	return _csv(list(DFIN_FII.tuple_required), [_valid_row()])


def _patch_download(monkeypatch: pytest.MonkeyPatch, str_text: str) -> list[str]:
	"""Patch the reader's download_file boundary to drop ``str_text``; capture requested URLs."""
	list_urls: list[str] = []

	def _fake_download(
		str_url: str, path_dest: Path, int_timeout_s: int = 60, retry_policy: object = None
	) -> Path:
		list_urls.append(str_url)
		path_dest.parent.mkdir(parents=True, exist_ok=True)
		path_dest.write_bytes(str_text.encode("ISO-8859-1"))
		return path_dest

	monkeypatch.setattr("filings_cvm.ingestion.fii.doc.dfin.dfin.download_file", _fake_download)
	return list_urls


def test_read_returns_all_contract_columns(monkeypatch: pytest.MonkeyPatch) -> None:
	"""The frame carries exactly the contract's columns (plus provenance).

	Parameters
	----------
	monkeypatch : pytest.MonkeyPatch
		Fixture used to replace the download boundary.
	"""
	_patch_download(monkeypatch, _default_csv())

	df_ = DfinFiiReader(date_ref=REF).read()

	assert len(df_) == 1
	assert list(df_.columns) == list(DFIN_FII.output_columns)


def test_read_coerces_both_date_columns(monkeypatch: pytest.MonkeyPatch) -> None:
	"""``Data_Referencia`` and ``Data_Entrega`` become pure ``date`` objects.

	Parameters
	----------
	monkeypatch : pytest.MonkeyPatch
		Fixture used to replace the download boundary.
	"""
	_patch_download(monkeypatch, _default_csv())

	df_ = DfinFiiReader(date_ref=REF).read()

	assert df_["Data_Referencia"].iloc[0] == date(2025, 7, 31)
	assert df_["Data_Entrega"].iloc[0] == date(2025, 10, 30)


def test_read_returns_link_download_as_text_and_does_not_follow_it(
	monkeypatch: pytest.MonkeyPatch,
) -> None:
	"""``Link_Download`` is exact source text; the only URL fetched is the DFIN CSV itself.

	The reader indexes documents — it must not download the linked statements.

	Parameters
	----------
	monkeypatch : pytest.MonkeyPatch
		Fixture used to replace the download boundary.
	"""
	list_urls = _patch_download(monkeypatch, _default_csv())

	df_ = DfinFiiReader(date_ref=REF).read()

	assert df_["Link_Download"].iloc[0] == _LINK
	assert isinstance(df_["Link_Download"].iloc[0], str)
	# The fnet link is never requested — only the year's index CSV is.
	assert list_urls == ["https://dados.cvm.gov.br/dados/FII/DOC/DFIN/DADOS/dfin_fii_2025.csv"]
	assert not any("fnet" in str_url for str_url in list_urls)


def test_date_ref_selects_the_year(monkeypatch: pytest.MonkeyPatch) -> None:
	"""Only ``date_ref.year`` reaches the URL — the dump is year-partitioned.

	Parameters
	----------
	monkeypatch : pytest.MonkeyPatch
		Fixture used to replace the download boundary.
	"""
	list_urls = _patch_download(monkeypatch, _default_csv())

	DfinFiiReader(date_ref=date(2024, 2, 29)).read()

	assert list_urls == ["https://dados.cvm.gov.br/dados/FII/DOC/DFIN/DADOS/dfin_fii_2024.csv"]


def test_read_keeps_versao_as_text(monkeypatch: pytest.MonkeyPatch) -> None:
	"""``Versao`` stays exact source text, never coerced to a number.

	Parameters
	----------
	monkeypatch : pytest.MonkeyPatch
		Fixture used to replace the download boundary.
	"""
	_patch_download(monkeypatch, _default_csv())

	df_ = DfinFiiReader(date_ref=REF).read()

	assert df_["Versao"].iloc[0] == "1"
	assert isinstance(df_["Versao"].iloc[0], str)


def test_read_raises_contract_error_on_missing_required_column(
	monkeypatch: pytest.MonkeyPatch,
) -> None:
	"""Dropping a declared column violates the contract.

	Parameters
	----------
	monkeypatch : pytest.MonkeyPatch
		Fixture used to replace the download boundary.
	"""
	list_cols = [c for c in DFIN_FII.tuple_required if c != "Link_Download"]
	list_row = [
		v
		for c, v in zip(DFIN_FII.tuple_required, _valid_row(), strict=True)
		if c != "Link_Download"
	]
	_patch_download(monkeypatch, _csv(list_cols, [list_row]))

	with pytest.raises(ContractError):
		DfinFiiReader(date_ref=REF).read()


def test_read_persists_csv_when_path_raw_is_given(
	monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
	"""With ``path_raw`` set, the raw CSV survives the read.

	Parameters
	----------
	monkeypatch : pytest.MonkeyPatch
		Fixture used to replace the download boundary.
	tmp_path : pathlib.Path
		Pytest-provided scratch directory standing in for the bronze layer.
	"""
	_patch_download(monkeypatch, _default_csv())
	path_raw = tmp_path / "bronze"

	DfinFiiReader(date_ref=REF, path_raw=path_raw).read()

	assert (path_raw / f"dfin_fii_{YEAR}.csv").is_file()


def test_reader_follows_the_retry_policy_standard(monkeypatch: pytest.MonkeyPatch) -> None:
	"""The reader declares its own ``_RETRY_POLICY`` and lets an instance override it.

	Parameters
	----------
	monkeypatch : pytest.MonkeyPatch
		Fixture used to replace the download boundary.
	"""
	cls_custom = RetryPolicy(int_max_attempts=8)

	assert isinstance(DfinFiiReader._RETRY_POLICY, RetryPolicy)
	assert DfinFiiReader(date_ref=REF)._retry_policy is DfinFiiReader._RETRY_POLICY
	assert DfinFiiReader(date_ref=REF, retry_policy=cls_custom)._retry_policy is cls_custom


def test_read_rejects_wrong_argument_type(monkeypatch: pytest.MonkeyPatch) -> None:
	"""The inherited ABCTypeCheckerMeta rejects a mistyped argument at call time.

	Parameters
	----------
	monkeypatch : pytest.MonkeyPatch
		Fixture used to replace the download boundary.
	"""
	_patch_download(monkeypatch, _default_csv())

	with pytest.raises(TypeError):
		DfinFiiReader(date_ref=REF).read(int_timeout_s="nope")
