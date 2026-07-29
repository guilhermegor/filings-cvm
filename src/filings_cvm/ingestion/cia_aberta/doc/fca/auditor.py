"""CVM FCA CIA_ABERTA (auditor) — ingestion (leitura) reader.

The company's auditors and their technical leads.

⚠️ Carries **personal data**: ``CPF_Responsavel_Tecnico`` (49 CPFs in 2025) and the by-name-mixed
``CPF_CNPJ_Auditor``. Both are exact source text and neither is declared a CNPJ column — in 2025
``CPF_CNPJ_Auditor`` happens to be all CNPJ, but a year holding a CPF would break such a check.
``Data_Fim_Atuacao_Responsavel_Tecnico`` is 100% blank, so every value becomes ``NaT``.

Download/unzip/parse is inherited from the private `_BaseFcaReader`; this module only declares
which member it reads and how it is typed.
"""

from __future__ import annotations

from typing import ClassVar

from filings_cvm._internal.config.contracts.fca_cia_aberta import FCA_CIA_ABERTA_AUDITOR
from filings_cvm._internal.utils.tabular_reader import FileContract
from filings_cvm.ingestion.cia_aberta.doc.fca._base_fca_reader import _BaseFcaReader


class FcaCiaAbertaAuditorReader(_BaseFcaReader):
	"""Read the FCA CIA_ABERTA `auditor` member into a typed DataFrame.

	Methods
	-------
	read(int_timeout_s)
		Download, unzip, and parse the reference year's member (inherited).
	"""

	_MEMBER_STEM: ClassVar[str] = "fca_cia_aberta_auditor"
	_CONTRACT: ClassVar[FileContract] = FCA_CIA_ABERTA_AUDITOR
	_DATE_COLS: ClassVar[tuple[str, ...]] = (
		"Data_Referencia",
		"Data_Inicio_Atuacao_Auditor",
		"Data_Fim_Atuacao_Auditor",
		"Data_Inicio_Atuacao_Responsavel_Tecnico",
		"Data_Fim_Atuacao_Responsavel_Tecnico",
	)
	_LABEL: ClassVar[str] = "auditor"
