"""CVM FCA CIA_ABERTA (DRI) — ingestion (leitura) reader.

The *Diretor de Relações com Investidores* and their contact details.

⚠️ Carries **personal data**: ``CPF_Responsavel`` holds 1,003 CPFs and 4 CNPJs in 2025 — a mixed
person-or-company identifier. It is returned as exact source text and is **not** declared a CNPJ
column; the committed fixture is header-only for this reason.

Download/unzip/parse is inherited from the private `_BaseFcaReader`; this module only declares
which member it reads and how it is typed.
"""

from __future__ import annotations

from typing import ClassVar

from filings_cvm._internal.config.contracts.fca_cia_aberta import FCA_CIA_ABERTA_DRI
from filings_cvm._internal.utils.tabular_reader import FileContract
from filings_cvm.ingestion.cia_aberta.doc.fca._base_fca_reader import _BaseFcaReader


class FcaCiaAbertaDriReader(_BaseFcaReader):
	"""Read the FCA CIA_ABERTA `DRI` member into a typed DataFrame.

	Methods
	-------
	read(int_timeout_s)
		Download, unzip, and parse the reference year's member (inherited).
	"""

	_MEMBER_STEM: ClassVar[str] = "fca_cia_aberta_dri"
	_CONTRACT: ClassVar[FileContract] = FCA_CIA_ABERTA_DRI
	_DATE_COLS: ClassVar[tuple[str, ...]] = (
		"Data_Referencia",
		"Data_Inicio_Atuacao",
		"Data_Fim_Atuacao",
	)
	_LABEL: ClassVar[str] = "DRI"
