"""Unit tests for the CIA_ABERTA/EVENTOS/RECOMPRA_ACOES readers — all 3 members.

`cia_aberta_recompra_acoes.zip` is the registry of **share buy-back programmes**: the programme
itself, the brokers engaged in it and the counts per share type and class, all joined by
`ID_Programa`.

Four things carry the weight here:

1. every contract is compared against the **verbatim header bytes CVM publishes** — every other
   test builds its input from ``tuple_required`` and is therefore a tautology;
2. ⚠️⚠️ ``quantidades`` declares **no CNPJ column**, because the member genuinely has none. An
   empty ``tuple_cnpj_cols`` is indistinguishable from an oversight unless it is asserted, so it
   is — together with the sibling members that *do* declare one;
3. ⚠️ this dataset **does not follow its `DOC` neighbours**: it is a snapshot (no ``date_ref``),
   its filename puts the root first, and its columns are CamelCase rather than ``CNPJ_CIA`` /
   ``DT_REFER``. The divergence is asserted against a live `DOC` contract;
4. two of the three members carry **no date column at all**.

Mock the single I/O boundary (``download_file``); no network.
"""

from dataclasses import dataclass
from datetime import date
import io
from pathlib import Path
import zipfile

import pandas as pd
import pytest

from filings_cvm import RetryPolicy
from filings_cvm._internal.config.contracts import (
	CIA_ABERTA_RECOMPRA_ACOES,
	CIA_ABERTA_RECOMPRA_ACOES_INTERMEDIARIOS,
	CIA_ABERTA_RECOMPRA_ACOES_QUANTIDADES,
	DFP_CIA_ABERTA,
	FileContract,
)
from filings_cvm._internal.config.ports.ingestion_reader import IngestionReader
from filings_cvm._internal.utils.tabular_reader import ContractError
from filings_cvm.ingestion.cia_aberta import (
	MetaRecompraAcoesReader,
	RecompraAcoesIntermediariosReader,
	RecompraAcoesQuantidadesReader,
	RecompraAcoesReader,
)


VALID_CNPJ = "11.222.333/0001-81"
URL = (
	"https://dados.cvm.gov.br/dados/CIA_ABERTA/EVENTOS/RECOMPRA_ACOES/DADOS/"
	"cia_aberta_recompra_acoes.zip"
)
MODULE = "filings_cvm.ingestion.cia_aberta.eventos.recompra_acoes._base_recompra_acoes_reader"
PATH_FIXTURES = Path(__file__).resolve().parents[1] / "fixtures" / "cia_aberta_recompra_acoes"


@dataclass(frozen=True)
class RecompraCase:
	"""One reader's spec: how to build it and which member it reads."""

	cls_reader: type[IngestionReader]
	cls_contract: FileContract
	str_member: str


CASES: tuple[RecompraCase, ...] = (
	RecompraCase(RecompraAcoesReader, CIA_ABERTA_RECOMPRA_ACOES, "cia_aberta_recompra_acoes.csv"),
	RecompraCase(
		RecompraAcoesIntermediariosReader,
		CIA_ABERTA_RECOMPRA_ACOES_INTERMEDIARIOS,
		"cia_aberta_recompra_acoes_intermediarios.csv",
	),
	RecompraCase(
		RecompraAcoesQuantidadesReader,
		CIA_ABERTA_RECOMPRA_ACOES_QUANTIDADES,
		"cia_aberta_recompra_acoes_quantidades.csv",
	),
)
IDS = [case.cls_reader.__name__ for case in CASES]

# The CNPJ columns each member declares — measured, not read off the header names. ``quantidades``
# has none at all, which is the decision this map exists to make explicit.
DICT_CNPJ_COLS: dict[str, tuple[str, ...]] = {
	"cia_aberta_recompra_acoes.csv": ("CNPJ_Companhia",),
	"cia_aberta_recompra_acoes_intermediarios.csv": ("CNPJ_Intermediario",),
	"cia_aberta_recompra_acoes_quantidades.csv": (),
}


def _value_for(str_col: str) -> str:
	"""Return a plausible source value for one column, by name."""
	if str_col.startswith("CNPJ"):
		return VALID_CNPJ
	if str_col.startswith("Data_"):
		return "2025-08-25"
	if str_col.startswith("Quantidade_"):
		return "5730834040"
	if str_col == "ID_Programa":
		return "1042"
	return "x"


def _row(cls_contract: FileContract) -> list[str]:
	"""One valid row in the contract's column order, identifying its own member."""
	return [_value_for(c) for c in cls_contract.tuple_required]


