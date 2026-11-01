"""Pydantic models for the CVM Extrato das Informações sobre o Fundo XML standard — V1 (ICVM 450).

Direction-neutral schema for ``PadraoXMLInfExtrato450.asp``
(https://cvmweb.cvm.gov.br/SWB/Sistemas/SCW/PadroesXML/PadraoXMLInfExtrato450.asp). It shares
nothing structurally with the V3 schema in ``extrato.py`` (V3 is a different questionnaire), so
only the generic building blocks are imported from it: the closed/frozen block base, the
``S``/``N`` flag, and the decimal, date and day-count field types.

**Field order is the XML order.** Each field is the lower-cased tag from the page's sample file
and sits where the sample puts it; the writer walks ``model_fields`` in declaration order.

The page's sample file and its tag list disagree in a few places (CNPJ tag, a block with no
closing tag, a repeated ``LIM_CIA_ABERTA``). Every such choice, and what the page leaves
unsaid (decimal scales, bounds on day counts), is stated on ``docs/submission/extrato_v1.md``.
"""

from __future__ import annotations

from decimal import Decimal
import re
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
from filings_cvm._internal.config.schemas.extrato import (
	DateField,
	DaysField,
	Money2,
	Percent4,
	Ratio4,
	Text200,
	Yn,
)
from filings_cvm._internal.utils.typing import type_checker
from filings_cvm._internal.utils.xml_fields import check_cnpj_shape, check_xml_text, strict_decimal


_DIGITS = 18
_MAX_ROWS = 1000


@type_checker
def _strip_leading_zeros(value: str) -> str:
	"""Drop the zero filler the page forbids in every field.

	Parameters
	----------
	value : str
		A bare, validated CNPJ.

	Returns
	-------
	str
		The CNPJ without leading zeros.
	"""
	return value.lstrip("0")


# "Pontos, traços, barras e zeros à esquerda devem ser omitidos" (the page, on the CNPJ).
_CnpjV1 = Annotated[
	str,
	AfterValidator(check_cnpj_shape),
	AfterValidator(validated_cnpj),
	AfterValidator(_strip_leading_zeros),
]
# The page: "Inteiro com duas casas decimais" (question 34), or the literal SL.
_Ratio2 = Annotated[
	Decimal,
	BeforeValidator(strict_decimal(2)),
	Field(ge=Decimal(0), max_digits=_DIGITS, decimal_places=2),
]

_XML_TEXT = AfterValidator(check_xml_text)
_Text50 = Annotated[str, StringConstraints(min_length=1, max_length=50), _XML_TEXT]
_Text100 = Annotated[str, StringConstraints(min_length=1, max_length=100), _XML_TEXT]
_Text400 = Annotated[str, StringConstraints(min_length=1, max_length=400), _XML_TEXT]
_Text4000 = Annotated[str, StringConstraints(min_length=1, max_length=4000), _XML_TEXT]
# "Somente dígitos com, no máximo, 4 / 11 posições"; no zero filler, so the first digit is 1-9.
_Ddd = Annotated[str, StringConstraints(pattern=r"^[1-9][0-9]{0,3}$")]
_Telefone = Annotated[str, StringConstraints(pattern=r"^[1-9][0-9]{0,10}$")]

_SECONDARY_MARKETS = Literal[1, 2, 3]  # table A: BOVESPA, CETIP, SOMA
_DistributionCode = Annotated[int, Field(strict=True, ge=1, le=3)]  # table B
_PolicyCode = Annotated[int, Field(strict=True, ge=1, le=4)]  # table C
_QuotaBaseCode = Annotated[int, Field(strict=True, ge=1, le=2)]  # table E
_EntryQuotaCode = Literal[1, 2, 3, 6]  # table F — the page skips 4 and 5
_INDEX_CODES = frozenset({*range(1, 36), 99})  # table D

_NUMERIC_TEXT = re.compile(r"[0-9.,\s+-]+")


@type_checker
def _not_numeric(value: str) -> str:
	"""Refuse a numeric-looking text where the page wants a number or a description.

	``TX_ADM`` is a numeric percentage, or free text for qualified-investor funds. Without this
	a number the percentage type rejected (``"150"``) would slip through as text.

	Parameters
	----------
	value : str
		The free text.

	Returns
	-------
	str
		The same text.

	Raises
	------
	ValueError
		If the text is only digits and separators.
	"""
	if _NUMERIC_TEXT.fullmatch(value):
		raise ValueError("a numeric TX_ADM must be a valid percentage (0 to 100)")
	return value


