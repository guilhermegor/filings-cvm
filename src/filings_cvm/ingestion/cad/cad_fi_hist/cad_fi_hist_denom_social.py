"""CVM CAD/FI histórico — denominação social change-log reader.

The ``cad_fi_hist_denom_social.csv`` member of ``cad_fi_hist.zip``: the history of each fund's
legal name. See ``_base_cad_fi_hist_reader`` for shared behaviour.
"""

from __future__ import annotations

from typing import ClassVar

from filings_cvm._internal.config.contracts import CAD_FI_HIST_DENOM_SOCIAL, FileContract
from filings_cvm.ingestion.cad.cad_fi_hist._base_cad_fi_hist_reader import _BaseCadFiHistReader


class CadastroFiHistDenomSocialReader(_BaseCadFiHistReader):
	"""Read the CAD/FI *denominação social* change-log into a typed DataFrame."""

	_MEMBER: ClassVar[str] = "cad_fi_hist_denom_social.csv"
	_CONTRACT: ClassVar[FileContract] = CAD_FI_HIST_DENOM_SOCIAL
	_DATE_COLS: ClassVar[tuple[str, ...]] = (
		"DT_REG",
		"DT_INI_DENOM_SOCIAL",
		"DT_FIM_DENOM_SOCIAL",
	)
	_LABEL: ClassVar[str] = "denominação social"
