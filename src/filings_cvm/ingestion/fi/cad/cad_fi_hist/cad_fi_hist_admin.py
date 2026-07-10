"""CVM CAD/FI histórico — administrador change-log reader.

The ``cad_fi_hist_admin.csv`` member of ``cad_fi_hist.zip``: the history of each fund's
administrator. See ``_base_cad_fi_hist_reader`` for the shared
behaviour (no ``date_ref``, no grain, shared archive, ``path_raw``).
"""

from __future__ import annotations

from typing import ClassVar

from filings_cvm._internal.config.contracts import CAD_FI_HIST_ADMIN, FileContract
from filings_cvm.ingestion.fi.cad.cad_fi_hist._base_cad_fi_hist_reader import _BaseCadFiHistReader


class CadastroFiHistAdminReader(_BaseCadFiHistReader):
	"""Read the CAD/FI *administrador* change-log into a typed DataFrame."""

	_MEMBER: ClassVar[str] = "cad_fi_hist_admin.csv"
	_CONTRACT: ClassVar[FileContract] = CAD_FI_HIST_ADMIN
	_DATE_COLS: ClassVar[tuple[str, ...]] = ("DT_REG", "DT_INI_ADMIN", "DT_FIM_ADMIN")
	_LABEL: ClassVar[str] = "administrador"
