"""CVM CAD/FI histórico — custodiante change-log reader.

The ``cad_fi_hist_custodiante.csv`` member of ``cad_fi_hist.zip``: the history of each fund's
custodiante. See ``_base_cad_fi_hist_reader`` for shared behaviour.
"""

from __future__ import annotations

from typing import ClassVar

from filings_cvm._internal.config.contracts import CAD_FI_HIST_CUSTODIANTE, FileContract
from filings_cvm.ingestion.fi.cad.cad_fi_hist._base_cad_fi_hist_reader import _BaseCadFiHistReader


class CadastroFiHistCustodianteReader(_BaseCadFiHistReader):
	"""Read the CAD/FI *custodiante* change-log into a typed DataFrame."""

	_MEMBER: ClassVar[str] = "cad_fi_hist_custodiante.csv"
	_CONTRACT: ClassVar[FileContract] = CAD_FI_HIST_CUSTODIANTE
	_DATE_COLS: ClassVar[tuple[str, ...]] = (
		"DT_REG",
		"DT_INI_CUSTODIANTE",
		"DT_FIM_CUSTODIANTE",
	)
	_LABEL: ClassVar[str] = "custodiante"
