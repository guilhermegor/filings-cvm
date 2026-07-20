"""CVM AGENTE_AUTON/CAD — legal-person (pessoa jurídica) autonomous-agent registry reader.

The ``cad_agente_auton_pj.csv`` member of ``cad_agente_auton.zip``: the registry of
autonomous-agent firms (masked CNPJ, corporate and commercial names, dates/reason/situation,
address, phone, e-mail, website). See ``_base_agente_auton_reader`` for the shared behaviour.
"""

from __future__ import annotations

from typing import ClassVar

from filings_cvm._internal.config.contracts import CAD_AGENTE_AUTON_PJ, FileContract
from filings_cvm.ingestion.agente_auton.cad._base_agente_auton_reader import _BaseAgenteAutonReader


class AgenteAutonPjReader(_BaseAgenteAutonReader):
	"""Read the AGENTE_AUTON/CAD *pessoa jurídica* registry into a typed DataFrame."""

	_MEMBER: ClassVar[str] = "cad_agente_auton_pj.csv"
	_CONTRACT: ClassVar[FileContract] = CAD_AGENTE_AUTON_PJ
	_DATE_COLS: ClassVar[tuple[str, ...]] = ("DT_REG", "DT_CANCEL", "DT_INI_SIT")
	_LABEL: ClassVar[str] = "pessoa jurídica"
