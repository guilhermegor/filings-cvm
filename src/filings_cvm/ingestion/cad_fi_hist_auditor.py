"""CVM CAD/FI histórico — auditor change-log reader.

The ``cad_fi_hist_auditor.csv`` member of ``cad_fi_hist.zip``: the history of each fund's
auditor. See :mod:`filings_cvm.ingestion._base_cad_fi_hist_reader` for the shared behaviour.
"""

from __future__ import annotations

from typing import ClassVar

from filings_cvm._internal.config.contracts import CAD_FI_HIST_AUDITOR, FileContract
from filings_cvm.ingestion._base_cad_fi_hist_reader import _BaseCadFiHistReader


class CadastroFiHistAuditorReader(_BaseCadFiHistReader):
	"""Read the CAD/FI *auditor* change-log into a typed DataFrame."""

	_MEMBER: ClassVar[str] = "cad_fi_hist_auditor.csv"
	_CONTRACT: ClassVar[FileContract] = CAD_FI_HIST_AUDITOR
	_DATE_COLS: ClassVar[tuple[str, ...]] = ("DT_REG", "DT_INI_AUDITOR", "DT_FIM_AUDITOR")
	_LABEL: ClassVar[str] = "auditor"
