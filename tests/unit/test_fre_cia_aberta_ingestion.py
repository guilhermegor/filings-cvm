"""Unit tests for the CIA_ABERTA/DOC/FRE readers — slices 1 and 2 of 4.

`fre_cia_aberta_AAAA.zip` is the portal's largest dataset (36 members, ~131k rows), shipped in four
themed slices. This file covers the first fifteen members — index + capital, and
administração/pessoas — and grows as the later slices land.

Four things carry the weight here:

1. the **index uses a different naming convention from its own satellites** (`CNPJ_CIA` /
   `DT_REFER` vs `CNPJ_Companhia` / `Data_Referencia`), matching FCA but **not** CGVN — there is no
   cross-dataset rule, so the divergence is asserted in both directions;
2. money and count columns (`Valor_Capital`, `Quantidade_*`, `Percentual_*`) stay **exact source
   text**, never binary floats;
3. **which columns are CNPJ columns is measured, not read off the header name.** Two members
   declare more than one, and three columns that *look* like identifiers are deliberately excluded
   because the real values are mixed CPF/CNPJ — including one whose name says neither
   (`Documento_Pessoa_Relacionada`);
4. `membro_comite` and `administrador_membro_conselho_fiscal` have the **same column count (21)**
   and different columns, so a copied contract would ship wrong with the suite green.

Every test except one builds its input from each contract's `tuple_required`, so it is a tautology.
The exception is :func:`test_contracts_match_the_published_headers`, which compares all fifteen
contracts against the **verbatim header bytes CVM publishes**.

Mock the single I/O boundary (``download_file``); no network.
"""

from dataclasses import dataclass
from datetime import date
import io
from pathlib import Path
import zipfile

import pandas as pd
import pytest

from filings_cvm import (
	CgvnCiaAbertaReader,
	FreCiaAbertaAdministradorMembroConselhoFiscalReader,
	FreCiaAbertaAuditorReader,
	FreCiaAbertaCapitalSocialClasseAcaoReader,
	FreCiaAbertaCapitalSocialReader,
	FreCiaAbertaCapitalSocialTituloConversivelReader,
	FreCiaAbertaDistribuicaoCapitalClasseAcaoReader,
	FreCiaAbertaDistribuicaoCapitalReader,
	FreCiaAbertaMembroComiteReader,
	FreCiaAbertaMercadoEstrangeiroReader,
	FreCiaAbertaPosicaoAcionariaClasseAcaoReader,
	FreCiaAbertaPosicaoAcionariaReader,
	FreCiaAbertaReader,
	FreCiaAbertaRelacaoFamiliarReader,
	FreCiaAbertaRelacaoSubordinacaoReader,
	FreCiaAbertaResponsavelReader,
	MetaFreCiaAbertaReader,
)
from filings_cvm._internal.config.contracts import (
	CGVN_CIA_ABERTA,
	FRE_CIA_ABERTA,
	FRE_CIA_ABERTA_ADMINISTRADOR_MEMBRO_CONSELHO_FISCAL,
	FRE_CIA_ABERTA_AUDITOR,
	FRE_CIA_ABERTA_CAPITAL_SOCIAL,
	FRE_CIA_ABERTA_CAPITAL_SOCIAL_CLASSE_ACAO,
	FRE_CIA_ABERTA_CAPITAL_SOCIAL_TITULO_CONVERSIVEL,
	FRE_CIA_ABERTA_DISTRIBUICAO_CAPITAL,
	FRE_CIA_ABERTA_DISTRIBUICAO_CAPITAL_CLASSE_ACAO,
	FRE_CIA_ABERTA_MEMBRO_COMITE,
	FRE_CIA_ABERTA_MERCADO_ESTRANGEIRO,
	FRE_CIA_ABERTA_POSICAO_ACIONARIA,
	FRE_CIA_ABERTA_POSICAO_ACIONARIA_CLASSE_ACAO,
	FRE_CIA_ABERTA_RELACAO_FAMILIAR,
	FRE_CIA_ABERTA_RELACAO_SUBORDINACAO,
	FRE_CIA_ABERTA_RESPONSAVEL,
	FileContract,
)
from filings_cvm._internal.config.ports.ingestion_reader import IngestionReader
from filings_cvm._internal.utils.tabular_reader import ContractError


