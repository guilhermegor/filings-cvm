"""Pydantic models for the CVM Daily Report (Informe Diário) XML standard — V3.

V3 (valid from 2015-10-01, ICVM 555/512) is described by the CVM page
(https://cvmweb.cvm.gov.br/SWB/Sistemas/SCW/PadroesXML/PadraoXMLInfoDiarioNetV3.asp).
Measured against the V4 schema in :mod:`filings_cvm._internal.config.schemas.informe_diario`
the page differs in exactly two ways:

* ``VERSAO`` is ``3.0`` (``COD_DOC`` stays ``1``, namespace ``urn:infdiario``).
* The fund is identified **only** by ``CNPJ_FDO``; ``COD_SUBCLASSE`` does not exist in V3.

Every other block (tag order, decimal scales, ``COTST_SIGNIF``) is identical, so the V3
models extend the V4 ones rather than copying them.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, field_validator

from filings_cvm._internal.config.schemas.informe_diario import (
	InformeDiarioDocument,
	InformeDiarioHeader,
	InformeDiarioInform,
)


class InformeDiarioV3Header(InformeDiarioHeader, BaseModel):
	"""CAB_INFORM — V3 header; ``VERSAO`` is pinned to ``3.0`` and ``COD_DOC`` to ``1``."""

	versao: Literal["3.0"] = "3.0"
	cod_doc: Literal[1] = 1


class InformeDiarioV3Inform(InformeDiarioInform, BaseModel):
	"""INFORM — V3 fund block, keyed by ``CNPJ_FDO`` only (no ``COD_SUBCLASSE``)."""

	cnpj_fdo: str

	@field_validator("cod_subclasse")
	@classmethod
	def _reject_subclasse(cls, v: str | None) -> str | None:
		"""Reject ``COD_SUBCLASSE``, which the V3 standard does not define.

		Parameters
		----------
		v : Optional[str]
			The subclass code, which must be absent.

		Returns
		-------
		Optional[str]
			``None``.

		Raises
		------
		ValueError
			If a subclass code is given.
		"""
		if v is not None:
			raise ValueError("cod_subclasse does not exist in Informe Diário V3")
		return v


class InformeDiarioV3Document(InformeDiarioDocument, BaseModel):
	"""DOC_ARQ — complete V3 document (up to 100 funds).

	``informs`` deliberately narrows the V4 element type (V3 informs never carry a
	subclass), hence the invariance ``type: ignore`` below.
	"""

	header: InformeDiarioV3Header
	informs: list[InformeDiarioV3Inform] = Field(max_length=100)  # type: ignore[assignment]
