"""CVM Entrega de Documentos FI -- ingestion (leitura) reader.

Reads the all-documents member `fi_entrega_documento_AAAAMM.csv` of
`fi_entrega_documento_AAAAMM.zip` (dataset `FI/DOC/ENTREGA`), series `202501` onward. The
daily-fund member of the same ZIP is read by :class:`EntregaFiDiarioReader`.
"""

from __future__ import annotations

from typing import ClassVar

from filings_cvm._internal.config.contracts.entrega_fi import ENTREGA_FI
from filings_cvm._internal.utils.tabular_reader import FileContract
from filings_cvm.ingestion.fi.doc.entrega._base_entrega_reader import _BaseEntregaReader


class EntregaFiReader(_BaseEntregaReader):
	"""Read the CVM FI document-delivery index (all document types) into a DataFrame.

	Methods
	-------
	read(int_timeout_s)
		Download, unzip and parse the reference month's index (inherited).
	"""

	_CONTRACT: ClassVar[FileContract] = ENTREGA_FI
	_LABEL: ClassVar[str] = "all documents"
	_MEMBER_INFIX: ClassVar[str] = ""
