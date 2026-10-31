"""Pydantic models for the CVM Informe Mensal FIDC XML standard (ICVM 576, from 2019-11-01).

This is the *shared schema* — the direction-neutral contract for one CVM XML standard.
The ``submission`` section builds these models and serialises them to XML; it ships
inside the wheel under ``_internal`` but is **not** part of the public API on its own.

The authoritative source is the CVM page
https://cvmweb.cvm.gov.br/SWB/Sistemas/SCW/PadroesXML/PadraoXMLMensalFIDC576.asp
(root ``DOC_ARQ`` in the ``urn:fidc`` namespace; one file = one fund and one month).

Conventions, all taken from that page:

* A field's XML tag is its attribute name upper-cased; where the same tag name
  means different things in different blocks the tag is given as an ``alias``.
  Attribute order **is** the XML element order (the writer walks the fields).
* Monetary, quantity and percentage fields carry **2** decimal places; unit values
  and quantities of quotas (``QT_COTAS``/``VL_COTAS`` of the series/class blocks,
  ``VL_COTA`` of the amortisations) carry up to **8**. Excess precision is truncated
  toward zero (``ROUND_DOWN``), never rounded.
* Every value tag is mandatory ("preencher com zero se não houver valores"); only the
  blocks the page calls optional (cedent lists, quota-holder breakdown, expected
  performance, the open-fund redemption terms) may be omitted.
* The ``SOMATÓRIO`` tags (items 1-30 of the page) must equal the sum of the tags the
  page lists for them; the models reject a document whose totals disagree.
"""

from __future__ import annotations

from decimal import Decimal
import re
from typing import Annotated, Literal

from pydantic import (
	BaseModel,
	BeforeValidator,
	ConfigDict,
	Field,
	field_validator,
	model_validator,
)

from filings_cvm._internal.config.schemas._fields import truncate_to_scale, validated_cnpj
from filings_cvm._internal.utils.br_identifiers import is_valid_cnpj, is_valid_cpf
from filings_cvm._internal.utils.typing import type_checker


# DT_COMPT: "MM/AAAA".
_COMPETENCE_RE = re.compile(r"^(0[1-9]|1[0-2])/\d{4}$")

# Placeholders the page prescribes for a debtor/cedent with no CNPJ / an exempt CPF.
_NO_CNPJ_PLACEHOLDER = "99.999.999/9999-99"
_NO_CPF_PLACEHOLDER = "999.999.999-99"

# Monetary / quantity / percentage: "duas casas decimais".
Money = Annotated[Decimal, BeforeValidator(truncate_to_scale(2)), Field(decimal_places=2)]
# Unit values and quota quantities: "até 8 casas decimais".
Quota8 = Annotated[Decimal, BeforeValidator(truncate_to_scale(8)), Field(decimal_places=8)]
# Head-counts: "inteiro com até 14 dígitos".
Count = Annotated[int, Field(ge=0, lt=10**14)]

# Maturity / delinquency / prepayment buckets shared by the two COMPMT blocks.
_BUCKETS = (
	"30",
	"31_60",
	"61_90",
	"91_120",
	"121_150",
	"151_180",
	"181_360",
	"361_720",
	"721_1080",
	"1080",
)


@type_checker
def _require_sum(label: str, total: Decimal, plus: list[Decimal], minus: list[Decimal]) -> None:
	"""Check a SOMATÓRIO tag equals the sum the CVM page prescribes for it.

	Parameters
	----------
	label : str
		The tag (and page item) being checked, for the error message.
	total : Decimal
		The value reported in the SOMATÓRIO tag.
	plus : list[Decimal]
		The tags that are added.
	minus : list[Decimal]
		The tags that are subtracted.

	Raises
	------
	ValueError
		If ``total`` differs from ``sum(plus) - sum(minus)``.
	"""
	expected = sum(plus, Decimal(0)) - sum(minus, Decimal(0))
	if total != expected:
		raise ValueError(f"{label}: SOMATÓRIO must be {expected}, got {total}")


@type_checker
def _cpf_or_cnpj(value: str) -> str:
	"""Validate a CPF/CNPJ field, accepting the page's no-document placeholders.

	Parameters
	----------
	value : str
		A CPF or CNPJ in any shape, or one of the two prescribed placeholders.

	Returns
	-------
	str
		The value, unchanged (the page shows masked placeholders, so no
		normalisation is imposed).

	Raises
	------
	ValueError
		If the value is neither a valid CPF, a valid CNPJ nor a placeholder.
	"""
	if value in {_NO_CNPJ_PLACEHOLDER, _NO_CPF_PLACEHOLDER}:
		return value
	if is_valid_cnpj(value) or is_valid_cpf(value):
		return value
	raise ValueError(f"invalid CPF/CNPJ: {value!r}")


CpfCnpj = Annotated[str, BeforeValidator(_cpf_or_cnpj)]


class _FidcBlock(BaseModel):
	"""Base for every block: unknown tags are errors, aliases may be used by name."""

	model_config = ConfigDict(populate_by_name=True, extra="forbid")


# --------------------------------------------------------------------------- CAB_INFORM


