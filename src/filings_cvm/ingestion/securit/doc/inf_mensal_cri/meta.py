"""CVM **META** for the SECURIT INF_MENSAL_CRI dataset (`SECURIT/DOC/INF_MENSAL_CRI`).

The spec CVM publishes for the 11 members of `inf_mensal_cri_AAAA.zip` — the declared description,
type and size of every field, which the artifact's own header cannot carry. The 23rd (and, for the
`securit/` root, last) ``Meta*Reader``.

⚠️ **The field names come back truncated at 50 characters, verbatim as CVM publishes them.**
`fluxo_caixa`'s `Pagamentos_Classe_Subordinada_Mezanino_Amortizacao_Principal` (60 chars in the
real header) appears here as its 50-char prefix. Do not "repair" it — compare `real[:50] == meta`.

⚠️ **A `Data_`-named field is not necessarily a date, and the META is the authority.**
`geral.Data_LTV` is declared **`varchar`** here (and is 100% empty in the data), and
`classe.Indice_Subordinacao_Data_Base` is **`numeric`** — both stay ``str`` in their readers on the
META's word, not the name's.
"""

from __future__ import annotations

from typing import ClassVar

from filings_cvm._internal.config.contracts.meta import META_INF_MENSAL_CRI
from filings_cvm._internal.utils.tabular_reader import FileContract
from filings_cvm.ingestion._base_meta_reader import BaseMetaReader


class MetaInfMensalCriReader(BaseMetaReader):
	"""Read the META of the CVM SECURIT INF_MENSAL_CRI dataset.

	Methods
	-------
	read(int_timeout_s)
		Download and parse the META into a validated DataFrame (inherited).
	"""

	_META_URL: ClassVar[str] = (
		"https://dados.cvm.gov.br/dados/SECURIT/DOC/INF_MENSAL_CRI/META/meta_inf_mensal_cri.zip"
	)
	_CONTRACT: ClassVar[FileContract] = META_INF_MENSAL_CRI
	_MEMBER_STEM: ClassVar[str] = "inf_mensal_cri"
