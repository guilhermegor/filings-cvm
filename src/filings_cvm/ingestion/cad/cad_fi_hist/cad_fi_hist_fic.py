"""CVM CAD/FI histórico — fundo de cotas change-log reader.

The ``cad_fi_hist_fic.csv`` member of ``cad_fi_hist.zip``: the history of each fund's
fund-of-quotas (FIC) status. See ``_base_cad_fi_hist_reader`` for
shared behaviour.
"""

from __future__ import annotations

from typing import ClassVar

from filings_cvm._internal.config.contracts import CAD_FI_HIST_FIC, FileContract
from filings_cvm.ingestion.cad.cad_fi_hist._base_cad_fi_hist_reader import _BaseCadFiHistReader


class CadastroFiHistFicReader(_BaseCadFiHistReader):
	"""Read the CAD/FI *fundo de cotas* change-log into a typed DataFrame."""

	_MEMBER: ClassVar[str] = "cad_fi_hist_fic.csv"
	_CONTRACT: ClassVar[FileContract] = CAD_FI_HIST_FIC
	_DATE_COLS: ClassVar[tuple[str, ...]] = ("DT_REG", "DT_INI_ST_COTAS", "DT_FIM_ST_COTAS")
	_LABEL: ClassVar[str] = "fundo de cotas"
