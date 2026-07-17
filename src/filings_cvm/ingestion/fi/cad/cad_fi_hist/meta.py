"""CVM **META** for the FI Cadastro histórico dataset (`FI/CAD`, `cad_fi_hist.zip`).

The spec CVM publishes for the 19 per-attribute change-log members of `cad_fi_hist.zip` — the
declared description, type and size of every field.

⚠️ **Not the same dataset as `meta_cad_fi.txt`**
(:mod:`filings_cvm.ingestion.fi.cad.cadastro_fi`): same stem, different extension, 19 sections
instead of one flat document.
"""

from __future__ import annotations

from typing import ClassVar

from filings_cvm._internal.config.contracts.meta import META_CAD_FI_HIST
from filings_cvm._internal.utils.tabular_reader import FileContract
from filings_cvm.ingestion._base_meta_reader import BaseMetaReader


class MetaCadFiHistReader(BaseMetaReader):
	"""Read the META of the CVM FI Cadastro histórico dataset.

	Methods
	-------
	read(int_timeout_s)
		Download and parse the META into a validated DataFrame (inherited).
	"""

	_META_URL: ClassVar[str] = "https://dados.cvm.gov.br/dados/FI/CAD/META/meta_cad_fi.zip"
	_CONTRACT: ClassVar[FileContract] = META_CAD_FI_HIST
	_MEMBER_STEM: ClassVar[str] = "cad_fi_hist"
