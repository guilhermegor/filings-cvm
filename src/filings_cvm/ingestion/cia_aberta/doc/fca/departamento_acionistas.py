"""CVM FCA CIA_ABERTA (departamento de acionistas) — ingestion (leitura) reader.

The shareholder-relations department's contact and address.

⚠️ **Header-only in 2025** (0 data rows). Its contract therefore declares **no** CNPJ column: the
CNPJ check requires a *present* valid value, so a legitimately empty artifact would otherwise raise
``ContractError``. Same failure class as the CRI header-only members.

Download/unzip/parse is inherited from the private `_BaseFcaReader`; this module only declares
which member it reads and how it is typed.
"""

from __future__ import annotations

from typing import ClassVar

from filings_cvm._internal.config.contracts.fca_cia_aberta import (
	FCA_CIA_ABERTA_DEPARTAMENTO_ACIONISTAS,
)
from filings_cvm._internal.utils.tabular_reader import FileContract
from filings_cvm.ingestion.cia_aberta.doc.fca._base_fca_reader import _BaseFcaReader


class FcaCiaAbertaDepartamentoAcionistasReader(_BaseFcaReader):
	"""Read the FCA CIA_ABERTA `departamento de acionistas` member into a typed DataFrame.

	Methods
	-------
	read(int_timeout_s)
		Download, unzip, and parse the reference year's member (inherited).
	"""

	_MEMBER_STEM: ClassVar[str] = "fca_cia_aberta_departamento_acionistas"
	_CONTRACT: ClassVar[FileContract] = FCA_CIA_ABERTA_DEPARTAMENTO_ACIONISTAS
	_DATE_COLS: ClassVar[tuple[str, ...]] = (
		"Data_Referencia",
		"Data_Inicio_Contato",
		"Data_Fim_Contato",
	)
	_LABEL: ClassVar[str] = "departamento de acionistas"