def _csv_text(list_cols: list[str], list_rows: list[list[str]]) -> str:
	"""Serialise a header + rows into the CVM ``;``-separated CSV shape."""
	return "\n".join([";".join(list_cols), *[";".join(r) for r in list_rows]]) + "\n"


def _member_row(case: RecompraCase) -> list[str]:
	"""Build a valid row that **identifies its own member** through ``ID_Programa``.

	Every member shares that column, so stamping the member name into it makes a reader pointed at
	the wrong file visible — the discipline the DFP slice established.
	"""
	return [
		case.str_member if str_col == "ID_Programa" else _value_for(str_col)
		for str_col in case.cls_contract.tuple_required
	]


def _all_members(dict_override: dict[str, str] | None = None) -> bytes:
	"""Build the archive holding all three members, one identifiable row each."""
	dict_members = {
		case.str_member: _csv_text(list(case.cls_contract.tuple_required), [_member_row(case)])
		for case in CASES
	}
	dict_members.update(dict_override or {})
	buffer = io.BytesIO()
	with zipfile.ZipFile(buffer, "w") as cls_zip:
		for str_name, str_csv in dict_members.items():
			cls_zip.writestr(str_name, str_csv.encode("ISO-8859-1"))
	return buffer.getvalue()


def _patch(monkeypatch: pytest.MonkeyPatch, bytes_payload: bytes) -> list[str]:
	"""Patch the shared base's download_file to drop ``bytes_payload``; capture requested URLs."""
	list_urls: list[str] = []

	def _fake_download(
		str_url: str, path_dest: Path, int_timeout_s: int = 60, retry_policy: object = None
	) -> Path:
		list_urls.append(str_url)
		path_dest.parent.mkdir(parents=True, exist_ok=True)
		path_dest.write_bytes(bytes_payload)
		return path_dest

	monkeypatch.setattr(f"{MODULE}.download_file", _fake_download)
	return list_urls


def test_contracts_match_the_published_headers() -> None:
	"""All three contracts equal the verbatim headers CVM publishes — the oracle."""
	for case in CASES:
		str_line = (PATH_FIXTURES / case.str_member.replace(".csv", "_header.csv")).read_text(
			encoding="iso-8859-1"
		)
		assert case.cls_contract.tuple_required == tuple(str_line.strip().split(";")), (
			case.str_member
		)
	assert [len(c.cls_contract.tuple_required) for c in CASES] == [11, 3, 5]


def test_quantidades_declares_no_cnpj_column_because_it_has_none() -> None:
	"""⚠️⚠️ An empty ``tuple_cnpj_cols`` is a measured decision, not an oversight.

	``quantidades`` identifies nothing but the programme it belongs to — it carries no CNPJ column
	at all, so declaring one would invent a column the source does not have (and a contract naming
	a missing column fails every read). Emptiness looks identical to forgetfulness in a diff, so it
	is asserted here alongside the siblings that *do* declare one.
	"""
	for case in CASES:
		assert case.cls_contract.tuple_cnpj_cols == DICT_CNPJ_COLS[case.str_member], (
			case.str_member
		)
	# The empty one is empty *because* no column of its own carries a CNPJ.
	assert not [
		c for c in CIA_ABERTA_RECOMPRA_ACOES_QUANTIDADES.tuple_required if "CNPJ" in c.upper()
	]
	# ...while both siblings do carry one, and declare exactly it.
	assert "CNPJ_Companhia" in CIA_ABERTA_RECOMPRA_ACOES.tuple_required
	assert "CNPJ_Intermediario" in CIA_ABERTA_RECOMPRA_ACOES_INTERMEDIARIOS.tuple_required


def test_this_dataset_does_not_follow_its_doc_neighbours() -> None:
	"""⚠️ CamelCase columns and a snapshot URL — the `DOC` datasets in the same root do neither.

	`CIA_ABERTA/DOC` ships `<ds>_cia_aberta_AAAA.zip` with `CNPJ_CIA` / `DT_REFER`. This one
	ships a year-less `cia_aberta_recompra_acoes.zip` with `CNPJ_Companhia` and
	`Data_Deliberacao`, and even inverts the filename so the *root* comes first. DFP is asserted
	as the live counter-example, so a template-minded change to either one fails here.
	"""
	set_cols = set(CIA_ABERTA_RECOMPRA_ACOES.tuple_required)

	assert {"CNPJ_Companhia", "Data_Deliberacao"} <= set_cols
	assert "CNPJ_CIA" not in set_cols
	assert "DT_REFER" not in set_cols
	# The neighbour in the same root uses the other convention, and still does.
	assert "CNPJ_CIA" in DFP_CIA_ABERTA.tuple_required
	assert "CNPJ_Companhia" not in DFP_CIA_ABERTA.tuple_required
	# The URL carries no year — this is a snapshot.
	assert "cia_aberta_recompra_acoes.zip" in URL
	assert not any(str_year in URL for str_year in ("2024", "2025", "2026", "AAAA"))


