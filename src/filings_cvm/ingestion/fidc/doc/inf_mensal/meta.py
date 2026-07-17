"""CVM **META** for the FIDC Informe Mensal dataset (`FIDC/DOC/INF_MENSAL`).

The spec CVM publishes for the 17 table members of `inf_mensal_fidc_AAAAMM.zip` — the declared
description, type and size of every field. Note the `_txt` infix in the archive name
(`meta_inf_mensal_fidc_txt.zip`).
"""

from __future__ import annotations

from typing import ClassVar

from filings_cvm._internal.config.contracts.meta import META_INF_MENSAL_FIDC
from filings_cvm._internal.utils.tabular_reader import FileContract
from filings_cvm.ingestion._base_meta_reader import BaseMetaReader


class MetaInfMensalFidcReader(BaseMetaReader):
	"""Read the META of the CVM FIDC Informe Mensal dataset.

	Methods
	-------
	read(int_timeout_s)
		Download and parse the META into a validated DataFrame (inherited).
	"""

	_META_URL: ClassVar[str] = (
		"https://dados.cvm.gov.br/dados/FIDC/DOC/INF_MENSAL/META/meta_inf_mensal_fidc_txt.zip"
	)
	_CONTRACT: ClassVar[FileContract] = META_INF_MENSAL_FIDC
	_MEMBER_STEM: ClassVar[str] = "inf_mensal_fidc"
