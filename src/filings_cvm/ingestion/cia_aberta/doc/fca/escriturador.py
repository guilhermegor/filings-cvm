"""CVM FCA CIA_ABERTA (escriturador) — ingestion (leitura) reader.

The company's share registrars (*escrituradores*).

The only member with **two** CNPJ columns — ``CNPJ_Companhia`` and ``CNPJ_Escriturador``, both
100% valid in 2025, so both are declared.

Download/unzip/parse is inherited from the private `_BaseFcaReader`; this module only declares
which member it reads and how it is typed.
"""

from __future__ import annotations

from typing import ClassVar

from filings_cvm._internal.config.contracts.fca_cia_aberta import FCA_CIA_ABERTA_ESCRITURADOR
from filings_cvm._internal.utils.tabular_reader import FileContract
from filings_cvm.ingestion.cia_aberta.doc.fca._base_fca_reader import _BaseFcaReader


class FcaCiaAbertaEscrituradorReader(_BaseFcaReader):
	"""Read the FCA CIA_ABERTA `escriturador` member into a typed DataFrame.

	Methods
	-------
	read(int_timeout_s)
		Download, unzip, and parse the reference year's member (inherited).
	"""

	_MEMBER_STEM: ClassVar[str] = "fca_cia_aberta_escriturador"
	_CONTRACT: ClassVar[FileContract] = FCA_CIA_ABERTA_ESCRITURADOR
	_DATE_COLS: ClassVar[tuple[str, ...]] = (
		"Data_Referencia",
		"Data_Inicio_Atuacao",
		"Data_Fim_Atuacao",
	)
	_LABEL: ClassVar[str] = "escriturador"
