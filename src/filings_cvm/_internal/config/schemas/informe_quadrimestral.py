"""Pydantic models for the CVM Informe Quadrimestral (FIP) XML standard — V2.

Direction-neutral schema for ``PadraoXMLInfoTrimV2.asp``
(https://cvmweb.cvm.gov.br/SWB/Sistemas/SCW/PadroesXML/PadraoXMLInfoTrimV2.asp), the former
Informe Trimestral. The ``submission`` section builds these models and serialises them to XML.

**Field order is the XML order.** The writer walks ``model_fields`` in declaration order and
names each element ``<FIELD_NAME.upper()>``, so every field is the lower-cased tag from the page
and sits where the page's sample file puts it. A list field repeats its element; a nested model
is a block. ``ListaCotstCateg`` and ``ListaClasseCotas`` exist because the page wraps the
repeated element in a container tag.

The page states the decimal shape for every number: up to 12 integer digits and up to 8 decimal
digits. Excess decimal places are truncated toward zero, never rounded. What the page leaves
unsaid is decided here and stated on ``docs/submission/informe_quadrimestral.md``.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Annotated, Literal

from pydantic import AfterValidator, BaseModel, BeforeValidator, ConfigDict, Field, model_validator

from filings_cvm._internal.config.schemas._fields import validated_cnpj
from filings_cvm._internal.utils.xml_fields import (
	check_br_date,
	check_cnpj_shape,
	check_month_year,
	strict_decimal,
)


# "decimal com até 12 algarismos na parte inteira e até 8 na parte decimal".
_DECIMAL_SCALE = 8
_DECIMAL_DIGITS = 20
_PERCENT_MAX = Decimal(100)
_INT_MAX = 999_999_999_999
_MAX_INFORMS = 100
_MAX_CATEGORIES = 15  # Tabela I has 15 codes; each may appear once per fund
# The competence is the last month of a civil quadrimester.
_QUADRIMESTER_END_MONTHS = frozenset({"04", "08", "12"})

# Quantities and capital: cannot be negative.
AmountField = Annotated[
	Decimal,
	BeforeValidator(strict_decimal(_DECIMAL_SCALE)),
	Field(ge=Decimal(0), max_digits=_DECIMAL_DIGITS, decimal_places=_DECIMAL_SCALE),
]
# Net asset value and quota value: a fund under water has a negative one.
SignedAmountField = Annotated[
	Decimal,
	BeforeValidator(strict_decimal(_DECIMAL_SCALE)),
	Field(max_digits=_DECIMAL_DIGITS, decimal_places=_DECIMAL_SCALE),
]
# A share of the subscribed quotas: 0 to 100.
PercentField = Annotated[
	Decimal,
	BeforeValidator(strict_decimal(_DECIMAL_SCALE)),
	Field(
		ge=Decimal(0),
		le=_PERCENT_MAX,
		max_digits=_DECIMAL_DIGITS,
		decimal_places=_DECIMAL_SCALE,
	),
]
# "número inteiro" counts.
CountField = Annotated[int, Field(strict=True, ge=0, le=_INT_MAX)]
ClassNumberField = Annotated[int, Field(strict=True, ge=1, le=_INT_MAX)]

CompetenceField = Annotated[str, AfterValidator(check_month_year)]
DateField = Annotated[str, AfterValidator(check_br_date)]
CnpjField = Annotated[str, AfterValidator(check_cnpj_shape), AfterValidator(validated_cnpj)]

# Tabela I — categoria de cotistas, written exactly as the table prints the codes.
CategoryCode = Literal[
	"001",
	"002",
	"003",
	"004",
	"005",
	"006",
	"007",
	"008",
	"009",
	"010",
	"011",
	"012",
	"013",
	"014",
	"015",
]
YesNo = Literal["S", "N"]


class InformeQuadrimestralBlock(BaseModel):
	"""Base of every Informe Quadrimestral block: closed (no unknown fields) and immutable."""

	model_config = ConfigDict(extra="forbid", frozen=True)


class InformeQuadrimestralHeader(InformeQuadrimestralBlock):
	"""CAB_INFORM — document header."""

	cod_doc: Literal[51] = 51
	dt_compt: CompetenceField
	dt_gerac_arq: DateField
	versao: Literal["2.0"] = "2.0"

	@model_validator(mode="after")
	def _check_quadrimester(self) -> InformeQuadrimestralHeader:
		"""Require the competence month to close a civil quadrimester (04, 08 or 12).

		Returns
		-------
		InformeQuadrimestralHeader
			The validated header.

		Raises
		------
		ValueError
			If the month is not April, August or December.
		"""
		if self.dt_compt[:2] not in _QUADRIMESTER_END_MONTHS:
			raise ValueError("dt_compt month must close a quadrimester: 04, 08 or 12")
		return self


class CotistCategory(InformeQuadrimestralBlock):
	"""COTST_CATEG — subscribers of one category (Tabela I)."""

	cod_categ: CategoryCode
	qtd_cotst_subscr: CountField
	pr_cotas_subscr: PercentField


class ListaCotstCateg(InformeQuadrimestralBlock):
	"""LISTA_COTST_CATEG — subscribers by category, then the totals."""

	cotst_categ: list[CotistCategory] = Field(min_length=1, max_length=_MAX_CATEGORIES)
	tot_cotst_subscr: CountField
	tx_num_tot_cot: PercentField

	@model_validator(mode="after")
	def _check_unique_categories(self) -> ListaCotstCateg:
		"""Reject the same category twice for one fund.

		Returns
		-------
		ListaCotstCateg
			The validated block.

		Raises
		------
		ValueError
			If a category code repeats.
		"""
		codes = [c.cod_categ for c in self.cotst_categ]
		if len(set(codes)) != len(codes):
			raise ValueError("a cotist category appears twice for the same fund")
		return self


class ClasseCotas(InformeQuadrimestralBlock):
	"""CLASSE_COTAS — one quota class."""

	num_classe: ClassNumberField
	num_cotst_subs: CountField
	qtd_atual_cotas_subs: AmountField
	qtd_atual_cotas_integ: AmountField
	vl_atual_cota: SignedAmountField
	direito_polit_especial: YesNo
	direito_dist_econ_finan: YesNo


class ListaClasseCotas(InformeQuadrimestralBlock):
	"""LISTA_CLASSE_COTAS — the quota classes of a fund."""

	classe_cotas: list[ClasseCotas] = Field(min_length=1)

	@model_validator(mode="after")
	def _check_unique_classes(self) -> ListaClasseCotas:
		"""Reject the same class number twice for one fund.

		Returns
		-------
		ListaClasseCotas
			The validated block.

		Raises
		------
		ValueError
			If a class number repeats.
		"""
		numbers = [c.num_classe for c in self.classe_cotas]
		if len(set(numbers)) != len(numbers):
			raise ValueError("a quota class number appears twice for the same fund")
		return self


class InformeQuadrimestralInform(InformeQuadrimestralBlock):
	"""INFORM — the quadrimester report of one fund."""

	nr_pf_pj_fdo: CnpjField
	entid_invest: YesNo
	publico_alvo: Literal[2, 3]
	vl_pl_fdo: SignedAmountField
	vl_capital_comprom: AmountField
	qtd_cotas_subscr: AmountField
	vl_tot_capital_subscr: AmountField
	qtd_cotas_integr: AmountField
	vl_tot_capital_integr: AmountField
	vl_tot_cotas_outros_fip: AmountField
	lista_cotst_categ: ListaCotstCateg
	lista_classe_cotas: ListaClasseCotas


class InformeQuadrimestralDocument(InformeQuadrimestralBlock):
	"""DOC_ARQ — a whole file: one competence, 1 to 100 funds."""

	header: InformeQuadrimestralHeader
	informs: list[InformeQuadrimestralInform] = Field(min_length=1, max_length=_MAX_INFORMS)

	@model_validator(mode="after")
	def _check_unique_funds(self) -> InformeQuadrimestralDocument:
		"""Reject the same fund twice in one file.

		Returns
		-------
		InformeQuadrimestralDocument
			The validated document.

		Raises
		------
		ValueError
			If a CNPJ repeats.
		"""
		cnpjs = [i.nr_pf_pj_fdo for i in self.informs]
		if len(set(cnpjs)) != len(cnpjs):
			raise ValueError("a fund appears twice in the file")
		return self
