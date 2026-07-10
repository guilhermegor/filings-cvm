"""CVM CAD/FI histórico — condomínio change-log reader.

The ``cad_fi_hist_condom.csv`` member of ``cad_fi_hist.zip``: the history of each fund's
condomínio type. See ``_base_cad_fi_hist_reader`` for shared behaviour.
"""

from __future__ import annotations

from typing import ClassVar

from filings_cvm._internal.config.contracts import CAD_FI_HIST_CONDOM, FileContract
from filings_cvm.ingestion.fi.cad.cad_fi_hist._base_cad_fi_hist_reader import _BaseCadFiHistReader


class CadastroFiHistCondomReader(_BaseCadFiHistReader):
	"""Read the CAD/FI *condomínio* change-log into a typed DataFrame."""

	_MEMBER: ClassVar[str] = "cad_fi_hist_condom.csv"
	_CONTRACT: ClassVar[FileContract] = CAD_FI_HIST_CONDOM
	_DATE_COLS: ClassVar[tuple[str, ...]] = ("DT_REG", "DT_INI_CONDOM", "DT_FIM_CONDOM")
	_LABEL: ClassVar[str] = "condomínio"
