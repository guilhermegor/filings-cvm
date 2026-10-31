"""Pydantic models for the CVM Lâmina de Fundos (fund fact sheet) XML standard — V3.

Direction-neutral schema for ``PadraoXMLLaminaV3.asp``
(https://cvmweb.cvm.gov.br/SWB/Sistemas/SCW/PadroesXML/PadraoXMLLaminaV3.asp). The ``submission``
section builds these models and serialises them to XML.

**Field order is the XML order.** The writer walks ``model_fields`` in declaration order and
names each element ``<FIELD_NAME.upper()>``, so every field is the lower-cased tag from the page
and sits where the page's sample file puts it. A list field repeats its element; a nested model
is a block. The three ``Lista*``/``AntesInic2`` models exist only because the page wraps a
repeated element in a container tag.

What the page leaves unsaid is decided here and stated on ``docs/submission/lamina.md``: the
page gives every decimal field no stated scale, so decimal scales follow the
repository policy (money 2 places, percentages 4, truncated toward zero) and every value is
range-bounded; text lengths are the page's "até N casas".
"""

from __future__ import annotations

from decimal import Decimal
from typing import Annotated, Literal

from pydantic import (
	AfterValidator,
	BaseModel,
	BeforeValidator,
	ConfigDict,
	Field,
	StringConstraints,
	model_validator,
)

from filings_cvm._internal.config.schemas._fields import validated_cnpj
from filings_cvm._internal.utils.xml_fields import (
	check_br_date,
	check_cnpj_shape,
	check_hhmm,
	check_long_digits,
	check_month_year,
	check_xml_text,
	parse_br_date,
	strict_decimal,
)


# Decimal scale table. The page states no scale for these; the scales are the repository
# policy, not a CVM figure. "Non-negative"/"bounded" carry the range the field's meaning implies.
_MONEY_DIGITS = 18
_PERCENT_DIGITS = 18
_MONEY_SCALE = 2
_PERCENT_SCALE = 4
_PERCENT_MAX = Decimal(100)

# Money that cannot be negative (minimums, taxes, fees, expenses).
MoneyField = Annotated[
	Decimal,
	BeforeValidator(strict_decimal(_MONEY_SCALE)),
	Field(ge=Decimal(0), max_digits=_MONEY_DIGITS, decimal_places=_MONEY_SCALE),
]
# Money that may be negative: PL_FUNDO (PL_NEGAT exists), AJUSTE_PERFOR, hypothetical returns.
SignedMoneyField = Annotated[
	Decimal,
	BeforeValidator(strict_decimal(_MONEY_SCALE)),
	Field(max_digits=_MONEY_DIGITS, decimal_places=_MONEY_SCALE),
]
# A share of the PL or of an amount: 0 to 100.
PercentField = Annotated[
	Decimal,
	BeforeValidator(strict_decimal(_PERCENT_SCALE)),
	Field(
		ge=Decimal(0), le=_PERCENT_MAX, max_digits=_PERCENT_DIGITS, decimal_places=_PERCENT_SCALE
	),
]
# A ratio with no stated ceiling (ALAV, leverage limit over the PL): 0 or more.
RatioField = Annotated[
	Decimal,
	BeforeValidator(strict_decimal(_PERCENT_SCALE)),
	Field(ge=Decimal(0), max_digits=_PERCENT_DIGITS, decimal_places=_PERCENT_SCALE),
]
# A return or index variation: may be negative and exceed 100.
SignedPercentField = Annotated[
	Decimal,
	BeforeValidator(strict_decimal(_PERCENT_SCALE)),
	Field(max_digits=_PERCENT_DIGITS, decimal_places=_PERCENT_SCALE),
]

# The page's "short": a signed 16-bit integer. Every use below is a count, so non-negative.
_SHORT_MAX = 32767
ShortField = Annotated[int, Field(strict=True, ge=0, le=_SHORT_MAX)]
YearField = Annotated[int, Field(strict=True, ge=1900, le=9999)]
MonthField = Annotated[int, Field(strict=True, ge=1, le=12)]
RiskField = Annotated[int, Field(strict=True, ge=1, le=5)]

