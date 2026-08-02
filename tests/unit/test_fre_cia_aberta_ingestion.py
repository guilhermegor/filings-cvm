"""Unit tests for the CIA_ABERTA/DOC/FRE readers — all four slices, all 36 members.

`fre_cia_aberta_AAAA.zip` is the portal's largest dataset (36 members, ~131k rows), shipped in four
themed slices — index + capital, administração/pessoas, diversidade, and remuneração / valores
mobiliários / transações. This file covers every one of them.

Eight things carry the weight here:

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
   and different columns, so a copied contract would ship wrong with the suite green;
5. the diversidade slice adds **five more same-width pairs** — `*_local_*` vs `*_posicao_*` differ
   only in their grouping column — so the same hazard occurs six times in this one dataset;
6. those diversidade members are **aggregate counts, not personal data**, despite names that read
   as individual-level protected attributes. That claim is asserted from the columns, because
   asserting it from the member name is the mistake that was already made here once;
7. the remuneração slice adds **four more same-width pairs**, three of which also share their
   first ten columns — the tightest collision in the dataset;
8. **an empty column is a property of the year, not of the schema.** Two `participacao_sociedade`
   date columns are empty throughout 2025 and stay dates, and
   `transacao_parte_relacionada.Documento_Parte_Relacionada` is empty throughout 2025 and stays
   **out** of `tuple_cnpj_cols`, because it is a CPF-or-CNPJ column by design.

Every test except one builds its input from each contract's `tuple_required`, so it is a tautology.
The exception is :func:`test_contracts_match_the_published_headers`, which compares all thirty-six
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

from filings_cvm._internal.config.contracts import (
	CGVN_CIA_ABERTA,
	FRE_CIA_ABERTA,
	FRE_CIA_ABERTA_ACAO_ENTREGUE,
	FRE_CIA_ABERTA_ADMINISTRADOR_DECLARACAO_GENERO,
	FRE_CIA_ABERTA_ADMINISTRADOR_DECLARACAO_RACA,
	FRE_CIA_ABERTA_ADMINISTRADOR_MEMBRO_CONSELHO_FISCAL,
	FRE_CIA_ABERTA_ADMINISTRADOR_PCD,
	FRE_CIA_ABERTA_AUDITOR,
	FRE_CIA_ABERTA_CAPITAL_SOCIAL,
	FRE_CIA_ABERTA_CAPITAL_SOCIAL_CLASSE_ACAO,
	FRE_CIA_ABERTA_CAPITAL_SOCIAL_TITULO_CONVERSIVEL,
	FRE_CIA_ABERTA_DISTRIBUICAO_CAPITAL,
	FRE_CIA_ABERTA_DISTRIBUICAO_CAPITAL_CLASSE_ACAO,
	FRE_CIA_ABERTA_EMPREGADO_LOCAL_DECLARACAO_GENERO,
	FRE_CIA_ABERTA_EMPREGADO_LOCAL_DECLARACAO_RACA,
	FRE_CIA_ABERTA_EMPREGADO_LOCAL_FAIXA_ETARIA,
	FRE_CIA_ABERTA_EMPREGADO_PCD,
	FRE_CIA_ABERTA_EMPREGADO_POSICAO_DECLARACAO_GENERO,
	FRE_CIA_ABERTA_EMPREGADO_POSICAO_DECLARACAO_RACA,
	FRE_CIA_ABERTA_EMPREGADO_POSICAO_FAIXA_ETARIA,
	FRE_CIA_ABERTA_EMPREGADO_POSICAO_LOCAL,
	FRE_CIA_ABERTA_MEMBRO_COMITE,
	FRE_CIA_ABERTA_MERCADO_ESTRANGEIRO,
	FRE_CIA_ABERTA_OUTRO_VALOR_MOBILIARIO,
	FRE_CIA_ABERTA_PARTICIPACAO_SOCIEDADE,
	FRE_CIA_ABERTA_POSICAO_ACIONARIA,
	FRE_CIA_ABERTA_POSICAO_ACIONARIA_CLASSE_ACAO,
	FRE_CIA_ABERTA_RELACAO_FAMILIAR,
	FRE_CIA_ABERTA_RELACAO_SUBORDINACAO,
	FRE_CIA_ABERTA_REMUNERACAO_ACAO,
	FRE_CIA_ABERTA_REMUNERACAO_MAXIMA_MINIMA_MEDIA,
	FRE_CIA_ABERTA_REMUNERACAO_TOTAL_ORGAO,
	FRE_CIA_ABERTA_REMUNERACAO_VARIAVEL,
	FRE_CIA_ABERTA_RESPONSAVEL,
	FRE_CIA_ABERTA_TITULAR_VALOR_MOBILIARIO,
	FRE_CIA_ABERTA_TITULO_EXTERIOR,
	FRE_CIA_ABERTA_TRANSACAO_PARTE_RELACIONADA,
	FileContract,
)
from filings_cvm._internal.config.ports.ingestion_reader import IngestionReader
from filings_cvm._internal.utils.tabular_reader import ContractError
from filings_cvm.ingestion.cia_aberta import (
	CgvnCiaAbertaReader,
	FreCiaAbertaAcaoEntregueReader,
	FreCiaAbertaAdministradorDeclaracaoGeneroReader,
	FreCiaAbertaAdministradorDeclaracaoRacaReader,
	FreCiaAbertaAdministradorMembroConselhoFiscalReader,
	FreCiaAbertaAdministradorPcdReader,
	FreCiaAbertaAuditorReader,
	FreCiaAbertaCapitalSocialClasseAcaoReader,
	FreCiaAbertaCapitalSocialReader,
	FreCiaAbertaCapitalSocialTituloConversivelReader,
	FreCiaAbertaDistribuicaoCapitalClasseAcaoReader,
	FreCiaAbertaDistribuicaoCapitalReader,
	FreCiaAbertaEmpregadoLocalDeclaracaoGeneroReader,
	FreCiaAbertaEmpregadoLocalDeclaracaoRacaReader,
	FreCiaAbertaEmpregadoLocalFaixaEtariaReader,
	FreCiaAbertaEmpregadoPcdReader,
	FreCiaAbertaEmpregadoPosicaoDeclaracaoGeneroReader,
	FreCiaAbertaEmpregadoPosicaoDeclaracaoRacaReader,
	FreCiaAbertaEmpregadoPosicaoFaixaEtariaReader,
	FreCiaAbertaEmpregadoPosicaoLocalReader,
	FreCiaAbertaMembroComiteReader,
	FreCiaAbertaMercadoEstrangeiroReader,
	FreCiaAbertaOutroValorMobiliarioReader,
	FreCiaAbertaParticipacaoSociedadeReader,
	FreCiaAbertaPosicaoAcionariaClasseAcaoReader,
	FreCiaAbertaPosicaoAcionariaReader,
	FreCiaAbertaReader,
	FreCiaAbertaRelacaoFamiliarReader,
	FreCiaAbertaRelacaoSubordinacaoReader,
	FreCiaAbertaRemuneracaoAcaoReader,
	FreCiaAbertaRemuneracaoMaximaMinimaMediaReader,
	FreCiaAbertaRemuneracaoTotalOrgaoReader,
	FreCiaAbertaRemuneracaoVariavelReader,
	FreCiaAbertaResponsavelReader,
	FreCiaAbertaTitularValorMobiliarioReader,
	FreCiaAbertaTituloExteriorReader,
	FreCiaAbertaTransacaoParteRelacionadaReader,
	MetaFreCiaAbertaReader,
)


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
	# Slice 3 of 4 — the diversidade members, which hold aggregate counts per company
	# and never individual-level data.
	FreCase(
		FreCiaAbertaAdministradorPcdReader,
		FRE_CIA_ABERTA_ADMINISTRADOR_PCD,
		"fre_cia_aberta_administrador_PCD",
	),
	FreCase(
		FreCiaAbertaAdministradorDeclaracaoGeneroReader,
		FRE_CIA_ABERTA_ADMINISTRADOR_DECLARACAO_GENERO,
		"fre_cia_aberta_administrador_declaracao_genero",
	),
	FreCase(
		FreCiaAbertaAdministradorDeclaracaoRacaReader,
		FRE_CIA_ABERTA_ADMINISTRADOR_DECLARACAO_RACA,
		"fre_cia_aberta_administrador_declaracao_raca",
	),
	FreCase(
		FreCiaAbertaEmpregadoPcdReader,
		FRE_CIA_ABERTA_EMPREGADO_PCD,
		"fre_cia_aberta_empregado_PCD",
	),
	FreCase(
		FreCiaAbertaEmpregadoLocalDeclaracaoGeneroReader,
		FRE_CIA_ABERTA_EMPREGADO_LOCAL_DECLARACAO_GENERO,
		"fre_cia_aberta_empregado_local_declaracao_genero",
	),
	FreCase(
		FreCiaAbertaEmpregadoLocalDeclaracaoRacaReader,
		FRE_CIA_ABERTA_EMPREGADO_LOCAL_DECLARACAO_RACA,
		"fre_cia_aberta_empregado_local_declaracao_raca",
	),
	FreCase(
		FreCiaAbertaEmpregadoLocalFaixaEtariaReader,
		FRE_CIA_ABERTA_EMPREGADO_LOCAL_FAIXA_ETARIA,
		"fre_cia_aberta_empregado_local_faixa_etaria",
	),
	FreCase(
		FreCiaAbertaEmpregadoPosicaoDeclaracaoGeneroReader,
		FRE_CIA_ABERTA_EMPREGADO_POSICAO_DECLARACAO_GENERO,
		"fre_cia_aberta_empregado_posicao_declaracao_genero",
	),
	FreCase(
		FreCiaAbertaEmpregadoPosicaoDeclaracaoRacaReader,
		FRE_CIA_ABERTA_EMPREGADO_POSICAO_DECLARACAO_RACA,
		"fre_cia_aberta_empregado_posicao_declaracao_raca",
	),
	FreCase(
		FreCiaAbertaEmpregadoPosicaoFaixaEtariaReader,
		FRE_CIA_ABERTA_EMPREGADO_POSICAO_FAIXA_ETARIA,
		"fre_cia_aberta_empregado_posicao_faixa_etaria",
	),
	FreCase(
		FreCiaAbertaEmpregadoPosicaoLocalReader,
		FRE_CIA_ABERTA_EMPREGADO_POSICAO_LOCAL,
		"fre_cia_aberta_empregado_posicao_local",
	),
	# Slice 4 of 4 — remuneração, valores mobiliários and transações, closing the dataset at 36.
	FreCase(
		FreCiaAbertaAcaoEntregueReader,
		FRE_CIA_ABERTA_ACAO_ENTREGUE,
		"fre_cia_aberta_acao_entregue",
	),
	FreCase(
		FreCiaAbertaRemuneracaoAcaoReader,
		FRE_CIA_ABERTA_REMUNERACAO_ACAO,
		"fre_cia_aberta_remuneracao_acao",
	),
	FreCase(
		FreCiaAbertaRemuneracaoMaximaMinimaMediaReader,
		FRE_CIA_ABERTA_REMUNERACAO_MAXIMA_MINIMA_MEDIA,
		"fre_cia_aberta_remuneracao_maxima_minima_media",
	),
	FreCase(
		FreCiaAbertaRemuneracaoTotalOrgaoReader,
		FRE_CIA_ABERTA_REMUNERACAO_TOTAL_ORGAO,
		"fre_cia_aberta_remuneracao_total_orgao",
	),
	FreCase(
		FreCiaAbertaRemuneracaoVariavelReader,
		FRE_CIA_ABERTA_REMUNERACAO_VARIAVEL,
		"fre_cia_aberta_remuneracao_variavel",
	),
	FreCase(
		FreCiaAbertaOutroValorMobiliarioReader,
		FRE_CIA_ABERTA_OUTRO_VALOR_MOBILIARIO,
		"fre_cia_aberta_outro_valor_mobiliario",
	),
	FreCase(
		FreCiaAbertaTitularValorMobiliarioReader,
		FRE_CIA_ABERTA_TITULAR_VALOR_MOBILIARIO,
		"fre_cia_aberta_titular_valor_mobiliario",
	),
	FreCase(
		FreCiaAbertaTituloExteriorReader,
		FRE_CIA_ABERTA_TITULO_EXTERIOR,
		"fre_cia_aberta_titulo_exterior",
	),
	FreCase(
		FreCiaAbertaParticipacaoSociedadeReader,
		FRE_CIA_ABERTA_PARTICIPACAO_SOCIEDADE,
		"fre_cia_aberta_participacao_sociedade",
	),
	FreCase(
		FreCiaAbertaTransacaoParteRelacionadaReader,
		FRE_CIA_ABERTA_TRANSACAO_PARTE_RELACIONADA,
		"fre_cia_aberta_transacao_parte_relacionada",
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
	# The invested company's own CNPJ, beside the filer's.
	"fre_cia_aberta_participacao_sociedade": ("CNPJ_Companhia", "CNPJ"),
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
	# Empty throughout 2025 and still excluded, because its sibling ``Tipo_Pessoa`` is a PF/PJ
	# flag — the column holds a CPF or a CNPJ by design, so declaring it would pass every empty
	# year and fail the first populated one.
	"fre_cia_aberta_transacao_parte_relacionada": ("Documento_Parte_Relacionada",),
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
	"""All thirty-six contracts equal the verbatim headers CVM publishes — the oracle."""
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
		10,
		12,
		14,
		10,
		11,
		13,
		9,
		11,
		13,
		9,
		12,
		14,
		14,
		14,
		27,
		18,
		24,
		9,
		21,
		21,
		22,
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


# Pairs of diversidade members with the SAME column count and DIFFERENT columns, measured on the
# 2025 artifact. Each pair is a place where a copied contract would pass every test except the
# one comparing it to the pinned header.
COLLIDING_PAIRS = (
	(FRE_CIA_ABERTA_EMPREGADO_LOCAL_FAIXA_ETARIA, FRE_CIA_ABERTA_EMPREGADO_POSICAO_FAIXA_ETARIA),
	(FRE_CIA_ABERTA_ADMINISTRADOR_PCD, FRE_CIA_ABERTA_EMPREGADO_PCD),
	(
		FRE_CIA_ABERTA_EMPREGADO_LOCAL_DECLARACAO_GENERO,
		FRE_CIA_ABERTA_EMPREGADO_POSICAO_DECLARACAO_GENERO,
	),
	(FRE_CIA_ABERTA_ADMINISTRADOR_DECLARACAO_GENERO, FRE_CIA_ABERTA_EMPREGADO_POSICAO_LOCAL),
	(
		FRE_CIA_ABERTA_EMPREGADO_LOCAL_DECLARACAO_RACA,
		FRE_CIA_ABERTA_EMPREGADO_POSICAO_DECLARACAO_RACA,
	),
)


@pytest.mark.parametrize(("cls_left", "cls_right"), COLLIDING_PAIRS)
def test_same_width_diversidade_members_are_not_the_same_columns(
	cls_left: FileContract, cls_right: FileContract
) -> None:
	"""Five pairs share a column count; none shares a column list.

	The diversidade members differ by one grouping column (`Local` vs `Posicao` vs
	`Orgao_Administracao`) and by which buckets they carry, so a copied contract lines up on width
	and fails only against the pinned header. Asserting the width match *and* the column mismatch
	states why each pair is a hazard rather than just restating one contract.

	Parameters
	----------
	cls_left : FileContract
		The first contract of the colliding pair.
	cls_right : FileContract
		The second contract of the colliding pair.
	"""
	assert len(cls_left.tuple_required) == len(cls_right.tuple_required)
	assert cls_left.tuple_required != cls_right.tuple_required


def test_every_diversidade_contract_has_a_distinct_column_list() -> None:
	"""No two of the eleven diversidade members share a column list — none is a copy of another."""
	list_contracts = [case.cls_contract for case in CASES[15:26]]

	assert len(list_contracts) == 11
	assert len({c.tuple_required for c in list_contracts}) == 11


def test_diversidade_members_carry_counts_and_no_personal_identifier() -> None:
	"""The diversidade members are aggregates: `Quantidade_*` totals, no CPF, one company CNPJ.

	This is the correction that measurement forced. Member names like `*_declaracao_raca` /
	`*_declaracao_genero` / `*_PCD` read as individual-level protected attributes, and were once
	classified that way from the name alone. The columns say otherwise — they are counts per
	company and grouping, and no individual appears in any of them.
	"""
	for case in CASES[15:26]:
		tuple_cols = case.cls_contract.tuple_required
		assert any(c.startswith("Quantidade_") for c in tuple_cols), case.str_stem
		assert not [c for c in tuple_cols if "CPF" in c.upper()], case.str_stem
		assert not [c for c in tuple_cols if c.startswith("Nome_") and c != "Nome_Companhia"], (
			case.str_stem
		)
		# Only the filing company's CNPJ is declared — the counts are not identifiers.
		assert case.cls_contract.tuple_cnpj_cols == ("CNPJ_Companhia",), case.str_stem


def test_diversidade_counts_come_back_as_exact_text(monkeypatch: pytest.MonkeyPatch) -> None:
	"""`Quantidade_*` is a count and stays source text, never a binary float.

	Parameters
	----------
	monkeypatch : pytest.MonkeyPatch
		Fixture used to replace the download boundary.
	"""
	_patch(monkeypatch, _all_members())

	df_ = FreCiaAbertaAdministradorDeclaracaoRacaReader(date_ref=DATE_REF).read()

	assert df_["Quantidade_Preto"].iloc[0] == QUANTIDADE
	assert isinstance(df_["Quantidade_Preto"].iloc[0], str)


def test_administrador_pcd_accepts_blank_counts(monkeypatch: pytest.MonkeyPatch) -> None:
	"""A blank `Quantidade_*` is an absent declaration, not a zero — it stays empty, never 0.

	Roughly a fifth of `administrador_PCD`'s 2025 rows leave the counts blank. Coercing those to
	`0` would invent a declaration the company never made, and the difference is invisible once
	summed.

	Parameters
	----------
	monkeypatch : pytest.MonkeyPatch
		Fixture used to replace the download boundary.
	"""
	list_cols = list(FRE_CIA_ABERTA_ADMINISTRADOR_PCD.tuple_required)
	list_blank = ["" if c.startswith("Quantidade_") else _value_for(c) for c in list_cols]
	str_csv = _csv_text(list_cols, [_row(FRE_CIA_ABERTA_ADMINISTRADOR_PCD), list_blank])
	_patch(monkeypatch, _all_members({"fre_cia_aberta_administrador_PCD_2025.csv": str_csv}))

	df_ = FreCiaAbertaAdministradorPcdReader(date_ref=DATE_REF).read()

	assert len(df_) == 2
	assert df_["Quantidade_PCD"].iloc[0] == QUANTIDADE
	assert pd.isna(df_["Quantidade_PCD"].iloc[1])


def test_the_pcd_pair_overlap_is_exactly_as_documented() -> None:
	"""The PCD pair shares 8 of 10 columns, differing in exactly two each.

	The overlap is stated in three docstrings and two docs pages as the reason the anti-copy test
	exists — so it is a claim, and an unverified claim in prose is how a wrong number survives. It
	was wrong once: "only six" shipped in a wheel docstring and was caught by an install-verify,
	not by this suite, because nothing asserted the intersection.

	The true figure makes the hazard **worse**, which is the point: the two members are more alike
	than the prose said.
	"""
	set_admin = set(FRE_CIA_ABERTA_ADMINISTRADOR_PCD.tuple_required)
	set_empregado = set(FRE_CIA_ABERTA_EMPREGADO_PCD.tuple_required)

	assert len(set_admin) == len(set_empregado) == 10
	assert len(set_admin & set_empregado) == 8
	assert set_admin - set_empregado == {"Orgao_Administracao", "Nao_Aplicavel"}
	assert set_empregado - set_admin == {"Codigo_Posicao", "Posicao"}


# Pairs of remuneração-slice members with the SAME column count and DIFFERENT columns. The first
# three collide at 14 and share their first ten columns, which is the tightest collision in the
# dataset; the last pair collides at 21 with near-disjoint lists.
COLLIDING_PAIRS_SLICE_4 = (
	(FRE_CIA_ABERTA_ACAO_ENTREGUE, FRE_CIA_ABERTA_REMUNERACAO_ACAO),
	(FRE_CIA_ABERTA_ACAO_ENTREGUE, FRE_CIA_ABERTA_REMUNERACAO_MAXIMA_MINIMA_MEDIA),
	(FRE_CIA_ABERTA_REMUNERACAO_ACAO, FRE_CIA_ABERTA_REMUNERACAO_MAXIMA_MINIMA_MEDIA),
	(FRE_CIA_ABERTA_TITULO_EXTERIOR, FRE_CIA_ABERTA_PARTICIPACAO_SOCIEDADE),
)


@pytest.mark.parametrize(("cls_left", "cls_right"), COLLIDING_PAIRS_SLICE_4)
def test_same_width_remuneracao_members_are_not_the_same_columns(
	cls_left: FileContract, cls_right: FileContract
) -> None:
	"""Four more same-width pairs, none of them a copy of the other.

	`acao_entregue`, `remuneracao_acao` and `remuneracao_maxima_minima_media` all have 14 columns
	**and share the first ten**, so a contract copied between them lines up on width, on prefix,
	and on every generated-input test — only the pinned header disagrees.

	Parameters
	----------
	cls_left : FileContract
		The first contract of the colliding pair.
	cls_right : FileContract
		The second contract of the colliding pair.
	"""
	assert len(cls_left.tuple_required) == len(cls_right.tuple_required)
	assert cls_left.tuple_required != cls_right.tuple_required


def test_the_three_fourteen_column_members_share_exactly_their_first_ten() -> None:
	"""The shared prefix is stated as a hazard in prose, so it is asserted rather than believed.

	Sharing ten of fourteen columns is what makes these three the easiest members in the dataset to
	conflate. A number asserted only in a docstring has already shipped wrong in this dataset once.
	"""
	tuple_acao = FRE_CIA_ABERTA_ACAO_ENTREGUE.tuple_required
	tuple_remun = FRE_CIA_ABERTA_REMUNERACAO_ACAO.tuple_required
	tuple_max = FRE_CIA_ABERTA_REMUNERACAO_MAXIMA_MINIMA_MEDIA.tuple_required

	assert len(tuple_acao) == len(tuple_remun) == len(tuple_max) == 14
	assert tuple_acao[:10] == tuple_remun[:10]
	assert tuple_acao[:8] == tuple_max[:8]
	# The divergence is real and in the tail, not a reordering of the same names.
	assert len({tuple_acao, tuple_remun, tuple_max}) == 3
	assert set(tuple_acao[10:]).isdisjoint(tuple_remun[10:])


def test_participacao_sociedade_declares_the_invested_company_cnpj() -> None:
	"""The only member of this slice with two CNPJ columns — the filer's and the investee's."""
	assert FRE_CIA_ABERTA_PARTICIPACAO_SOCIEDADE.tuple_cnpj_cols == ("CNPJ_Companhia", "CNPJ")
	assert "CNPJ" in FRE_CIA_ABERTA_PARTICIPACAO_SOCIEDADE.tuple_required


def test_read_honours_the_foreign_subsidiary_cnpj_placeholder(
	monkeypatch: pytest.MonkeyPatch,
) -> None:
	"""`00000000000000` is returned as published, and does not fail the CNPJ check.

	792 of the 6.511 `CNPJ` values in 2025 are that literal placeholder — what CVM publishes for a
	subsidiary abroad with no Brazilian CNPJ. The contract requires *at least one* valid value in
	the column, so a mixed artifact passes and the placeholders survive untouched. Rewriting them
	to `NA` would erase the distinction between "no Brazilian CNPJ" and "not reported".

	Parameters
	----------
	monkeypatch : pytest.MonkeyPatch
		Fixture used to replace the download boundary.
	"""
	str_placeholder = "00000000000000"
	list_cols = list(FRE_CIA_ABERTA_PARTICIPACAO_SOCIEDADE.tuple_required)
	list_foreign = [str_placeholder if c == "CNPJ" else _value_for(c) for c in list_cols]
	str_csv = _csv_text(list_cols, [_row(FRE_CIA_ABERTA_PARTICIPACAO_SOCIEDADE), list_foreign])
	_patch(monkeypatch, _all_members({"fre_cia_aberta_participacao_sociedade_2025.csv": str_csv}))

	df_ = FreCiaAbertaParticipacaoSociedadeReader(date_ref=DATE_REF).read()

	assert len(df_) == 2
	assert df_["CNPJ"].iloc[1] == str_placeholder
	assert isinstance(df_["CNPJ"].iloc[1], str)


def test_read_rejects_a_participacao_sociedade_of_placeholders_only(
	monkeypatch: pytest.MonkeyPatch,
) -> None:
	"""The tolerance is "at least one valid", not "anything goes" — an all-placeholder file fails.

	This pins the edge the previous test relies on. Without it, "the placeholder is accepted" could
	equally describe a contract that had stopped checking the column at all.

	Parameters
	----------
	monkeypatch : pytest.MonkeyPatch
		Fixture used to replace the download boundary.
	"""
	list_cols = list(FRE_CIA_ABERTA_PARTICIPACAO_SOCIEDADE.tuple_required)
	list_foreign = ["00000000000000" if c == "CNPJ" else _value_for(c) for c in list_cols]
	str_csv = _csv_text(list_cols, [list_foreign, list_foreign])
	_patch(monkeypatch, _all_members({"fre_cia_aberta_participacao_sociedade_2025.csv": str_csv}))

	with pytest.raises(ContractError):
		FreCiaAbertaParticipacaoSociedadeReader(date_ref=DATE_REF).read()


def test_participacao_sociedade_empty_date_columns_are_still_dates(
	monkeypatch: pytest.MonkeyPatch,
) -> None:
	"""`Data_Valor_Mercado` and `Data_Valor_Contabil` are empty all through 2025 and still dates.

	The dataset's META types both `date`, and twelve of this member's columns arrive empty in 2025
	— emptiness is a property of the year, not of the schema. Asserted on the **dtype**, because a
	blank field becomes a missing value under `dtype="str"` too, so `isna().all()` holds either
	way; only `datetime64` vs `string` distinguishes a declared date from text.

	Parameters
	----------
	monkeypatch : pytest.MonkeyPatch
		Fixture used to replace the download boundary.
	"""
	tuple_empty = ("Data_Valor_Mercado", "Data_Valor_Contabil")
	list_cols = list(FRE_CIA_ABERTA_PARTICIPACAO_SOCIEDADE.tuple_required)
	list_row = ["" if c in tuple_empty else _value_for(c) for c in list_cols]
	str_csv = _csv_text(list_cols, [list_row, list_row])
	_patch(monkeypatch, _all_members({"fre_cia_aberta_participacao_sociedade_2025.csv": str_csv}))

	df_ = FreCiaAbertaParticipacaoSociedadeReader(date_ref=DATE_REF).read()

	for str_col in tuple_empty:
		assert str_col in FreCiaAbertaParticipacaoSociedadeReader._DATE_COLS
		assert pd.api.types.is_datetime64_any_dtype(df_[str_col]), str_col
		assert df_[str_col].isna().all(), str_col


def test_duracao_transacao_is_free_text_and_never_coerced(monkeypatch: pytest.MonkeyPatch) -> None:
	"""879 of its 11.238 values look like `DD/MM/YYYY`, and it is still not a date column.

	The META types it `varchar`, and the majority of its values are prose ("indeterminado", "5
	anos"). Coercing the minority that parse would silently produce a column that is `NaT` wherever
	the company wrote a sentence, and — being day-first — would misread the ones that do parse.

	Parameters
	----------
	monkeypatch : pytest.MonkeyPatch
		Fixture used to replace the download boundary.
	"""
	str_br_date = "31/12/2025"
	list_cols = list(FRE_CIA_ABERTA_TRANSACAO_PARTE_RELACIONADA.tuple_required)
	list_row = [str_br_date if c == "Duracao_Transacao" else _value_for(c) for c in list_cols]
	str_csv = _csv_text(list_cols, [list_row])
	_patch(
		monkeypatch, _all_members({"fre_cia_aberta_transacao_parte_relacionada_2025.csv": str_csv})
	)

	df_ = FreCiaAbertaTransacaoParteRelacionadaReader(date_ref=DATE_REF).read()

	assert "Duracao_Transacao" not in FreCiaAbertaTransacaoParteRelacionadaReader._DATE_COLS
	assert df_["Duracao_Transacao"].iloc[0] == str_br_date
	assert isinstance(df_["Duracao_Transacao"].iloc[0], str)
	assert df_["Data_Transacao"].iloc[0] == date(2025, 8, 25)


def test_remuneracao_amounts_come_back_as_exact_text(monkeypatch: pytest.MonkeyPatch) -> None:
	"""The slice's monetary columns stay source text — this is its densest concentration of money.

	Parameters
	----------
	monkeypatch : pytest.MonkeyPatch
		Fixture used to replace the download boundary.
	"""
	str_salario = "3141592653.58"
	list_cols = list(FRE_CIA_ABERTA_REMUNERACAO_TOTAL_ORGAO.tuple_required)
	list_row = [str_salario if c == "Salario" else _value_for(c) for c in list_cols]
	str_csv = _csv_text(list_cols, [list_row])
	_patch(monkeypatch, _all_members({"fre_cia_aberta_remuneracao_total_orgao_2025.csv": str_csv}))

	df_ = FreCiaAbertaRemuneracaoTotalOrgaoReader(date_ref=DATE_REF).read()

	assert df_["Salario"].iloc[0] == str_salario
	assert isinstance(df_["Salario"].iloc[0], str)


def test_the_fre_dataset_is_complete_at_thirty_six_members() -> None:
	"""All 36 members are in, each with its own contract and none sharing a column list.

	The four slices were written months apart, so the closing assertion is that nothing was lost or
	duplicated between them — 36 distinct stems, 36 distinct column lists.
	"""
	assert len(CASES) == 36
	assert len({case.str_stem for case in CASES}) == 36
	assert len({case.cls_contract.tuple_required for case in CASES}) == 36
	assert len({case.cls_contract.str_source_key for case in CASES}) == 36
