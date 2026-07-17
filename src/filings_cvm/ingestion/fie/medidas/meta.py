"""CVM **META** for the FIE Medidas Mensais dataset (`FIE/MEDIDAS`).

The spec CVM publishes for `medidas_mes_fie_AAAAMM.csv` — the declared description, type and size
of each field. A flat `.txt`, so the whole document is one section. `FIE/MEDIDAS` also publishes a
`.csv` META; the `.txt` is used deliberately, matching every other dataset's format.
"""

from __future__ import annotations

from typing import ClassVar

from filings_cvm._internal.config.contracts.meta import META_MEDIDAS_MES_FIE
from filings_cvm._internal.utils.tabular_reader import FileContract
from filings_cvm.ingestion._base_meta_reader import BaseMetaReader


class MetaMedidasMesFieReader(BaseMetaReader):
	"""Read the META of the CVM FIE Medidas Mensais dataset.

	Methods
	-------
	read(int_timeout_s)
		Download and parse the META into a validated DataFrame (inherited).
	"""

	_META_URL: ClassVar[str] = (
		"https://dados.cvm.gov.br/dados/FIE/MEDIDAS/META/meta_medidas_mes_fie.txt"
	)
	_CONTRACT: ClassVar[FileContract] = META_MEDIDAS_MES_FIE
