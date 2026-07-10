"""CVM CAD/FI histórico — situação change-log reader.

The ``cad_fi_hist_sit.csv`` member of ``cad_fi_hist.zip``: the history of each fund's
situation (``EM FUNCIONAMENTO NORMAL``, ``CANCELADA``, …) — the change-log most useful for
reconstructing when a fund was live. See :mod:`filings_cvm.ingestion._base_cad_fi_hist_reader`
for shared behaviour.
"""

from __future__ import annotations

from typing import ClassVar

from filings_cvm._internal.config.contracts import CAD_FI_HIST_SIT, FileContract
from filings_cvm.ingestion._base_cad_fi_hist_reader import _BaseCadFiHistReader


class CadastroFiHistSitReader(_BaseCadFiHistReader):
	"""Read the CAD/FI *situação* change-log into a typed DataFrame."""

	_MEMBER: ClassVar[str] = "cad_fi_hist_sit.csv"
	_CONTRACT: ClassVar[FileContract] = CAD_FI_HIST_SIT
	_DATE_COLS: ClassVar[tuple[str, ...]] = ("DT_REG", "DT_INI_SIT", "DT_FIM_SIT")
	_LABEL: ClassVar[str] = "situação"