# Date shapes.
CompetenceField = Annotated[str, AfterValidator(check_month_year)]
DateField = Annotated[str, AfterValidator(check_br_date)]
TimeField = Annotated[str, AfterValidator(check_hhmm)]
PhoneField = Annotated[str, AfterValidator(check_long_digits)]

# Identifier of a subclass: the page gives no format; the bound is this library's assumption.
_SUBCLASS_CODE_MAX = 50
SubclassCodeField = Annotated[
	str,
	StringConstraints(min_length=1, max_length=_SUBCLASS_CODE_MAX, strip_whitespace=False),
	AfterValidator(check_xml_text),
]

CnpjField = Annotated[str, AfterValidator(check_cnpj_shape), AfterValidator(validated_cnpj)]

# Limits the page states.
_MAX_INFORMS = 70
_MAX_PORTFOLIO_ASSETS = 5
_MAX_ANNUAL_ROWS = 5
_MAX_MONTHLY_ROWS = 12


# "string com até N casas": non-blank, XML-safe, windows-1252-encodable, at most N characters.
_XML_TEXT = AfterValidator(check_xml_text)
Text20 = Annotated[str, StringConstraints(min_length=1, max_length=20), _XML_TEXT]
Text50 = Annotated[str, StringConstraints(min_length=1, max_length=50), _XML_TEXT]
Text100 = Annotated[str, StringConstraints(min_length=1, max_length=100), _XML_TEXT]
Text300 = Annotated[str, StringConstraints(min_length=1, max_length=300), _XML_TEXT]
Text500 = Annotated[str, StringConstraints(min_length=1, max_length=500), _XML_TEXT]
Text600 = Annotated[str, StringConstraints(min_length=1, max_length=600), _XML_TEXT]
Text900 = Annotated[str, StringConstraints(min_length=1, max_length=900), _XML_TEXT]
Text1000 = Annotated[str, StringConstraints(min_length=1, max_length=1000), _XML_TEXT]


class LaminaBlock(BaseModel):
	"""Base of every Lâmina block: closed (no unknown fields) and immutable."""

	model_config = ConfigDict(extra="forbid", frozen=True)


class LaminaHeader(LaminaBlock):
	"""CAB_INFORM — document header."""

	cod_doc: Literal[24] = 24
	versao: Literal["3.0"] = "3.0"
	dt_compt: CompetenceField
	dt_gerac_arq: DateField


class LaminaCarencia(LaminaBlock):
	"""CARENCIA — grace period (optional block)."""

	dias_car: ShortField
	cond_car: Text500


class LaminaConversao(LaminaBlock):
	"""CONVERSAO — quota-conversion rules."""

	abert_fech: Literal["A", "F"]
	dia_aplic: ShortField
	abert_fech_c: Literal["A", "F"]
	dia_resg: ShortField


class LaminaTaxaAdministracao(LaminaBlock):
	"""INFOR_TX_ADM — management fee: fixed (``F``) or variable (``V``)."""

	tipo_tx_adm: Literal["F", "V"]
	tx_adm: PercentField | None = None
	tx_min: PercentField | None = None
	tx_max: PercentField | None = None
	esclarec: Text500 | None = None

	@model_validator(mode="after")
	def _check_fee_shape(self) -> LaminaTaxaAdministracao:
		"""Require TX_ADM for a fixed fee, and TX_MIN with TX_MAX for a variable one.

		Returns
		-------
		LaminaTaxaAdministracao
			The validated block.

		Raises
		------
		ValueError
			If the fee fields do not match ``tipo_tx_adm`` or the minimum exceeds the maximum.
		"""
		if self.tipo_tx_adm == "F":
			if self.tx_adm is None or self.tx_min is not None or self.tx_max is not None:
				raise ValueError("a fixed fee (F) takes tx_adm only")
			return self
		if self.tx_adm is not None or self.tx_min is None or self.tx_max is None:
			raise ValueError("a variable fee (V) takes tx_min and tx_max, not tx_adm")
		if self.tx_min > self.tx_max:
			raise ValueError("tx_min must not exceed tx_max")
		return self