class InfMensalFidcHeader(_FidcBlock):
	"""CAB_INFORM — fund identification and, for open funds, the redemption terms."""

	dt_compt: str
	nr_cnpj_adm: Annotated[str, BeforeValidator(validated_cnpj)]
	nr_cnpj_fundo: Annotated[str, BeforeValidator(validated_cnpj)]
	tp_condominio: Literal["ABERTO", "FECHADO"]
	fdo_excl: Literal["SIM", "NAO"]
	cotst_vincul: Literal["SIM", "NAO"]
	pr_entre_resgate: int | None = Field(default=None, ge=0, le=9999)
	tp_dias_resgate: Literal["1", "2"] | None = None
	pr_entre_conver: int | None = Field(default=None, ge=0, le=9999)
	tp_dias_conver: Literal["1", "2"] | None = None

	@field_validator("dt_compt")
	@classmethod
	def _check_competence(cls, v: str) -> str:
		"""Validate DT_COMPT follows ``MM/AAAA``.

		Parameters
		----------
		v : str
			Value to validate.

		Returns
		-------
		str
			The validated value.

		Raises
		------
		ValueError
			If the value is not ``MM/AAAA``.
		"""
		if not _COMPETENCE_RE.match(v):
			raise ValueError(f"expected MM/AAAA, got {v!r}")
		return v

	@model_validator(mode="after")
	def _closed_fund_has_no_redemption_terms(self) -> InfMensalFidcHeader:
		"""Reject the four open-fund-only tags on a closed fund.

		Returns
		-------
		InfMensalFidcHeader
			The validated header.

		Raises
		------
		ValueError
			If ``tp_condominio`` is ``FECHADO`` and any redemption tag is present.
		"""
		terms = (
			self.pr_entre_resgate,
			self.tp_dias_resgate,
			self.pr_entre_conver,
			self.tp_dias_conver,
		)
		if self.tp_condominio == "FECHADO" and any(t is not None for t in terms):
			raise ValueError("PR_ENTRE_*/TP_DIAS_* are restricted to open funds (ABERTO)")
		return self


# ----------------------------------------------------------------------- APLIC_ATIVO


class CedentCredExiste(_FidcBlock):
	"""CEDENT_CRED_EXISTE — one cedent above 10% of the fund's net equity."""

	nr_pf_pj_cedent_cred_existe: CpfCnpj
	pr_cedent_cred_existe: Money


class ListaCedentCredExiste(_FidcBlock):
	"""LISTA_CEDENT_CRED_EXISTE — cedents of the rights acquired with risk transfer."""

	cedent_cred_existe: list[CedentCredExiste] = Field(min_length=1)


class Cedent(_FidcBlock):
	"""CEDENT — one cedent above 10% of the fund's net equity."""

	nr_pf_pj_cedent: CpfCnpj
	pr_cedent: Money


class ListaCedent(_FidcBlock):
	"""LISTA_CEDENT — cedents of the rights acquired without risk transfer."""

	cedent: list[Cedent] = Field(min_length=1)


class CredExiste(_FidcBlock):
	"""CRED_EXISTE — rights acquired with substantial transfer of risks and benefits."""

	vl_som_dicred_aquis: Money
	vl_cred_existe_venc_adimpl: Money
	vl_cred_existe_venc_inad: Money
	vl_cred_total_venc_inad: Money
	vl_cred_existe_inad: Money
	vl_cred_refer_dicred_perfo: Money
	vl_cred_venc_pend: Money
	vl_cred_origem_emp_proc_recup: Money
	vl_decor_receit_public: Money
	vl_cred_acao_judic: Money
	vl_cred_const_jur_fatrisc: Money
	vl_outros_cred: Money
	vl_provis_reduc_recup: Money

	@model_validator(mode="after")
	def _check_item_3_and_provision(self) -> CredExiste:
		"""Check item 3 (somatório) and the provision ceiling.

		Returns
		-------
		CredExiste
			The validated block.

		Raises
		------
		ValueError
			If the total is wrong or the provision exceeds the exposures it covers.
		"""
		exposures = [
			self.vl_cred_existe_venc_adimpl,
			self.vl_cred_existe_venc_inad,
			self.vl_cred_existe_inad,
			self.vl_cred_refer_dicred_perfo,
			self.vl_cred_venc_pend,
		]
		if not Decimal(0) <= self.vl_provis_reduc_recup <= sum(exposures, Decimal(0)):
			raise ValueError("VL_PROVIS_REDUC_RECUP must be positive and <= the covered credits")
		_require_sum(
			"VL_SOM_DICRED_AQUIS (item 3)",
			self.vl_som_dicred_aquis,
			exposures,
			[self.vl_provis_reduc_recup],
		)
		return self


class Dicred(_FidcBlock):
	"""DICRED — rights acquired without substantial transfer of risks and benefits."""

	vl_dicred: Money
	vl_dicred_cedent: Money
	vl_dicred_existe_venc_inad: Money
	vl_dicred_total_venc_inad: Money
	vl_dicred_existe_inad: Money
	vl_dicred_refer_dicred_perfo: Money
	vl_dicred_venc_pend: Money
	vl_dicred_origem_emp_proc_recup: Money
	vl_dicred_receit_public: Money
	vl_dicred_acao_judic: Money
	vl_dicred_const_jur_fatrisc: Money
	vl_dicred_outros_cred: Money
	vl_dicred_provis_reduc_recup: Money

	@model_validator(mode="after")
	def _check_item_3_and_provision(self) -> Dicred:
		"""Check item 3 (somatório) and the provision ceiling.

		Returns
		-------
		Dicred
			The validated block.

		Raises
		------
		ValueError
			If the total is wrong or the provision exceeds the exposures it covers.
		"""
		exposures = [
			self.vl_dicred_cedent,
			self.vl_dicred_existe_venc_inad,
			self.vl_dicred_existe_inad,
			self.vl_dicred_refer_dicred_perfo,
			self.vl_dicred_venc_pend,
		]
		if not Decimal(0) <= self.vl_dicred_provis_reduc_recup <= sum(exposures, Decimal(0)):
			raise ValueError(
				"VL_DICRED_PROVIS_REDUC_RECUP must be positive and <= covered credits"
			)
		_require_sum(
			"VL_DICRED (item 3)",
			self.vl_dicred,
			exposures,
			[self.vl_dicred_provis_reduc_recup],
		)
		return self


