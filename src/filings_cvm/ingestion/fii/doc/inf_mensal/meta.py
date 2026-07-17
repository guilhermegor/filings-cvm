"""CVM **META** for the FII Informe Mensal dataset (`FII/DOC/INF_MENSAL`).

The spec CVM publishes for the 3 members of `inf_mensal_fii_AAAA.zip` (geral, ativo_passivo,
complemento) — the declared description, type and size of every field.
"""

from __future__ import annotations

from typing import ClassVar

from filings_cvm._internal.config.contracts.meta import META_INF_MENSAL_FII
from filings_cvm._internal.utils.tabular_reader import FileContract
from filings_cvm.ingestion._base_meta_reader import BaseMetaReader


class MetaInfMensalFiiReader(BaseMetaReader):
	"""Read the META of the CVM FII Informe Mensal dataset.

	Methods
	-------
	read(int_timeout_s)
		Download and parse the META into a validated DataFrame (inherited).
	"""

	_META_URL: ClassVar[str] = (
		"https://dados.cvm.gov.br/dados/FII/DOC/INF_MENSAL/META/meta_inf_mensal_fii.zip"
	)
	_CONTRACT: ClassVar[FileContract] = META_INF_MENSAL_FII
	_MEMBER_STEM: ClassVar[str] = "inf_mensal_fii"