_TxAdmText = Annotated[
	str,
	StringConstraints(min_length=1, max_length=400),
	_XML_TEXT,
	AfterValidator(_not_numeric),
]


class _Block(BaseModel):
	"""Base of every Extrato V1 block: closed (no unknown fields) and immutable."""

	model_config = ConfigDict(extra="forbid", frozen=True)


@type_checker
def _require_when(block: BaseModel, flag: str, trigger: str, name: str) -> None:
	"""Require a field exactly when a flag has a given answer (mandatory then, forbidden else).

	Parameters
	----------
	block : BaseModel
		The block being validated.
	flag : str
		Name of the ``S``/``N`` field.
	trigger : str
		The answer that makes ``name`` mandatory.
	name : str
		Name of the dependent field.

	Raises
	------
	ValueError
		If ``name`` is missing when required, or present when not.
	"""
	if (getattr(block, flag) == trigger) != (getattr(block, name) is not None):
		raise ValueError(
			f"{name.upper()} is required when {flag.upper()} is {trigger}, else omitted"
		)


@type_checker
def _only_if(block: BaseModel, flag: str, trigger: str, name: str) -> None:
	"""Reject a field the page says to fill *only if* a flag has a given answer.

	The field stays optional when the flag matches — the sample
	marks it "(opcional)" — but is refused when it does not.

	Parameters
	----------
	block : BaseModel
		The block being validated.
	flag : str
		Name of the ``S``/``N`` field.
	trigger : str
		The answer that allows ``name``.
	name : str
		Name of the dependent field.

	Raises
	------
	ValueError
		If ``name`` is present while ``flag`` has another answer.
	"""
	if getattr(block, flag) != trigger and getattr(block, name) is not None:
		raise ValueError(f"{name.upper()} must be omitted unless {flag.upper()} is {trigger}")


@type_checker
def _ordered(low: Decimal | None, high: Decimal | None, label: str) -> None:
	"""Require a minimum not to exceed its maximum when both are given.

	Parameters
	----------
	low : Decimal | None
		The ``PR_MIN_*`` value.
	high : Decimal | None
		The ``PR_MAX_*`` value.
	label : str
		The limit's name, for the message.

	Raises
	------
	ValueError
		If the minimum is above the maximum.
	"""
	if low is not None and high is not None and low > high:
		raise ValueError(f"PR_MIN_{label} must not exceed PR_MAX_{label}")


class ExtratoV1Header(_Block):
	"""CAB_INFORM — document header (``COD_DOC`` 41, ``VERSAO`` 1.0)."""

	cod_doc: Literal[41] = 41
	versao: Literal["1.0"] = "1.0"
	dt_gerac_arq: DateField


class _BaseInformForm(_Block):
	"""BASE_INFORM_FORM — the documents the form is based on."""

	dt_assemb: DateField | None = None
	dt_vigor_inform: DateField
	dt_prosp: DateField


class _CotaMercSecund(_Block):
	"""COTA_MERC_SECUND — secondary-market trading (closed funds only)."""

	cota_negoc_merc_secund: Yn
	cod_merc_secund: _SECONDARY_MARKETS | None = None

	@model_validator(mode="after")
	def _check_market(self) -> _CotaMercSecund:
		"""Allow the market code only for a fund whose quotas are traded.

		Returns
		-------
		_CotaMercSecund
			The validated block.
		"""
		_only_if(self, "cota_negoc_merc_secund", "S", "cod_merc_secund")
		return self


class _TelAtendCotista(_Block):
	"""TEL_ATEND_COTISTA — customer-service phone."""

	nr_ddd: _Ddd
	nr_tel: _Telefone


class _ServAtendCotista(_Block):
	"""SERV_ATEND_COTISTA — customer-service contact."""

	tel_atend_cotista: _TelAtendCotista
	ds_ender: _Text50
	ds_email: _Text50 | None = None
	ds_web: _Text50 | None = None
	ds_nome_resp: _Text100


class _ResgCotasV1(_Block):
	"""RESG_COTAS — redemption grace period."""

	carencia_resg_cotas: Yn
	dias_resg_cotas: DaysField | None = None

	@model_validator(mode="after")
	def _check_days(self) -> _ResgCotasV1:
		"""Allow the grace days only when there is a grace period.

		Returns
		-------
		_ResgCotasV1
			The validated block.
		"""
		_only_if(self, "carencia_resg_cotas", "S", "dias_resg_cotas")
		return self


