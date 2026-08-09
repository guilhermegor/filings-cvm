"""Unit tests for the FI/DOC/EXTRATO readers.

The dataset publishes **two artifacts**: `extrato_fi_AAAA.csv` (every filing of that year) and
`extrato_fi.csv` (a fixed-URL snapshot: the latest filing per fund). The yearly series also changed
schema at 2020 — 116 columns keyed by `CNPJ_FUNDO` through 2019, 117 keyed by `TP_FUNDO_CLASSE` +
`CNPJ_FUNDO_CLASSE` from 2020.

Four things carry the weight here:

1. each of the three contracts is compared against the **verbatim header bytes CVM publishes**;
2. the two yearly regimes share **115 of their columns**, so the difference is pinned *exactly*;
3. the snapshot shares the current header **and is a different artifact** — same columns, different
   grain, different `source_key`, no `date_ref`;
4. only `DT_COMPTC` is a date — `PRAZO` holds `DD/MM/YYYY` strings and must stay text.

Mock the single I/O boundary (`download_file` in the shared base); no network.
"""

from datetime import date
from pathlib import Path

import pytest

from filings_cvm._internal.config.contracts import (
	EXTRATO_FI,
	EXTRATO_FI_PRE2020,
	EXTRATO_FI_SNAPSHOT,
)
from filings_cvm._internal.utils.tabular_reader import ContractError
from filings_cvm.ingestion.fi import (
	ExtratoFiPre2020Reader,
	ExtratoFiReader,
	ExtratoFiSnapshotReader,
	MetaExtratoFiReader,
)


VALID_CNPJ = "11.222.333/0001-81"
REF = date(2025, 6, 15)
BASE = "https://dados.cvm.gov.br/dados/FI/DOC/EXTRATO/DADOS/"
PATH_FIXTURES = Path(__file__).resolve().parents[1] / "fixtures" / "extrato_fi"


def _csv(list_cols: list[str], list_rows: list[list[str]]) -> str:
	"""Serialise a header + rows into the CVM ``;``-separated, ISO-8859-1 CSV shape."""
	return "\n".join([";".join(list_cols)] + [";".join(r) for r in list_rows]) + "\n"


def _row_for(
	tuple_cols: tuple[str, ...], dict_overrides: dict[str, str] | None = None
) -> list[str]:
	"""Build one row for ``tuple_cols``, filling each column with a plausible measured value."""
	dict_values: dict[str, str] = {
		"TP_FUNDO_CLASSE": "CLASSES - FIF",
		"CNPJ_FUNDO_CLASSE": VALID_CNPJ,
		"CNPJ_FUNDO": VALID_CNPJ,
		"DENOM_SOCIAL": "FUNDO DE INVESTIMENTO FINANCEIRO EXEMPLO",
		"DT_COMPTC": "2025-01-02",
		# varchar in the META, and full of DD/MM/YYYY in the real file — never a date column.
		"PRAZO": "01/03/2033",
		"CONDOM": "Aberto",
		# Twelve decimal places, exactly as CVM publishes them; the scale is load-bearing.
		"TAXA_PERFM": "0.010000000000",
		"TAXA_ADM": "0.500000000000",
		"INF_TAXA_PERFM": "% a superar: 35% CDI + 65 % IBrX + 0,755%",
	}
	dict_values.update(dict_overrides or {})
	return [dict_values.get(str_col, "0") for str_col in tuple_cols]


def _default_csv(tuple_cols: tuple[str, ...], dict_overrides: dict[str, str] | None = None) -> str:
	"""Header + one valid row for the given contract's columns."""
	return _csv(list(tuple_cols), [_row_for(tuple_cols, dict_overrides)])


def _patch_download(monkeypatch: pytest.MonkeyPatch, str_text: str) -> list[str]:
	"""Patch the shared base's download_file boundary; capture requested URLs."""
	list_urls: list[str] = []

	def _fake_download(
		str_url: str, path_dest: Path, int_timeout_s: int = 60, retry_policy: object = None
	) -> Path:
		list_urls.append(str_url)
		path_dest.parent.mkdir(parents=True, exist_ok=True)
		path_dest.write_bytes(str_text.encode("ISO-8859-1"))
		return path_dest

	monkeypatch.setattr(
		"filings_cvm.ingestion.fi.doc.extrato._base_extrato_reader.download_file", _fake_download
	)
	return list_urls