class ValoresMob(_FidcBlock):
	"""VALORES_MOB — securities."""

	vl_som_valores_mob: Money
	vl_debt: Money
	vl_cri: Money
	vl_np_comerc: Money
	vl_letra_financ: Money
	vl_cota_fdo_icvm409: Money
	vl_outro_dicred: Money

	@model_validator(mode="after")
	def _check_item_4(self) -> ValoresMob:
		"""Check item 4 (somatório de valores mobiliários).

		Returns
		-------
		ValoresMob
			The validated block.
		"""
		_require_sum(
			"VL_SOM_VALORES_MOB (item 4)",
			self.vl_som_valores_mob,
			[
				self.vl_debt,
				self.vl_cri,
				self.vl_np_comerc,
				self.vl_letra_financ,
				self.vl_cota_fdo_icvm409,
				self.vl_outro_dicred,
			],
			[],
		)
		return self


class MercDerivativo(_FidcBlock):
	"""MERC_DERIVATIVO — positions held in derivatives markets."""

	vl_som_merc_derivativo: Money
	vl_merc_termo_pos_comprd: Money
	vl_merc_op_pos_titul: Money
	vl_merc_fut_ajust_posit: Money
	vl_difer_swap_receb: Money
	vl_cobert_prest: Money
	vl_depos_margem: Money

	@model_validator(mode="after")
	def _check_item_5(self) -> MercDerivativo:
		"""Check item 5 (cover and margin deposits are not part of the sum).

		Returns
		-------
		MercDerivativo
			The validated block.
		"""
		_require_sum(
			"VL_SOM_MERC_DERIVATIVO (item 5)",
			self.vl_som_merc_derivativo,
			[
				self.vl_merc_termo_pos_comprd,
				self.vl_merc_op_pos_titul,
				self.vl_merc_fut_ajust_posit,
				self.vl_difer_swap_receb,
			],
			[],
		)
		return self


class OutrosAtivos(_FidcBlock):
	"""OUTROS_ATIVOS — other assets, by realisation horizon."""

	vl_som_outros_ativos: Money
	vl_outro_vl_receb_curprz: Money
	vl_outro_vl_receb_lprazo: Money

	@model_validator(mode="after")
	def _check_item_6(self) -> OutrosAtivos:
		"""Check item 6 (somatório de outros ativos).

		Returns
		-------
		OutrosAtivos
			The validated block.
		"""
		_require_sum(
			"VL_SOM_OUTROS_ATIVOS (item 6)",
			self.vl_som_outros_ativos,
			[self.vl_outro_vl_receb_curprz, self.vl_outro_vl_receb_lprazo],
			[],
		)
		return self


