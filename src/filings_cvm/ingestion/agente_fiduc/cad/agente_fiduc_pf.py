"""CVM AGENTE_FIDUC/CAD — natural-person (pessoa física) fiduciary-agent registry reader.

The ``cad_agente_fiduc_pf.csv`` member of ``cad_agente_fiduc.zip``: the registry of fiduciary
agents who are natural persons (name, registration/cancellation/situation dates). See
``_base_agente_fiduc_reader`` for the shared behaviour.
"""

from __future__ import annotations

from typing import ClassVar

from filings_cvm._internal.config.contracts import CAD_AGENTE_FIDUC_PF, FileContract
from filings_cvm.ingestion.agente_fiduc.cad._base_agente_fiduc_reader import _BaseAgenteFiducReader


class AgenteFiducPfReader(_BaseAgenteFiducReader):
	"""Read the AGENTE_FIDUC/CAD *pessoa física* registry into a typed DataFrame."""

	_MEMBER: ClassVar[str] = "cad_agente_fiduc_pf.csv"
	_CONTRACT: ClassVar[FileContract] = CAD_AGENTE_FIDUC_PF
	_DATE_COLS: ClassVar[tuple[str, ...]] = ("DT_REG", "DT_CANCEL", "DT_INI_SIT")
	_LABEL: ClassVar[str] = "pessoa física"
