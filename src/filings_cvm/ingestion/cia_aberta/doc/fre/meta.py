"""CVM **META** for the Companhias Abertas FRE dataset (`CIA_ABERTA/DOC/FRE`).

The spec CVM publishes for the *Formulário de Referência* members — the declared description, type
and size of each field.

⚠️ The URL is **constant per dataset and never derived**. Here the standard prefixed form works —
`meta_fre_cia_aberta.zip` — while the loose `.txt`, the no-prefix `fre_cia_aberta.zip` (the correct
form for the sibling FCA) and the `_txt`-infixed variant all return **404**.

⚠️ The archive holds **50 members for 36 data members**, and its member naming is **mixed**: most
carry the `meta_fre_cia_aberta*` prefix but at least one
(`fre_cia_aberta_empregado_local_faixa_etaria.txt`) does not. The extra sections and the
inconsistent prefix are returned **as published** — the parser labels each section from the member
name it actually finds, and nothing is normalised.
"""

from __future__ import annotations

from typing import ClassVar

from filings_cvm._internal.config.contracts.meta import META_FRE_CIA_ABERTA
from filings_cvm._internal.utils.tabular_reader import FileContract
from filings_cvm.ingestion._base_meta_reader import BaseMetaReader


class MetaFreCiaAbertaReader(BaseMetaReader):
	"""Read the META of the CVM Companhias Abertas FRE dataset.

	Methods
	-------
	read(int_timeout_s)
		Download and parse the META into a validated DataFrame (inherited).
	"""

	_META_URL: ClassVar[str] = (
		"https://dados.cvm.gov.br/dados/CIA_ABERTA/DOC/FRE/META/meta_fre_cia_aberta.zip"
	)
	_CONTRACT: ClassVar[FileContract] = META_FRE_CIA_ABERTA
