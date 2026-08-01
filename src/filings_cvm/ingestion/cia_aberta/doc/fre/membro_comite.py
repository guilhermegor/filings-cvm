"""CVM FRE CIA_ABERTA (membros de comitês) — ingestion (leitura) reader.

One row per person serving on a company committee (audit, compensation, risk, …), with the
mandate dates and the professional background declared for them.

⚠️ **Contains personal data.** `Nome`, `CPF`, `Data_Nascimento`, `Profissao` and
`Experiencia_Profissional` all describe an individual. `CPF` is returned as exact published text
and is **never** declared a CNPJ column; the only CNPJ column is the filing company's.

⚠️ **Not a copy of the administradores member despite the same column count (21).** This one
carries `Tipo_Comite` / `Descricao_Outros_Comites` / `Cargo_Ocupado` /
`Descricao_Outro_Cargo_Ocupado` where that one carries `Orgao_Administracao` /
`Cargo_Eletivo_Ocupado` / `Complemento_Cargo_Eletivo_Ocupado` / `Eleito_Controlador`. Reusing the
sibling's contract would leave every test green and the frame wrong.

`Data_Posse` and `Data_Inicio_Primeiro_Mandato` arrive partly blank, so those cells become `NaT`.

Download/unzip/parse is inherited from the private `_BaseFreReader`; this module only declares
which member it reads and how it is typed.
"""

from __future__ import annotations

from typing import ClassVar

from filings_cvm._internal.config.contracts.fre_cia_aberta import FRE_CIA_ABERTA_MEMBRO_COMITE
from filings_cvm._internal.utils.tabular_reader import FileContract
from filings_cvm.ingestion.cia_aberta.doc.fre._base_fre_reader import _BaseFreReader


class FreCiaAbertaMembroComiteReader(_BaseFreReader):
	"""Read the FRE CIA_ABERTA `membros de comitês` member into a typed DataFrame.

	Methods
	-------
	read(int_timeout_s)
		Download, unzip, and parse the reference year's member (inherited).
	"""

	_MEMBER_STEM: ClassVar[str] = "fre_cia_aberta_membro_comite"
	_CONTRACT: ClassVar[FileContract] = FRE_CIA_ABERTA_MEMBRO_COMITE
	_DATE_COLS: ClassVar[tuple[str, ...]] = (
		"Data_Referencia",
		"Data_Eleicao",
		"Data_Posse",
		"Data_Inicio_Primeiro_Mandato",
		"Data_Nascimento",
	)
	_LABEL: ClassVar[str] = "membros de comitês"
