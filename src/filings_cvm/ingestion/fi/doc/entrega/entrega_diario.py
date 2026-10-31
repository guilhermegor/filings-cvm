"""CVM Entrega de Documentos FI (daily-fund report) -- ingestion (leitura) reader.

Reads the member `fi_entrega_documento_diario_AAAAMM.csv` of `fi_entrega_documento_AAAAMM.zip`
(dataset `FI/DOC/ENTREGA`). Same header as :class:`EntregaFiReader` but only `DIÁRIO FUNDOS`
rows, ~14x more of them (1.4M in `202609`).
"""

from __future__ import annotations

from typing import ClassVar

from filings_cvm._internal.config.contracts.entrega_fi import ENTREGA_FI_DIARIO
from filings_cvm._internal.utils.tabular_reader import FileContract
from filings_cvm.ingestion.fi.doc.entrega._base_entrega_reader import _BaseEntregaReader


class EntregaFiDiarioReader(_BaseEntregaReader):
	"""Read the CVM FI daily-fund delivery index into a DataFrame.

	Methods
	-------
	read(int_timeout_s)
		Download, unzip and parse the reference month's index (inherited).
	"""

	_CONTRACT: ClassVar[FileContract] = ENTREGA_FI_DIARIO
	_LABEL: ClassVar[str] = "daily funds"
	_MEMBER_INFIX: ClassVar[str] = "_diario"
