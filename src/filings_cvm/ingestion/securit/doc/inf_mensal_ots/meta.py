"""CVM **META** for the SECURIT INF_MENSAL_OTS dataset (`SECURIT/DOC/INF_MENSAL_OTS`).

The spec CVM publishes for the 8 members of `inf_mensal_ots_AAAA.zip` — the declared description,
type and size of every field. ⚠️ Shares its 8 section names with `INF_MENSAL_CRA`
(:mod:`filings_cvm.ingestion.securit.doc.inf_mensal_cra`), but the two datasets' column lists do
not match.
"""

from __future__ import annotations

from typing import ClassVar

from filings_cvm._internal.config.contracts.meta import META_INF_MENSAL_OTS
from filings_cvm._internal.utils.tabular_reader import FileContract
from filings_cvm.ingestion._base_meta_reader import BaseMetaReader


class MetaInfMensalOtsReader(BaseMetaReader):
	"""Read the META of the CVM SECURIT INF_MENSAL_OTS dataset.

	Methods
	-------
	read(int_timeout_s)
		Download and parse the META into a validated DataFrame (inherited).
	"""

	_META_URL: ClassVar[str] = (
		"https://dados.cvm.gov.br/dados/SECURIT/DOC/INF_MENSAL_OTS/META/meta_inf_mensal_ots.zip"
	)
	_CONTRACT: ClassVar[FileContract] = META_INF_MENSAL_OTS
	_MEMBER_STEM: ClassVar[str] = "inf_mensal_ots"
