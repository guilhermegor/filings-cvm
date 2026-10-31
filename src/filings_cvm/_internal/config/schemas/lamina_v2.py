"""Pydantic models for the CVM Lâmina de Fundos XML standard — V2.

Direction-neutral schema for ``PadraoXMLLaminaV2.asp``
(https://cvmweb.cvm.gov.br/SWB/Sistemas/SCW/PadroesXML/PadraoXMLLaminaV2.asp).

Measured against the V3 page (2026-10-31): the two standards have the same tag set in the same
order, and every field description is identical except three. V2 has no ``COD_SUBCLASSE`` (the
subclass identifier arrived with V3), its ``CNPJ_FUNDO`` is always the fund's CNPJ, and
``VERSAO`` is ``2.0``. So every block is **reused from** :mod:`filings_cvm._internal.config.
schemas.lamina`; only the header, the ``INFORM`` and the document are specialised here, and
the field order (the XML order) is inherited, since an overridden field keeps its position.
The redundant ``BaseModel`` base satisfies ``bin/check_schemas.py``, which reads local bases only.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from filings_cvm._internal.config.schemas.lamina import (
	_MAX_INFORMS,
	CnpjField,
	LaminaDocument,
	LaminaHeader,
	LaminaInform,
)


class LaminaV2Header(LaminaHeader, BaseModel):
	"""CAB_INFORM — document header of the V2 standard (``VERSAO`` is ``2.0``)."""

	versao: Literal["2.0"] = "2.0"  # type: ignore[assignment]


class LaminaV2Inform(LaminaInform, BaseModel):
	"""INFORM — the fact sheet of one fund; V2 identifies it by CNPJ only."""

	cnpj_fundo: CnpjField
	cod_subclasse: None = None


class LaminaV2Document(LaminaDocument, BaseModel):
	"""DOC_ARQ — a whole V2 Lâmina file: one competence, 1 to 70 funds."""

	header: LaminaV2Header
	informs: list[LaminaV2Inform] = Field(min_length=1, max_length=_MAX_INFORMS)  # type: ignore[assignment]
