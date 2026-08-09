"""Unit tests for the FI/DOC/PERFIL_MENSAL readers.

``perfil_mensal_fi_AAAAMM.csv`` is a plain CSV (not a ZIP), partitioned by **month**. The series
carries **two schemas** under one filename pattern: 106 columns keyed by ``CNPJ_FUNDO`` through
``202311``, then 107 keyed by ``TP_FUNDO_CLASSE`` + ``CNPJ_FUNDO_CLASSE`` from ``202312``.

Four things carry the weight here:

1. each contract is compared against the **verbatim header bytes CVM publishes** — every other test
   builds its input from ``tuple_required`` and is therefore a tautology;
2. the two regimes share **105 of their columns**, so the difference between them is pinned
   *exactly*, in both directions — deriving one contract from the other is right about 105 names;
3. the six ``CPF_CNPJ_*`` columns hold a CPF **or** a CNPJ, so they stay out of the CNPJ check;
4. the five ``CENARIO_FPR_*`` columns look numeric and are free text.

Mock the single I/O boundary (``download_file`` in the shared base); no network (the autouse guard
in ``conftest.py`` also blocks any real socket).
"""

from datetime import date
from pathlib import Path

import pandas as pd
import pytest

from filings_cvm._internal.config.contracts import PERFIL_MENSAL_FI, PERFIL_MENSAL_FI_PRE175
from filings_cvm._internal.utils.tabular_reader import ContractError
from filings_cvm.ingestion.fi import (
	MetaPerfilMensalFiReader,
	PerfilMensalPre175Reader,
	PerfilMensalReader,
)


VALID_CNPJ = "11.222.333/0001-81"
REF_POST = date(2025, 6, 15)
REF_PRE = date(2023, 6, 15)
URL_POST = "https://dados.cvm.gov.br/dados/FI/DOC/PERFIL_MENSAL/DADOS/perfil_mensal_fi_202506.csv"
PATH_FIXTURES = Path(__file__).resolve().parents[1] / "fixtures" / "perfil_mensal_fi"

# The two ISO date columns, both in the tail the regimes share.
DATE_COLS = ("DT_COMPTC", "DT_COTA_TAXA_PERFM")

# CPF-or-CNPJ by definition: each has a sibling ``PF_PJ_*`` whose domain is ``PF``/``PJ``.
CPF_CNPJ_COLS = (
	"CPF_CNPJ_COMITENTE_1",
	"CPF_CNPJ_COMITENTE_2",
	"CPF_CNPJ_COMITENTE_3",
	"CPF_CNPJ_EMISSOR_1",
	"CPF_CNPJ_EMISSOR_2",
	"CPF_CNPJ_EMISSOR_3",
)

# Look numeric, are free text — measured values carry a comma decimal separator and prose.
CENARIO_COLS = (
	"CENARIO_FPR_IBOVESPA",
	"CENARIO_FPR_JUROS",
	"CENARIO_FPR_CUPOM",
	"CENARIO_FPR_DOLAR",
	"CENARIO_FPR_OUTRO",
)


def _csv(list_cols: list[str], list_rows: list[list[str]]) -> str:
	"""Serialise a header + rows into the CVM ``;``-separated, ISO-8859-1 CSV shape."""
	lines = [";".join(list_cols)] + [";".join(r) for r in list_rows]
	return "\n".join(lines) + "\n"


def _row_for(
	tuple_cols: tuple[str, ...], dict_overrides: dict[str, str] | None = None
) -> list[str]:
	"""Build one row for ``tuple_cols``, filling each column with a plausible measured value."""
	dict_values: dict[str, str] = {
		"TP_FUNDO_CLASSE": "CLASSES - FIF",
		"CNPJ_FUNDO_CLASSE": VALID_CNPJ,
		"CNPJ_FUNDO": VALID_CNPJ,
		"DENOM_SOCIAL": "FUNDO DE INVESTIMENTO FINANCEIRO EXEMPLO",
		"DT_COMPTC": "2025-06-30",
		"DT_COTA_TAXA_PERFM": "2025-07-03",
		"VERSAO": "3",
		# Scale is load-bearing here — trailing zeros must survive as published text.
		"PR_VAR_CARTEIRA": "0.1000",
		"PR_COMITENTE_1": "0.10",
		"VL_COTA_TAXA_PERFM": "1984223115.42",
		# Comma decimal separator, exactly as CVM publishes it in this column.
		"CENARIO_FPR_IBOVESPA": "-0,0004",
		"CENARIO_FPR_JUROS": "pessimista",
		"PF_PJ_COMITENTE_1": "PJ",
		"PF_PJ_COMITENTE_2": "PF",
		"CPF_CNPJ_COMITENTE_1": VALID_CNPJ,
		"CPF_CNPJ_COMITENTE_2": "123.456.789-09",
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
		"filings_cvm.ingestion.fi.doc.perfil_mensal._base_perfil_mensal_reader.download_file",
		_fake_download,
	)
	return list_urls


