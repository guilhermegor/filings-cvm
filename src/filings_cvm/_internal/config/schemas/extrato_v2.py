"""Pydantic models for the CVM Extrato das Informações sobre o Fundo XML standard — V2.

Direction-neutral schema for ``PadraoXMLInfExtratoV2.asp``
(https://cvmweb.cvm.gov.br/SWB/Sistemas/SCW/PadroesXML/PadraoXMLInfExtratoV2.asp).

Measured against the page (2026-10-31): V2 and V3 share the same sample file tag for tag and in
the same order; only ``VERSAO`` (``2.0`` here, ``3.0`` there) differs structurally. The V3
``ExtratoRow`` (and its blocks) is therefore reused through import, not copied; only the header,
which pins ``VERSAO``, and the document that carries it are declared here.
"""

from __future__ import annotations

from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field

from filings_cvm._internal.config.schemas.extrato import DateField, ExtratoRow


_MAX_ROWS = 1000


class ExtratoV2Header(BaseModel):
	"""CAB_INFORM — V2 document header (``COD_DOC`` 41, ``VERSAO`` 2.0)."""

	model_config = ConfigDict(extra="forbid", frozen=True)

	cod_doc: Literal[41] = 41
	versao: Literal["2.0"] = "2.0"
	dt_gerac_arq: DateField


class ExtratoV2Document(BaseModel):
	"""DOC_ARQ — a whole Extrato V2 file: one header and one row per fund."""

	model_config = ConfigDict(extra="forbid", frozen=True)

	header: ExtratoV2Header
	rows: Annotated[list[ExtratoRow], Field(min_length=1, max_length=_MAX_ROWS)]