# ---- the pinned oracle -------------------------------------------------------------------------


@pytest.mark.parametrize(
	("contract", "str_fixture", "int_cols"),
	[
		(EXTRATO_FI, "extrato_fi_header.csv", 117),
		(EXTRATO_FI_PRE2020, "extrato_fi_pre2020_header.csv", 116),
		(EXTRATO_FI_SNAPSHOT, "extrato_fi_snapshot_header.csv", 117),
	],
)
def test_each_contract_matches_its_own_published_header(
	contract: object, str_fixture: str, int_cols: int
) -> None:
	"""Each contract equals the verbatim header CVM publishes for **its own** artifact.

	Every other test builds its input from ``tuple_required``, so it can only agree with whatever
	was written there. These compare against bytes we did not author — including the snapshot's,
	which is pinned separately even though it currently matches the yearly one.
	"""
	str_line = (PATH_FIXTURES / str_fixture).read_text(encoding="iso-8859-1")

	assert contract.tuple_required == tuple(str_line.strip().split(";"))
	assert len(contract.tuple_required) == int_cols


# ---- the two yearly regimes --------------------------------------------------------------------


def test_the_yearly_regimes_differ_exactly_in_the_leading_key_block() -> None:
	"""115 columns are identical; the whole difference is the leading identifier block.

	Deriving one contract from the other is right about 115 of 116 names, so the divergence is
	asserted in **both** directions rather than assumed.
	"""
	tuple_post = EXTRATO_FI.tuple_required
	tuple_pre = EXTRATO_FI_PRE2020.tuple_required

	assert tuple_post[:2] == ("TP_FUNDO_CLASSE", "CNPJ_FUNDO_CLASSE")
	assert tuple_pre[:1] == ("CNPJ_FUNDO",)
	assert tuple_post[2:] == tuple_pre[1:]
	assert len(tuple_post[2:]) == 115
	assert set(tuple_post) - set(tuple_pre) == {"TP_FUNDO_CLASSE", "CNPJ_FUNDO_CLASSE"}
	assert set(tuple_pre) - set(tuple_post) == {"CNPJ_FUNDO"}


def test_each_regime_declares_only_its_own_identifier_as_a_cnpj_column() -> None:
	"""The CNPJ column follows the regime — never both, never the sibling's."""
	assert EXTRATO_FI.tuple_cnpj_cols == ("CNPJ_FUNDO_CLASSE",)
	assert EXTRATO_FI_PRE2020.tuple_cnpj_cols == ("CNPJ_FUNDO",)
	assert EXTRATO_FI_SNAPSHOT.tuple_cnpj_cols == ("CNPJ_FUNDO_CLASSE",)


def test_the_regime_readers_are_not_named_after_a_regulation() -> None:
	"""The cutover is 2020; Resolução CVM 175 is from Dec 2022, so it cannot be the cause.

	The Perfil Mensal readers *are* named ``…Pre175``, because there the measured cutover
	(``202312``) matches that rollout. Carrying the name here would assert a cause the dates
	refute — a reader name is an assertion, and this one is pinned to stop the copy.

	The sweep is over the package's ``__all__`` rather than over the imported class: asserting
	``ExtratoFiPre2020Reader.__name__`` would be a tautology (a full rename breaks the import
	before any assertion runs), while this also catches a **partial** rename that leaves the
	package importable.
	"""
	import filings_cvm.ingestion.fi.doc.extrato as pkg

	assert [n for n in pkg.__all__ if "175" in n] == []
	assert "ExtratoFiPre2020Reader" in pkg.__all__
	assert ExtratoFiPre2020Reader._LAST_YEAR == 2019
	assert ExtratoFiReader._FIRST_YEAR == 2020


# ---- the snapshot is a different artifact, not a copy -------------------------------------------