VALID_CNPJ = "11.222.333/0001-81"
DATE_REF = date(2025, 6, 15)
URL = "https://dados.cvm.gov.br/dados/CIA_ABERTA/DOC/FRE/DADOS/fre_cia_aberta_2025.zip"
MODULE = "filings_cvm.ingestion.cia_aberta.doc.fre._base_fre_reader"
PATH_FIXTURES = Path(__file__).resolve().parents[1] / "fixtures" / "fre_cia_aberta"

# A money value whose scale a binary float would not survive intact.
VALOR_CAPITAL = "1984223115.42"
QUANTIDADE = "2865417084"


@dataclass(frozen=True)
class FreCase:
	"""One reader's spec: how to build it and which member it reads."""

	cls_reader: type[IngestionReader]
	cls_contract: FileContract
	str_stem: str


CASES: tuple[FreCase, ...] = (
	FreCase(FreCiaAbertaReader, FRE_CIA_ABERTA, "fre_cia_aberta"),
	FreCase(
		FreCiaAbertaCapitalSocialReader,
		FRE_CIA_ABERTA_CAPITAL_SOCIAL,
		"fre_cia_aberta_capital_social",
	),
	FreCase(
		FreCiaAbertaCapitalSocialClasseAcaoReader,
		FRE_CIA_ABERTA_CAPITAL_SOCIAL_CLASSE_ACAO,
		"fre_cia_aberta_capital_social_classe_acao",
	),
	FreCase(
		FreCiaAbertaCapitalSocialTituloConversivelReader,
		FRE_CIA_ABERTA_CAPITAL_SOCIAL_TITULO_CONVERSIVEL,
		"fre_cia_aberta_capital_social_titulo_conversivel",
	),
	FreCase(
		FreCiaAbertaDistribuicaoCapitalReader,
		FRE_CIA_ABERTA_DISTRIBUICAO_CAPITAL,
		"fre_cia_aberta_distribuicao_capital",
	),
	FreCase(
		FreCiaAbertaDistribuicaoCapitalClasseAcaoReader,
		FRE_CIA_ABERTA_DISTRIBUICAO_CAPITAL_CLASSE_ACAO,
		"fre_cia_aberta_distribuicao_capital_classe_acao",
	),
	FreCase(
		FreCiaAbertaResponsavelReader, FRE_CIA_ABERTA_RESPONSAVEL, "fre_cia_aberta_responsavel"
	),
	FreCase(
		FreCiaAbertaMercadoEstrangeiroReader,
		FRE_CIA_ABERTA_MERCADO_ESTRANGEIRO,
		"fre_cia_aberta_mercado_estrangeiro",
	),
	# Slice 2 of 4 — administração/pessoas, holding every CPF-bearing member.
	FreCase(FreCiaAbertaAuditorReader, FRE_CIA_ABERTA_AUDITOR, "fre_cia_aberta_auditor"),
	FreCase(
		FreCiaAbertaAdministradorMembroConselhoFiscalReader,
		FRE_CIA_ABERTA_ADMINISTRADOR_MEMBRO_CONSELHO_FISCAL,
		"fre_cia_aberta_administrador_membro_conselho_fiscal",
	),
	FreCase(
		FreCiaAbertaMembroComiteReader,
		FRE_CIA_ABERTA_MEMBRO_COMITE,
		"fre_cia_aberta_membro_comite",
	),
	FreCase(
		FreCiaAbertaRelacaoFamiliarReader,
		FRE_CIA_ABERTA_RELACAO_FAMILIAR,
		"fre_cia_aberta_relacao_familiar",
	),
	FreCase(
		FreCiaAbertaRelacaoSubordinacaoReader,
		FRE_CIA_ABERTA_RELACAO_SUBORDINACAO,
		"fre_cia_aberta_relacao_subordinacao",
	),
	FreCase(
		FreCiaAbertaPosicaoAcionariaReader,
		FRE_CIA_ABERTA_POSICAO_ACIONARIA,
		"fre_cia_aberta_posicao_acionaria",
	),
	FreCase(
		FreCiaAbertaPosicaoAcionariaClasseAcaoReader,
		FRE_CIA_ABERTA_POSICAO_ACIONARIA_CLASSE_ACAO,
		"fre_cia_aberta_posicao_acionaria_classe_acao",
	),
)
IDS = [case.cls_reader.__name__ for case in CASES]

