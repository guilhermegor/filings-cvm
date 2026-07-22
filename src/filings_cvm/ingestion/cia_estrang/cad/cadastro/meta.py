"""CVM **META** for the Companhias Estrangeiras Cadastro dataset (`CIA_ESTRANG/CAD`).

The spec CVM publishes for `cad_cia_estrang.csv` — the declared description, type and size of each
field. A flat `.txt`, so the whole document is one section.
"""

from __future__ import annotations

from typing import ClassVar

from filings_cvm._internal.config.contracts.meta import META_CAD_CIA_ESTRANG
from filings_cvm._internal.utils.tabular_reader import FileContract
from filings_cvm.ingestion._base_meta_reader import BaseMetaReader


class MetaCadCiaEstrangReader(BaseMetaReader):
	"""Read the META of the CVM Companhias Estrangeiras Cadastro dataset.

	Methods
	-------
	read(int_timeout_s)
		Download and parse the META into a validated DataFrame (inherited).
	"""

	_META_URL: ClassVar[str] = (
		"https://dados.cvm.gov.br/dados/CIA_ESTRANG/CAD/META/meta_cad_cia_estrang.txt"
	)
	_CONTRACT: ClassVar[FileContract] = META_CAD_CIA_ESTRANG
