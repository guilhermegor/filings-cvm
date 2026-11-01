"""Pydantic models for the CVM Lâmina de Fundos XML standard — V1.

Direction-neutral schema for ``PadraoXMLLamina.asp``
(https://cvmweb.cvm.gov.br/SWB/Sistemas/SCW/PadroesXML/PadraoXMLLamina.asp). V1 is the original
layout (``COD_DOC`` 24, ``VERSAO`` 1.0, Instrução CVM 522). Every nested block and every field
type is the same as in V3, so they are imported from ``schemas.lamina`` rather than redeclared;
only what the page changes is declared here.

**What V1 changes against V3, measured on the page:** ``INFORM`` is keyed by ``CNPJ_FUNDO``
alone (no ``COD_SUBCLASSE``); it has ``CONC_EMISSOR`` and a mandatory ``ALAV``; it lacks
``UTILIZ_DERIV_APENAS_PROTECAO_CART``, ``PERC_MAX``, ``OBS_HOR_APL_RESG``, ``TP_PRAZO_DIAS``
(``PRAZO_PAGAM`` is always in business days), ``DS_FORMA_REMUN_DISTR``, ``PRINC_DISTR_OFERTA``,
``PRINC_CONFLITO_INTERES`` and ``INFO_ADIC``. The field order is the page's sample order.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from filings_cvm._internal.config.schemas.lamina import (
	_MAX_INFORMS,
	CnpjField,
	CompetenceField,
	DateField,
	LaminaCarencia,
	LaminaConversao,
	LaminaDespesas,
	LaminaInform,
	LaminaInformExemploComp,
	LaminaInforTabRentAnual,
	LaminaListaCompCarteira,
	LaminaListaTabRentAnual,
	LaminaListaTabRentMensal,
	LaminaTabSimulDespesas,
	LaminaTabVarDesemp,
	LaminaTaxaAdministracao,
	LaminaTaxaEntrada,
	LaminaTaxaSaida,
	MoneyField,
	PercentField,
	PhoneField,
	RatioField,
	RiskField,
	ShortField,
	Text50,
	Text100,
	Text500,
	Text1000,
	TimeField,
)


class LaminaV1Block(BaseModel):
	"""Base of the V1 blocks declared here: closed (no unknown fields) and immutable."""

	model_config = ConfigDict(extra="forbid", frozen=True)


class LaminaV1Header(LaminaV1Block):
	"""CAB_INFORM — document header (``COD_DOC`` 24, ``VERSAO`` 1.0)."""

	cod_doc: Literal[24] = 24
	versao: Literal["1.0"] = "1.0"
	dt_compt: CompetenceField
	dt_gerac_arq: DateField


class LaminaV1Inform(LaminaV1Block):
	"""INFORM — the fact sheet of one fund (V1 layout)."""

	cnpj_fundo: CnpjField
	nome_fantasia: Text500
	end_eletr: Text100
	desc_pub_alvo: Text1000
	restr_inv: Text500
	desc_objet: Text1000
	desc_pol_inv: Text1000
	ativo_ext: PercentField
	cred_priv: PercentField
	alav: RatioField
	conc_emissor: PercentField
	perdas_sign: Literal["S", "N"]
	pl_negat: Literal["S", "N"]
	inv_inicial: MoneyField
	inv_adic: MoneyField
	resg_min: MoneyField
	hor_apl_resg: TimeField
	valor_perm: MoneyField
	carencia: LaminaCarencia | None = None
	conversao: LaminaConversao
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
	tel_sac: PhoneField
	reclamacoes: Text50

	@model_validator(mode="after")
	def _check_return_tables(self) -> LaminaV1Inform:
		"""Apply V3's cross-checks on the return tables; the three tables are identical.

		Returns
		-------
		LaminaV1Inform
			The validated block.
		"""
		vars(LaminaInform)["_check_return_tables"](self)  # shared rule, one implementation
		return self


class LaminaV1Document(LaminaV1Block):
	"""DOC_ARQ — a whole V1 Lâmina file: one competence, 1 to 70 funds."""

	header: LaminaV1Header
	informs: list[LaminaV1Inform] = Field(min_length=1, max_length=_MAX_INFORMS)

	@model_validator(mode="after")
	def _check_unique_funds(self) -> LaminaV1Document:
		"""Reject the same fund twice in one file.

		Returns
		-------
		LaminaV1Document
			The validated document.

		Raises
		------
		ValueError
			If a CNPJ repeats.
		"""
		cnpjs = [i.cnpj_fundo for i in self.informs]
		if len(set(cnpjs)) != len(cnpjs):
			raise ValueError("a fund appears twice in the file")
		return self