def test_only_the_registry_declares_date_columns() -> None:
	"""Two of the three members carry no date column at all — the ADM_CART shape."""
	assert RecompraAcoesReader._DATE_COLS == ("Data_Deliberacao", "Data_Final_Prazo")
	assert RecompraAcoesIntermediariosReader._DATE_COLS == ()
	assert RecompraAcoesQuantidadesReader._DATE_COLS == ()


def test_every_member_joins_on_id_programa() -> None:
	"""``ID_Programa`` is the key all three share, and it stays text."""
	for case in CASES:
		assert "ID_Programa" in case.cls_contract.tuple_required, case.str_member
		assert case.cls_contract.tuple_required[0] == "ID_Programa", case.str_member


@pytest.mark.parametrize("case", CASES, ids=IDS)
def test_read_returns_all_contract_columns(
	case: RecompraCase, monkeypatch: pytest.MonkeyPatch
) -> None:
	"""Each reader's frame carries exactly its contract's columns, plus provenance.

	Parameters
	----------
	case : RecompraCase
		The reader spec under test.
	monkeypatch : pytest.MonkeyPatch
		Fixture used to replace the download boundary.
	"""
	_patch(monkeypatch, _all_members())

	df_ = case.cls_reader().read()

	assert len(df_) == 1
	assert list(df_.columns) == list(case.cls_contract.output_columns)


@pytest.mark.parametrize("case", CASES, ids=IDS)
def test_read_selects_its_own_member(case: RecompraCase, monkeypatch: pytest.MonkeyPatch) -> None:
	"""Each reader reads the member named by its own ``_MEMBER`` — not a sibling's.

	Parameters
	----------
	case : RecompraCase
		The reader spec under test.
	monkeypatch : pytest.MonkeyPatch
		Fixture used to replace the download boundary.
	"""
	_patch(monkeypatch, _all_members())

	df_ = case.cls_reader().read()

	assert case.str_member == case.cls_reader._MEMBER
	assert df_["ID_Programa"].iloc[0] == case.str_member


@pytest.mark.parametrize("case", CASES, ids=IDS)
def test_reader_takes_no_date_ref(case: RecompraCase) -> None:
	"""Reject ``date_ref`` — this dataset is a snapshot, with no year in its URL.

	Parameters
	----------
	case : RecompraCase
		The reader spec under test.
	"""
	with pytest.raises(TypeError):
		case.cls_reader(date_ref=date(2025, 6, 15))


def test_read_coerces_the_registry_date_columns(monkeypatch: pytest.MonkeyPatch) -> None:
	"""``Data_Deliberacao`` and ``Data_Final_Prazo`` become pure ``date`` objects.

	Parameters
	----------
	monkeypatch : pytest.MonkeyPatch
		Fixture used to replace the download boundary.
	"""
	_patch(monkeypatch, _all_members())

	df_ = RecompraAcoesReader().read()

	assert df_["Data_Deliberacao"].iloc[0] == date(2025, 8, 25)
	assert df_["Data_Final_Prazo"].iloc[0] == date(2025, 8, 25)


def test_read_keeps_counts_as_exact_text(monkeypatch: pytest.MonkeyPatch) -> None:
	"""``Quantidade_*`` are counts and stay source text, never binary floats.

	Parameters
	----------
	monkeypatch : pytest.MonkeyPatch
		Fixture used to replace the download boundary.
	"""
	_patch(monkeypatch, _all_members())

	df_ = RecompraAcoesReader().read()

	assert df_["Quantidade_Acoes_Ordinarias"].iloc[0] == "5730834040"
	assert isinstance(df_["Quantidade_Acoes_Ordinarias"].iloc[0], str)