# The CNPJ columns each member declares, **as measured against the 2025 artifact** — not derived
# from the header names. Members absent from this map declare the filing company's column alone.
DICT_CNPJ_COLS: dict[str, tuple[str, ...]] = {
	"fre_cia_aberta": ("CNPJ_CIA",),
	"fre_cia_aberta_auditor": ("CNPJ_Companhia", "CNPJ_Auditor"),
	"fre_cia_aberta_relacao_familiar": (
		"CNPJ_Companhia",
		"CNPJ_Emissor",
		"CNPJ_Emissor_Pessoa_Relacionada",
	),
}

# Columns holding a document that is CPF, or CPF *and* CNPJ, so none may be declared a CNPJ column.
DICT_NON_CNPJ_DOCS: dict[str, tuple[str, ...]] = {
	"fre_cia_aberta_auditor": ("CPF_Auditor",),
	"fre_cia_aberta_administrador_membro_conselho_fiscal": ("CPF",),
	"fre_cia_aberta_membro_comite": ("CPF",),
	"fre_cia_aberta_relacao_familiar": ("CPF_Administrador", "CPF_Pessoa_Relacionada"),
	# It holds both kinds of document — thousands of CNPJ against a few dozen CPF in 2025 —
	# even though its name says neither one of them.
	"fre_cia_aberta_relacao_subordinacao": ("CPF_Administrador", "Documento_Pessoa_Relacionada"),
	"fre_cia_aberta_posicao_acionaria": (
		"CPF_CNPJ_Acionista",
		"CPF_CNPJ_Acionista_Relacionado",
		"CPF_CNPJ_Representante_legal",
	),
}


def _value_for(str_col: str) -> str:
	"""Return a plausible source value for one column, by name."""
	if "CNPJ" in str_col.upper():
		return VALID_CNPJ
	if str_col.startswith("Data_") or str_col in ("DT_REFER", "DT_RECEB"):
		return "2025-08-25"
	if str_col.startswith("Valor_"):
		return VALOR_CAPITAL
	if str_col.startswith("Quantidade_"):
		return QUANTIDADE
	if str_col.startswith("Percentual_"):
		return "12.3456"
	return "x"


def _row(cls_contract: FileContract) -> list[str]:
	"""One valid row in the contract's column order."""
	return [_value_for(c) for c in cls_contract.tuple_required]


def _csv_text(list_cols: list[str], list_rows: list[list[str]]) -> str:
	"""Serialise a header + rows into the CVM ``;``-separated CSV shape."""
	return "\n".join([";".join(list_cols), *[";".join(r) for r in list_rows]]) + "\n"


