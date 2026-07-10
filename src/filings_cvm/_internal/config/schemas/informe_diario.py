"""Pydantic models for the CVM Daily Report (Informe Diário) XML standard — V4.

This is the *shared schema* — the direction-neutral contract for one CVM XML
standard. The ``submission`` section builds these models and serialises them to
XML; the future ``ingestion`` section will parse CVM XML back into them. It ships
inside the wheel under ``_internal`` but is **not** part of the public API on its
own — the ``submission``/``ingestion`` packages re-export the names consumers need.

Per-field decimal scales mirror the CVM XML standard ``PadrãoXMLInfoDiarioNet`` (V4,
https://cvmweb.cvm.gov.br/SWB/Sistemas/SCW/PadroesXML/PadraoXMLInfoDiarioNetV4.asp).
The standard states monetary fields as "decimal com N casas"; ``VL_QUOTA`` allows up
to 12 and ``PR_COTST`` up to 4. Values carrying more decimal places than the standard
permits are truncated toward zero (``ROUND_DOWN``), never rounded, so a reported value
is never inflated past what the standard allows.

Each ``INFORM`` block identifies its fund by **exactly one** of ``CNPJ_FDO`` (fund
class) or ``COD_SUBCLASSE`` (subclass), as the standard requires. CNPJ/CPF fields are
validated with this library's own check-digit validators and stored bare/unmasked.
"""

from __future__ import annotations

from decimal import Decimal
import re
from typing import Annotated, Literal

from pydantic import (
	BaseModel,
	BeforeValidator,
	Field,
	ValidationInfo,
	field_validator,
	model_validator,
)

from filings_cvm._internal.config.schemas._fields import (
	truncate_to_scale,
	validate_person_doc,
	validated_cnpj,
)


# Brazilian full-date format used by every date field in this standard.
_DATE_BR_RE = re.compile(r"^\d{2}/\d{2}/\d{4}$")

# Decimal field types with the scale pinned to the CVM Informe Diário standard.
# Monetary values: "decimal com 2 casas".
TwoDecimalField = Annotated[
	Decimal, BeforeValidator(truncate_to_scale(2)), Field(decimal_places=2)
]
# VL_QUOTA: "decimal com até 12 casas".
QuotaValueField = Annotated[
	Decimal, BeforeValidator(truncate_to_scale(12)), Field(decimal_places=12)
]
# PR_COTST: shareholder participation percentage, "decimal com até 4 casas".
ParticipationField = Annotated[
	Decimal,
	BeforeValidator(truncate_to_scale(4)),
	Field(ge=Decimal("0"), le=Decimal("100"), decimal_places=4),
]


class InformeDiarioHeader(BaseModel):
	"""CAB_INFORM — document-level header block."""

	cod_doc: int = 1
	dt_compt: str
	dt_gerac_arq: str
	versao: str = "4.0"

	@field_validator("dt_compt", "dt_gerac_arq")
	@classmethod
	def _check_br_date(cls, v: str) -> str:
		"""Validate a date field follows the DD/MM/AAAA format.

		Parameters
		----------
		v : str
			Value to validate.

		Returns
		-------
		str
			Validated value.

		Raises
		------
		ValueError
			If value does not follow DD/MM/AAAA format.
		"""
		if not _DATE_BR_RE.match(v):
			raise ValueError("date must follow DD/MM/AAAA format.")
		return v


class SignificantShareholder(BaseModel):
	"""COTST_SIGNIF — one shareholder holding 20% or more of the fund's net worth."""

	tp_pessoa: Literal["PF", "PJ"]
	cpf_cnpj_cotst: str
	pr_cotst: ParticipationField

	@field_validator("cpf_cnpj_cotst")
	@classmethod
	def _check_cotst_doc(cls, v: str, info: ValidationInfo) -> str:
		"""Validate and normalise the shareholder document against its person type.

		Parameters
		----------
		v : str
			The shareholder document (CPF or CNPJ) in any shape.
		info : ValidationInfo
			Validation context; ``tp_pessoa`` (declared first) is read from it.

		Returns
		-------
		str
			The document in bare, unmasked form.

		Raises
		------
		ValueError
			If the document is not a valid CPF (PF) or CNPJ (PJ).
		"""
		return validate_person_doc(info.data.get("tp_pessoa", ""), v)


class InformeDiarioInform(BaseModel):
	"""INFORM — one fund's daily movement, keyed by CNPJ_FDO xor COD_SUBCLASSE."""

	cnpj_fdo: str | None = None
	cod_subclasse: str | None = None
	data_prox_pl: str
	vl_total: TwoDecimalField
	vl_quota: QuotaValueField
	patrim_liq: TwoDecimalField
	captc_dia: TwoDecimalField
	resg_dia: TwoDecimalField
	vl_total_sai: TwoDecimalField
	vl_total_atv: TwoDecimalField
	nr_cotst: int = Field(ge=0)
	lista_cotst_signif: list[SignificantShareholder] | None = None

	@field_validator("data_prox_pl")
	@classmethod
	def _check_data_prox_pl(cls, v: str) -> str:
		"""Validate the next-PL date follows the DD/MM/AAAA format.

		Parameters
		----------
		v : str
			Value to validate.

		Returns
		-------
		str
			Validated value.

		Raises
		------
		ValueError
			If value does not follow DD/MM/AAAA format.
		"""
		if not _DATE_BR_RE.match(v):
			raise ValueError("data_prox_pl must follow DD/MM/AAAA format.")
		return v

	@field_validator("cnpj_fdo")
	@classmethod
	def _check_cnpj(cls, v: str | None) -> str | None:
		"""Validate and normalise the fund-class CNPJ when present (check-digit aware).

		Parameters
		----------
		v : Optional[str]
			The fund-class CNPJ, or ``None`` when the informe is for a subclass.

		Returns
		-------
		Optional[str]
			The unmasked (bare) CNPJ, or ``None``.

		Raises
		------
		ValueError
			If a value is given that is not a valid CNPJ.
		"""
		if v is None:
			return None
		return validated_cnpj(v)

	@model_validator(mode="after")
	def _check_fund_identifier(self) -> InformeDiarioInform:
		"""Require exactly one fund identifier — CNPJ_FDO xor COD_SUBCLASSE.

		Returns
		-------
		InformeDiarioInform
			The validated model.

		Raises
		------
		ValueError
			If both identifiers are set or neither is.
		"""
		has_cnpj = self.cnpj_fdo is not None
		has_subclasse = self.cod_subclasse is not None
		if has_cnpj == has_subclasse:
			raise ValueError("provide exactly one of cnpj_fdo or cod_subclasse")
		return self


class InformeDiarioDocument(BaseModel):
	"""DOC_ARQ — complete CVM Daily Report XML document (up to 100 funds)."""

	header: InformeDiarioHeader
	informs: list[InformeDiarioInform] = Field(max_length=100)