def test_read_leaves_classe_acao_blank(monkeypatch: pytest.MonkeyPatch) -> None:
	"""``Classe_Acao`` is empty in 97,5% of real rows — ordinary shares have no class.

	Blank stays blank; substituting a placeholder would invent a class the company never declared.

	Parameters
	----------
	monkeypatch : pytest.MonkeyPatch
		Fixture used to replace the download boundary.
	"""
	list_cols = list(CIA_ABERTA_RECOMPRA_ACOES_QUANTIDADES.tuple_required)
	list_blank = ["" if c == "Classe_Acao" else _value_for(c) for c in list_cols]
	str_csv = _csv_text(list_cols, [list_blank])
	_patch(monkeypatch, _all_members({"cia_aberta_recompra_acoes_quantidades.csv": str_csv}))

	df_ = RecompraAcoesQuantidadesReader().read()

	assert pd.isna(df_["Classe_Acao"].iloc[0])
	assert df_["Quantidade_Operacao"].iloc[0] == "5730834040"


@pytest.mark.parametrize("case", CASES, ids=IDS)
def test_read_requests_the_shared_snapshot_url(
	case: RecompraCase, monkeypatch: pytest.MonkeyPatch
) -> None:
	"""Every reader fetches the same fixed-URL archive.

	Parameters
	----------
	case : RecompraCase
		The reader spec under test.
	monkeypatch : pytest.MonkeyPatch
		Fixture used to replace the download boundary.
	"""
	list_urls = _patch(monkeypatch, _all_members())

	case.cls_reader().read()

	assert list_urls == [URL]


@pytest.mark.parametrize("case", CASES, ids=IDS)
def test_read_stamps_provenance(case: RecompraCase, monkeypatch: pytest.MonkeyPatch) -> None:
	"""Each frame carries its own source key and the shared archive URL.

	Parameters
	----------
	case : RecompraCase
		The reader spec under test.
	monkeypatch : pytest.MonkeyPatch
		Fixture used to replace the download boundary.
	"""
	_patch(monkeypatch, _all_members())

	df_ = case.cls_reader().read()

	assert df_["source_key"].iloc[0] == case.cls_contract.str_source_key
	assert df_["url"].iloc[0] == URL


def test_read_raises_contract_error_on_a_missing_column(monkeypatch: pytest.MonkeyPatch) -> None:
	"""A member missing a required column fails before any typing is applied.

	Parameters
	----------
	monkeypatch : pytest.MonkeyPatch
		Fixture used to replace the download boundary.
	"""
	list_cols = list(CIA_ABERTA_RECOMPRA_ACOES.tuple_required)[:-1]
	str_csv = _csv_text(list_cols, [[_value_for(c) for c in list_cols]])
	_patch(monkeypatch, _all_members({"cia_aberta_recompra_acoes.csv": str_csv}))

	with pytest.raises(ContractError):
		RecompraAcoesReader().read()


def test_read_persists_the_shared_raw_zip(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
	"""``path_raw`` keeps the one archive all three readers share.

	CVM overwrites this file in place, so a persisted snapshot is the only record of what the
	registry said that day.

	Parameters
	----------
	monkeypatch : pytest.MonkeyPatch
		Fixture used to replace the download boundary.
	tmp_path : pathlib.Path
		Pytest-provided throwaway directory standing in for the bronze landing zone.
	"""
	_patch(monkeypatch, _all_members())
	path_raw = tmp_path / "bronze"

	RecompraAcoesQuantidadesReader(path_raw=path_raw).read()

	assert (path_raw / "cia_aberta_recompra_acoes.zip").exists()


def test_meta_url_is_the_prefixed_zip() -> None:
	"""RECOMPRA_ACOES's META is ``meta_cia_aberta_recompra_acoes.zip``.

	Measured two independent ways — a ``HEAD`` returning 200, and the ``META/`` directory listing
	where it is the only file. Five other candidate spellings 404, including the ``_txt`` infix
	that is correct for DFP and ITR in this very root.
	"""
	assert MetaRecompraAcoesReader._META_URL == (
		"https://dados.cvm.gov.br/dados/CIA_ABERTA/EVENTOS/RECOMPRA_ACOES/META/"
		"meta_cia_aberta_recompra_acoes.zip"
	)
	assert MetaRecompraAcoesReader._CONTRACT.str_source_key == "meta_cia_aberta_recompra_acoes"


def test_readers_follow_the_retry_policy_standard() -> None:
	"""Each reader declares its own ``_RETRY_POLICY`` and lets an instance override it."""
	cls_custom = RetryPolicy(int_max_attempts=8)

	for case in CASES:
		assert isinstance(case.cls_reader._RETRY_POLICY, RetryPolicy), case.str_member
		assert case.cls_reader()._retry_policy is case.cls_reader._RETRY_POLICY
		assert case.cls_reader(retry_policy=cls_custom)._retry_policy is cls_custom
