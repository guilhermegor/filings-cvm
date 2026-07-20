"""CVM AGENTE_FIDUC/CAD — legal-person (pessoa jurídica) fiduciary-agent registry reader.

The ``cad_agente_fiduc_pj.csv`` member of ``cad_agente_fiduc.zip``: the registry of
fiduciary-agent firms (masked CNPJ, corporate name, dates, address and phone). See
``_base_agente_fiduc_reader`` for the shared behaviour.
"""

from __future__ import annotations

from typing import ClassVar

from filings_cvm._internal.config.contracts import CAD_AGENTE_FIDUC_PJ, FileContract
from filings_cvm.ingestion.agente_fiduc.cad._base_agente_fiduc_reader import _BaseAgenteFiducReader


class AgenteFiducPjReader(_BaseAgenteFiducReader):
	"""Read the AGENTE_FIDUC/CAD *pessoa jurídica* registry into a typed DataFrame."""

	_MEMBER: ClassVar[str] = "cad_agente_fiduc_pj.csv"
	_CONTRACT: ClassVar[FileContract] = CAD_AGENTE_FIDUC_PJ
	_DATE_COLS: ClassVar[tuple[str, ...]] = ("DT_REG", "DT_CANCEL", "DT_INI_SIT")
	_LABEL: ClassVar[str] = "pessoa jurídica"