class _CalcTxPerfmV1(_Block):
	"""CALC_TX_PERFM — performance-fee calculation.

	The page makes the rate, index code and index share mandatory for funds for non-qualified
	investors, and lets qualified-investor funds describe the fee in ``INFO_ADICIONAL`` instead.
	The document has no investor-type field, so the block must hold either the three mandatory
	fields or the description, and the description may not accompany the formula's fields.
	"""

	vl_tx_perfm: Percent4 | None = None
	cod_param_tx_perfm: Annotated[int, Field(strict=True)] | None = None
	pr_ind_refer: Ratio4 | None = None
	pr_cupom: Percent4 | None = None
	info_adicional: _Text400 | None = None

	@model_validator(mode="after")
	def _check_index_code(self) -> _CalcTxPerfmV1:
		"""Require the index code to be one of table D.

		Returns
		-------
		_CalcTxPerfmV1
			The validated block.

		Raises
		------
		ValueError
			If the code is not 1-35 or 99.
		"""
		if self.cod_param_tx_perfm not in _INDEX_CODES | {None}:
			raise ValueError("COD_PARAM_TX_PERFM must be a table D code (1-35 or 99)")
		return self

	@model_validator(mode="after")
	def _check_formula_is_whole(self) -> _CalcTxPerfmV1:
		"""Require the three mandatory fields together or not at all.

		Returns
		-------
		_CalcTxPerfmV1
			The validated block.

		Raises
		------
		ValueError
			If only some of the three are given.
		"""
		missing = (self.vl_tx_perfm, self.cod_param_tx_perfm, self.pr_ind_refer).count(None)
		if missing in (1, 2):
			raise ValueError("VL_TX_PERFM, COD_PARAM_TX_PERFM and PR_IND_REFER go together")
		return self

	@model_validator(mode="after")
	def _check_not_empty(self) -> _CalcTxPerfmV1:
		"""Require either the formula or the description.

		Returns
		-------
		_CalcTxPerfmV1
			The validated block.

		Raises
		------
		ValueError
			If the block carries neither.
		"""
		if self.vl_tx_perfm is None and self.info_adicional is None:
			raise ValueError("CALC_TX_PERFM needs the formula fields or INFO_ADICIONAL")
		return self


class _PrazoPagam(_Block):
	"""PRAZO_PAGAM — performance-fee payment term."""

	vl_prazo_pagam: DaysField
	ds_prazo_pagam: Literal["D", "M", "A"]


class _TxPerfmV1(_Block):
	"""TX_PERFM — performance fee (the calculation, appropriation and payment only if charged)."""

	cobra_tx_perfm: Yn
	calc_tx_perfm: _CalcTxPerfmV1 | None = None
	prazo_aprop: DaysField | None = None
	prazo_pagam: _PrazoPagam | None = None

	@model_validator(mode="after")
	def _check_fee_details(self) -> _TxPerfmV1:
		"""Require the calculation, appropriation and payment term exactly when the fee is charged.

		Returns
		-------
		_TxPerfmV1
			The validated block.
		"""
		for name in ("calc_tx_perfm", "prazo_aprop", "prazo_pagam"):
			_require_when(self, "cobra_tx_perfm", "S", name)
		return self


# A charged fee takes exactly one amount (fixed R$ or percentage); an uncharged one takes none.
_AMOUNTS_ALLOWED = {"S": 1, "N": 0}


@type_checker
def _check_one_amount(flag: str, fixed: Decimal | None, percent: Decimal | None) -> None:
	"""Require exactly one of fixed R$ / percentage when a fee is charged, none otherwise.

	Parameters
	----------
	flag : str
		The ``COBRA_*`` answer.
	fixed : Decimal | None
		The fixed amount in R$.
	percent : Decimal | None
		The percentage over the application or redemption.

	Raises
	------
	ValueError
		If the number of amounts does not match the answer.
	"""
	if (fixed, percent).count(None) != 2 - _AMOUNTS_ALLOWED[flag]:
		raise ValueError("a charged fee takes exactly one amount; an uncharged one takes none")


class _TxIngressoV1(_Block):
	"""TX_INGRESSO — entry fee, fixed (R$) or a percentage of the application."""

	cobra_tx_ingresso: Yn
	vl_fixo_tx_ingresso: Money2 | None = None
	pr_tx_ingresso: Percent4 | None = None

	@model_validator(mode="after")
	def _check_amount(self) -> _TxIngressoV1:
		"""Apply the one-amount rule.

		Returns
		-------
		_TxIngressoV1
			The validated block.
		"""
		_check_one_amount(self.cobra_tx_ingresso, self.vl_fixo_tx_ingresso, self.pr_tx_ingresso)
		return self


