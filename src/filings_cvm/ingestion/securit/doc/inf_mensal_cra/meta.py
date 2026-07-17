"""CVM **META** for the SECURIT INF_MENSAL_CRA dataset (`SECURIT/DOC/INF_MENSAL_CRA`).

The spec CVM publishes for the 8 members of `inf_mensal_cra_AAAA.zip` — the declared description,
type and size of every field, which the artifact's own header cannot carry.

⚠️ **The field names come back truncated at 50 characters, verbatim as CVM publishes them.** This
dataset is the proof: `Pagamentos_Classe_Subordinada_Mezanino_Amortizacao_Principal` (60 chars in
the real header) appears here as its 50-char prefix. Do not "repair" it — compare
`real[:50] == meta`.
"""

from __future__ import annotations

from typing import ClassVar

from filings_cvm._internal.config.contracts.meta import META_INF_MENSAL_CRA
from filings_cvm._internal.utils.tabular_reader import FileContract
from filings_cvm.ingestion._base_meta_reader import BaseMetaReader


class MetaInfMensalCraReader(BaseMetaReader):
	"""Read the META of the CVM SECURIT INF_MENSAL_CRA dataset.

	Methods
	-------
	read(int_timeout_s)
		Download and parse the META into a validated DataFrame (inherited).
	"""

	_META_URL: ClassVar[str] = (
		"https://dados.cvm.gov.br/dados/SECURIT/DOC/INF_MENSAL_CRA/META/meta_inf_mensal_cra.zip"
	)
	_CONTRACT: ClassVar[FileContract] = META_INF_MENSAL_CRA
	_MEMBER_STEM: ClassVar[str] = "inf_mensal_cra"