class LaminaTaxaEntrada(LaminaBlock):
	"""INFOR_TX_ENTR — entry fee (optional block)."""

	tx_entr: PercentField
	cond_entr: Text500


class LaminaTaxaSaida(LaminaBlock):
	"""INFOR_TX_SAIDA — exit fee (optional block)."""

	dias_saida: ShortField
	tx_saida: PercentField
	cond_saida: Text500


class LaminaDespesas(LaminaBlock):
	"""INFOR_DESPESAS — expenses over a period (optional for funds under one year)."""

	despesas: PercentField
	inic_periodo: DateField
	fim_periodo: DateField
	end_elet_adm: Text100

	@model_validator(mode="after")
	def _check_period(self) -> LaminaDespesas:
		"""Require the period to start no later than it ends.

		Returns
		-------
		LaminaDespesas
			The validated block.

		Raises
		------
		ValueError
			If ``inic_periodo`` is after ``fim_periodo``.
		"""
		if parse_br_date(self.inic_periodo) > parse_br_date(self.fim_periodo):
			raise ValueError("inic_periodo must not be after fim_periodo")
		return self


class LaminaCompCarteira(LaminaBlock):
	"""COMP_CARTEIRA — one asset type of the portfolio."""

	especie_ativo: Text500
	perc_pl: PercentField


class LaminaListaCompCarteira(LaminaBlock):
	"""LISTA_COMP_CARTEIRA — portfolio composition: PL plus 1 to 5 asset types."""

	pl_fundo: SignedMoneyField
	comp_carteira: list[LaminaCompCarteira] = Field(min_length=1, max_length=_MAX_PORTFOLIO_ASSETS)


class LaminaAntesInic2(LaminaBlock):
	"""ANTES_INIC2 — years with no past-return data because the fund did not yet exist."""

	ano: list[YearField] = Field(min_length=1, max_length=_MAX_ANNUAL_ROWS)

	@model_validator(mode="after")
	def _check_unique(self) -> LaminaAntesInic2:
		"""Reject a repeated year.

		Returns
		-------
		LaminaAntesInic2
			The validated block.

		Raises
		------
		ValueError
			If a year appears twice.
		"""
		if len(set(self.ano)) != len(self.ano):
			raise ValueError("ano must not repeat a year")
		return self


class LaminaInforTabRentAnual(LaminaBlock):
	"""INFOR_TAB_RENT_ANUAL — 5-year accumulated return and reference index."""

	rent_5anos: SignedPercentField | None = None
	ind_refer: Text20 | None = None
	rent_ind_ref: SignedPercentField | None = None
	anos_abaixo: Annotated[int, Field(strict=True, ge=0, le=_MAX_ANNUAL_ROWS)] | None = None
	inic_funcio: DateField | None = None
	antes_inic2: LaminaAntesInic2 | None = None

	@model_validator(mode="after")
	def _check_index(self) -> LaminaInforTabRentAnual:
		"""Allow the index variation only when there is a reference index.

		Returns
		-------
		LaminaInforTabRentAnual
			The validated block.

		Raises
		------
		ValueError
			If ``rent_ind_ref`` is given without ``ind_refer``.
		"""
		if self.rent_ind_ref is not None and self.ind_refer is None:
			raise ValueError("rent_ind_ref requires ind_refer")
		return self


class LaminaTabRentAnual(LaminaBlock):
	"""TAB_RENT_ANUAL — one year of return."""

	ano_rent: YearField
	rent_liq: SignedPercentField
	var_ind_ref: SignedPercentField | None = None
	rent_perc_ind_ref: SignedPercentField | None = None
	comentarios: Text500 | None = None


