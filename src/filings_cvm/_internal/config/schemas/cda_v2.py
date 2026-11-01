"""Pydantic models for the CVM CDA (Composição e Diversificação das Aplicações) XML — V2.

Direction-neutral schema mirroring the submission XML described at
https://cvmweb.cvm.gov.br/SWB/Sistemas/SCW/PadroesXML/PadraoXMLCDANet.aspx
(namespace ``urn:cda``, ``COD_DOC=3``, ``VERSAO=2.0``).

Reuses the V4 schema's scalar types (``Money``, ``Quantity``, ``BrDate`` ...), the
``EMIS`` block and the ``NEGOC`` block. What V2 changes, measured on the page: five repetition
blocks instead of eight, ``POS_FIM`` carries ``CUSTO_CORREC_POS_FIM`` (cost of the final
position), ``QTDE_DIAS_CONFID`` is mandatory, there is no ``EMPR_LIGADA`` and no
``COD_SUBCLASSE``, and Table A has its own matrix (Vendas / Aquisições / Posição Final with
Quant., Custo and Mercado) plus the related asset types per application type.
"""

from __future__ import annotations

from typing import Annotated, ClassVar, Literal

from pydantic import AfterValidator, BaseModel, ConfigDict, Field, model_validator

from filings_cvm._internal.config.schemas._fields import validated_cnpj
from filings_cvm._internal.config.schemas.cda import (
	_COMPT_RE,
	BrDate,
	CdaEmitter,
	Money,
	PatrimonyValue,
	Quantity,
	SignedMoney,
	Text,
	TradedQuantity,
)
from filings_cvm._internal.utils.typing import type_checker


# Table A: application type -> (sales, acquisitions, final quantity, cost) flags, with
# "S" required, "OP" optional, "N" forbidden. Market value is required for every type.
_STD = ("OP", "OP", "S", "S")
_NONE = ("N", "N", "N", "N")
_TABLE_A: dict[int, tuple[str, str, str, str]] = {
	**dict.fromkeys((37, 39, 40, 44, 45, 48, 74, 75, 92, 93, 148, 151), _STD),
	**dict.fromkeys((152, 153, 185, 187, 189, 190), _STD),
	42: ("N", "OP", "S", "S"),
	43: ("OP", "N", "S", "S"),
	**dict.fromkeys((91, 143, 146), ("N", "N", "S", "S")),
	**dict.fromkeys((94, 96, 97), _NONE),
	**dict.fromkeys((102, 103), ("OP", "OP", "S", "N")),
	147: ("N", "N", "N", "S"),
	**dict.fromkeys((183, 184), ("N", "N", "N", "OP")),
	186: ("N", "N", "S", "N"),
}
# Table A "Tipo de Ativos Relacionados": application type -> admissible COD_TP_ATIV.
_RELATED: dict[int, frozenset[int]] = {
	37: frozenset({1, 2, 13}),
	**dict.fromkeys((39, 40), frozenset({3, 4})),
	42: frozenset({5}),
	43: frozenset({5}),
	44: frozenset({7}),
	45: frozenset({6}),
	48: frozenset({10, 21, 23, 25, 999}),
	74: frozenset({10}),
	75: frozenset({8}),
	91: frozenset({1, 2, 6, 7}),
	**dict.fromkeys((92, 93, 190), frozenset({22})),
	**dict.fromkeys((94, 96, 97, 187), frozenset({999})),
	**dict.fromkeys((102, 103), frozenset({9})),
	**dict.fromkeys((143, 146), frozenset({1, 2})),
	147: frozenset({8, 10}),
	148: frozenset({6, 7, 8}),
	151: frozenset({11, 12, 16}),
	152: frozenset({14, 15, 17, 18, 19, 24}),
	153: frozenset({20}),
	**dict.fromkeys((183, 184), frozenset({26})),
	185: frozenset({10}),
	186: frozenset({1, 2, 13}),
	189: frozenset({10, 27}),
}
# Asset types the page lists for DEMAIS_CODIF (all but 8 Título Público, 22 Cotas, 26 SWAP).
_CODED_ASSETS = frozenset(range(1, 28)) - {8, 22, 26}
_BLOCK_EXCLUSIVE = {
	"TIT_PUB": frozenset({75}),
	"COTAS": frozenset({92, 93, 190}),
	"SWAP": frozenset({183, 184}),
}
# Blocks x application types: DEMAIS_CODIF takes any type that relates to a coded asset
# and has a block of its own nowhere else; DEMAIS_N_CODIF takes every Table A type.
_BLOCK_APLIC_TYPES: dict[str, frozenset[int]] = {
	**_BLOCK_EXCLUSIVE,
	"DEMAIS_CODIF": frozenset(
		code
		for code, assets in _RELATED.items()
		if assets & _CODED_ASSETS and code not in {75, 92, 93, 190, 183, 184}
	),
	"DEMAIS_N_CODIF": frozenset(_TABLE_A),
}


class _Strict(BaseModel):
	"""Base of every V2 model: an unknown or misspelled field is an error, not dropped."""

	model_config = ConfigDict(extra="forbid")


