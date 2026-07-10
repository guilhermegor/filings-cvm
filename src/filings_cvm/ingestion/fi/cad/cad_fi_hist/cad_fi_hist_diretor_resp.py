"""CVM CAD/FI histórico — diretor responsável change-log reader.

The ``cad_fi_hist_diretor_resp.csv`` member of ``cad_fi_hist.zip``: the history of each fund's
responsible director. See ``_base_cad_fi_hist_reader`` for shared
behaviour.
"""

from __future__ import annotations

from typing import ClassVar

from filings_cvm._internal.config.contracts import CAD_FI_HIST_DIRETOR_RESP, FileContract
from filings_cvm.ingestion.fi.cad.cad_fi_hist._base_cad_fi_hist_reader import _BaseCadFiHistReader


class CadastroFiHistDiretorRespReader(_BaseCadFiHistReader):
	"""Read the CAD/FI *diretor responsável* change-log into a typed DataFrame."""

	_MEMBER: ClassVar[str] = "cad_fi_hist_diretor_resp.csv"
	_CONTRACT: ClassVar[FileContract] = CAD_FI_HIST_DIRETOR_RESP
	_DATE_COLS: ClassVar[tuple[str, ...]] = ("DT_REG", "DT_INI_DIRETOR", "DT_FIM_DIRETOR")
	_LABEL: ClassVar[str] = "diretor responsável"
