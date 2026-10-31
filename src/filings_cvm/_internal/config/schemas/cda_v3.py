"""Pydantic models for the CVM CDA XML — V3.

Delta over the V4 schema (:mod:`filings_cvm._internal.config.schemas.cda`), measured on
https://cvmweb.cvm.gov.br/SWB/Sistemas/SCW/PadroesXML/PadraoXMLCDANetV3.aspx (namespace
``urn:cda``, ``COD_DOC=3``, ``VERSAO=3.0``). Everything V3 shares with V4 (scales, Tables A-D
and F, block x application-type map, TIT_PUB, SWAP, DEMAIS_*, TIT_AGRO_CRED_PRIV) is imported,
not copied. What differs on the V3 page:

* ``VERSAO`` is ``3.0`` and a file holds at most 50 funds (V4: 1000).
* ``COTAS`` carries only ``CNPJ_FDO`` (no subclass code).
* ``DEP_PRAZO_TIT_IF`` has no ``DESC_ATIV_VINC``.
* ``INV_EXT`` has no ``INV_COLETIVO`` / ``GEST_INV_COLETIVO`` and its ``APLIC`` no ``ATIVO_EXT``.
"""

from __future__ import annotations

from typing import Annotated, Literal

from pydantic import BaseModel, Field, model_validator

from filings_cvm._internal.config.schemas.cda import (
	BrDate,
	CdaAplic,
	CdaCotas,
	CdaDepPrazoTitIf,
	CdaDocument,
	CdaHeader,
	CdaInform,
	CdaRiskRating,
	Text,
	_check_aplic,
	_check_rating,
)


# ponytail: V3 models subclass the V4 ones; ``BaseModel`` is repeated as a base only because
# bin/check_schemas.py resolves bases within one file (its documented limit).
class CdaV3Header(CdaHeader, BaseModel):
	"""CAB_INFORM — document header (COD_DOC fixed at 3, VERSAO at 3.0)."""

	versao: Literal["3.0"] = "3.0"  # type: ignore[assignment]


class CdaV3Cotas(CdaCotas, BaseModel):
	"""COTAS — V3 identifies the invested fund by ``CNPJ_FDO`` only."""

	@model_validator(mode="after")
	def _no_subclass(self) -> CdaV3Cotas:
		"""Reject the V4-only subclass code.

		Returns
		-------
		CdaV3Cotas
			The model.

		Raises
		------
		ValueError
			If ``cod_subclasse`` is set.
		"""
		if self.cod_subclasse is not None:
			raise ValueError("cod_subclasse does not exist in CDA V3; use cnpj_fdo")
		return self


class CdaV3DepPrazoTitIf(CdaDepPrazoTitIf, BaseModel):
	"""DEP_PRAZO_TIT_IF — V3 has no ``DESC_ATIV_VINC``."""

	@model_validator(mode="after")
	def _no_desc_ativ_vinc(self) -> CdaV3DepPrazoTitIf:
		"""Reject the V4-only linked-asset description.

		Returns
		-------
		CdaV3DepPrazoTitIf
			The model.

		Raises
		------
		ValueError
			If ``desc_ativ_vinc`` is set.
		"""
		if self.desc_ativ_vinc is not None:
			raise ValueError("desc_ativ_vinc does not exist in CDA V3")
		return self


class CdaV3InvExt(BaseModel):
	"""INV_EXT — foreign investment (189), V3 layout (no collective-investment flags)."""

	cod_tp_ativ: int
	nm_emis: Annotated[Text, Field(max_length=150)]
	dt_venc: BrDate | None = None
	cod_pais: int
	cod_bv_merc: Text
	cod_ativo_bv_merc: Text
	st_classif_risco: Literal["S", "N"]
	classif_risco: CdaRiskRating | None = None
	aplic: CdaAplic

	@model_validator(mode="after")
	def _rules(self) -> CdaV3InvExt:
		"""Apply block rules; V3 has no ATIVO_EXT.

		Returns
		-------
		CdaV3InvExt
			The model.

		Raises
		------
		ValueError
			If ``aplic.ativo_ext`` is set.
		"""
		if self.aplic.ativo_ext is not None:
			raise ValueError("ativo_ext does not exist in CDA V3")
		_check_rating(self.st_classif_risco, self.classif_risco)
		_check_aplic("INV_EXT", self.aplic, 189, self.cod_tp_ativ)
		return self


class CdaV3Inform(CdaInform, BaseModel):
	"""INFORM — one fund/class, with the V3 block models."""

	cotas: list[CdaV3Cotas] = Field(default_factory=list)  # type: ignore[assignment]
	dep_prazo_tit_if: list[CdaV3DepPrazoTitIf] = Field(default_factory=list)  # type: ignore[assignment]
	inv_ext: list[CdaV3InvExt] = Field(default_factory=list)  # type: ignore[assignment]


class CdaV3Document(CdaDocument, BaseModel):
	"""DOC_ARQ — complete CDA V3 file (at most 50 funds, one competence)."""

	header: CdaV3Header
	informs: list[CdaV3Inform] = Field(max_length=50)  # type: ignore[assignment]