def test_the_snapshot_shares_the_yearly_columns_but_is_a_distinct_source() -> None:
	"""Same 117 columns (measured), different artifact — so a distinct contract and source key.

	Sharing the column list must not collapse the two: provenance and the drift job identify a
	source by its ``source_key``, and these answer different questions.
	"""
	assert EXTRATO_FI_SNAPSHOT.tuple_required == EXTRATO_FI.tuple_required
	assert EXTRATO_FI_SNAPSHOT.str_source_key == "extrato_fi_snapshot"
	assert EXTRATO_FI.str_source_key == "extrato_fi"
	assert EXTRATO_FI_PRE2020.str_source_key == "extrato_fi_pre2020"


def test_the_snapshot_reader_takes_no_date_ref() -> None:
	"""Its URL is fixed, so a reference period would be a lie the signature must not tell."""
	with pytest.raises(TypeError):
		ExtratoFiSnapshotReader(date(2025, 1, 1))  # type: ignore[arg-type]


def test_the_snapshot_reads_the_unpartitioned_url(monkeypatch: pytest.MonkeyPatch) -> None:
	"""``extrato_fi.csv`` — no year in the name."""
	list_urls = _patch_download(monkeypatch, _default_csv(EXTRATO_FI_SNAPSHOT.tuple_required))

	df_ = ExtratoFiSnapshotReader().read()

	assert list_urls == [BASE + "extrato_fi.csv"]
	assert df_["source_key"].iloc[0] == "extrato_fi_snapshot"


# ---- year window guard --------------------------------------------------------------------------


@pytest.mark.parametrize(
	("cls_reader", "date_bad", "str_sibling"),
	[
		(ExtratoFiReader, date(2019, 12, 31), "ExtratoFiPre2020Reader"),
		(ExtratoFiPre2020Reader, date(2020, 1, 1), "ExtratoFiReader"),
		(ExtratoFiPre2020Reader, date(2014, 12, 31), "ExtratoFiReader"),
	],
)
def test_a_year_outside_the_regime_raises_and_names_the_sibling(
	cls_reader: type, date_bad: date, str_sibling: str
) -> None:
	"""Asking a reader for the other regime's year fails fast, before any download."""
	with pytest.raises(ValueError, match=str_sibling):
		cls_reader(date_bad)


@pytest.mark.parametrize(
	("cls_reader", "date_ok"),
	[
		(ExtratoFiReader, date(2020, 1, 1)),
		(ExtratoFiPre2020Reader, date(2019, 12, 31)),
		(ExtratoFiPre2020Reader, date(2015, 1, 1)),
	],
)
def test_the_boundary_year_of_each_regime_is_accepted(cls_reader: type, date_ok: date) -> None:
	"""``2019``/``2020`` are the measured cutover pair — both boundaries inclusive."""
	assert cls_reader(date_ok) is not None


def test_a_closed_regime_defaults_to_its_last_covered_year() -> None:
	"""``ExtratoFiPre2020Reader()`` must be constructible with no arguments.

	Defaulting to today would raise, which makes the reader unusable by any generic caller — the
	sweeps that instantiate every reader with defaults included.
	"""
	assert ExtratoFiPre2020Reader()._str_url.endswith("extrato_fi_2019.csv")
	assert ExtratoFiReader(REF)._str_url.endswith("extrato_fi_2025.csv")


# ---- the read path ------------------------------------------------------------------------------


def test_read_builds_the_yearly_url_and_returns_the_row(monkeypatch: pytest.MonkeyPatch) -> None:
	"""``date_ref`` selects the year, and the parsed frame carries the source row."""
	list_urls = _patch_download(monkeypatch, _default_csv(EXTRATO_FI.tuple_required))

	df_ = ExtratoFiReader(REF).read()

	assert list_urls == [BASE + "extrato_fi_2025.csv"]
	assert df_["CNPJ_FUNDO_CLASSE"].iloc[0] == VALID_CNPJ


def test_the_pre2020_reader_reads_its_own_116_column_artifact(
	monkeypatch: pytest.MonkeyPatch,
) -> None:
	"""The legacy reader accepts the 116-column header and keys on ``CNPJ_FUNDO``."""
	_patch_download(monkeypatch, _default_csv(EXTRATO_FI_PRE2020.tuple_required))

	df_ = ExtratoFiPre2020Reader(date(2019, 6, 1)).read()

	assert df_["CNPJ_FUNDO"].iloc[0] == VALID_CNPJ
	assert "TP_FUNDO_CLASSE" not in df_.columns


