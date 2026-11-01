"""Pydantic models for the CVM Informe Mensal FIDC XML standard, ICVM 489 (until 2019-11-01).

The authoritative source is the CVM page
https://cvmweb.cvm.gov.br/SWB/Sistemas/SCW/PadroesXML/PadraoXMLMensalFIDC489.asp
(root ``DOC_ARQ`` in the ``urn:fidc`` namespace; one file = one fund and one month).

This is the *predecessor* of the ICVM 576 layout (``schemas/inf_mensal_fidc.py``). Every
block whose tags, order, scales and rules are identical on the two pages is imported from
that module, never copied. This module declares only what the two pages measurably differ on:

* ``CAB_INFORM`` has the six identification tags and none of the four open-fund redemption
  terms (``PR_ENTRE_*`` / ``TP_DIAS_*``).
* ``APLIC_ATIVO`` has no ``LISTA_CEDENT_CRED_EXISTE`` and no ``VL_PVS_*`` provisions, so item 2
  (carteira) has nothing to subtract; ``DICRED`` carries only ``VL_DICRED`` and
  ``VL_DICRED_CEDENT`` and is no item-3 total.
* ``OUTRAS_INFORM`` is flat and has no ``NUM_COTISTAS_DESC`` and no ``GARANTIA``: the
  per-series and per-class blocks are siblings named ``*_SENIOR_SERIE`` / ``*_SUBORD``, and
  the holders count is four plain integers.

Conventions, all taken from the page:

* A field's XML tag is its attribute name upper-cased; attribute order **is** the XML
  element order (the writer walks the fields).
* Monetary, quantity and percentage fields carry **2** decimal places; unit values and
  quantities of quotas carry up to **8**. Excess precision is truncated, never rounded.
* Repetition per series/class is not an XML attribute on the page; it follows from "separar
  por classe e série", "classe subordinada N" and item 31 ("Subordinada 1 + ... + n"). The
  senior side is mandatory ("todos os fundos possuem no mínimo cota sênior"); the
  subordinate side may be empty.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Annotated, Literal

from pydantic import BaseModel, BeforeValidator, ConfigDict, Field, model_validator

from filings_cvm._internal.config.schemas._fields import validated_cnpj
from filings_cvm._internal.config.schemas.inf_mensal_fidc import (
	Amortizacao,
	CartSegmt,
	CompmtDicred,
	CotasMovimento,
	Count,
	CredExiste,
	DesempClasse,
	InformSacados,
	Liquidez,
	ListaCedent,
	MercDerivativo,
	Money,
	NegocDicredMes,
	OutrosAtivos,
	Passiv,
	Patrliq,
	SerieClasse,
	TaxaNegocDicredMes,
	ValoresMob,
	_require_sum,
)
from filings_cvm._internal.utils.typing import type_checker
from filings_cvm._internal.utils.xml_fields import check_month_year


__all__ = [
	"AplicAtivo489",
	"Dicred489",
	"InfMensalFidc489Document",
	"InfMensalFidc489Header",
	"InfMensalFidc489Inform",
	"NumCotistas489",
	"OutrasInform489",
	"RentMes489",
]


class _Block489(BaseModel):
	"""Base for every block: unknown tags are errors, aliases may be used by name."""

	model_config = ConfigDict(populate_by_name=True, extra="forbid")


# --------------------------------------------------------------------------- CAB_INFORM


class InfMensalFidc489Header(_Block489):
	"""CAB_INFORM — fund identification (six tags, all mandatory)."""

	dt_compt: Annotated[str, BeforeValidator(check_month_year)]
	nr_cnpj_adm: Annotated[str, BeforeValidator(validated_cnpj)]
	nr_cnpj_fundo: Annotated[str, BeforeValidator(validated_cnpj)]
	tp_condominio: Literal["ABERTO", "FECHADO"]
	fdo_excl: Literal["SIM", "NAO"]
	cotst_vincul: Literal["SIM", "NAO"]


# ----------------------------------------------------------------------- APLIC_ATIVO


class Dicred489(_Block489):
	"""DICRED — rights acquired without substantial transfer of risks and benefits."""

	vl_dicred: Money
	vl_dicred_cedent: Money


class AplicAtivo489(_Block489):
	"""APLIC_ATIVO — assets (no provisions, no cedent list under CRED_EXISTE)."""

	vl_disponib: Money
	vl_carteira: Money
	cred_existe: CredExiste
	dicred: Dicred489
	lista_cedent: ListaCedent | None = None
	valores_mob: ValoresMob
	vl_titpub_fed: Money
	vl_cdb: Money
	vl_aplic_oper_compss: Money
	vl_ativ_financ_rf: Money
	vl_cota_fidc: Money
	vl_cota_fidc_nao_padrao: Money
	vl_contr_compra_venda_prestc_futura: Money
	merc_derivativo: MercDerivativo
	outros_ativos: OutrosAtivos
	vl_som_aplic_ativo: Money

	@model_validator(mode="after")
	def _check_items_1_and_2(self) -> AplicAtivo489:
		"""Check item 2 (somatório de carteira) and item 1 (somatório de ativos).

		Returns
		-------
		AplicAtivo489
			The validated block.
		"""
		_require_sum(
			"VL_CARTEIRA (item 2)",
			self.vl_carteira,
			[
				self.cred_existe.vl_som_dicred_aquis,
				self.dicred.vl_dicred,
				self.valores_mob.vl_som_valores_mob,
				self.vl_titpub_fed,
				self.vl_cdb,
				self.vl_aplic_oper_compss,
				self.vl_ativ_financ_rf,
				self.vl_cota_fidc,
				self.vl_cota_fidc_nao_padrao,
				self.vl_contr_compra_venda_prestc_futura,
			],
			[],
		)
		_require_sum(
			"VL_SOM_APLIC_ATIVO (item 1)",
			self.vl_som_aplic_ativo,
			[
				self.vl_disponib,
				self.vl_carteira,
				self.merc_derivativo.vl_som_merc_derivativo,
				self.outros_ativos.vl_som_outros_ativos,
				self.merc_derivativo.vl_depos_margem,
			],
			[],
		)
		return self


# ----------------------------------------------------------------- OUTRAS_INFORM


class NumCotistas489(_Block489):
	"""NUM_COTISTAS — four plain counts; subordinate classes repeat QT_COTISTAS_SUBORD."""

	qt_total_cotistas: Count
	qt_total_cotistas_senior: Count
	qt_total_cotistas_subord: Count
	qt_cotistas_subord: list[Count] = Field(default_factory=list)

	@model_validator(mode="after")
	def _check_items_30_and_31(self) -> NumCotistas489:
		"""Check item 30 (total) and item 31 (subordinate classes).

		Returns
		-------
		NumCotistas489
			The validated block.
		"""
		_require_sum(
			"QT_TOTAL_COTISTAS (item 30)",
			Decimal(self.qt_total_cotistas),
			[Decimal(self.qt_total_cotistas_senior), Decimal(self.qt_total_cotistas_subord)],
			[],
		)
		_require_sum(
			"QT_TOTAL_COTISTAS_SUBORD (item 31)",
			Decimal(self.qt_total_cotistas_subord),
			[Decimal(n) for n in self.qt_cotistas_subord],
			[],
		)
		return self


class RentMes489(_Block489):
	"""RENT_MES — return in the month, in percent, per senior series / subordinate class."""

	pr_apurada_senior: list[Money] = Field(min_length=1)
	pr_apurada_subord: list[Money] = Field(default_factory=list)


class OutrasInform489(_Block489):
	"""OUTRAS_INFORM — flat: series, return, flows, liquidity and performance."""

	num_cotistas: NumCotistas489
	desc_serie_classe_senior_serie: list[SerieClasse] = Field(min_length=1)
	desc_serie_classe_subord: list[SerieClasse] = Field(default_factory=list)
	rent_mes: RentMes489
	capt_mes_senior_serie: list[CotasMovimento] = Field(min_length=1)
	capt_mes_subord: list[CotasMovimento] = Field(default_factory=list)
	resg_mes_senior_serie: list[CotasMovimento] = Field(min_length=1)
	resg_mes_subord: list[CotasMovimento] = Field(default_factory=list)
	resg_solic_senior_serie: list[CotasMovimento] = Field(min_length=1)
	resg_solic_subord: list[CotasMovimento] = Field(default_factory=list)
	amort_senior_serie: list[Amortizacao] = Field(min_length=1)
	amort_subord: list[Amortizacao] = Field(default_factory=list)
	liquidez: Liquidez | None = None
	desemp_senior: list[DesempClasse] = Field(default_factory=list)
	desemp_subord: list[DesempClasse] = Field(default_factory=list)


# --------------------------------------------------------------- LISTA_INFORM / root


class InfMensalFidc489Inform(_Block489):
	"""LISTA_INFORM — the single informe of the file (one fund, one month)."""

	aplic_ativo: AplicAtivo489
	cart_segmt: CartSegmt
	passiv: Passiv
	patrliq: Patrliq
	compmt_dicred_aquis: CompmtDicred
	compmt_dicred_sem_aquis: CompmtDicred
	negoc_dicred_mes: NegocDicredMes
	inform: InformSacados
	taxa_negoc_dicred_mes: TaxaNegocDicredMes
	outras_inform: OutrasInform489

	@model_validator(mode="after")
	def _check_maturity_and_delinquency_cross_totals(self) -> InfMensalFidc489Inform:
		"""Check the page's maturity and default totals against CRED_EXISTE.

		Only the block with risk transfer has the underlying tags in this layout; the
		page states no such rule for the block without it.

		Returns
		-------
		InfMensalFidc489Inform
			The validated block.
		"""
		ce = self.aplic_ativo.cred_existe
		block = self.compmt_dicred_aquis
		_require_sum(
			"VL_SOM_PRAZO_VENC vs portfolio",
			block.vl_som_prazo_venc,
			[
				ce.vl_cred_existe_venc_adimpl,
				ce.vl_cred_existe_venc_inad,
				ce.vl_cred_refer_dicred_perfo,
			],
			[ce.vl_cred_total_venc_inad],
		)
		_require_sum(
			"VL_SOM_INAD_VENC vs portfolio",
			block.vl_som_inad_venc,
			[ce.vl_cred_total_venc_inad, ce.vl_cred_existe_inad, ce.vl_cred_venc_pend],
			[],
		)
		return self


@type_checker
def _liquidity_filled(liquidez: Liquidez | None) -> bool:
	"""Tell whether LIQUIDEZ carries at least one filled tag.

	Parameters
	----------
	liquidez : Liquidez or None
		The block, or ``None`` when it was omitted.

	Returns
	-------
	bool
		``True`` when any LIQUIDEZ tag has a value.
	"""
	return bool(liquidez and liquidez.model_dump(exclude_none=True))


@type_checker
def _liquidity_unmet(tp_condominio: str, liquidez: Liquidez | None) -> bool:
	"""Tell whether the open-fund LIQUIDEZ rule is broken.

	Parameters
	----------
	tp_condominio : str
		``ABERTO`` or ``FECHADO``.
	liquidez : Liquidez or None
		The block, or ``None`` when it was omitted.

	Returns
	-------
	bool
		``True`` for an open fund with no LIQUIDEZ tag filled.
	"""
	return tp_condominio == "ABERTO" and not _liquidity_filled(liquidez)


class InfMensalFidc489Document(_Block489):
	"""DOC_ARQ — a complete ICVM 489 Informe Mensal FIDC file (one fund and competence)."""

	cab_inform: InfMensalFidc489Header
	lista_inform: InfMensalFidc489Inform

	@model_validator(mode="after")
	def _open_fund_reports_liquidity(self) -> InfMensalFidc489Document:
		"""Require LIQUIDEZ content for open funds (optional for closed ones).

		Returns
		-------
		InfMensalFidc489Document
			The validated document.

		Raises
		------
		ValueError
			If the fund is open and no LIQUIDEZ field is filled.
		"""
		liquidez = self.lista_inform.outras_inform.liquidez
		if _liquidity_unmet(self.cab_inform.tp_condominio, liquidez):
			raise ValueError("open funds must fill at least one LIQUIDEZ field")
		return self