class AplicAtivo(_FidcBlock):
	"""APLIC_ATIVO — assets."""

	vl_disponib: Money
	vl_carteira: Money
	cred_existe: CredExiste
	lista_cedent_cred_existe: ListaCedentCredExiste | None = None
	dicred: Dicred
	lista_cedent: ListaCedent | None = None
	valores_mob: ValoresMob
	vl_titpub_fed: Money
	vl_cdb: Money
	vl_aplic_oper_compss: Money
	vl_ativ_financ_rf: Money
	vl_cota_fidc: Money
	vl_cota_fidc_nao_padrao: Money
	vl_contr_compra_venda_prestc_futura: Money
	vl_pvs_dbt_cri_nta_pms: Money
	vl_pvs_cta_fnd_inv: Money
	vl_pvs_otr_atv: Money
	merc_derivativo: MercDerivativo
	outros_ativos: OutrosAtivos
	vl_som_aplic_ativo: Money

	@model_validator(mode="after")
	def _check_items_1_and_2(self) -> AplicAtivo:
		"""Check item 2 (somatório de carteira) and item 1 (somatório de ativos).

		Returns
		-------
		AplicAtivo
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
			[self.vl_pvs_dbt_cri_nta_pms, self.vl_pvs_cta_fnd_inv, self.vl_pvs_otr_atv],
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


# ---------------------------------------------------------------------- CART_SEGMT


class SegmtComerc(_FidcBlock):
	"""SEGMT_COMERC — commercial segment."""

	vl_som_segmt_comerc: Money
	vl_comerc: Money
	vl_comerc_varj: Money
	vl_arrend_mercnt: Money

	@model_validator(mode="after")
	def _check_item_8(self) -> SegmtComerc:
		"""Check item 8.

		Returns
		-------
		SegmtComerc
			The validated block.
		"""
		_require_sum(
			"VL_SOM_SEGMT_COMERC (item 8)",
			self.vl_som_segmt_comerc,
			[self.vl_comerc, self.vl_comerc_varj, self.vl_arrend_mercnt],
			[],
		)
		return self


class SegmtServ(_FidcBlock):
	"""SEGMT_SERV — services segment."""

	vl_som_segmt_serv: Money
	vl_serv: Money
	vl_serv_public: Money
	vl_serv_educ: Money
	vl_serv_entreten: Money

	@model_validator(mode="after")
	def _check_item_9(self) -> SegmtServ:
		"""Check item 9.

		Returns
		-------
		SegmtServ
			The validated block.
		"""
		_require_sum(
			"VL_SOM_SEGMT_SERV (item 9)",
			self.vl_som_segmt_serv,
			[self.vl_serv, self.vl_serv_public, self.vl_serv_educ, self.vl_serv_entreten],
			[],
		)
		return self


class SegmtFinanc(_FidcBlock):
	"""SEGMT_FINANC — financial segment."""

	vl_som_segmt_financ: Money
	vl_financ_cred_pessoa: Money
	vl_financ_cred_pessoa_consig: Money
	vl_financ_cred_corpor: Money
	vl_financ_mmarket: Money
	vl_financ_veicl: Money
	vl_financ_imobil_empsrl: Money
	vl_financ_imobil_resid: Money
	vl_financ_outro: Money

	@model_validator(mode="after")
	def _check_item_10(self) -> SegmtFinanc:
		"""Check item 10.

		Returns
		-------
		SegmtFinanc
			The validated block.
		"""
		_require_sum(
			"VL_SOM_SEGMT_FINANC (item 10)",
			self.vl_som_segmt_financ,
			[
				self.vl_financ_cred_pessoa,
				self.vl_financ_cred_pessoa_consig,
				self.vl_financ_cred_corpor,
				self.vl_financ_mmarket,
				self.vl_financ_veicl,
				self.vl_financ_imobil_empsrl,
				self.vl_financ_imobil_resid,
				self.vl_financ_outro,
			],
			[],
		)
		return self


class SegmtFact(_FidcBlock):
	"""SEGMT_FACT — factoring segment."""

	vl_som_segmt_fact: Money
	vl_fact_pessoa: Money
	vl_fact_corpor: Money

	@model_validator(mode="after")
	def _check_item_11(self) -> SegmtFact:
		"""Check item 11.

		Returns
		-------
		SegmtFact
			The validated block.
		"""
		_require_sum(
			"VL_SOM_SEGMT_FACT (item 11)",
			self.vl_som_segmt_fact,
			[self.vl_fact_pessoa, self.vl_fact_corpor],
			[],
		)
		return self


class SegmtSetorPublic(_FidcBlock):
	"""SEGMT_SETOR_PUBLIC — public-sector segment (art. 1, par. 1, II, ICVM 444)."""

	vl_som_segmt_setor_public: Money
	vl_setor_public_precat: Money
	vl_setor_public_cred_tribut: Money
	vl_setor_public_roya: Money
	vl_setor_public_outro: Money

	@model_validator(mode="after")
	def _check_item_12(self) -> SegmtSetorPublic:
		"""Check item 12.

		Returns
		-------
		SegmtSetorPublic
			The validated block.
		"""
		_require_sum(
			"VL_SOM_SEGMT_SETOR_PUBLIC (item 12)",
			self.vl_som_segmt_setor_public,
			[
				self.vl_setor_public_precat,
				self.vl_setor_public_cred_tribut,
				self.vl_setor_public_roya,
				self.vl_setor_public_outro,
			],
			[],
		)
		return self


class CartSegmt(_FidcBlock):
	"""CART_SEGMT — portfolio by segment."""

	vl_som_cart_segmt: Money
	vl_ind: Money
	vl_merc_imobil: Money
	segmt_comerc: SegmtComerc
	segmt_serv: SegmtServ
	vl_agroneg: Money
	segmt_financ: SegmtFinanc
	vl_cart_cred: Money
	segmt_fact: SegmtFact
	segmt_setor_public: SegmtSetorPublic
	vl_acao_judic: Money
	vl_proprd_marca_patent: Money

	@model_validator(mode="after")
	def _check_item_7(self) -> CartSegmt:
		"""Check item 7 (somatório de carteira por segmento).

		Returns
		-------
		CartSegmt
			The validated block.
		"""
		_require_sum(
			"VL_SOM_CART_SEGMT (item 7)",
			self.vl_som_cart_segmt,
			[
				self.vl_ind,
				self.vl_merc_imobil,
				self.segmt_comerc.vl_som_segmt_comerc,
				self.segmt_serv.vl_som_segmt_serv,
				self.vl_agroneg,
				self.segmt_financ.vl_som_segmt_financ,
				self.vl_cart_cred,
				self.segmt_fact.vl_som_segmt_fact,
				self.segmt_setor_public.vl_som_segmt_setor_public,
				self.vl_acao_judic,
				self.vl_proprd_marca_patent,
			],
			[],
		)
		return self


# -------------------------------------------------------------- PASSIV / PATRLIQ


class PassivValores(_FidcBlock):
	"""PASSIV_VALORES — amounts payable."""

	vl_som_passiv_valores: Money
	vl_pgto_curprz: Money
	vl_pgto_lprazo: Money

	@model_validator(mode="after")
	def _check_item_14(self) -> PassivValores:
		"""Check item 14.

		Returns
		-------
		PassivValores
			The validated block.
		"""
		_require_sum(
			"VL_SOM_PASSIV_VALORES (item 14)",
			self.vl_som_passiv_valores,
			[self.vl_pgto_curprz, self.vl_pgto_lprazo],
			[],
		)
		return self


class PassivPosicoes(_FidcBlock):
	"""PASSIV_POSICOES — derivatives positions held (liabilities)."""

	vl_som_passiv_posicoes: Money
	vl_pos_mant_vend: Money
	vl_pos_mant_lanc: Money
	vl_pos_mant_ajt_fut: Money
	vl_pos_mant_swap_pagar: Money

	@model_validator(mode="after")
	def _check_item_15(self) -> PassivPosicoes:
		"""Check item 15.

		Returns
		-------
		PassivPosicoes
			The validated block.
		"""
		_require_sum(
			"VL_SOM_PASSIV_POSICOES (item 15)",
			self.vl_som_passiv_posicoes,
			[
				self.vl_pos_mant_vend,
				self.vl_pos_mant_lanc,
				self.vl_pos_mant_ajt_fut,
				self.vl_pos_mant_swap_pagar,
			],
			[],
		)
		return self


class Passiv(_FidcBlock):
	"""PASSIV — liabilities."""

	vl_som_passiv: Money
	passiv_valores: PassivValores
	passiv_posicoes: PassivPosicoes

	@model_validator(mode="after")
	def _check_item_13(self) -> Passiv:
		"""Check item 13.

		Returns
		-------
		Passiv
			The validated block.
		"""
		_require_sum(
			"VL_SOM_PASSIV (item 13)",
			self.vl_som_passiv,
			[
				self.passiv_valores.vl_som_passiv_valores,
				self.passiv_posicoes.vl_som_passiv_posicoes,
			],
			[],
		)
		return self


class Patrliq(_FidcBlock):
	"""PATRLIQ — net equity."""

	vl_som_patrliq: Money
	vl_patrim_liq: Money
	vl_patrim_liq_medio: Money

	@model_validator(mode="after")
	def _check_item_16(self) -> Patrliq:
		"""Check item 16.

		Returns
		-------
		Patrliq
			The validated block.
		"""
		_require_sum("VL_SOM_PATRLIQ (item 16)", self.vl_som_patrliq, [self.vl_patrim_liq], [])
		return self


# --------------------------------------------------------------------- COMPMT_DICRED


class CompmtDicred(_FidcBlock):
	"""COMPMT_DICRED_AQUIS / COMPMT_DICRED_SEM_AQUIS — portfolio behaviour by bucket.

	The two blocks have the same tag list; the page numbers their totals 17-19 (with
	risk transfer) and 20-22 (without).
	"""

	vl_som_prazo_venc: Money
	vl_prazo_venc_30: Money
	vl_prazo_venc_31_60: Money
	vl_prazo_venc_61_90: Money
	vl_prazo_venc_91_120: Money
	vl_prazo_venc_121_150: Money
	vl_prazo_venc_151_180: Money
	vl_prazo_venc_181_360: Money
	vl_prazo_venc_361_720: Money
	vl_prazo_venc_721_1080: Money
	vl_prazo_venc_1080: Money
	vl_som_inad_venc: Money
	vl_inad_venc_30: Money
	vl_inad_venc_31_60: Money
	vl_inad_venc_61_90: Money
	vl_inad_venc_91_120: Money
	vl_inad_venc_121_150: Money
	vl_inad_venc_151_180: Money
	vl_inad_venc_181_360: Money
	vl_inad_venc_361_720: Money
	vl_inad_venc_721_1080: Money
	vl_inad_venc_1080: Money
	vl_som_pago_antcp: Money
	vl_pago_antcp_30: Money
	vl_pago_antcp_31_60: Money
	vl_pago_antcp_61_90: Money
	vl_pago_antcp_91_120: Money
	vl_pago_antcp_121_150: Money
	vl_pago_antcp_151_180: Money
	vl_pago_antcp_181_360: Money
	vl_pago_antcp_361_720: Money
	vl_pago_antcp_721_1080: Money
	vl_pago_antcp_1080: Money

	@model_validator(mode="after")
	def _check_bucket_totals(self) -> CompmtDicred:
		"""Check the three bucket totals (items 17-19 / 20-22).

		Returns
		-------
		CompmtDicred
			The validated block.
		"""
		for total, prefix in (
			("vl_som_prazo_venc", "vl_prazo_venc_"),
			("vl_som_inad_venc", "vl_inad_venc_"),
			("vl_som_pago_antcp", "vl_pago_antcp_"),
		):
			_require_sum(
				total.upper(),
				getattr(self, total),
				[getattr(self, f"{prefix}{b}") for b in _BUCKETS],
				[],
			)
		return self


# ------------------------------------------------------------- NEGOC_DICRED_MES


class QtVl(_FidcBlock):
	"""A (QT_DICRED_AQUIS, VL_DICRED_AQUIS) pair — quantity and value of acquisitions."""

	qt_dicred_aquis: Money
	vl_dicred_aquis: Money


class Alienacao(_FidcBlock):
	"""A (QT, VL, VL contábil) triple — disposals of credit rights."""

	qt_dicred_alien: Money
	vl_dicred_alien: Money
	vl_dicred_alien_contab: Money


class NegocDicredMes(_FidcBlock):
	"""NEGOC_DICRED_MES — credit-rights deals made in the month."""

	aquisicoes: QtVl
	negoc_dicred_mes_aquis: QtVl
	negoc_dicred_mes_sem_aquis: QtVl
	negoc_dicred_mes_venc_adimpl: QtVl
	negoc_dicred_mes_venc_inad: QtVl
	negoc_dicred_mes_inad: QtVl
	dicred_mes_alien: Alienacao
	dicred_mes_alien_cedent: Alienacao
	dicred_mes_alien_prest: Alienacao
	dicred_mes_alien_tercr: Alienacao
	dicred_mes_alien_subst: Alienacao
	dicred_mes_alien_recomp: Alienacao

	@model_validator(mode="after")
	def _check_items_23_to_29(self) -> NegocDicredMes:
		"""Check items 23-29 (acquisition and disposal totals).

		Returns
		-------
		NegocDicredMes
			The validated block.
		"""
		for field in ("qt_dicred_aquis", "vl_dicred_aquis"):
			_require_sum(
				f"AQUISICOES.{field.upper()} (items 23/24)",
				getattr(self.aquisicoes, field),
				[
					getattr(self.negoc_dicred_mes_aquis, field),
					getattr(self.negoc_dicred_mes_sem_aquis, field),
				],
				[],
			)
			_require_sum(
				f"NEGOC_DICRED_MES_AQUIS.{field.upper()} (items 25/26)",
				getattr(self.negoc_dicred_mes_aquis, field),
				[
					getattr(self.negoc_dicred_mes_venc_adimpl, field),
					getattr(self.negoc_dicred_mes_venc_inad, field),
					getattr(self.negoc_dicred_mes_inad, field),
				],
				[],
			)
		for field in ("qt_dicred_alien", "vl_dicred_alien", "vl_dicred_alien_contab"):
			_require_sum(
				f"DICRED_MES_ALIEN.{field.upper()} (items 27-29)",
				getattr(self.dicred_mes_alien, field),
				[
					getattr(self.dicred_mes_alien_cedent, field),
					getattr(self.dicred_mes_alien_prest, field),
					getattr(self.dicred_mes_alien_tercr, field),
				],
				[],
			)
		return self


# ------------------------------------------------------------------------ INFORM


class DevSacado(_FidcBlock):
	"""DEV_SACADOS — one of the largest debtors (sacados) of the fund."""

	nr_pf_pj_sacado_deved_1: CpfCnpj
	vl_sacado_deved_1: Money
	pr_sacado_deved_1: Money


class ListaDevSacados(_FidcBlock):
	"""LISTA_DEV_SACADOS — the (up to) 25 largest debtors, in decreasing order."""

	dev_sacados: list[DevSacado] = Field(min_length=1, max_length=25)
	vl_som_lista_dev_sacados: Money
	pr_som_lista_dev_sacados: Money

	@model_validator(mode="after")
	def _check_totals(self) -> ListaDevSacados:
		"""Check the two sums against the listed debtors.

		Returns
		-------
		ListaDevSacados
			The validated block.
		"""
		_require_sum(
			"VL_SOM_LISTA_DEV_SACADOS",
			self.vl_som_lista_dev_sacados,
			[d.vl_sacado_deved_1 for d in self.dev_sacados],
			[],
		)
		_require_sum(
			"PR_SOM_LISTA_DEV_SACADOS",
			self.pr_som_lista_dev_sacados,
			[d.pr_sacado_deved_1 for d in self.dev_sacados],
			[],
		)
		return self


class InformSacados(_FidcBlock):
	"""INFORM — debtors report."""

	lista_dev_sacados: ListaDevSacados


# ---------------------------------------------------------- TAXA_NEGOC_DICRED_MES


class Taxa(_FidcBlock):
	"""Minimum / weighted-average / maximum rate, in percent (``9,0``, not ``0,09``)."""

	tx_min: Money
	tx_medio: Money
	tx_maximo: Money


class TaxaAquis(_FidcBlock):
	"""TAXA_NEGOC_DICRED_MES_AQUIS — rates, rights with risk transfer."""

	desc_compra: Taxa = Field(alias="TAXA_NEGOC_DICRED_MES_AQUIS_DESC_COMPRA")
	desc_venda: Taxa = Field(alias="TAXA_NEGOC_DICRED_MES_AQUIS_DESC_VENDA")
	juros_compra: Taxa = Field(alias="TAXA_NEGOC_DICRED_MES_AQUIS_JUROS_COMPRA")
	juros_venda: Taxa = Field(alias="TAXA_NEGOC_DICRED_MES_AQUIS_JUROS_VENDA")


class TaxaSemAquis(_FidcBlock):
	"""TAXA_NEGOC_DICRED_MES_SEM_AQUIS — rates, rights without risk transfer."""

	desc_compra: Taxa = Field(alias="TAXA_NEGOC_DICRED_MES_SEM_AQUIS_DESC_COMPRA")
	desc_venda: Taxa = Field(alias="TAXA_NEGOC_DICRED_MES_SEM_AQUIS_DESC_VENDA")
	juros_compra: Taxa = Field(alias="TAXA_NEGOC_DICRED_MES_SEM_AQUIS_JUROS_COMPRA")
	juros_venda: Taxa = Field(alias="TAXA_NEGOC_DICRED_MES_SEM_AQUIS_JUROS_VENDA")


class TaxaValorMobili(_FidcBlock):
	"""TAXA_NEGOC_DICRED_MES_VALOR_MOBILI — rates, securities."""

	desc_compra: Taxa = Field(alias="TAXA_NEGOC_DICRED_MES_VALOR_MOBILI_DESC_COMPRA")
	desc_venda: Taxa = Field(alias="TAXA_NEGOC_DICRED_MES_VALOR_MOBILI_DESC_VENDA")
	juros_compra: Taxa = Field(alias="TAXA_NEGOC_DICRED_MES_VALOR_MOBILI_JUROS_COMPRA")
	juros_venda: Taxa = Field(alias="TAXA_NEGOC_DICRED_MES_VALOR_MOBILI_JUROS_VENDA")


class TaxaTitpubFed(_FidcBlock):
	"""TAXA_NEGOC_DICRED_MES_TITPUB_FED — rates, federal public bonds."""

	desc_compra: Taxa = Field(alias="TAXA_NEGOC_DICRED_MES_TITPUB_FED_DESC_COMPRA")
	desc_venda: Taxa = Field(alias="TAXA_NEGOC_DICRED_MES_TITPUB_FED_DESC_VENDA")
	juros_compra: Taxa = Field(alias="TAXA_NEGOC_DICRED_MES_TITPUB_FED_JUROS_COMPRA")
	juros_venda: Taxa = Field(alias="TAXA_NEGOC_DICRED_MES_TITPUB_FED_JUROS_VENDA")


class TaxaCdb(_FidcBlock):
	"""TAXA_NEGOC_DICRED_MES_CDB — rates, bank CDs."""

	desc_compra: Taxa = Field(alias="TAXA_NEGOC_DICRED_MES_CDB_DESC_COMPRA")
	desc_venda: Taxa = Field(alias="TAXA_NEGOC_DICRED_MES_CDB_DESC_VENDA")
	juros_compra: Taxa = Field(alias="TAXA_NEGOC_DICRED_MES_CDB_JUROS_COMPRA")
	juros_venda: Taxa = Field(alias="TAXA_NEGOC_DICRED_MES_CDB_JUROS_VENDA")


class TaxaAtivRf(_FidcBlock):
	"""TAXA_NEGOC_DICRED_MES_ATIV_RF — rates, other fixed-income assets."""

	desc_compra: Taxa = Field(alias="TAXA_NEGOC_DICRED_MES_ATIV_RF_DESC_COMPRA")
	desc_venda: Taxa = Field(alias="TAXA_NEGOC_DICRED_MES_ATIV_RF_DESC_VENDA")
	juros_compra: Taxa = Field(alias="TAXA_NEGOC_DICRED_MES_ATIV_RF_JUROS_COMPRA")
	juros_venda: Taxa = Field(alias="TAXA_NEGOC_DICRED_MES_ATIV_RF_JUROS_VENDA")


class TaxaNegocDicredMes(_FidcBlock):
	"""TAXA_NEGOC_DICRED_MES — rates practised in the month's deals."""

	taxa_negoc_dicred_mes_aquis: TaxaAquis
	taxa_negoc_dicred_mes_sem_aquis: TaxaSemAquis
	taxa_negoc_dicred_mes_valor_mobili: TaxaValorMobili
	taxa_negoc_dicred_mes_titpub_fed: TaxaTitpubFed
	taxa_negoc_dicred_mes_cdb: TaxaCdb
	taxa_negoc_dicred_mes_ativ_rf: TaxaAtivRf