def test_reading_the_wrong_regimes_artifact_raises_contract_error(
	monkeypatch: pytest.MonkeyPatch,
) -> None:
	"""A 116-column file served for a 2020+ year violates the contract, and is never parsed."""
	_patch_download(monkeypatch, _default_csv(EXTRATO_FI_PRE2020.tuple_required))

	with pytest.raises(ContractError):
		ExtratoFiReader(REF).read()


def test_only_dt_comptc_is_coerced_and_prazo_stays_text(
	monkeypatch: pytest.MonkeyPatch,
) -> None:
	"""One date column of 117 — and ``PRAZO``'s ``DD/MM/YYYY`` is text, never a misparsed date.

	A coerced column yields a real :class:`datetime.date`, which text can never produce; that is
	the discriminating check, not the frame's dtype.
	"""
	_patch_download(monkeypatch, _default_csv(EXTRATO_FI.tuple_required))

	df_ = ExtratoFiReader(REF).read()

	assert df_["DT_COMPTC"].iloc[0] == date(2025, 1, 2)
	assert df_["PRAZO"].iloc[0] == "01/03/2033"
	assert isinstance(df_["PRAZO"].iloc[0], str)
	for str_col in EXTRATO_FI.tuple_required:
		if str_col != "DT_COMPTC":
			assert isinstance(df_[str_col].iloc[0], str), str_col


def test_twelve_decimal_places_survive_as_published_text(
	monkeypatch: pytest.MonkeyPatch,
) -> None:
	"""``TAXA_PERFM`` arrives with 12 decimals; a float would render ``0.01`` and lose the scale.

	Asserted as the published **text** — a numeric comparison is true in both the exact and the
	lossy world.
	"""
	_patch_download(monkeypatch, _default_csv(EXTRATO_FI.tuple_required))

	df_ = ExtratoFiReader(REF).read()

	assert df_["TAXA_PERFM"].iloc[0] == "0.010000000000"
	assert df_["TAXA_ADM"].iloc[0] == "0.500000000000"


def test_free_text_with_percent_and_commas_is_kept_verbatim(
	monkeypatch: pytest.MonkeyPatch,
) -> None:
	"""``INF_TAXA_PERFM`` is prose carrying ``%`` and comma decimals — never coerced or cleaned."""
	_patch_download(monkeypatch, _default_csv(EXTRATO_FI.tuple_required))

	df_ = ExtratoFiReader(REF).read()

	assert df_["INF_TAXA_PERFM"].iloc[0] == "% a superar: 35% CDI + 65 % IBrX + 0,755%"


def test_a_missing_column_raises_contract_error(monkeypatch: pytest.MonkeyPatch) -> None:
	"""A dropped column is a contract violation, raised before any typing happens."""
	tuple_cols = tuple(c for c in EXTRATO_FI.tuple_required if c != "TAXA_ADM")
	_patch_download(monkeypatch, _default_csv(tuple_cols))

	with pytest.raises(ContractError):
		ExtratoFiReader(REF).read()


def test_the_frame_is_provenance_stamped(monkeypatch: pytest.MonkeyPatch) -> None:
	"""The provenance columns are appended after contract validation."""
	_patch_download(monkeypatch, _default_csv(EXTRATO_FI.tuple_required))

	df_ = ExtratoFiReader(REF).read()

	assert df_["url"].iloc[0] == BASE + "extrato_fi_2025.csv"
	assert df_["source_key"].iloc[0] == "extrato_fi"


def test_path_raw_keeps_the_downloaded_csv(
	monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
	"""``path_raw`` persists the untouched artifact for a bronze layer."""
	_patch_download(monkeypatch, _default_csv(EXTRATO_FI_SNAPSHOT.tuple_required))

	ExtratoFiSnapshotReader(path_raw=tmp_path).read()

	assert (tmp_path / "extrato_fi.csv").exists()


# ---- META --------------------------------------------------------------------------------------


def test_the_meta_url_is_the_flat_txt_and_is_never_derived() -> None:
	"""``meta_extrato_fi.txt`` is the only file in the dataset's META directory."""
	assert MetaExtratoFiReader._META_URL.endswith("/META/meta_extrato_fi.txt")
	assert MetaExtratoFiReader._CONTRACT.str_source_key == "meta_extrato_fi"