# ---- the pinned oracle -------------------------------------------------------------------------


def test_post175_contract_matches_the_published_header() -> None:
	"""The post-175 contract equals the verbatim header CVM publishes for ``202506``."""
	str_line = (PATH_FIXTURES / "perfil_mensal_fi_header.csv").read_text(encoding="iso-8859-1")

	assert PERFIL_MENSAL_FI.tuple_required == tuple(str_line.strip().split(";"))
	assert len(PERFIL_MENSAL_FI.tuple_required) == 107


def test_pre175_contract_matches_the_published_header() -> None:
	"""The pre-175 contract equals the verbatim header CVM publishes for ``202311``."""
	str_line = (PATH_FIXTURES / "perfil_mensal_fi_pre175_header.csv").read_text(
		encoding="iso-8859-1"
	)

	assert PERFIL_MENSAL_FI_PRE175.tuple_required == tuple(str_line.strip().split(";"))
	assert len(PERFIL_MENSAL_FI_PRE175.tuple_required) == 106


# ---- the two regimes: 105 shared columns, one differing key block ------------------------------


def test_the_two_regimes_differ_exactly_in_the_leading_key_block() -> None:
	"""105 of the columns are identical; the whole difference is the leading identifier block.

	This is the tightest copy trap in the dataset: writing one contract from the other and "just
	fixing the first column" is right about 105 of 106 names. The divergence is therefore asserted
	in **both** directions — what each regime has that the other does not, and that everything
	after the key block matches position for position.
	"""
	tuple_post = PERFIL_MENSAL_FI.tuple_required
	tuple_pre = PERFIL_MENSAL_FI_PRE175.tuple_required

	assert tuple_post[:2] == ("TP_FUNDO_CLASSE", "CNPJ_FUNDO_CLASSE")
	assert tuple_pre[:1] == ("CNPJ_FUNDO",)
	# Everything from DENOM_SOCIAL onward is the same sequence in both.
	assert tuple_post[2:] == tuple_pre[1:]
	assert set(tuple_post) - set(tuple_pre) == {"TP_FUNDO_CLASSE", "CNPJ_FUNDO_CLASSE"}
	assert set(tuple_pre) - set(tuple_post) == {"CNPJ_FUNDO"}


def test_each_regime_declares_only_its_own_identifier_as_a_cnpj_column() -> None:
	"""The CNPJ column follows the regime — never both, never the sibling's."""
	assert PERFIL_MENSAL_FI.tuple_cnpj_cols == ("CNPJ_FUNDO_CLASSE",)
	assert PERFIL_MENSAL_FI_PRE175.tuple_cnpj_cols == ("CNPJ_FUNDO",)


# ---- CPF-or-CNPJ columns stay out of the CNPJ check --------------------------------------------


def test_cpf_cnpj_columns_are_required_but_never_declared_as_cnpj_columns() -> None:
	"""The six ``CPF_CNPJ_*`` columns hold a CPF or a CNPJ, so no CNPJ check may run on them.

	Each has a sibling ``PF_PJ_*`` column whose domain is ``PF``/``PJ``, and the ``PF`` case occurs
	in the published data. Declaring one would pass in an all-PJ month and raise on the first
	individual — the failure would land on a caller, in a month nobody tested.
	"""
	for contract in (PERFIL_MENSAL_FI, PERFIL_MENSAL_FI_PRE175):
		for str_col in CPF_CNPJ_COLS:
			assert str_col in contract.tuple_required
			assert str_col not in contract.tuple_cnpj_cols


def test_every_cpf_cnpj_column_has_its_pf_pj_sibling() -> None:
	"""The exclusion above is structural: the sibling column is what types each value."""
	tuple_required = PERFIL_MENSAL_FI.tuple_required

	for str_col in CPF_CNPJ_COLS:
		assert str_col.replace("CPF_CNPJ_", "PF_PJ_") in tuple_required


