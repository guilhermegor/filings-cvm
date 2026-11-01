"""Pydantic models for the CVM Informe Semestral de Investidor Nao Residente (INR) standard.

Shared, direction-neutral schema. The standard is **two files sent together** for the same
competence and the same investors: Parte I (``COD_DOC`` 69, resource flows) and Parte II
(``COD_DOC`` 70, applications). Field names, scales and cardinalities follow the CVM pages
``PadraoXMLInfoSemestralINRParte1.asp`` and ``PadraoXMLInfoSemestralINRParte2.aspx``.

Scales (where the page states none, the assumption is documented in
``docs/submission/inr_semestral.md``):

- Parte I values are "numerico e inteiro": non-negative integers, in reais.
- ``QTDE_POS_FIM``: up to 15 integer and 6 decimal places; ``MERC_POS_FIM``, ``NOCION_POS_FIM``
  and ``NOCION_SWAP``: up to 15 integer and 2 decimal places. Excess places are truncated
  (``ROUND_DOWN``), never rounded, and a ``float`` is refused.
- Indexer percentage, coupon and contracted rate: up to 3 integer and 6 decimal places.

Rules the page states as tables are enforced here: the block <-> application-type table, the
application-type <-> asset-type table (Table B) and the required/forbidden quantity and notional
fields per application type (Table A).
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
	StrictStr,
	model_validator,
)

from filings_cvm._internal.utils.inr_semestral_codes import (
	APPLICATION_FIELD_RULES,
	ASSET_TYPES,
	ASSET_TYPES_BY_APPLICATION,
	BLOCK_APPLICATIONS,
	COUNTRIES,
	EXCHANGES,
	INDEXERS,
	SWAP_CODES,
)
from filings_cvm._internal.utils.inr_semestral_fields import (
	check_br_date,
	check_cod_partic,
	check_code,
	check_cvm_code,
	check_month_year,
	ensure,
	strict_decimal,
	strict_int,
	text_field,
	to_cnpj_field,
	to_person_doc,
)
from filings_cvm._internal.utils.typing import type_checker


_MAX_PARTICIPANTS = 1000

_SWAP_PREFIX = "SWP"

# Parte I values: "numerico e inteiro".
_IntegerValue = Annotated[int, BeforeValidator(strict_int), Field(ge=0)]
# Parte II amounts: up to 15 integer and 2 decimal places.
_MoneyValue = Annotated[
	Decimal, BeforeValidator(strict_decimal(2)), Field(max_digits=17, decimal_places=2)
]
# QTDE_POS_FIM: up to 15 integer and 6 decimal places, never negative.
_QuantityValue = Annotated[
	Decimal,
	BeforeValidator(strict_decimal(6)),
	Field(ge=Decimal(0), max_digits=21, decimal_places=6),
]
# Indexer percentage, coupon, contracted rate: up to 3 integer and 6 decimal places.
_RateValue = Annotated[
	Decimal,
	BeforeValidator(strict_decimal(6)),
	Field(ge=Decimal(0), max_digits=9, decimal_places=6),
]

_DateBr = Annotated[StrictStr, AfterValidator(check_br_date)]
_Competence = Annotated[StrictStr, AfterValidator(check_month_year)]
_CodPartic = Annotated[StrictStr, AfterValidator(check_cod_partic)]
_CvmCode = Annotated[StrictStr, AfterValidator(check_cvm_code)]
_Cnpj = Annotated[StrictStr, AfterValidator(to_cnpj_field)]
_Code = Annotated[StrictStr, AfterValidator(check_code)]
_SimNao = Literal["S", "N"]
_IssuerName = Annotated[StrictStr, AfterValidator(text_field(150))]
_AssetDescription = Annotated[StrictStr, AfterValidator(text_field(1000))]


@type_checker
def _require_member(value: str, table: frozenset[str], label: str) -> str:
	"""Require ``value`` to be a code of one of the spec's tables.

	Parameters
	----------
	value : str
		The code.
	table : frozenset[str]
		The valid codes.
	label : str
		Table name for the error message.

	Returns
	-------
	str
		The same code.

	Raises
	------
	ValueError
		If the code is not in the table.
	"""
	if value not in table:
		raise ValueError(f"{value!r} is not a code of {label}")
	return value


_AssetTypeCode = Annotated[
	StrictStr, AfterValidator(lambda v: _require_member(v, ASSET_TYPES, "Table C"))
]
_IndexerCode = Annotated[
	StrictStr, AfterValidator(lambda v: _require_member(v, INDEXERS, "Table D"))
]
_CountryCode = Annotated[
	StrictStr, AfterValidator(lambda v: _require_member(v, COUNTRIES, "Table G"))
]
_ExchangeCode = Annotated[
	StrictStr, AfterValidator(lambda v: _require_member(v, EXCHANGES, "Table H"))
]


class _Strict(BaseModel):
	"""Base config: unknown fields are rejected so a typo cannot silently drop data."""

	model_config = ConfigDict(extra="forbid")


# ---------------------------------------------------------------------------------------------
# Parte I (COD_DOC 69)
# ---------------------------------------------------------------------------------------------


class InrParte1Header(_Strict):
	"""``CAB_INFORM`` of Parte I.

	Attributes
	----------
	cod_doc : str
		Always ``"69"``.
	versao : str
		Always ``"1.0"``.
	cd_cvm : str
		CVM code of the investor's representative (up to 5 digits).
	dt_compt : str
		Competence, ``MM/AAAA``.
	dt_gerac_arq : str
		File generation date, ``DD/MM/AAAA``.
	"""

	cod_doc: Literal["69"] = "69"
	versao: Literal["1.0"] = "1.0"
	cd_cvm: _CvmCode
	dt_compt: _Competence
	dt_gerac_arq: _DateBr


class InrEntradaSaida(_Strict):
	"""``ENTRADA_SAIDA``: resources in and out during the period, in reais.

	Attributes
	----------
	vl_entr : int
		``VL_ENTR``.
	vl_saida : int
		``VL_SAIDA``.
	"""

	vl_entr: _IntegerValue
	vl_saida: _IntegerValue


class InrTransfRecursos(_Strict):
	"""``TRANSF_RECURSOS``: transfers between investment modalities, in reais.

	Attributes
	----------
	vl_invest_carteira_haver_nres : int
		Portfolio investment to non-resident holdings.
	vl_haver_nres_invest_carteira : int
		Non-resident holdings to portfolio investment.
	vl_invest_carteira_adr : int
		Portfolio investment to depositary receipts.
	vl_adr_invest_carteira : int
		Depositary receipts to portfolio investment.
	vl_invest_carteira_estrang_direta : int
		Portfolio investment to direct foreign investment.
	vl_estrang_direta_invest_carteira : int
		Direct foreign investment to portfolio investment.
	"""

	vl_invest_carteira_haver_nres: _IntegerValue
	vl_haver_nres_invest_carteira: _IntegerValue
	vl_invest_carteira_adr: _IntegerValue
	vl_adr_invest_carteira: _IntegerValue
	vl_invest_carteira_estrang_direta: _IntegerValue
	vl_estrang_direta_invest_carteira: _IntegerValue


class InrRecursoRecebido(_Strict):
	"""One resource received (``RECURSOS_RECEB_*``).

	Attributes
	----------
	cd_partic_origem : str
		Full code of the originating investor.
	vl_recebido : int
		Amount received, in reais.
	"""

	cd_partic_origem: _CodPartic
	vl_recebido: _IntegerValue


class InrRecursoEnviado(_Strict):
	"""One resource sent (``RECURSOS_ENV_*``).

	Attributes
	----------
	cd_partic_dest : str
		Full code of the destination investor.
	vl_enviado : int
		Amount sent, in reais.
	"""

	cd_partic_dest: _CodPartic
	vl_enviado: _IntegerValue


class InrRecursosEntreInvestidores(_Strict):
	"""``RECURSOS_MESMO_INVEST`` / ``RECURSOS_OUTRO_INVEST`` (both optional, repeating).

	Attributes
	----------
	recebidos : list[InrRecursoRecebido]
		Resources received; empty omits the ``RECURSOS_RECEB_*`` blocks.
	enviados : list[InrRecursoEnviado]
		Resources sent; empty omits the ``RECURSOS_ENV_*`` blocks.
	"""

	recebidos: list[InrRecursoRecebido] = Field(default_factory=list)
	enviados: list[InrRecursoEnviado] = Field(default_factory=list)


class InrParticipante(_Strict):
	"""One ``PARTICIPANTE`` of Parte I.

	Attributes
	----------
	cod_partic : str
		Participant code ``AAAAA.BBBBBB.CCCCCC.T-DV``.
	entrada_saida : InrEntradaSaida
		Resources in and out.
	transf_recursos : InrTransfRecursos
		Transfers between modalities.
	recursos_mesmo_invest : InrRecursosEntreInvestidores or None
		Resources exchanged with the same investor; ``None`` omits the block.
	recursos_outro_invest : InrRecursosEntreInvestidores or None
		Resources exchanged with a different non-resident investor; ``None`` omits the block.
	patrim_liq : int
		Net equity, in reais.
	"""

	cod_partic: _CodPartic
	entrada_saida: InrEntradaSaida
	transf_recursos: InrTransfRecursos
	recursos_mesmo_invest: InrRecursosEntreInvestidores | None = None
	recursos_outro_invest: InrRecursosEntreInvestidores | None = None
	patrim_liq: _IntegerValue


@type_checker
def _check_participant(cod_partic: str, seen: set[str], cd_cvm: str) -> None:
	"""Require a participant code to be new and issued under the representative.

	Parameters
	----------
	cod_partic : str
		The participant code.
	seen : set[str]
		Codes already seen; this one is added.
	cd_cvm : str
		The header's representative CVM code.

	Raises
	------
	ValueError
		If the code repeats or its first segment differs from ``cd_cvm``.
	"""
	ensure(cod_partic not in seen, f"duplicate participant {cod_partic}")
	seen.add(cod_partic)
	ensure(
		cod_partic.split(".")[0] == cd_cvm,
		f"participant {cod_partic} is not under representative {cd_cvm}",
	)


class InrParte1Document(_Strict):
	"""A whole Parte I file.

	Attributes
	----------
	header : InrParte1Header
		File header.
	participantes : list[InrParticipante]
		1 to 1000 participants with distinct codes, all under the header's representative.
	"""

	header: InrParte1Header
	participantes: list[InrParticipante] = Field(min_length=1, max_length=_MAX_PARTICIPANTS)

	@model_validator(mode="after")
	def _check_participants(self) -> InrParte1Document:
		"""Require distinct participant codes issued under the header's representative.

		Returns
		-------
		InrParte1Document
			The validated document.

		Raises
		------
		ValueError
			If a code repeats or its first segment (representative) differs from ``cd_cvm``.
		"""
		seen: set[str] = set()
		for part in self.participantes:
			_check_participant(part.cod_partic, seen, self.header.cd_cvm)
		return self


# ---------------------------------------------------------------------------------------------
# Parte II (COD_DOC 70)
# ---------------------------------------------------------------------------------------------


class InrParte2Header(_Strict):
	"""``CAB_INFORM`` of Parte II.

	Attributes
	----------
	cod_doc : str
		Always ``"70"``.
	versao : str
		Always ``"1.0"``.
	dt_compt : str
		Competence, ``MM/AAAA``; the same for every participant of the file.
	dt_gerac_arq : str
		File generation date, ``DD/MM/AAAA``.
	"""

	cod_doc: Literal["70"] = "70"
	versao: Literal["1.0"] = "1.0"
	dt_compt: _Competence
	dt_gerac_arq: _DateBr


class InrPosFim(_Strict):
	"""``POS_FIM`` without notional (blocks whose types never carry one in the block).

	Attributes
	----------
	qtde_pos_fim : Decimal or None
		Final quantity; required or forbidden depending on the application type (Table A).
	merc_pos_fim : Decimal
		Market value of the final position, always required.
	"""

	qtde_pos_fim: _QuantityValue | None = None
	merc_pos_fim: _MoneyValue


class InrPosFimNocional(InrPosFim):
	"""``POS_FIM`` of the blocks that may carry ``NOCION_POS_FIM``.

	Attributes
	----------
	nocion_pos_fim : Decimal or None
		Final notional; required or forbidden depending on the application type (Table A).
	"""

	nocion_pos_fim: _MoneyValue | None = None


class InrClassifRisco(_Strict):
	"""``CLASSIF_RISCO``: risk rating of the issuer.

	Attributes
	----------
	ag_classif_risco : str
		Rating agency, up to 200 characters.
	dt_classif_risco : str
		Rating date, ``DD/MM/AAAA``.
	grau_classif_risco : str
		Rating grade, up to 6 characters.
	"""

	ag_classif_risco: Annotated[StrictStr, AfterValidator(text_field(200))]
	dt_classif_risco: _DateBr
	grau_classif_risco: Annotated[StrictStr, AfterValidator(text_field(6))]


class InrIndexador(_Strict):
	"""``TIT_POS_FIX_INDEX``: indexer of a post-fixed security.

	Attributes
	----------
	tit_pos_fix_cod_index : str
		Indexer code (Table D).
	tit_pos_fix_pr_index : Decimal
		Percentage of the indexer (102 for 102% of the CDI).
	tit_pos_fix_cupom : Decimal
		Coupon (zero when there is none; the spec makes the tag mandatory for post-fixed).
	"""

	tit_pos_fix_cod_index: _IndexerCode
	tit_pos_fix_pr_index: _RateValue
	tit_pos_fix_cupom: _RateValue


class InrEmissorPj(_Strict):
	"""``EMIS`` of ``DEP_PRAZO_TIT_IF``: a financial institution identified by CNPJ.

	Attributes
	----------
	cnpj_emis : str
		Issuer CNPJ; stored unmasked without leading zeros, as the spec asks.
	nm_emis : str
		Issuer name, up to 150 characters.
	"""

	cnpj_emis: _Cnpj
	nm_emis: _IssuerName


class InrEmissorPfPj(_Strict):
	"""``EMIS`` of the agribusiness / private-credit / uncoded blocks (PF or PJ).

	Attributes
	----------
	tp_pf_pj_emis : str
		``"PF"`` or ``"PJ"``.
	nr_pf_pj_emis : str
		CPF or CNPJ matching the type; stored unmasked without leading zeros.
	nm_emis : str
		Issuer name, up to 150 characters.
	"""

	tp_pf_pj_emis: Literal["PF", "PJ"]
	nr_pf_pj_emis: StrictStr
	nm_emis: _IssuerName

	@model_validator(mode="after")
	def _check_document(self) -> InrEmissorPfPj:
		"""Validate the document against the person type and normalise it.

		Returns
		-------
		InrEmissorPfPj
			The validated issuer.
		"""
		self.nr_pf_pj_emis = to_person_doc(self.tp_pf_pj_emis, self.nr_pf_pj_emis)
		return self


class _IndexedSecurity(_Strict):
	"""Shared post-fixed / pre-fixed rule of the two fixed-income blocks.

	Attributes
	----------
	st_tit_pos_fix : str
		``"S"`` when post-fixed, ``"N"`` when pre-fixed.
	tit_pos_fix_index : InrIndexador or None
		Required when post-fixed, forbidden when pre-fixed.
	tit_pre_fix_taxa_contr : Decimal or None
		Contracted rate; required when pre-fixed, forbidden when post-fixed.
	"""

	st_tit_pos_fix: _SimNao
	tit_pos_fix_index: InrIndexador | None = None
	tit_pre_fix_taxa_contr: _RateValue | None = None

	@model_validator(mode="after")
	def _check_indexation(self) -> _IndexedSecurity:
		"""Enforce the post-fixed / pre-fixed field exclusivity.

		Returns
		-------
		_IndexedSecurity
			The validated model.

		Raises
		------
		ValueError
			If the fields do not match ``st_tit_pos_fix``.
		"""
		post = self.st_tit_pos_fix == "S"
		ensure(
			post == (self.tit_pos_fix_index is not None),
			"tit_pos_fix_index is required if post-fixed and forbidden otherwise",
		)
		ensure(
			post != (self.tit_pre_fix_taxa_contr is not None),
			"tit_pre_fix_taxa_contr is required if pre-fixed and forbidden otherwise",
		)
		return self


@type_checker
def _check_rating(st_classif_risco: str, classif_risco: InrClassifRisco | None) -> None:
	"""Require the rating block exactly when the issuer is rated.

	Parameters
	----------
	st_classif_risco : str
		``"S"`` or ``"N"``.
	classif_risco : InrClassifRisco or None
		The rating block.

	Raises
	------
	ValueError
		If the block is missing for ``"S"`` or present for ``"N"``.
	"""
	if (st_classif_risco == "S") != (classif_risco is not None):
		raise ValueError("classif_risco is required if st_classif_risco is 'S' and omitted if 'N'")


@type_checker
def _check_flag(field: str, rule: str, present: bool, cod_tp_aplic: str) -> None:
	"""Require a Table A field to be present exactly when its rule says ``"S"``.

	Parameters
	----------
	field : str
		Field name for the error message.
	rule : str
		``"S"`` (required) or anything else (forbidden).
	present : bool
		Whether the field is informed.
	cod_tp_aplic : str
		The application type code.

	Raises
	------
	ValueError
		If presence does not match the rule.
	"""
	verb = {"S": "required"}.get(rule, "forbidden")
	ensure(
		(rule == "S") == present,
		f"{field} is {verb} for application type {cod_tp_aplic}",
	)


@type_checker
def _check_application(
	block: str, cod_tp_aplic: str, pos_fim: InrPosFim, *, notional_in_block: bool
) -> None:
	"""Apply the block table and Table A to one application.

	Parameters
	----------
	block : str
		The block tag.
	cod_tp_aplic : str
		The application type code.
	pos_fim : InrPosFim
		The final position.
	notional_in_block : bool
		Whether the block's ``POS_FIM`` can carry ``NOCION_POS_FIM``.

	Raises
	------
	ValueError
		If the type is not reportable in the block, or a quantity/notional field is present or
		missing against Table A.
	"""
	ensure(
		cod_tp_aplic in BLOCK_APPLICATIONS[block],
		f"application type {cod_tp_aplic} cannot be reported in {block}",
	)
	quantity_rule, notional_rule = APPLICATION_FIELD_RULES[cod_tp_aplic]
	_check_flag("qtde_pos_fim", quantity_rule, pos_fim.qtde_pos_fim is not None, cod_tp_aplic)
	if not notional_in_block:
		return
	has_notional = getattr(pos_fim, "nocion_pos_fim", None) is not None
	_check_flag("nocion_pos_fim", notional_rule, has_notional, cod_tp_aplic)


@type_checker
def _check_asset_type(cod_tp_aplic: str, cod_tp_ativ: str) -> None:
	"""Apply Table B: the asset type must be related to the application type.

	Parameters
	----------
	cod_tp_aplic : str
		The application type code.
	cod_tp_ativ : str
		The asset type code.

	Raises
	------
	ValueError
		If Table B does not relate the two.
	"""
	if cod_tp_ativ not in ASSET_TYPES_BY_APPLICATION[cod_tp_aplic]:
		raise ValueError(
			f"asset type {cod_tp_ativ} is not related to application type {cod_tp_aplic}"
		)


class InrTitPub(_Strict):
	"""``TIT_PUB``: SELIC public security (application 75 or 147).

	Attributes
	----------
	cod_selic : str
		SELIC code.
	dt_venc : str
		Maturity, ``DD/MM/AAAA``.
	cod_tp_aplic : str
		``"75"`` or ``"147"``.
	pos_fim : InrPosFim
		Final position (quantity and market value).
	"""

	cod_selic: _Code
	dt_venc: _DateBr
	cod_tp_aplic: Literal["75", "147"]
	pos_fim: InrPosFim

	@model_validator(mode="after")
	def _check(self) -> InrTitPub:
		"""Apply the block and Table A rules.

		Returns
		-------
		InrTitPub
			The validated block.
		"""
		_check_application("TIT_PUB", self.cod_tp_aplic, self.pos_fim, notional_in_block=False)
		return self


class InrCotas(_Strict):
	"""``COTAS``: fund shares (application 197, implicit in the XML).

	Attributes
	----------
	cnpj_fdo : str
		CNPJ of the invested fund; stored unmasked without leading zeros.
	pos_fim : InrPosFim
		Final position (quantity and market value).
	"""

	cnpj_fdo: _Cnpj
	pos_fim: InrPosFim

	@model_validator(mode="after")
	def _check(self) -> InrCotas:
		"""Apply the block and Table A rules.

		Returns
		-------
		InrCotas
			The validated block.
		"""
		_check_application("COTAS", "197", self.pos_fim, notional_in_block=False)
		return self


class InrSwap(_Strict):
	"""``SWAP``: swap differential (application 183 receivable or 184 payable).

	Attributes
	----------
	cod_swap : str
		``"SWP"`` followed by a Table E code (for example ``"SWPSAB"``).
	cod_tp_aplic : str
		``"183"`` or ``"184"``.
	pos_fim : InrPosFim
		Final position (market value only; the notional goes in ``NOCION_SWAP``).
	"""

	cod_swap: StrictStr
	cod_tp_aplic: Literal["183", "184"]
	pos_fim: InrPosFim

	@model_validator(mode="after")
	def _check(self) -> InrSwap:
		"""Apply the swap-code, block and Table A rules.

		Returns
		-------
		InrSwap
			The validated block.

		Raises
		------
		ValueError
			If ``cod_swap`` is not ``SWP`` + a Table E code.
		"""
		if not self.cod_swap.startswith(_SWAP_PREFIX):
			raise ValueError("cod_swap must start with 'SWP'")
		_require_member(self.cod_swap[len(_SWAP_PREFIX) :], SWAP_CODES, "Table E")
		_check_application("SWAP", self.cod_tp_aplic, self.pos_fim, notional_in_block=False)
		return self


class InrDemaisCodif(_Strict):
	"""``DEMAIS_CODIF``: other coded assets.

	Attributes
	----------
	cod_ativ : str
		Asset code from the CVM public asset registry.
	cod_tp_ativ : str
		Asset type (Table C), related to the application type by Table B.
	dt_ini_vigen : str
		Start of the asset's validity, ``DD/MM/AAAA``.
	cod_tp_aplic : str
		Application type reportable in this block.
	pos_fim : InrPosFimNocional
		Final position; the notional follows Table A.
	"""

	cod_ativ: _Code
	cod_tp_ativ: _AssetTypeCode
	dt_ini_vigen: _DateBr
	cod_tp_aplic: StrictStr
	pos_fim: InrPosFimNocional

	@model_validator(mode="after")
	def _check(self) -> InrDemaisCodif:
		"""Apply the block, Table A and Table B rules.

		Returns
		-------
		InrDemaisCodif
			The validated block.
		"""
		_check_application("DEMAIS_CODIF", self.cod_tp_aplic, self.pos_fim, notional_in_block=True)
		_check_asset_type(self.cod_tp_aplic, self.cod_tp_ativ)
		return self


class InrDepPrazoTitIf(_IndexedSecurity):
	"""``DEP_PRAZO_TIT_IF``: term deposits and other financial-institution paper (type 74).

	Attributes
	----------
	cod_tp_ativ : str
		Asset type, related to application 74 by Table B.
	emis : InrEmissorPj
		Issuer.
	dt_venc : str
		Maturity, ``DD/MM/AAAA``.
	st_classif_risco : str
		``"S"`` when the issuer is rated.
	classif_risco : InrClassifRisco or None
		Rating; required when ``st_classif_risco`` is ``"S"``.
	pos_fim : InrPosFim
		Final position (quantity and market value).
	"""

	cod_tp_ativ: _AssetTypeCode
	emis: InrEmissorPj
	dt_venc: _DateBr
	st_classif_risco: _SimNao
	classif_risco: InrClassifRisco | None = None
	pos_fim: InrPosFim

	@model_validator(mode="after")
	def _check(self) -> InrDepPrazoTitIf:
		"""Apply the rating, block, Table A and Table B rules.

		Returns
		-------
		InrDepPrazoTitIf
			The validated block.
		"""
		_check_rating(self.st_classif_risco, self.classif_risco)
		_check_application("DEP_PRAZO_TIT_IF", "74", self.pos_fim, notional_in_block=False)
		_check_asset_type("74", self.cod_tp_ativ)
		return self


class InrTitAgroCredPriv(_IndexedSecurity):
	"""``TIT_AGRO_CRED_PRIV``: agribusiness and private-credit securities.

	Attributes
	----------
	cod_tp_ativ : str
		Asset type, related to the application type by Table B.
	emis : InrEmissorPfPj
		Issuer.
	dt_venc : str
		Maturity, ``DD/MM/AAAA``.
	st_tit_reg_cetip : str
		``"S"`` when registered at CETIP.
	st_tit_garant_seguro : str
		``"S"`` when guaranteed or insured.
	cnpj_instit_financ : str or None
		CNPJ of the co-obligated financial institution, when there is one.
	cod_tp_aplic : str
		``"193"``, ``"195"`` or ``"196"``.
	pos_fim : InrPosFim
		Final position (quantity and market value).
	"""

	cod_tp_ativ: _AssetTypeCode
	emis: InrEmissorPfPj
	dt_venc: _DateBr
	st_tit_reg_cetip: _SimNao
	st_tit_garant_seguro: _SimNao
	cnpj_instit_financ: _Cnpj | None = None
	cod_tp_aplic: Literal["193", "195", "196"]
	pos_fim: InrPosFim

	@model_validator(mode="after")
	def _check(self) -> InrTitAgroCredPriv:
		"""Apply the block, Table A and Table B rules.

		Returns
		-------
		InrTitAgroCredPriv
			The validated block.
		"""
		_check_application(
			"TIT_AGRO_CRED_PRIV", self.cod_tp_aplic, self.pos_fim, notional_in_block=False
		)
		_check_asset_type(self.cod_tp_aplic, self.cod_tp_ativ)
		return self


class InrAtivoExterior(_Strict):
	"""``ATIVO_EXT``: description of the asset abroad.

	Attributes
	----------
	desc_at_ext : str
		Text, up to 50 characters.
	qtde_at_ext : int
		Quantity (integer).
	valor_at_ext : Decimal
		Value; the page gives no scale, so 2 places truncated are assumed.
	"""

	desc_at_ext: Annotated[StrictStr, AfterValidator(text_field(50))]
	qtde_at_ext: _IntegerValue
	valor_at_ext: _MoneyValue


class InrInvExt(_Strict):
	"""``INV_EXT``: investment abroad (application 189, implicit in the XML).

	Attributes
	----------
	cod_tp_ativ : str
		Asset type, related to application 189 by Table B.
	inv_coletivo : str
		``"S"`` when the asset is a collective investment vehicle.
	gest_inv_coletivo : str
		``"S"`` when the vehicle's management has direct or indirect local-manager influence.
	nm_emis : str
		Issuer name, up to 150 characters.
	dt_venc : str or None
		Maturity, if any.
	cod_pais : str
		Country code (Table G).
	cod_bv_merc : str
		Exchange or OTC market code (Table H).
	cod_ativo_bv_merc : str
		Trading code of the asset at that venue.
	st_classif_risco : str
		``"S"`` when the issuer is rated.
	classif_risco : InrClassifRisco or None
		Rating; required when ``st_classif_risco`` is ``"S"``.
	dt_aplic : str
		Date of the application, ``DD/MM/AAAA``.
	pos_fim : InrPosFim
		Final position (quantity and market value).
	ativo_ext : InrAtivoExterior or None
		Asset-abroad detail, when informed.
	"""

	cod_tp_ativ: _AssetTypeCode
	inv_coletivo: _SimNao
	gest_inv_coletivo: _SimNao
	nm_emis: _IssuerName
	dt_venc: _DateBr | None = None
	cod_pais: _CountryCode
	cod_bv_merc: _ExchangeCode
	cod_ativo_bv_merc: _Code
	st_classif_risco: _SimNao
	classif_risco: InrClassifRisco | None = None
	dt_aplic: _DateBr
	pos_fim: InrPosFim
	ativo_ext: InrAtivoExterior | None = None

	@model_validator(mode="after")
	def _check(self) -> InrInvExt:
		"""Apply the rating, block, Table A and Table B rules.

		Returns
		-------
		InrInvExt
			The validated block.
		"""
		_check_rating(self.st_classif_risco, self.classif_risco)
		_check_application("INV_EXT", "189", self.pos_fim, notional_in_block=False)
		_check_asset_type("189", self.cod_tp_ativ)
		return self


class InrDemaisNCodif(_Strict):
	"""``DEMAIS_N_CODIF``: other assets without a registry code.

	Attributes
	----------
	cod_tp_ativ : str
		Asset type, related to the application type by Table B.
	desc : str
		Asset description, up to 1000 characters.
	emis : InrEmissorPfPj
		Issuer.
	cod_tp_aplic : str
		Application type reportable in this block.
	pos_fim : InrPosFimNocional
		Final position; the notional follows Table A.
	"""

	cod_tp_ativ: _AssetTypeCode
	desc: _AssetDescription
	emis: InrEmissorPfPj
	cod_tp_aplic: StrictStr
	pos_fim: InrPosFimNocional

	@model_validator(mode="after")
	def _check(self) -> InrDemaisNCodif:
		"""Apply the block, Table A and Table B rules.

		Returns
		-------
		InrDemaisNCodif
			The validated block.
		"""
		_check_application(
			"DEMAIS_N_CODIF", self.cod_tp_aplic, self.pos_fim, notional_in_block=True
		)
		_check_asset_type(self.cod_tp_aplic, self.cod_tp_ativ)
		return self


class InrInform(_Strict):
	"""One ``INFORM`` of Parte II: the applications of one participant.

	The XML requires the asset blocks in a fixed order; the fields below are listed in that
	order and the writer emits them so. Each list may be empty (the block is then omitted) but
	at least one block must be informed.

	Attributes
	----------
	cod_partic : str
		Participant code ``AAAAA.BBBBBB.CCCCCC.T-DV``.
	tit_pub, cotas, swap : list
		First three blocks.
	nocion_swap : Decimal or None
		``NOCION_SWAP``; required when there is a ``swap`` block, forbidden otherwise.
	demais_codif, dep_prazo_tit_if, tit_agro_cred_priv, inv_ext, demais_n_codif : list
		Remaining blocks.
	"""

	cod_partic: _CodPartic
	tit_pub: list[InrTitPub] = Field(default_factory=list)
	cotas: list[InrCotas] = Field(default_factory=list)
	swap: list[InrSwap] = Field(default_factory=list)
	nocion_swap: _MoneyValue | None = None
	demais_codif: list[InrDemaisCodif] = Field(default_factory=list)
	dep_prazo_tit_if: list[InrDepPrazoTitIf] = Field(default_factory=list)
	tit_agro_cred_priv: list[InrTitAgroCredPriv] = Field(default_factory=list)
	inv_ext: list[InrInvExt] = Field(default_factory=list)
	demais_n_codif: list[InrDemaisNCodif] = Field(default_factory=list)

	@model_validator(mode="after")
	def _check(self) -> InrInform:
		"""Require one block at least, and ``NOCION_SWAP`` exactly when swaps are present.

		Returns
		-------
		InrInform
			The validated participant.

		Raises
		------
		ValueError
			If no block is informed or ``nocion_swap`` does not match the swap blocks.
		"""
		blocks = (
			self.tit_pub,
			self.cotas,
			self.swap,
			self.demais_codif,
			self.dep_prazo_tit_if,
			self.tit_agro_cred_priv,
			self.inv_ext,
			self.demais_n_codif,
		)
		ensure(any(blocks), "at least one asset block must be informed")
		ensure(
			bool(self.swap) == (self.nocion_swap is not None),
			"nocion_swap is required with swap blocks and forbidden without",
		)
		return self


class InrParte2Document(_Strict):
	"""A whole Parte II file.

	Attributes
	----------
	header : InrParte2Header
		File header.
	informs : list[InrInform]
		1 to 1000 participants with distinct codes.
	"""

	header: InrParte2Header
	informs: list[InrInform] = Field(min_length=1, max_length=_MAX_PARTICIPANTS)

	@model_validator(mode="after")
	def _check_participants(self) -> InrParte2Document:
		"""Require distinct participant codes.

		Returns
		-------
		InrParte2Document
			The validated document.

		Raises
		------
		ValueError
			If a participant code repeats.
		"""
		codes = [inform.cod_partic for inform in self.informs]
		if len(set(codes)) != len(codes):
			raise ValueError("duplicate participant code")
		return self
