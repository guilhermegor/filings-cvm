"""CVM **META** for the FI Complemento dataset (`FI/DOC/COMPL`).

The spec CVM publishes for the 4 members of `compl_fi_AAAAMM.zip`, as `meta_compl_fi_txt.zip`
(infixed `_txt`; members `meta_compl_fi.txt`, `meta_compl_fi_inf.txt`,
`meta_compl_fi_inf_cotst.txt`, `meta_compl_fi_prest.txt`).
"""

from __future__ import annotations

from typing import ClassVar

from filings_cvm._internal.config.contracts.meta import META_COMPL_FI
from filings_cvm._internal.utils.tabular_reader import FileContract
from filings_cvm.ingestion._base_meta_reader import BaseMetaReader


class MetaComplFiReader(BaseMetaReader):
	"""Read the META of the CVM FI Complemento dataset.

	Methods
	-------
	read(int_timeout_s)
		Download and parse the META into a validated DataFrame (inherited).
	"""

	_META_URL: ClassVar[str] = (
		"https://dados.cvm.gov.br/dados/FI/DOC/COMPL/META/meta_compl_fi_txt.zip"
	)
	_CONTRACT: ClassVar[FileContract] = META_COMPL_FI
	_MEMBER_STEM: ClassVar[str] = "compl_fi"
