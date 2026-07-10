"""CVM CAD/FI histórico — gestor change-log reader.

The ``cad_fi_hist_gestor.csv`` member of ``cad_fi_hist.zip``: the history of each fund's
manager. ``CPF_CNPJ_GESTOR`` holds a CPF where ``PF_PJ_GESTOR == "PF"``, so it is read as text
and not validated as a CNPJ. See ``_base_cad_fi_hist_reader`` for
shared behaviour.
"""

from __future__ import annotations

from typing import ClassVar

from filings_cvm._internal.config.contracts import CAD_FI_HIST_GESTOR, FileContract
from filings_cvm.ingestion.fi.cad.cad_fi_hist._base_cad_fi_hist_reader import _BaseCadFiHistReader


class CadastroFiHistGestorReader(_BaseCadFiHistReader):
	"""Read the CAD/FI *gestor* change-log into a typed DataFrame."""

	_MEMBER: ClassVar[str] = "cad_fi_hist_gestor.csv"
	_CONTRACT: ClassVar[FileContract] = CAD_FI_HIST_GESTOR
	_DATE_COLS: ClassVar[tuple[str, ...]] = ("DT_REG", "DT_INI_GESTOR", "DT_FIM_GESTOR")
	_LABEL: ClassVar[str] = "gestor"