class LaminaListaTabRentAnual(LaminaBlock):
	"""LISTA_TAB_RENT_ANUAL — up to the last 5 years of return."""

	tab_rent_anual: list[LaminaTabRentAnual] = Field(min_length=1, max_length=_MAX_ANNUAL_ROWS)


class LaminaTabRentMensal(LaminaBlock):
	"""TAB_RENT_MENSAL — one month of return (XML tag ``MES``, as in the page's sample)."""

	mes: MonthField
	rent_mens: SignedPercentField
	var_mens_ind_ref: SignedPercentField | None = None
	rent_mens_perc_ind_ref: SignedPercentField | None = None
	comentarios: Text500 | None = None


class LaminaListaTabRentMensal(LaminaBlock):
	"""LISTA_TAB_RENT_MENSAL — up to the last 12 months of return."""

	tab_rent_mensal: list[LaminaTabRentMensal] = Field(min_length=1, max_length=_MAX_MONTHLY_ROWS)


class LaminaTabVarDesemp(LaminaBlock):
	"""TAB_VAR_DESEMP — performance variation and its formula."""

	var_desemp: SignedPercentField
	formula_rentab: Text500
	cenario_gatilho: Text500 | None = None
	esclarec: Text500 | None = None


class LaminaInformExemploComp(LaminaBlock):
	"""INFORM_EXEMPLO_COMP — worked cost example for the issue year."""

	ano_ant: YearField
	ano_emiss: YearField
	valor_resg: MoneyField
	impostos: MoneyField
	valor_ing: MoneyField | None = None
	valor_saida: MoneyField | None = None
	ajuste_perfor: SignedMoneyField | None = None
	valor_despesas: MoneyField

	@model_validator(mode="after")
	def _check_years(self) -> LaminaInformExemploComp:
		"""Require ANO_ANT to be the year immediately before ANO_EMISS.

		Returns
		-------
		LaminaInformExemploComp
			The validated block.

		Raises
		------
		ValueError
			If ``ano_ant`` is not ``ano_emiss - 1``.
		"""
		if self.ano_ant != self.ano_emiss - 1:
			raise ValueError("ano_ant must be the year immediately before ano_emiss")
		return self


class LaminaTabSimulDespesas(LaminaBlock):
	"""TAB_SIMUL_DESPESAS — 3- and 5-year expense simulation."""

	desp_prev3: MoneyField
	desp_prev5: MoneyField
	retor_brut3: SignedMoneyField
	retor_brut5: SignedMoneyField


