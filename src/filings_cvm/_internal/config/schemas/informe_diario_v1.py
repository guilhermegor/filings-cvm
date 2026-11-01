"""Pydantic models for the CVM Daily Report (Informe Diário) XML standard — V1.

V1 is the original ``PadraoXMLInfoDiarioNet`` layout, valid until 2012-07-01
(https://cvmweb.cvm.gov.br/SWB/Sistemas/SCW/PadroesXML/PadraoXMLInfoDiarioNet.asp).
Measured against the V4 schema, the page differs as follows:

* ``CAB_INFORM`` has no ``VERSAO`` tag — only ``COD_DOC`` (``1``), ``DT_COMPT`` and
  ``DT_GERAC_ARQ``.
* ``INFORM`` is keyed by ``CNPJ_FDO`` alone (no ``COD_SUBCLASSE``) and has no
  ``DATA_PROX_PL``, ``VL_TOTAL_SAI`` or ``VL_TOTAL_ATV``.
* The tag order is ``CNPJ_FDO, VL_TOTAL, VL_QUOTA, PATRIM_LIQ, CAPTC_DIA, RESG_DIA,
  NR_COTST, LISTA_COTST_SIGNIF``.

The decimal scales (2 places for money, up to 12 for ``VL_QUOTA``, up to 4 for
``PR_COTST``) and the ``COTST_SIGNIF`` block are identical to V4, so those pieces are
imported from the V4 schema rather than redeclared.
"""

from __future__ import annotations

from pydantic import BaseModel, Field, field_validator

from filings_cvm._internal.config.schemas._fields import validated_cnpj
from filings_cvm._internal.config.schemas.informe_diario import (
	QuotaValueField,
	SignificantShareholder,
	TwoDecimalField,
)
from filings_cvm._internal.utils.xml_fields import parse_br_date


class InformeDiarioV1Header(BaseModel):
	"""CAB_INFORM — document-level header block (no VERSAO tag in V1)."""

	cod_doc: int = 1
	dt_compt: str
	dt_gerac_arq: str

	@field_validator("cod_doc")
	@classmethod
	def _check_cod_doc(cls, v: int) -> int:
		"""Require the Informe Diário document code, which the page fixes at ``1``.

		Parameters
		----------
		v : int
			Value to validate.

		Returns
		-------
		int
			Validated value.

		Raises
		------
		ValueError
			If the code is not ``1``.
		"""
		if v != 1:
			raise ValueError("cod_doc must be 1 for the Informe Diário.")
		return v

	@field_validator("dt_compt", "dt_gerac_arq")
	@classmethod
	def _check_br_date(cls, v: str) -> str:
		"""Validate a date field is a real DD/MM/AAAA calendar date.

		Parameters
		----------
		v : str
			Value to validate.

		Returns
		-------
		str
			Validated value.
		"""
		parse_br_date(v)
		return v


class InformeDiarioV1Inform(BaseModel):
	"""INFORM — one fund's daily movement, keyed by CNPJ_FDO."""

	cnpj_fdo: str
	vl_total: TwoDecimalField
	vl_quota: QuotaValueField
	patrim_liq: TwoDecimalField
	captc_dia: TwoDecimalField
	resg_dia: TwoDecimalField
	nr_cotst: int = Field(ge=0)
	lista_cotst_signif: list[SignificantShareholder] | None = None

	@field_validator("cnpj_fdo")
	@classmethod
	def _check_cnpj(cls, v: str) -> str:
		"""Validate and normalise the fund CNPJ (check-digit aware).

		Parameters
		----------
		v : str
			The fund CNPJ in any shape.

		Returns
		-------
		str
			The unmasked (bare) CNPJ.
		"""
		return validated_cnpj(v)


class InformeDiarioV1Document(BaseModel):
	"""DOC_ARQ — complete CVM Daily Report V1 XML document (up to 100 funds)."""

	header: InformeDiarioV1Header
	informs: list[InformeDiarioV1Inform] = Field(min_length=1, max_length=100)