class _TxSaidaV1(_Block):
	"""TX_SAIDA — exit fee, fixed (R$) or a percentage of the redemption."""

	cobra_tx_saida: Yn
	vl_fixo_tx_saida: Money2 | None = None
	pr_tx_saida: Percent4 | None = None

	@model_validator(mode="after")
	def _check_amount(self) -> _TxSaidaV1:
		"""Apply the one-amount rule.

		Returns
		-------
		_TxSaidaV1
			The validated block.
		"""
		_check_one_amount(self.cobra_tx_saida, self.vl_fixo_tx_saida, self.pr_tx_saida)
		return self


class _OperDerivV1(_Block):
	"""OPER_DERIV — derivatives operations and the maximum margin."""

	realiz_oper_deriv: Yn
	pr_max_oper_deriv: Percent4 | None = None


class _RiscoMerc(_Block):
	"""RISCO_MERC — market-risk exposure limit."""

	exp_risco_merc: Yn
	ds_risco_merc: Text200 | None = None

	@model_validator(mode="after")
	def _check_description(self) -> _RiscoMerc:
		"""Allow the description only for a fund subject to a limit.

		Returns
		-------
		_RiscoMerc
			The validated block.
		"""
		_only_if(self, "exp_risco_merc", "S", "ds_risco_merc")
		return self


class _OperPatrimLiqV1(_Block):
	"""OPER_PATRIM_LIQ — operations above the net worth (``SL`` when unlimited)."""

	realiza_oper_patrim_liq: Yn
	qt_oper_patrim_liq: _Ratio2 | Literal["SL"] | None = None

	@model_validator(mode="after")
	def _check_multiple(self) -> _OperPatrimLiqV1:
		"""Require the multiple exactly when operations above the net worth are allowed.

		Returns
		-------
		_OperPatrimLiqV1
			The validated block.
		"""
		_require_when(self, "realiza_oper_patrim_liq", "S", "qt_oper_patrim_liq")
		return self


class _AtivExterV1(_Block):
	"""ATIV_EXTER — foreign assets."""

	invest_exterior: Yn
	horar_fech_merc: _Text100 | None = None
	pr_max_aplic_ativ_exter: Percent4 | None = None


class _LimCiaAberta(_Block):
	"""LIM_CIA_ABERTA — listed-company shares, per asset modality."""

	pr_min_cia_aberta: Percent4 | None = None
	pr_max_cia_aberta: Percent4 | None = None

	@model_validator(mode="after")
	def _check_order(self) -> _LimCiaAberta:
		"""Require the minimum not to exceed the maximum.

		Returns
		-------
		_LimCiaAberta
			The validated block.
		"""
		_ordered(self.pr_min_cia_aberta, self.pr_max_cia_aberta, "CIA_ABERTA")
		return self


class _LimTitpub(_Block):
	"""LIM_TITPUB — federal public securities."""

	pr_min_titpub: Percent4 | None = None
	pr_max_titpub: Percent4 | None = None

	@model_validator(mode="after")
	def _check_order(self) -> _LimTitpub:
		"""Require the minimum not to exceed the maximum.

		Returns
		-------
		_LimTitpub
			The validated block.
		"""
		_ordered(self.pr_min_titpub, self.pr_max_titpub, "TITPUB")
		return self


class _LimOperCompromTpf(_Block):
	"""LIM_OPER_COMPROM — repos backed by federal public securities."""

	pr_max_oper_comprom: Percent4 | None = None


class _LimAplicOperCompom(_Block):
	"""LIM_APLIC_OPER_COMPOM — repos backed by private securities."""

	pr_max_aplic_oper_compom: Percent4 | None = None


class _LimFdoInvest(_Block):
	"""LIM_FDO_INVEST — quotas of CVM 409 funds."""

	pr_max_aplic_fdo_invest: Percent4 | None = None


class _LimOutroFdoInvest(_Block):
	"""LIM_OUTRO_FDO_INVEST — quotas of other kinds of funds."""

	pr_max_aplic_outro_fdo_invest: Percent4 | None = None


class _LimCrepriv(_Block):
	"""LIM_CREPRIV — private credit, per issuer."""

	pr_max_aplic_crepriv: Percent4 | None = None


class _LimInstFin(_Block):
	"""LIM_INST_FIN — one financial institution."""

	pr_max_inst_fin: Percent4 | None = None


class _LimAplicCiaAberta(_Block):
	"""LIM_APLIC_CIA_ABERTA — one listed company, per issuer."""

	pr_max_aplic_cia_aberta: Percent4 | None = None


