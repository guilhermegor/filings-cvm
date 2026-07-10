"""CVM CAD/FI histórico — denominação comercial change-log reader.

The ``cad_fi_hist_denom_comerc.csv`` member of ``cad_fi_hist.zip``: the history of each fund's
commercial name. See :mod:`filings_cvm.ingestion._base_cad_fi_hist_reader` for shared behaviour.
"""

from __future__ import annotations

from typing import ClassVar

from filings_cvm._internal.config.contracts import CAD_FI_HIST_DENOM_COMERC, FileContract
from filings_cvm.ingestion._base_cad_fi_hist_reader import _BaseCadFiHistReader


class CadastroFiHistDenomComercReader(_BaseCadFiHistReader):
	"""Read the CAD/FI *denominação comercial* change-log into a typed DataFrame."""

	_MEMBER: ClassVar[str] = "cad_fi_hist_denom_comerc.csv"
	_CONTRACT: ClassVar[FileContract] = CAD_FI_HIST_DENOM_COMERC
	_DATE_COLS: ClassVar[tuple[str, ...]] = (
		"DT_REG",
		"DT_INI_DENOM_COMERC",
		"DT_FIM_DENOM_COMERC",
	)
	_LABEL: ClassVar[str] = "denominação comercial"
