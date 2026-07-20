"""CVM AGENTE_AUTON/CAD — natural-person (pessoa física) autonomous-agent registry reader.

The ``cad_agente_auton_pf.csv`` member of ``cad_agente_auton.zip``: the registry of autonomous
investment agents who are natural persons (name, registration/cancellation dates and reason,
situation). See ``_base_agente_auton_reader`` for the shared behaviour.
"""

from __future__ import annotations

from typing import ClassVar

from filings_cvm._internal.config.contracts import CAD_AGENTE_AUTON_PF, FileContract
from filings_cvm.ingestion.agente_auton.cad._base_agente_auton_reader import _BaseAgenteAutonReader


class AgenteAutonPfReader(_BaseAgenteAutonReader):
	"""Read the AGENTE_AUTON/CAD *pessoa física* registry into a typed DataFrame."""

	_MEMBER: ClassVar[str] = "cad_agente_auton_pf.csv"
	_CONTRACT: ClassVar[FileContract] = CAD_AGENTE_AUTON_PF
	_DATE_COLS: ClassVar[tuple[str, ...]] = ("DT_REG", "DT_CANCEL", "DT_INI_SIT")
	_LABEL: ClassVar[str] = "pessoa física"