@type_checker
def _check_competence(value: str) -> str:
	"""Require MM/AAAA.

	Parameters
	----------
	value : str
		_Competence.

	Returns
	-------
	str
		The same value.

	Raises
	------
	ValueError
		If the format is not MM/AAAA.
	"""
	if not _COMPT_RE.fullmatch(value):
		raise ValueError("dt_compt must follow MM/AAAA format.")
	return value


_Competence = Annotated[str, AfterValidator(_check_competence)]


class CdaV2Header(_Strict):
	"""CAB_INFORM — document header (COD_DOC fixed at 3, VERSAO at 2.0)."""

	cod_doc: Literal[3] = 3
	versao: Literal["2.0"] = "2.0"
	dt_compt: _Competence
	dt_gerac_arq: BrDate


@type_checker
def _together(name: str, quantity: object, value: object) -> None:
	"""Require a quantity and its value to be both filled or both omitted.

	Parameters
	----------
	name : str
		Suffix of the pair, for the message.
	quantity : object
		The quantity (or ``None``).
	value : object
		The value (or ``None``).

	Raises
	------
	ValueError
		If only one of the pair is filled.
	"""
	if (quantity is None) != (value is None):
		raise ValueError(f"qtde_{name} and vl_{name} must be filled together")


class CdaV2Negoc(_Strict):
	"""NEGOC — month's trades; TP_NEGOC is always present, quantity and value come in pairs."""

	tp_negoc: Literal[1, 2]
	qtde_vendas_negoc: TradedQuantity | None = None
	vl_vendas_negoc: Money | None = None
	qtde_aquis_negoc: TradedQuantity | None = None
	vl_aquis_negoc: Money | None = None

	@model_validator(mode="after")
	def _pairs(self) -> CdaV2Negoc:
		"""Require quantity and value to be filled together for sales and acquisitions.

		Returns
		-------
		CdaV2Negoc
			The model.
		"""
		_together("vendas_negoc", self.qtde_vendas_negoc, self.vl_vendas_negoc)
		_together("aquis_negoc", self.qtde_aquis_negoc, self.vl_aquis_negoc)
		return self


class CdaV2SwapNegoc(_Strict):
	"""NEGOC of a SWAP: only the negotiation type."""

	tp_negoc: Literal[1, 2]


class CdaV2PosFim(_Strict):
	"""POS_FIM — final quantity, cost and market value (cost and quantity per Table A)."""

	qtde_pos_fim: Quantity | None = None
	custo_correc_pos_fim: SignedMoney | None = None
	merc_pos_fim: SignedMoney


class CdaV2SwapPosFim(_Strict):
	"""POS_FIM of a SWAP: cost (optional) and market value."""

	custo_correc_pos_fim: SignedMoney | None = None
	merc_pos_fim: SignedMoney


class CdaV2SwapAplic(_Strict):
	"""APLIC of a SWAP (183 or 184)."""

	cod_tp_aplic: Literal[183, 184]
	qtde_dias_confid: int = Field(ge=0, le=90)
	negoc: CdaV2SwapNegoc | None = None
	pos_fim: CdaV2SwapPosFim


_FLAG_OK = {"S": lambda filled: filled, "N": lambda filled: not filled, "OP": lambda _: True}
_FLAG_MESSAGE = {"S": "is required for", "N": "must not be filled for", "OP": "is allowed for"}


@type_checker
def _rule(code: int, what: str, flag: str, filled: bool) -> None:
	"""Check one Table A column against its S / OP / N flag.

	Parameters
	----------
	code : int
		Application type, for the message.
	what : str
		Column name, for the message.
	flag : str
		``S``, ``OP`` or ``N``.
	filled : bool
		Whether the field was supplied.

	Raises
	------
	ValueError
		On a violation.
	"""
	if not _FLAG_OK[flag](filled):
		raise ValueError(f"{what} {_FLAG_MESSAGE[flag]} COD_TP_APLIC {code}")


@type_checker
def _check_block(block: str, code: int) -> None:
	"""Require the application type to be one the block accepts.

	Parameters
	----------
	block : str
		Enclosing block tag.
	code : int
		Application type.

	Raises
	------
	ValueError
		If the block does not accept the type.
	"""
	if code not in _BLOCK_APLIC_TYPES[block]:
		raise ValueError(f"COD_TP_APLIC {code} is not allowed in {block}")


@type_checker
def _check_related(code: int, tp_ativ: int | None) -> None:
	"""Require the asset type to be one Table A relates to the application type.

	Parameters
	----------
	code : int
		Application type.
	tp_ativ : Optional[int]
		``COD_TP_ATIV`` of the enclosing block (``None`` when it has none).

	Raises
	------
	ValueError
		If the asset type is not related to the application type.
	"""
	if tp_ativ not in _RELATED[code] | {None}:
		raise ValueError(f"COD_TP_ATIV {tp_ativ} is not valid for COD_TP_APLIC {code}")