# ----------------------------------------------------------------- OUTRAS_INFORM


class ClasseCotistas(_FidcBlock):
	"""CLASSE_SENIOR / CLASSE_SUBORD (under NUM_COTISTAS) — holders of one series."""

	vl_classe: Count


class NumCotistas(_FidcBlock):
	"""NUM_COTISTAS — number of quota holders."""

	qt_total_cotistas: Count
	qt_total_cotistas_senior: Count
	qt_total_cotistas_subord: Count
	classe_senior: list[ClasseCotistas] = Field(min_length=1)
	classe_subord: list[ClasseCotistas] = Field(default_factory=list)

	@model_validator(mode="after")
	def _check_item_30_and_series(self) -> NumCotistas:
		"""Check item 30 and the per-class totals against the per-series counts.

		Returns
		-------
		NumCotistas
			The validated block.

		Raises
		------
		ValueError
			If a total disagrees with the tags the page says it sums.
		"""
		_require_sum(
			"QT_TOTAL_COTISTAS (item 30)",
			Decimal(self.qt_total_cotistas),
			[Decimal(self.qt_total_cotistas_senior), Decimal(self.qt_total_cotistas_subord)],
			[],
		)
		for total, series, label in (
			(self.qt_total_cotistas_senior, self.classe_senior, "QT_TOTAL_COTISTAS_SENIOR"),
			(self.qt_total_cotistas_subord, self.classe_subord, "QT_TOTAL_COTISTAS_SUBORD"),
		):
			_require_sum(label, Decimal(total), [Decimal(c.vl_classe) for c in series], [])
		return self


