"""CVM **META** for the FI document-delivery dataset (`FI/DOC/ENTREGA`).

The spec CVM publishes for `fi_entrega_documento_AAAAMM.zip`: a flat `.txt`,
`meta_fi_entrega_documento.txt` (note the `fi_` prefix, absent from the `entrega` dataset slug).
Its 11 fields equal the header of both members. It declares `ID_Documento` `int` and
`Data_Hora_Entrega` `datetime`; CVM leaves most descriptions empty.
"""

from __future__ import annotations

from typing import ClassVar

from filings_cvm._internal.config.contracts.meta import META_ENTREGA_FI
from filings_cvm._internal.utils.tabular_reader import FileContract
from filings_cvm.ingestion._base_meta_reader import BaseMetaReader


class MetaEntregaFiReader(BaseMetaReader):
	"""Read the META of the CVM FI document-delivery dataset.

	Methods
	-------
	read(int_timeout_s)
		Download and parse the META into a validated DataFrame (inherited).
	"""

	_META_URL: ClassVar[str] = (
		"https://dados.cvm.gov.br/dados/FI/DOC/ENTREGA/META/meta_fi_entrega_documento.txt"
	)
	_CONTRACT: ClassVar[FileContract] = META_ENTREGA_FI
