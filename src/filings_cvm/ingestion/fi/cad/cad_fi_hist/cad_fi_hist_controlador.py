"""CVM CAD/FI histórico — controlador change-log reader.

The ``cad_fi_hist_controlador.csv`` member of ``cad_fi_hist.zip``: the history of each fund's
controlador. See ``_base_cad_fi_hist_reader`` for shared behaviour.
"""

from __future__ import annotations

from typing import ClassVar

from filings_cvm._internal.config.contracts import CAD_FI_HIST_CONTROLADOR, FileContract
from filings_cvm.ingestion.fi.cad.cad_fi_hist._base_cad_fi_hist_reader import _BaseCadFiHistReader


class CadastroFiHistControladorReader(_BaseCadFiHistReader):
	"""Read the CAD/FI *controlador* change-log into a typed DataFrame."""

	_MEMBER: ClassVar[str] = "cad_fi_hist_controlador.csv"
	_CONTRACT: ClassVar[FileContract] = CAD_FI_HIST_CONTROLADOR
	_DATE_COLS: ClassVar[tuple[str, ...]] = (
		"DT_REG",
		"DT_INI_CONTROLADOR",
		"DT_FIM_CONTROLADOR",
	)
	_LABEL: ClassVar[str] = "controlador"