def _all_members(dict_override: dict[str, str] | None = None) -> bytes:
	"""Build the archive holding this slice's members, one valid row each."""
	dict_members = {
		f"{case.str_stem}_2025.csv": _csv_text(
			list(case.cls_contract.tuple_required), [_row(case.cls_contract)]
		)
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
	"""All fifteen contracts equal the verbatim headers CVM publishes — the oracle."""
	for case in CASES:
		str_line = (PATH_FIXTURES / f"{case.str_stem}_header.csv").read_text(encoding="iso-8859-1")
		assert case.cls_contract.tuple_required == tuple(str_line.strip().split(";")), (
			case.str_stem
		)
	assert [len(c.cls_contract.tuple_required) for c in CASES] == [
		9,
		13,
		8,
		8,
		15,
		9,
		7,
		17,
		18,
		21,
		21,
		17,
		17,
		29,
		9,
	]


def test_the_index_uses_a_different_convention_from_its_satellites() -> None:
	"""FRE's index is uppercase-abbreviated; its satellites are CamelCase.

	FCA's index does the same and CGVN's does **not**, so there is no cross-dataset rule to infer.
	Both directions are asserted, plus the CGVN counter-example, so a template-minded change fails.
	"""
	set_index = set(FRE_CIA_ABERTA.tuple_required)

	assert {"CNPJ_CIA", "DT_REFER", "DT_RECEB", "DENOM_CIA", "ID_DOC", "LINK_DOC"} <= set_index
	assert "CNPJ_Companhia" not in set_index
	assert "Data_Referencia" not in set_index
	for case in CASES[1:]:
		set_sat = set(case.cls_contract.tuple_required)
		assert {"CNPJ_Companhia", "Data_Referencia"} <= set_sat, case.str_stem
		assert "CNPJ_CIA" not in set_sat, case.str_stem
	# The sibling CGVN index is the counter-example — CamelCase rather than uppercase.
	assert "CNPJ_Companhia" in CGVN_CIA_ABERTA.tuple_required
	assert "CNPJ_CIA" not in CGVN_CIA_ABERTA.tuple_required
	assert CgvnCiaAbertaReader._DATE_COLS[0] == "Data_Referencia"
	assert FreCiaAbertaReader._DATE_COLS == ("DT_REFER", "DT_RECEB")


def test_each_member_declares_its_own_cnpj_columns() -> None:
	"""Each member declares the CNPJ columns it actually has — one, two or three.

	FRE uses six different CNPJ column names across its 36 members, so nothing is inherited. The
	index declares ``CNPJ_CIA``; most satellites declare ``CNPJ_Companhia`` alone; ``auditor`` adds
	the auditor's own and ``relacao_familiar`` adds both sides' issuers. A blanket
	``== ("CNPJ_Companhia",)`` over every satellite — which held while only slice 1 existed — is
	exactly the assertion this replaces.
	"""
	for case in CASES:
		tuple_expected = DICT_CNPJ_COLS.get(case.str_stem, ("CNPJ_Companhia",))
		assert case.cls_contract.tuple_cnpj_cols == tuple_expected, case.str_stem
	# The declared counts genuinely differ across members, so no uniform rule holds.
	assert {len(c.cls_contract.tuple_cnpj_cols) for c in CASES} == {1, 2, 3}


def test_no_cpf_or_mixed_document_column_is_declared_a_cnpj_column() -> None:
	"""Personal and mixed-document columns stay out of ``tuple_cnpj_cols``.

	Two reasons, both load-bearing. A CPF is personal data and is not a company identifier, so
	asserting CNPJ validity over it is wrong in kind. And a *mixed* column would pass the check in
	a year whose values happened to be all-CNPJ, then fail the year one CPF appears — the contract
	would encode an accident of one artifact.

	``Documento_Pessoa_Relacionada`` is the case that a name-based rule gets wrong: it says neither
	CPF nor CNPJ and holds both.
	"""
	for case in CASES:
		tuple_docs = DICT_NON_CNPJ_DOCS.get(case.str_stem, ())
		for str_col in tuple_docs:
			assert str_col in case.cls_contract.tuple_required, f"{case.str_stem}.{str_col}"
			assert str_col not in case.cls_contract.tuple_cnpj_cols, f"{case.str_stem}.{str_col}"
	# No column named for CPF is ever declared, in any member — including future slices' shapes.
	for case in CASES:
		assert not [c for c in case.cls_contract.tuple_cnpj_cols if "CPF" in c.upper()], (
			case.str_stem
		)


def test_membro_comite_is_not_a_copy_of_the_administrador_member() -> None:
	"""Same column count (21), different columns — a copied contract would pass every other test.

	Both members describe people with a mandate, and both have exactly 21 columns, so the two
	are easy to conflate. They diverge in four columns each, and this asserts the divergence
	in **both** directions rather than only restating one contract.
	"""
	tuple_admin = FRE_CIA_ABERTA_ADMINISTRADOR_MEMBRO_CONSELHO_FISCAL.tuple_required
	tuple_comite = FRE_CIA_ABERTA_MEMBRO_COMITE.tuple_required

	assert len(tuple_admin) == len(tuple_comite) == 21
	assert tuple_admin != tuple_comite
	assert {
		"Orgao_Administracao",
		"Cargo_Eletivo_Ocupado",
		"Complemento_Cargo_Eletivo_Ocupado",
		"Eleito_Controlador",
	} <= set(tuple_admin) - set(tuple_comite)
	assert {
		"Tipo_Comite",
		"Descricao_Outros_Comites",
		"Cargo_Ocupado",
		"Descricao_Outro_Cargo_Ocupado",
	} <= set(tuple_comite) - set(tuple_admin)


def test_posicao_acionaria_keeps_the_lowercase_legal_spelling() -> None:
	"""CVM spells one column ``CPF_CNPJ_Representante_legal``; it is preserved verbatim.

	Its two siblings are ``CPF_CNPJ_Acionista`` and ``CPF_CNPJ_Acionista_Relacionado``, so the
	lowercase tail reads like a typo worth tidying. Normalising it would silently stop the column
	from being found in the real file.
	"""
	assert "CPF_CNPJ_Representante_legal" in FRE_CIA_ABERTA_POSICAO_ACIONARIA.tuple_required
	assert "CPF_CNPJ_Representante_Legal" not in FRE_CIA_ABERTA_POSICAO_ACIONARIA.tuple_required


def test_read_keeps_money_and_counts_as_exact_text(monkeypatch: pytest.MonkeyPatch) -> None:
	"""``Valor_Capital`` and ``Quantidade_*`` come back as published, never as floats.

	Asserted on the **string**, because a float comparison would not prove the point: Python's
	``repr`` round-trips many decimal strings exactly, so ``float()`` only visibly destroys a
	value when it carries trailing zeros or more precision than a double holds (see the VLMO
	reader, where ``61961072.9999543100`` does lose digits). Keeping the text is what guarantees
	fidelity for *every* value, not just the ones where the damage happens to be visible.

	Parameters
	----------
	monkeypatch : pytest.MonkeyPatch
		Fixture used to replace the download boundary.
	"""
	_patch(monkeypatch, _all_members())

	df_ = FreCiaAbertaCapitalSocialReader(date_ref=DATE_REF).read()

	assert df_["Valor_Capital"].iloc[0] == VALOR_CAPITAL
	assert isinstance(df_["Valor_Capital"].iloc[0], str)
	assert df_["Quantidade_Total_Acoes"].iloc[0] == QUANTIDADE
	assert isinstance(df_["Quantidade_Total_Acoes"].iloc[0], str)


@pytest.mark.parametrize("case", CASES, ids=IDS)
def test_read_returns_all_contract_columns(case: FreCase, monkeypatch: pytest.MonkeyPatch) -> None:
	"""Each reader's frame carries exactly its contract's columns, plus provenance.

	Parameters
	----------
	case : FreCase
		The reader spec under test.
	monkeypatch : pytest.MonkeyPatch
		Fixture used to replace the download boundary.
	"""
	_patch(monkeypatch, _all_members())

	df_ = case.cls_reader(date_ref=DATE_REF).read()

	assert len(df_) == 1
	assert list(df_.columns) == list(case.cls_contract.output_columns)


@pytest.mark.parametrize("case", CASES, ids=IDS)
def test_read_coerces_every_declared_date_column(
	case: FreCase, monkeypatch: pytest.MonkeyPatch
) -> None:
	"""Each reader coerces its own date columns — they differ per member (1 to 5 here).

	Parameters
	----------
	case : FreCase
		The reader spec under test.
	monkeypatch : pytest.MonkeyPatch
		Fixture used to replace the download boundary.
	"""
	_patch(monkeypatch, _all_members())

	df_ = case.cls_reader(date_ref=DATE_REF).read()

	assert case.cls_reader._DATE_COLS
	for str_col in case.cls_reader._DATE_COLS:
		assert isinstance(df_[str_col].iloc[0], date), f"{case.str_stem}.{str_col}"


def test_read_accepts_a_blank_data_ultima_assembleia(monkeypatch: pytest.MonkeyPatch) -> None:
	"""``Data_Ultima_Assembleia`` is blank in a couple of real rows — it becomes ``NaT``.

	Parameters
	----------
	monkeypatch : pytest.MonkeyPatch
		Fixture used to replace the download boundary.
	"""
	list_cols = list(FRE_CIA_ABERTA_DISTRIBUICAO_CAPITAL.tuple_required)
	list_blank = ["" if c == "Data_Ultima_Assembleia" else _value_for(c) for c in list_cols]
	str_csv = _csv_text(list_cols, [_row(FRE_CIA_ABERTA_DISTRIBUICAO_CAPITAL), list_blank])
	_patch(monkeypatch, _all_members({"fre_cia_aberta_distribuicao_capital_2025.csv": str_csv}))

	df_ = FreCiaAbertaDistribuicaoCapitalReader(date_ref=DATE_REF).read()

	assert len(df_) == 2
	assert df_["Data_Ultima_Assembleia"].iloc[0] == date(2025, 8, 25)
	assert pd.isna(df_["Data_Ultima_Assembleia"].iloc[1])


def test_read_accepts_an_entirely_blank_date_column(monkeypatch: pytest.MonkeyPatch) -> None:
	"""A date column that is blank in **every** row still types as a date, all ``NaT``.

	Two real cases in 2025: ``auditor.Data_Fim_Contratacao`` (an open engagement has no end
	date) and ``posicao_acionaria.Data_Composicao_Capital_Social``. Neither is dropped from
	``_DATE_COLS`` on the strength of one empty year — the column is a date by contract, and a
	later year that populates it must not suddenly come back as text.

	⚠️ Asserted on the **dtype**, because emptiness does not discriminate: pandas turns a blank
	field into a missing value under ``dtype="str"`` too, so ``isna().all()`` is ``True``
	whether or not the column is declared a date. Dropping it from ``_DATE_COLS`` yields
	``string``/``<NA>`` instead of ``datetime64``/``NaT`` — only the dtype tells them apart.

	Parameters
	----------
	monkeypatch : pytest.MonkeyPatch
		Fixture used to replace the download boundary.
	"""
	list_cols = list(FRE_CIA_ABERTA_AUDITOR.tuple_required)
	list_blank = ["" if c == "Data_Fim_Contratacao" else _value_for(c) for c in list_cols]
	str_csv = _csv_text(list_cols, [list_blank, list_blank])
	_patch(monkeypatch, _all_members({"fre_cia_aberta_auditor_2025.csv": str_csv}))

	df_ = FreCiaAbertaAuditorReader(date_ref=DATE_REF).read()

	assert len(df_) == 2
	assert "Data_Fim_Contratacao" in FreCiaAbertaAuditorReader._DATE_COLS
	assert pd.api.types.is_datetime64_any_dtype(df_["Data_Fim_Contratacao"])
	assert df_["Data_Fim_Contratacao"].isna().all()
	assert df_["Data_Inicio_Contratacao"].iloc[0] == date(2025, 8, 25)
	# The same shape in posicao_acionaria, which is likewise blank throughout 2025.
	assert "Data_Composicao_Capital_Social" in FreCiaAbertaPosicaoAcionariaReader._DATE_COLS


def test_read_keeps_personal_documents_as_exact_text(monkeypatch: pytest.MonkeyPatch) -> None:
	"""CPF and mixed-document columns come back as published text, never reformatted.

	Parameters
	----------
	monkeypatch : pytest.MonkeyPatch
		Fixture used to replace the download boundary.
	"""
	str_cpf = "596.116.268-00"
	list_cols = list(FRE_CIA_ABERTA_RELACAO_SUBORDINACAO.tuple_required)
	list_row = [str_cpf if c == "CPF_Administrador" else _value_for(c) for c in list_cols]
	str_csv = _csv_text(list_cols, [list_row])
	_patch(monkeypatch, _all_members({"fre_cia_aberta_relacao_subordinacao_2025.csv": str_csv}))

	df_ = FreCiaAbertaRelacaoSubordinacaoReader(date_ref=DATE_REF).read()

	assert df_["CPF_Administrador"].iloc[0] == str_cpf
	assert isinstance(df_["CPF_Administrador"].iloc[0], str)


@pytest.mark.parametrize("case", CASES, ids=IDS)
def test_read_requests_the_shared_yearly_url(
	case: FreCase, monkeypatch: pytest.MonkeyPatch
) -> None:
	"""Every FRE reader fetches the same yearly archive, selected by ``date_ref.year`` alone.

	Parameters
	----------
	case : FreCase
		The reader spec under test.
	monkeypatch : pytest.MonkeyPatch
		Fixture used to replace the download boundary.
	"""
	list_urls = _patch(monkeypatch, _all_members())

	case.cls_reader(date_ref=date(2025, 1, 1)).read()

	assert list_urls == [URL]


@pytest.mark.parametrize("case", CASES, ids=IDS)
def test_read_stamps_provenance(case: FreCase, monkeypatch: pytest.MonkeyPatch) -> None:
	"""Each frame carries its own source key and the shared archive URL.

	Parameters
	----------
	case : FreCase
		The reader spec under test.
	monkeypatch : pytest.MonkeyPatch
		Fixture used to replace the download boundary.
	"""
	_patch(monkeypatch, _all_members())

	df_ = case.cls_reader(date_ref=DATE_REF).read()

	assert df_["source_key"].iloc[0] == case.cls_contract.str_source_key
	assert df_["url"].iloc[0] == URL


def test_read_raises_contract_error_on_a_missing_column(
	monkeypatch: pytest.MonkeyPatch,
) -> None:
	"""A member missing a required column fails before any typing is applied.

	Parameters
	----------
	monkeypatch : pytest.MonkeyPatch
		Fixture used to replace the download boundary.
	"""
	list_cols = list(FRE_CIA_ABERTA_CAPITAL_SOCIAL.tuple_required)[:-1]
	str_csv = _csv_text(list_cols, [[_value_for(c) for c in list_cols]])
	_patch(monkeypatch, _all_members({"fre_cia_aberta_capital_social_2025.csv": str_csv}))

	with pytest.raises(ContractError):
		FreCiaAbertaCapitalSocialReader(date_ref=DATE_REF).read()


def test_read_persists_the_shared_raw_zip(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
	"""``path_raw`` keeps the one archive every FRE reader shares.

	Parameters
	----------
	monkeypatch : pytest.MonkeyPatch
		Fixture used to replace the download boundary.
	tmp_path : pathlib.Path
		Pytest-provided throwaway directory standing in for the bronze landing zone.
	"""
	_patch(monkeypatch, _all_members())
	path_raw = tmp_path / "bronze"

	FreCiaAbertaResponsavelReader(date_ref=DATE_REF, path_raw=path_raw).read()

	assert (path_raw / "fre_cia_aberta_2025.zip").exists()


def test_meta_url_is_the_standard_prefixed_zip() -> None:
	"""FRE's META is `meta_fre_cia_aberta.zip`; the other three candidates 404.

	Notably the no-prefix `fre_cia_aberta.zip` 404s even though that exact form is the **correct**
	one for the sibling FCA — the prefix is not portal policy, so each URL is pinned per dataset.
	"""
	assert MetaFreCiaAbertaReader._META_URL == (
		"https://dados.cvm.gov.br/dados/CIA_ABERTA/DOC/FRE/META/meta_fre_cia_aberta.zip"
	)
	assert MetaFreCiaAbertaReader._CONTRACT.str_source_key == "meta_fre_cia_aberta"
