"""CVM CAD/FI histórico — classe change-log reader.

The ``cad_fi_hist_classe.csv`` member of ``cad_fi_hist.zip``: the history of each fund's
class. See :mod:`filings_cvm.ingestion._base_cad_fi_hist_reader` for the shared behaviour.
"""

from __future__ import annotations

from typing import ClassVar

from filings_cvm._internal.config.contracts import CAD_FI_HIST_CLASSE, FileContract
from filings_cvm.ingestion._base_cad_fi_hist_reader import _BaseCadFiHistReader


class CadastroFiHistClasseReader(_BaseCadFiHistReader):
	"""Read the CAD/FI *classe* change-log into a typed DataFrame."""

	_MEMBER: ClassVar[str] = "cad_fi_hist_classe.csv"
	_CONTRACT: ClassVar[FileContract] = CAD_FI_HIST_CLASSE
	_DATE_COLS: ClassVar[tuple[str, ...]] = ("DT_REG", "DT_INI_CLASSE", "DT_FIM_CLASSE")
	_LABEL: ClassVar[str] = "classe"