# ---- month window guard ------------------------------------------------------------------------


@pytest.mark.parametrize(
	("cls_reader", "date_bad", "str_sibling"),
	[
		(PerfilMensalReader, date(2023, 11, 30), "PerfilMensalPre175Reader"),
		(PerfilMensalPre175Reader, date(2023, 12, 1), "PerfilMensalReader"),
	],
)
def test_a_month_outside_the_regime_raises_and_names_the_sibling(
	cls_reader: type, date_bad: date, str_sibling: str
) -> None:
	"""Asking a reader for the other regime's month fails fast, pointing at the right reader.

	Without this the caller downloads 13 MB and gets a ``ContractError`` about a missing column,
	which never mentions that a second reader exists.
	"""
	with pytest.raises(ValueError, match=str_sibling):
		cls_reader(date_bad)


@pytest.mark.parametrize(
	("cls_reader", "date_ok"),
	[
		(PerfilMensalReader, date(2023, 12, 1)),
		(PerfilMensalPre175Reader, date(2023, 11, 30)),
		(PerfilMensalPre175Reader, date(2019, 1, 31)),
	],
)
def test_the_boundary_month_of_each_regime_is_accepted(cls_reader: type, date_ok: date) -> None:
	"""``202311``/``202312`` are the measured cutover pair — both boundaries are inclusive."""
	assert cls_reader(date_ok) is not None


# ---- the read path -----------------------------------------------------------------------------


def test_read_builds_the_monthly_url_and_returns_the_row(monkeypatch: pytest.MonkeyPatch) -> None:
	"""``date_ref`` selects the month, and the parsed frame carries the source row."""
	list_urls = _patch_download(monkeypatch, _default_csv(PERFIL_MENSAL_FI.tuple_required))

	df_ = PerfilMensalReader(REF_POST).read()

	assert list_urls == [URL_POST]
	assert len(df_) == 1
	assert df_["CNPJ_FUNDO_CLASSE"].iloc[0] == VALID_CNPJ


def test_the_pre175_reader_reads_its_own_106_column_artifact(
	monkeypatch: pytest.MonkeyPatch,
) -> None:
	"""The pre-175 reader accepts the 106-column header and keys on ``CNPJ_FUNDO``."""
	_patch_download(monkeypatch, _default_csv(PERFIL_MENSAL_FI_PRE175.tuple_required))

	df_ = PerfilMensalPre175Reader(REF_PRE).read()

	assert df_["CNPJ_FUNDO"].iloc[0] == VALID_CNPJ
	assert "TP_FUNDO_CLASSE" not in df_.columns


def test_reading_the_wrong_regimes_artifact_raises_contract_error(
	monkeypatch: pytest.MonkeyPatch,
) -> None:
	"""A 106-column file served for a post-175 month violates the contract, and is never parsed."""
	_patch_download(monkeypatch, _default_csv(PERFIL_MENSAL_FI_PRE175.tuple_required))

	with pytest.raises(ContractError):
		PerfilMensalReader(REF_POST).read()


def test_date_columns_are_dates_and_every_other_column_is_text(
	monkeypatch: pytest.MonkeyPatch,
) -> None:
	"""Only the two declared date columns are coerced; everything else stays exact source text.

	A coerced column yields a real :class:`datetime.date`, which a text column can never produce —
	that is what distinguishes the two, not the frame's dtype (this repo coerces to pure ``date``
	objects, so a populated date column is ``object``, same as text).
	"""
	_patch_download(monkeypatch, _default_csv(PERFIL_MENSAL_FI.tuple_required))

	df_ = PerfilMensalReader(REF_POST).read()

	assert df_["DT_COMPTC"].iloc[0] == date(2025, 6, 30)
	assert df_["DT_COTA_TAXA_PERFM"].iloc[0] == date(2025, 7, 3)
	for str_col in PERFIL_MENSAL_FI.tuple_required:
		if str_col not in DATE_COLS:
			assert isinstance(df_[str_col].iloc[0], str), str_col


def test_decimal_columns_keep_the_sources_own_scale(monkeypatch: pytest.MonkeyPatch) -> None:
	"""Trailing zeros survive: a float would render ``0.1000`` as ``0.1`` and lose the scale.

	The value is asserted as the published **text**, not compared numerically — a numeric
	comparison is true in both the exact and the lossy world.
	"""
	_patch_download(monkeypatch, _default_csv(PERFIL_MENSAL_FI.tuple_required))

	df_ = PerfilMensalReader(REF_POST).read()

	assert df_["PR_VAR_CARTEIRA"].iloc[0] == "0.1000"
	assert df_["PR_COMITENTE_1"].iloc[0] == "0.10"
	assert df_["VL_COTA_TAXA_PERFM"].iloc[0] == "1984223115.42"


