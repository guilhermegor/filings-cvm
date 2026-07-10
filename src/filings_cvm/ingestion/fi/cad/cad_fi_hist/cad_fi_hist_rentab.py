"""CVM CAD/FI histórico — rentabilidade change-log reader.

The ``cad_fi_hist_rentab.csv`` member of ``cad_fi_hist.zip``: the history of each fund's
profitability class. See ``_base_cad_fi_hist_reader`` for shared
behaviour.
"""

from __future__ import annotations

from typing import ClassVar

from filings_cvm._internal.config.contracts import CAD_FI_HIST_RENTAB, FileContract
from filings_cvm.ingestion.fi.cad.cad_fi_hist._base_cad_fi_hist_reader import _BaseCadFiHistReader


class CadastroFiHistRentabReader(_BaseCadFiHistReader):
	"""Read the CAD/FI *rentabilidade* change-log into a typed DataFrame."""

	_MEMBER: ClassVar[str] = "cad_fi_hist_rentab.csv"
	_CONTRACT: ClassVar[FileContract] = CAD_FI_HIST_RENTAB
	_DATE_COLS: ClassVar[tuple[str, ...]] = ("DT_REG", "DT_INI_RENTAB", "DT_FIM_RENTAB")
	_LABEL: ClassVar[str] = "rentabilidade"