class CotistasPorTipo(_FidcBlock):
	"""CLS_SENIOR / CLS_SUBORDINADA — holders of a class, by investor type."""

	qnt_pss_fsc: Count
	qnt_pss_jrd: Count
	bnc_cmr: Count
	crt_dtr: Count
	otr_pss_jrd: Count
	inv_rsd: Count
	ent_abr_prd_cmp: Count
	ent_fch_prd: Count
	rgm_prp_prd_srv_pbl: Count
	scd_sgr_rsg: Count
	scd_cpt_ard_mer: Count
	fnd_inv_cts: Count
	fnd_inv_imb: Count
	otr_fnd_inv: Count
	clb_inv: Count
	camotr: Count

	def total(self) -> int:
		"""Sum of the holders over every investor type.

		Returns
		-------
		int
			Total holders of the class.
		"""
		return sum(getattr(self, name) for name in type(self).model_fields)


class NumCotistasDesc(_FidcBlock):
	"""NUM_COTISTAS_DESC — breakdown by investor type (tag mandatory, content may be empty)."""

	cls_senior: CotistasPorTipo | None = None
	cls_subordinada: CotistasPorTipo | None = None


class SerieClasse(_FidcBlock):
	"""DESC_SERIE_CLASSE_SENIOR / _SUBORD — quota count and unit value of one series."""

	qt_cotas: Quota8
	vl_cotas: Quota8


