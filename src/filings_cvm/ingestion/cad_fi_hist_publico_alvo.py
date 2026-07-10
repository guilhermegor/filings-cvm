"""CVM CAD/FI histórico — público-alvo change-log reader.

The ``cad_fi_hist_publico_alvo.csv`` member of ``cad_fi_hist.zip``: the history of each fund's
target audience. See :mod:`filings_cvm.ingestion._base_cad_fi_hist_reader` for shared behaviour.
"""

from __future__ import annotations

from typing import ClassVar

from filings_cvm._internal.config.contracts import CAD_FI_HIST_PUBLICO_ALVO, FileContract
from filings_cvm.ingestion._base_cad_fi_hist_reader import _BaseCadFiHistReader


class CadastroFiHistPublicoAlvoReader(_BaseCadFiHistReader):
	"""Read the CAD/FI *público-alvo* change-log into a typed DataFrame."""

	_MEMBER: ClassVar[str] = "cad_fi_hist_publico_alvo.csv"
	_CONTRACT: ClassVar[FileContract] = CAD_FI_HIST_PUBLICO_ALVO
	_DATE_COLS: ClassVar[tuple[str, ...]] = (
		"DT_REG",
		"DT_INI_PUBLICO_ALVO",
		"DT_FIM_PUBLICO_ALVO",
	)
	_LABEL: ClassVar[str] = "público-alvo"
