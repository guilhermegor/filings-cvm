"""CVM CAD/FI histórico — tributação de longo prazo change-log reader.

The ``cad_fi_hist_trib_lprazo.csv`` member of ``cad_fi_hist.zip``: the history of each fund's
long-term taxation status. See :mod:`filings_cvm.ingestion._base_cad_fi_hist_reader` for
shared behaviour.
"""

from __future__ import annotations

from typing import ClassVar

from filings_cvm._internal.config.contracts import CAD_FI_HIST_TRIB_LPRAZO, FileContract
from filings_cvm.ingestion._base_cad_fi_hist_reader import _BaseCadFiHistReader


class CadastroFiHistTribLprazoReader(_BaseCadFiHistReader):
	"""Read the CAD/FI *tributação de longo prazo* change-log into a typed DataFrame."""

	_MEMBER: ClassVar[str] = "cad_fi_hist_trib_lprazo.csv"
	_CONTRACT: ClassVar[FileContract] = CAD_FI_HIST_TRIB_LPRAZO
	_DATE_COLS: ClassVar[tuple[str, ...]] = (
		"DT_REG",
		"DT_INI_ST_TRIB_LPRAZO",
		"DT_FIM_ST_TRIB_LPRAZO",
	)
	_LABEL: ClassVar[str] = "tributação de longo prazo"
