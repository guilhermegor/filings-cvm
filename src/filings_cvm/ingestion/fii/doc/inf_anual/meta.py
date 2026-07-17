"""CVM **META** for the FII Informe Anual dataset (`FII/DOC/INF_ANUAL`).

The spec CVM publishes for the 12 members of `inf_anual_fii_AAAA.zip` — the declared description,
type and size of every field.
"""

from __future__ import annotations

from typing import ClassVar

from filings_cvm._internal.config.contracts.meta import META_INF_ANUAL_FII
from filings_cvm._internal.utils.tabular_reader import FileContract
from filings_cvm.ingestion._base_meta_reader import BaseMetaReader


class MetaInfAnualFiiReader(BaseMetaReader):
	"""Read the META of the CVM FII Informe Anual dataset.

	Methods
	-------
	read(int_timeout_s)
		Download and parse the META into a validated DataFrame (inherited).
	"""

	_META_URL: ClassVar[str] = (
		"https://dados.cvm.gov.br/dados/FII/DOC/INF_ANUAL/META/meta_inf_anual_fii.zip"
	)
	_CONTRACT: ClassVar[FileContract] = META_INF_ANUAL_FII
	_MEMBER_STEM: ClassVar[str] = "inf_anual_fii"