class CdaV2Aplic(_Strict):
	"""APLIC — application: confidentiality, negotiation and final position."""

	cod_tp_aplic: int
	qtde_dias_confid: int = Field(ge=0, le=90)
	negoc: CdaV2Negoc | None = None
	pos_fim: CdaV2PosFim

	def check_table_a(self, block: str, tp_ativ: int | None) -> None:
		"""Validate against the block, the Table A matrix and the related asset types.

		Parameters
		----------
		block : str
			Enclosing block tag.
		tp_ativ : Optional[int]
			``COD_TP_ATIV`` of the enclosing block, when it has one.

		Raises
		------
		ValueError
			On any rule violation.
		"""
		code = self.cod_tp_aplic
		_check_block(block, code)
		sales, acquisitions, quantity, cost = _TABLE_A[code]
		neg = self.negoc
		_rule(code, "vendas", sales, neg is not None and neg.qtde_vendas_negoc is not None)
		_rule(
			code, "aquisicoes", acquisitions, neg is not None and neg.qtde_aquis_negoc is not None
		)
		_rule(code, "posicao final", quantity, self.pos_fim.qtde_pos_fim is not None)
		_rule(code, "custo", cost, self.pos_fim.custo_correc_pos_fim is not None)
		_check_related(code, tp_ativ)


class CdaV2TitPub(_Strict):
	"""TIT_PUB — SELIC public security (type 75)."""

	cod_selic: Text
	dt_venc: BrDate
	aplic: CdaV2Aplic

	@model_validator(mode="after")
	def _rules(self) -> CdaV2TitPub:
		"""Apply block rules.

		Returns
		-------
		CdaV2TitPub
			The model.
		"""
		self.aplic.check_table_a("TIT_PUB", 8)
		return self


class CdaV2Cotas(_Strict):
	"""COTAS — fund shares (types 92, 93, 190)."""

	cnpj_fdo: str
	aplic: CdaV2Aplic

	@model_validator(mode="after")
	def _rules(self) -> CdaV2Cotas:
		"""Validate the CNPJ and apply block rules.

		Returns
		-------
		CdaV2Cotas
			The model.
		"""
		self.cnpj_fdo = validated_cnpj(self.cnpj_fdo)
		self.aplic.check_table_a("COTAS", 22)
		return self


class CdaV2Swap(_Strict):
	"""SWAP — swap differential (types 183, 184)."""

	cod_swap: str = Field(pattern=r"^SWP[A-Za-z0-9]{3}$")
	aplic: CdaV2SwapAplic


class CdaV2DemaisCodif(_Strict):
	"""DEMAIS_CODIF — other coded assets."""

	cod_ativ: Text
	cod_tp_ativ: int
	dt_ini_vigen: BrDate
	aplic: CdaV2Aplic

	@model_validator(mode="after")
	def _rules(self) -> CdaV2DemaisCodif:
		"""Apply block rules; the asset type must be one the page lists as coded.

		Returns
		-------
		CdaV2DemaisCodif
			The model.

		Raises
		------
		ValueError
			If the asset type is not a coded one.
		"""
		if self.cod_tp_ativ not in _CODED_ASSETS:
			raise ValueError(f"COD_TP_ATIV {self.cod_tp_ativ} is not a coded asset type")
		self.aplic.check_table_a("DEMAIS_CODIF", self.cod_tp_ativ)
		return self


class CdaV2DemaisNCodif(_Strict):
	"""DEMAIS_N_CODIF — other, uncoded assets."""

	cod_tp_ativ: int
	desc: Text = Field(max_length=1000)
	emis: CdaEmitter
	aplic: CdaV2Aplic

	@model_validator(mode="after")
	def _rules(self) -> CdaV2DemaisNCodif:
		"""Apply block rules.

		Returns
		-------
		CdaV2DemaisNCodif
			The model.
		"""
		self.aplic.check_table_a("DEMAIS_N_CODIF", self.cod_tp_ativ)
		return self


class CdaV2Inform(_Strict):
	"""INFORM — one fund/class. Block lists are emitted in the page's mandated order."""

	BLOCK_ORDER: ClassVar[tuple[str, ...]] = (
		"tit_pub",
		"cotas",
		"swap",
		"demais_codif",
		"demais_n_codif",
	)

	cnpj_fdo: str
	vl_pl: PatrimonyValue
	tit_pub: list[CdaV2TitPub] = Field(default_factory=list)
	cotas: list[CdaV2Cotas] = Field(default_factory=list)
	swap: list[CdaV2Swap] = Field(default_factory=list)
	demais_codif: list[CdaV2DemaisCodif] = Field(default_factory=list)
	demais_n_codif: list[CdaV2DemaisNCodif] = Field(default_factory=list)

	@model_validator(mode="after")
	def _cnpj(self) -> CdaV2Inform:
		"""Validate the CNPJ.

		Returns
		-------
		CdaV2Inform
			The model, with a bare CNPJ.
		"""
		self.cnpj_fdo = validated_cnpj(self.cnpj_fdo)
		return self


class CdaV2Document(_Strict):
	"""DOC_ARQ — complete CDA V2 file (at most 50 funds, one competence)."""

	header: CdaV2Header
	informs: list[CdaV2Inform] = Field(max_length=50)