class DescSerieClasse(_FidcBlock):
	"""DESC_SERIE_CLASSE — series description (item X-2)."""

	desc_serie_classe_senior: list[SerieClasse] = Field(min_length=1)
	desc_serie_classe_subord: list[SerieClasse] = Field(default_factory=list)


class RentClasse(_FidcBlock):
	"""RENT_CLASSE_SENIOR / _SUBORD — return of one series, in percent."""

	pr_apurada: Money


class RentMes(_FidcBlock):
	"""RENT_MES — return in the month (item X-3)."""

	rent_classe_senior: list[RentClasse] = Field(min_length=1)
	rent_classe_subord: list[RentClasse] = Field(default_factory=list)


class CotasMovimento(_FidcBlock):
	"""CLASSE_SENIOR / CLASSE_SUBORD under CAPT_MES, RESG_MES and RESG_SOLIC."""

	qt_cotas: Quota8
	vl_cotas: Money


class Amortizacao(_FidcBlock):
	"""CLASSE_SENIOR / CLASSE_SUBORD under AMORT."""

	vl_cota: Quota8
	vl_total: Money


class CaptMes(_FidcBlock):
	"""CAPT_MES — subscriptions in the month (item X-4.1)."""

	classe_senior: list[CotasMovimento] = Field(min_length=1)
	classe_subord: list[CotasMovimento] = Field(default_factory=list)


class ResgMes(_FidcBlock):
	"""RESG_MES — redemptions in the month (item X-4.2)."""

	classe_senior: list[CotasMovimento] = Field(min_length=1)
	classe_subord: list[CotasMovimento] = Field(default_factory=list)


class ResgSolic(_FidcBlock):
	"""RESG_SOLIC — redemptions requested and not yet paid (item X-4.3)."""

	classe_senior: list[CotasMovimento] = Field(min_length=1)
	classe_subord: list[CotasMovimento] = Field(default_factory=list)


