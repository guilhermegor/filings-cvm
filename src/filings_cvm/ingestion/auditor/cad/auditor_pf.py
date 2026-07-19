"""CVM AUDITOR/CAD — natural-person (pessoa física) auditor registry reader.

The ``cad_auditor_pf.csv`` member of ``cad_auditor.zip``: the registry of independent auditors who
are natural persons (CVM code, name, current situation). See ``_base_auditor_reader`` for the
shared behaviour.
"""

from __future__ import annotations

from typing import ClassVar

from filings_cvm._internal.config.contracts import CAD_AUDITOR_PF, FileContract
from filings_cvm.ingestion.auditor.cad._base_auditor_reader import _BaseAuditorReader


class AuditorPfReader(_BaseAuditorReader):
	"""Read the AUDITOR/CAD *pessoa física* registry into a typed DataFrame."""

	_MEMBER: ClassVar[str] = "cad_auditor_pf.csv"
	_CONTRACT: ClassVar[FileContract] = CAD_AUDITOR_PF
	_DATE_COLS: ClassVar[tuple[str, ...]] = ("DT_INI_SIT",)
	_LABEL: ClassVar[str] = "pessoa física"
