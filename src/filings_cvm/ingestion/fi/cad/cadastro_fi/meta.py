"""CVM **META** for the FI Cadastro dataset (`FI/CAD`, `cad_fi.csv`).

The spec CVM publishes for the legacy fund-registry snapshot — the declared description, type and
size of each field. A flat `.txt`, so the whole document is one section.

⚠️ **Not the same dataset as `meta_cad_fi.zip`** (:mod:`filings_cvm.ingestion.fi.cad.cad_fi_hist`):
same stem, different extension, different fields — the `.txt`/`.zip` split is deliberate CVM
naming, not a redundant duplicate.
"""

from __future__ import annotations

from typing import ClassVar

from filings_cvm._internal.config.contracts.meta import META_CAD_FI
from filings_cvm._internal.utils.tabular_reader import FileContract
from filings_cvm.ingestion._base_meta_reader import BaseMetaReader


class MetaCadastroFiReader(BaseMetaReader):
	"""Read the META of the CVM FI Cadastro dataset.

	Methods
	-------
	read(int_timeout_s)
		Download and parse the META into a validated DataFrame (inherited).
	"""

	_META_URL: ClassVar[str] = "https://dados.cvm.gov.br/dados/FI/CAD/META/meta_cad_fi.txt"
	_CONTRACT: ClassVar[FileContract] = META_CAD_FI