class LaminaInform(LaminaBlock):
	"""INFORM — the fact sheet of one fund class or subclass."""

	cnpj_fundo: CnpjField | None = None
	cod_subclasse: SubclassCodeField | None = None
	nome_fantasia: Text500
	end_eletr: Text100
	desc_pub_alvo: Text1000
	restr_inv: Text500
	desc_objet: Text1000
	desc_pol_inv: Text1000
	ativo_ext: PercentField
	cred_priv: PercentField
	alav: RatioField | None = None
	utiliz_deriv_apenas_protecao_cart: Literal["S", "N"]
	perdas_sign: Literal["S", "N"]
	pl_negat: Literal["S", "N"]
	perc_max: PercentField
	inv_inicial: MoneyField
	inv_adic: MoneyField
	resg_min: MoneyField
	hor_apl_resg: TimeField
	obs_hor_apl_resg: Text500
	valor_perm: MoneyField
	carencia: LaminaCarencia | None = None
	conversao: LaminaConversao
	tp_prazo_dias: Literal["1", "2"]
	prazo_pagam: ShortField
	infor_tx_adm: LaminaTaxaAdministracao
	infor_tx_entr: LaminaTaxaEntrada | None = None
	infor_tx_saida: LaminaTaxaSaida | None = None
	tx_desempenho: Text500
	infor_despesas: LaminaDespesas | None = None
	lista_comp_carteira: LaminaListaCompCarteira | None = None
	classif_risco: RiskField
	infor_tab_rent_anual: LaminaInforTabRentAnual | None = None
	lista_tab_rent_anual: LaminaListaTabRentAnual | None = None
	lista_tab_rent_mensal: LaminaListaTabRentMensal | None = None
	form_calc_rent: Text500 | None = None
	tab_var_desemp: LaminaTabVarDesemp | None = None
	inform_exemplo_comp: LaminaInformExemploComp | None = None
	tab_simul_despesas: LaminaTabSimulDespesas | None = None
	ds_forma_remun_distr: Text900
	princ_distr_oferta: Text300
	princ_conflito_interes: Text600
	tel_sac: PhoneField
	reclamacoes: Text50
	info_adic: Text500

	@model_validator(mode="after")
	def _check_identifier(self) -> LaminaInform:
		"""Require exactly one of CNPJ_FUNDO and COD_SUBCLASSE.

		Returns
		-------
		LaminaInform
			The validated block.

		Raises
		------
		ValueError
			If both identifiers or neither is set.
		"""
		if (self.cnpj_fundo is None) == (self.cod_subclasse is None):
			raise ValueError("provide exactly one of cnpj_fundo or cod_subclasse")
		return self

	@model_validator(mode="after")
	def _check_return_tables(self) -> LaminaInform:
		"""Check the rows of the annual and monthly return tables against each other.

		Years and months must not repeat, a year cannot be both reported and listed as
		"before the fund existed", and the index columns need a reference index.

		Returns
		-------
		LaminaInform
			The validated block.

		Raises
		------
		ValueError
			If a year or month repeats, the year sets overlap, or an index column is filled
			while ``ind_refer`` is absent.
		"""
		annual = self.lista_tab_rent_anual.tab_rent_anual if self.lista_tab_rent_anual else []
		monthly = self.lista_tab_rent_mensal.tab_rent_mensal if self.lista_tab_rent_mensal else []
		years = [row.ano_rent for row in annual]
		if len(set(years)) != len(years):
			raise ValueError("ano_rent must not repeat a year")
		months = [row.mes for row in monthly]
		if len(set(months)) != len(months):
			raise ValueError("mes must not repeat a month")
		info = self.infor_tab_rent_anual
		before_existence = set(info.antes_inic2.ano) if info and info.antes_inic2 else set()
		if before_existence & set(years):
			raise ValueError("a year cannot be both in antes_inic2 and in tab_rent_anual")
		index_cells = [
			*(c for r in annual for c in (r.var_ind_ref, r.rent_perc_ind_ref)),
			*(c for r in monthly for c in (r.var_mens_ind_ref, r.rent_mens_perc_ind_ref)),
		]
		has_index = info is not None and info.ind_refer is not None
		if not has_index and any(cell is not None for cell in index_cells):
			raise ValueError("index columns need infor_tab_rent_anual.ind_refer")
		return self


class LaminaDocument(LaminaBlock):
	"""DOC_ARQ — a whole Lâmina file: one competence, 1 to 70 funds."""

	header: LaminaHeader
	informs: list[LaminaInform] = Field(min_length=1, max_length=_MAX_INFORMS)

	@model_validator(mode="after")
	def _check_unique_funds(self) -> LaminaDocument:
		"""Reject the same fund class or subclass twice in one file.

		Returns
		-------
		LaminaDocument
			The validated document.

		Raises
		------
		ValueError
			If a CNPJ or a subclass code repeats.
		"""
		cnpjs = [i.cnpj_fundo for i in self.informs if i.cnpj_fundo is not None]
		codes = [i.cod_subclasse for i in self.informs if i.cod_subclasse is not None]
		if len(set(cnpjs)) != len(cnpjs) or len(set(codes)) != len(codes):
			raise ValueError("a fund class or subclass appears twice in the file")
		return self
