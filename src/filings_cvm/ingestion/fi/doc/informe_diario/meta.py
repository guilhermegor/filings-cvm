"""CVM **META** for the FI Informe Diário dataset (`FI/DOC/INF_DIARIO`).

The spec CVM publishes for `inf_diario_fi_AAAAMM.csv` — the declared description, type and size of
each field. A flat `.txt`, so the whole document is one section.
"""

from __future__ import annotations

from typing import ClassVar

from filings_cvm._internal.config.contracts.meta import META_INF_DIARIO_FI
from filings_cvm._internal.utils.tabular_reader import FileContract
from filings_cvm.ingestion._base_meta_reader import BaseMetaReader


class MetaInformeDiarioReader(BaseMetaReader):
	"""Read the META of the CVM FI Informe Diário dataset.

	Methods
	-------
	read(int_timeout_s)
		Download and parse the META into a validated DataFrame (inherited).
	"""

	_META_URL: ClassVar[str] = (
		"https://dados.cvm.gov.br/dados/FI/DOC/INF_DIARIO/META/meta_inf_diario_fi.txt"
	)
	_CONTRACT: ClassVar[FileContract] = META_INF_DIARIO_FI
