"""CVM AUDITOR/CAD — legal-person (pessoa jurídica) auditor registry reader.

The ``cad_auditor_pj.csv`` member of ``cad_auditor.zip``: the registry of audit firms (CVM code,
masked CNPJ, corporate name, situation and address). See ``_base_auditor_reader`` for the shared
behaviour.
"""

from __future__ import annotations

from typing import ClassVar

from filings_cvm._internal.config.contracts import CAD_AUDITOR_PJ, FileContract
from filings_cvm.ingestion.auditor.cad._base_auditor_reader import _BaseAuditorReader


class AuditorPjReader(_BaseAuditorReader):
	"""Read the AUDITOR/CAD *pessoa jurídica* registry into a typed DataFrame."""

	_MEMBER: ClassVar[str] = "cad_auditor_pj.csv"
	_CONTRACT: ClassVar[FileContract] = CAD_AUDITOR_PJ
	_DATE_COLS: ClassVar[tuple[str, ...]] = ("DT_INI_SIT",)
	_LABEL: ClassVar[str] = "pessoa jurídica"