class Amort(_FidcBlock):
	"""AMORT — amortisations (item X-4.4)."""

	classe_senior: list[Amortizacao] = Field(min_length=1)
	classe_subord: list[Amortizacao] = Field(default_factory=list)


class CaptaResgaAmorti(_FidcBlock):
	"""CAPTA_RESGA_AMORTI — subscriptions, redemptions and amortisations."""

	capt_mes: CaptMes
	resg_mes: ResgMes
	resg_solic: ResgSolic
	amort: Amort


class Liquidez(_FidcBlock):
	"""LIQUIDEZ — assets by liquidation horizon. Mandatory content for open funds."""

	vl_ativ_liqdez: Money | None = None
	vl_ativ_liqdez_30: Money | None = None
	vl_ativ_liqdez_60: Money | None = None
	vl_ativ_liqdez_90: Money | None = None
	vl_ativ_liqdez_180: Money | None = None
	vl_ativ_liqdez_360: Money | None = None
	vl_ativ_liqdez_mais_360: Money | None = None


class DesempClasse(_FidcBlock):
	"""CLASSE_SENIOR / CLASSE_SUBORD under DESEMP — expected vs realised performance."""

	desemp_esp: Money
	desemp_real: Money


class Desemp(_FidcBlock):
	"""DESEMP — expected performance. The tag is mandatory, its content may be empty."""

	classe_senior: DesempClasse | None = None
	classe_subord: DesempClasse | None = None


class Garantia(_FidcBlock):
	"""GARANTIA — guarantees linked to the credit rights."""

	vlr_gnt_vnc_drt_crd: Money
	prc_drt_cred_gnt_vnc: Money


class OutrasInform(_FidcBlock):
	"""OUTRAS_INFORM — Tabela X, other information."""

	num_cotistas: NumCotistas
	num_cotistas_desc: NumCotistasDesc = Field(default_factory=NumCotistasDesc)
	desc_serie_classe: DescSerieClasse
	rent_mes: RentMes
	capta_resga_amorti: CaptaResgaAmorti
	liquidez: Liquidez | None = None
	desemp: Desemp = Field(default_factory=Desemp)
	garantia: Garantia

	@model_validator(mode="after")
	def _check_breakdown_matches_totals(self) -> OutrasInform:
		"""Check the by-type breakdown against the class totals (Tabela X, item 4).

		Returns
		-------
		OutrasInform
			The validated block.
		"""
		for breakdown, total, label in (
			(
				self.num_cotistas_desc.cls_senior,
				self.num_cotistas.qt_total_cotistas_senior,
				"CLS_SENIOR",
			),
			(
				self.num_cotistas_desc.cls_subordinada,
				self.num_cotistas.qt_total_cotistas_subord,
				"CLS_SUBORDINADA",
			),
		):
			if breakdown is not None:
				_require_sum(label, Decimal(total), [Decimal(breakdown.total())], [])
		return self


# --------------------------------------------------------------- LISTA_INFORM / root


class InfMensalFidcInform(_FidcBlock):
	"""LISTA_INFORM — the single informe of the file (one fund, one month)."""

	aplic_ativo: AplicAtivo
	cart_segmt: CartSegmt
	passiv: Passiv
	patrliq: Patrliq
	compmt_dicred_aquis: CompmtDicred
	compmt_dicred_sem_aquis: CompmtDicred
	negoc_dicred_mes: NegocDicredMes
	inform: InformSacados
	taxa_negoc_dicred_mes: TaxaNegocDicredMes
	outras_inform: OutrasInform

	@model_validator(mode="after")
	def _check_maturity_and_delinquency_cross_totals(self) -> InfMensalFidcInform:
		"""Check the page's cross-block validation of the maturity and default totals.

		Returns
		-------
		InfMensalFidcInform
			The validated block.
		"""
		ce, di = self.aplic_ativo.cred_existe, self.aplic_ativo.dicred
		for block, performing, defaulted in (
			(
				self.compmt_dicred_aquis,
				[
					ce.vl_cred_existe_venc_adimpl,
					ce.vl_cred_existe_venc_inad,
					ce.vl_cred_refer_dicred_perfo,
				],
				[ce.vl_cred_total_venc_inad, ce.vl_cred_existe_inad, ce.vl_cred_venc_pend],
			),
			(
				self.compmt_dicred_sem_aquis,
				[
					di.vl_dicred_cedent,
					di.vl_dicred_existe_venc_inad,
					di.vl_dicred_refer_dicred_perfo,
				],
				[
					di.vl_dicred_total_venc_inad,
					di.vl_dicred_existe_inad,
					di.vl_dicred_venc_pend,
				],
			),
		):
			_require_sum(
				"VL_SOM_PRAZO_VENC vs portfolio",
				block.vl_som_prazo_venc,
				performing,
				[defaulted[0]],
			)
			_require_sum("VL_SOM_INAD_VENC vs portfolio", block.vl_som_inad_venc, defaulted, [])
		return self


class InfMensalFidcDocument(_FidcBlock):
	"""DOC_ARQ — a complete Informe Mensal FIDC file (a single fund and competence)."""

	cab_inform: InfMensalFidcHeader
	lista_inform: InfMensalFidcInform

	@model_validator(mode="after")
	def _open_fund_reports_liquidity(self) -> InfMensalFidcDocument:
		"""Require LIQUIDEZ content for open funds (optional for closed ones).

		Returns
		-------
		InfMensalFidcDocument
			The validated document.

		Raises
		------
		ValueError
			If the fund is open and no LIQUIDEZ field is filled.
		"""
		liquidez = self.lista_inform.outras_inform.liquidez
		filled = liquidez is not None and any(
			getattr(liquidez, f) is not None for f in type(liquidez).model_fields
		)
		if self.cab_inform.tp_condominio == "ABERTO" and not filled:
			raise ValueError("open funds must fill at least one LIQUIDEZ field")
		return self
