"""CVM FRE CIA_ABERTA (administradores e membros do conselho fiscal) — ingestion reader.

One row per person serving on a company's board, executive body or fiscal council, with the
mandate dates and the professional background declared for them.

⚠️ **Contains personal data.** `Nome`, `CPF`, `Data_Nascimento`, `Profissao` and
`Experiencia_Profissional` all describe an individual. `CPF` is returned as exact published text
and is **never** declared a CNPJ column; the only CNPJ column is the filing company's.

`Data_Posse` and `Data_Inicio_Primeiro_Mandato` arrive partly blank (an elected member who has
not taken office yet), so those cells become `NaT`.

`Numero_Mandatos_Consecutivos` and `Percentual_Participacao_Reunioes` are counts and stay exact
text — never a binary float; convert downstream.

Download/unzip/parse is inherited from the private `_BaseFreReader`; this module only declares
which member it reads and how it is typed.
"""

from __future__ import annotations

from typing import ClassVar

from filings_cvm._internal.config.contracts.fre_cia_aberta import (
	FRE_CIA_ABERTA_ADMINISTRADOR_MEMBRO_CONSELHO_FISCAL,
)
from filings_cvm._internal.utils.tabular_reader import FileContract
from filings_cvm.ingestion.cia_aberta.doc.fre._base_fre_reader import _BaseFreReader


class FreCiaAbertaAdministradorMembroConselhoFiscalReader(_BaseFreReader):
	"""Read the FRE CIA_ABERTA `administradores/conselho fiscal` member into a typed DataFrame.

	Methods
	-------
	read(int_timeout_s)
		Download, unzip, and parse the reference year's member (inherited).
	"""

	_MEMBER_STEM: ClassVar[str] = "fre_cia_aberta_administrador_membro_conselho_fiscal"
	_CONTRACT: ClassVar[FileContract] = FRE_CIA_ABERTA_ADMINISTRADOR_MEMBRO_CONSELHO_FISCAL
	_DATE_COLS: ClassVar[tuple[str, ...]] = (
		"Data_Referencia",
		"Data_Eleicao",
		"Data_Posse",
		"Data_Inicio_Primeiro_Mandato",
		"Data_Nascimento",
	)
	_LABEL: ClassVar[str] = "administradores/conselho fiscal"