class _LimMesmoFdoInvest(_Block):
	"""LIM_MESMO_FDO_INVEST — one same investment fund."""

	pr_max_aplic_mesmo_fdo_invest: Percent4 | None = None


class _LimAplicPfPj(_Block):
	"""LIM_APLIC_PF_PJ — one individual or other legal entity."""

	pr_max_aplic_pf_pj: Percent4 | None = None


class _LimTitAdm(_Block):
	"""LIM_TIT_ADM — securities of the administrator (mandatory)."""

	pr_max_tit_adm: Percent4


class _LimFdoAdm(_Block):
	"""LIM_FDO_ADM — funds under the same administrator (mandatory)."""

	pr_max_fdo_adm: Percent4


class _LimEmprestAcoes(_Block):
	"""LIM_EMPREST_ACOES — share lending (lender positions only)."""

	pr_min_emprest_acoes: Percent4 | None = None
	pr_max_emprest_acoes: Percent4 | None = None

	@model_validator(mode="after")
	def _check_order(self) -> _LimEmprestAcoes:
		"""Require the minimum not to exceed the maximum.

		Returns
		-------
		_LimEmprestAcoes
			The validated block.
		"""
		_ordered(self.pr_min_emprest_acoes, self.pr_max_emprest_acoes, "EMPREST_ACOES")
		return self


class _LimEmprestTitpub(_Block):
	"""LIM_EMPREST_TITPUB — public-security lending (lender positions only)."""

	pr_min_emprest_titpub: Percent4 | None = None
	pr_max_emprest_titpub: Percent4 | None = None

	@model_validator(mode="after")
	def _check_order(self) -> _LimEmprestTitpub:
		"""Require the minimum not to exceed the maximum.

		Returns
		-------
		_LimEmprestTitpub
			The validated block.
		"""
		_ordered(self.pr_min_emprest_titpub, self.pr_max_emprest_titpub, "EMPREST_TITPUB")
		return self


class ExtratoV1Row(_Block):
	"""ROW_EXTRATO — the extract of one fund."""

	cnpj_fdo: _CnpjV1
	base_inform_form: _BaseInformForm
	cota_merc_secund: _CotaMercSecund | None = None
	cod_distr_fdo: _DistributionCode
	serv_atend_cotista: _ServAtendCotista
	corret_mesmo_grp_adm: Yn
	cod_polit_invest: _PolicyCode
	ds_resumo_polit: _Text4000
	qt_dia_divulg_cart: DaysField
	prosp_polit_invest_taxa_adm: Yn
	vl_aplic_min: Money2
	vl_movim_min: Money2
	vl_saldo_min: Money2
	cod_cota_patrim_liq: _QuotaBaseCode
	cod_cota_entr: _EntryQuotaCode
	qt_dia_conv_cota: DaysField
	qt_dia_pagam_cota: DaysField
	resg_cotas: _ResgCotasV1
	tx_adm: Percent4 | _TxAdmText
	tx_perfm: _TxPerfmV1
	tx_ingresso: _TxIngressoV1
	tx_saida: _TxSaidaV1
	oper_deriv: _OperDerivV1
	deriv_prot_cart: Yn
	restr_contrp_adm: Yn
	restr_contrp_tesour: Yn
	aval_risco_merc: Yn
	risco_merc: _RiscoMerc
	oper_patrim_liq: _OperPatrimLiqV1
	ativ_exter: _AtivExterV1
	lim_cia_aberta: _LimCiaAberta | None = None
	lim_titpub: _LimTitpub | None = None
	lim_oper_comprom: _LimOperCompromTpf | None = None
	lim_aplic_oper_compom: _LimAplicOperCompom | None = None
	lim_fdo_invest: _LimFdoInvest | None = None
	lim_outro_fdo_invest: _LimOutroFdoInvest | None = None
	lim_crepriv: _LimCrepriv | None = None
	lim_inst_fin: _LimInstFin | None = None
	lim_aplic_cia_aberta: _LimAplicCiaAberta | None = None
	lim_mesmo_fdo_invest: _LimMesmoFdoInvest | None = None
	lim_aplic_pf_pj: _LimAplicPfPj | None = None
	lim_tit_adm: _LimTitAdm
	lim_fdo_adm: _LimFdoAdm
	lim_emprest_acoes: _LimEmprestAcoes | None = None
	lim_emprest_titpub: _LimEmprestTitpub | None = None


class ExtratoV1Document(_Block):
	"""DOC_ARQ — a whole Extrato V1 file: one header and one row per fund."""

	header: ExtratoV1Header
	rows: Annotated[list[ExtratoV1Row], Field(min_length=1, max_length=_MAX_ROWS)]
