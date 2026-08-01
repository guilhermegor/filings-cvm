"""CVM FRE CIA_ABERTA (relações de subordinação) — ingestion (leitura) reader.

Subordination, service and control relationships between a company's administrators and related
parties, over a declared fiscal year.

⚠️ **Contains personal data.** `Nome_Administrador` / `CPF_Administrador` identify an individual;
the CPF is returned as exact published text and is never declared a CNPJ column.

⚠️ **`Documento_Pessoa_Relacionada` holds CNPJ *and* CPF and is deliberately NOT a CNPJ column.**
Its name says neither, but it is the counterparty's document, typed by the sibling
`Tipo_Pessoa_Relacionada` flag (`PJ` / `PF`) — in 2025 it measured 8.462 CNPJ against 34 CPF, plus
placeholders. Declaring it would both assert a validity the data does not have and treat personal
data as a company identifier. **The header name is not evidence of what a column holds; the values
are.**

Download/unzip/parse is inherited from the private `_BaseFreReader`; this module only declares
which member it reads and how it is typed.
"""

from __future__ import annotations

from typing import ClassVar

from filings_cvm._internal.config.contracts.fre_cia_aberta import (
	FRE_CIA_ABERTA_RELACAO_SUBORDINACAO,
)
from filings_cvm._internal.utils.tabular_reader import FileContract
from filings_cvm.ingestion.cia_aberta.doc.fre._base_fre_reader import _BaseFreReader


class FreCiaAbertaRelacaoSubordinacaoReader(_BaseFreReader):
	"""Read the FRE CIA_ABERTA `relações de subordinação` member into a typed DataFrame.

	Methods
	-------
	read(int_timeout_s)
		Download, unzip, and parse the reference year's member (inherited).
	"""

	_MEMBER_STEM: ClassVar[str] = "fre_cia_aberta_relacao_subordinacao"
	_CONTRACT: ClassVar[FileContract] = FRE_CIA_ABERTA_RELACAO_SUBORDINACAO
	_DATE_COLS: ClassVar[tuple[str, ...]] = (
		"Data_Referencia",
		"Data_Inicio_Exercicio_Social",
		"Data_Fim_Exercicio_Social",
	)
	_LABEL: ClassVar[str] = "relações de subordinação"
