"""CVM FCA CIA_ABERTA (endereço) — ingestion (leitura) reader.

The company's registered addresses (the largest member by row count: 1,436 in 2025).

Download/unzip/parse is inherited from the private `_BaseFcaReader`; this module only declares
which member it reads and how it is typed.
"""

from __future__ import annotations

from typing import ClassVar

from filings_cvm._internal.config.contracts.fca_cia_aberta import FCA_CIA_ABERTA_ENDERECO
from filings_cvm._internal.utils.tabular_reader import FileContract
from filings_cvm.ingestion.cia_aberta.doc.fca._base_fca_reader import _BaseFcaReader


class FcaCiaAbertaEnderecoReader(_BaseFcaReader):
	"""Read the FCA CIA_ABERTA `endereço` member into a typed DataFrame.

	Methods
	-------
	read(int_timeout_s)
		Download, unzip, and parse the reference year's member (inherited).
	"""

	_MEMBER_STEM: ClassVar[str] = "fca_cia_aberta_endereco"
	_CONTRACT: ClassVar[FileContract] = FCA_CIA_ABERTA_ENDERECO
	_DATE_COLS: ClassVar[tuple[str, ...]] = ("Data_Referencia",)
	_LABEL: ClassVar[str] = "endereço"
