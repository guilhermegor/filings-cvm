"""CVM CAD/FI histórico — exclusivo change-log reader.

The ``cad_fi_hist_exclusivo.csv`` member of ``cad_fi_hist.zip``: the history of each fund's
exclusive-fund status. See ``_base_cad_fi_hist_reader`` for shared
behaviour.
"""

from __future__ import annotations

from typing import ClassVar

from filings_cvm._internal.config.contracts import CAD_FI_HIST_EXCLUSIVO, FileContract
from filings_cvm.ingestion.fi.cad.cad_fi_hist._base_cad_fi_hist_reader import _BaseCadFiHistReader


class CadastroFiHistExclusivoReader(_BaseCadFiHistReader):
	"""Read the CAD/FI *exclusivo* change-log into a typed DataFrame."""

	_MEMBER: ClassVar[str] = "cad_fi_hist_exclusivo.csv"
	_CONTRACT: ClassVar[FileContract] = CAD_FI_HIST_EXCLUSIVO
	_DATE_COLS: ClassVar[tuple[str, ...]] = (
		"DT_REG",
		"DT_INI_ST_EXCLUSIVO",
		"DT_FIM_ST_EXCLUSIVO",
	)
	_LABEL: ClassVar[str] = "exclusivo"