def test_cenario_columns_keep_comma_decimals_and_prose_verbatim(
	monkeypatch: pytest.MonkeyPatch,
) -> None:
	"""``CENARIO_FPR_*`` look numeric and are ``varchar`` in the META — never coerced.

	They mix a comma decimal separator with free text in the same column, so any numeric coercion
	either raises or silently mangles them.
	"""
	_patch_download(monkeypatch, _default_csv(PERFIL_MENSAL_FI.tuple_required))

	df_ = PerfilMensalReader(REF_POST).read()

	for str_col in CENARIO_COLS:
		assert pd.api.types.is_string_dtype(df_[str_col]), str_col
	assert df_["CENARIO_FPR_IBOVESPA"].iloc[0] == "-0,0004"
	assert df_["CENARIO_FPR_JUROS"].iloc[0] == "pessimista"


def test_a_blank_date_stays_a_date_column(monkeypatch: pytest.MonkeyPatch) -> None:
	"""``DT_COTA_TAXA_PERFM`` arrives ~84% blank; a blank becomes NA and the column stays a date.

	⚠️ Emptiness alone proves nothing — pandas turns a blank into a missing value under
	``dtype="str"`` too, so a file where the column is *entirely* blank is satisfied by either
	declaration. The discriminating evidence is a **populated** cell in the same column coming back
	as a real :class:`datetime.date`, so this fixture carries one blank row and one populated row.
	"""
	tuple_cols = PERFIL_MENSAL_FI.tuple_required
	str_csv = _csv(
		list(tuple_cols),
		[
			_row_for(tuple_cols, {"DT_COTA_TAXA_PERFM": ""}),
			_row_for(tuple_cols, {"DT_COTA_TAXA_PERFM": "2024-02-29"}),
		],
	)
	_patch_download(monkeypatch, str_csv)

	df_ = PerfilMensalReader(REF_POST).read()

	assert pd.isna(df_["DT_COTA_TAXA_PERFM"].iloc[0])
	assert df_["DT_COTA_TAXA_PERFM"].iloc[1] == date(2024, 2, 29)


def test_a_missing_column_raises_contract_error(monkeypatch: pytest.MonkeyPatch) -> None:
	"""A dropped column is a contract violation, raised before any typing happens."""
	tuple_cols = tuple(c for c in PERFIL_MENSAL_FI.tuple_required if c != "PR_ATIVO_CRED_PRIV")
	_patch_download(monkeypatch, _default_csv(tuple_cols))

	with pytest.raises(ContractError):
		PerfilMensalReader(REF_POST).read()


def test_the_frame_is_provenance_stamped(monkeypatch: pytest.MonkeyPatch) -> None:
	"""The six provenance columns are appended after contract validation."""
	_patch_download(monkeypatch, _default_csv(PERFIL_MENSAL_FI.tuple_required))

	df_ = PerfilMensalReader(REF_POST).read()

	assert df_["url"].iloc[0] == URL_POST
	assert df_["source_key"].iloc[0] == "perfil_mensal_fi"


def test_path_raw_keeps_the_downloaded_csv(
	monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
	"""``path_raw`` persists the untouched artifact for a bronze layer."""
	_patch_download(monkeypatch, _default_csv(PERFIL_MENSAL_FI.tuple_required))

	PerfilMensalReader(REF_POST, path_raw=tmp_path).read()

	assert (tmp_path / "perfil_mensal_fi_202506.csv").exists()


# ---- META --------------------------------------------------------------------------------------


def test_the_meta_url_is_the_flat_txt_and_is_never_derived() -> None:
	"""``meta_perfil_mensal_fi.txt`` is the only file in the dataset's META directory.

	The three other spellings this portal uses elsewhere (``.zip``, the ``_txt`` infix, the
	prefix-less form) all return 404 here, so the URL is pinned rather than built from a rule.
	"""
	assert MetaPerfilMensalFiReader._META_URL.endswith("/META/meta_perfil_mensal_fi.txt")
	assert MetaPerfilMensalFiReader._CONTRACT.str_source_key == "meta_perfil_mensal_fi"
