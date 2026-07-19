"""CVM **META** for the AUDITOR Cadastro dataset (`AUDITOR/CAD`, `cad_auditor.zip`).

The spec CVM publishes for the auditor registry — the declared description, type and size of each
field. A ZIP of two members (`meta_cad_auditor_pf.txt`, `meta_cad_auditor_pj.txt`), so the parsed
frame comes back as one long frame with each member's section in ``section``.
"""

from __future__ import annotations

from typing import ClassVar

from filings_cvm._internal.config.contracts.meta import META_CAD_AUDITOR
from filings_cvm._internal.utils.tabular_reader import FileContract
from filings_cvm.ingestion._base_meta_reader import BaseMetaReader


class MetaAuditorReader(BaseMetaReader):
	"""Read the META of the CVM AUDITOR Cadastro dataset.

	Methods
	-------
	read(int_timeout_s)
		Download and parse the META into a validated DataFrame (inherited).
	"""

	_META_URL: ClassVar[str] = (
		"https://dados.cvm.gov.br/dados/AUDITOR/CAD/META/meta_cad_auditor.zip"
	)
	_CONTRACT: ClassVar[FileContract] = META_CAD_AUDITOR
	_MEMBER_STEM: ClassVar[str] = "cad_auditor"
