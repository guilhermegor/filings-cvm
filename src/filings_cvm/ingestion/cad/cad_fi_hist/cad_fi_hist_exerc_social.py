"""CVM CAD/FI histórico — exercício social change-log reader.

The ``cad_fi_hist_exerc_social.csv`` member of ``cad_fi_hist.zip``: the history of each fund's
fiscal-year window. This member carries no non-date value column beyond the keys — its content
*is* the ``DT_INI_EXERC`` / ``DT_FIM_EXERC`` pair. See
``_base_cad_fi_hist_reader`` for shared behaviour.
"""

from __future__ import annotations

from typing import ClassVar

from filings_cvm._internal.config.contracts import CAD_FI_HIST_EXERC_SOCIAL, FileContract
from filings_cvm.ingestion.cad.cad_fi_hist._base_cad_fi_hist_reader import _BaseCadFiHistReader


class CadastroFiHistExercSocialReader(_BaseCadFiHistReader):
	"""Read the CAD/FI *exercício social* change-log into a typed DataFrame."""

	_MEMBER: ClassVar[str] = "cad_fi_hist_exerc_social.csv"
	_CONTRACT: ClassVar[FileContract] = CAD_FI_HIST_EXERC_SOCIAL
	_DATE_COLS: ClassVar[tuple[str, ...]] = ("DT_REG", "DT_INI_EXERC", "DT_FIM_EXERC")
	_LABEL: ClassVar[str] = "exercício social"
