"""CVM **META** for the FI Lâmina dataset (`FI/DOC/LAMINA`).

The spec CVM publishes for the members of `lamina_fi_AAAAMM.zip` (the fact sheet proper and its
carteira allocation member) — the declared description, type and size of every field. Note the
`_txt` infix in the archive name (`meta_lamina_fi_txt.zip`).
"""

from __future__ import annotations

from typing import ClassVar

from filings_cvm._internal.config.contracts.meta import META_LAMINA_FI
from filings_cvm._internal.utils.tabular_reader import FileContract
from filings_cvm.ingestion._base_meta_reader import BaseMetaReader


class MetaLaminaReader(BaseMetaReader):
	"""Read the META of the CVM FI Lâmina dataset.

	Methods
	-------
	read(int_timeout_s)
		Download and parse the META into a validated DataFrame (inherited).
	"""

	_META_URL: ClassVar[str] = (
		"https://dados.cvm.gov.br/dados/FI/DOC/LAMINA/META/meta_lamina_fi_txt.zip"
	)
	_CONTRACT: ClassVar[FileContract] = META_LAMINA_FI
	_MEMBER_STEM: ClassVar[str] = "lamina_fi"
