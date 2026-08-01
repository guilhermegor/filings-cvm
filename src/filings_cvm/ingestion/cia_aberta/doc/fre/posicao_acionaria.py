"""CVM FRE CIA_ABERTA (posição acionária) — ingestion (leitura) reader.

The shareholder base: who holds what, how much of each share type is outstanding, and whether the
holder is a controller or party to a shareholders' agreement. At ~31,5k rows it is the largest
member of this slice.

⚠️ **Three mixed `CPF_CNPJ_*` columns, none of them declared a CNPJ column.**
`CPF_CNPJ_Acionista`, `CPF_CNPJ_Acionista_Relacionado` and `CPF_CNPJ_Representante_legal` hold
either document — in 2025 the first measured 9.841 CPF against 6.542 CNPJ — so they carry personal
data and cannot be asserted valid as CNPJ. They are returned as exact published text, placeholders
included. Only the filing company's `CNPJ_Companhia` is declared.

⚠️ `CPF_CNPJ_Representante_legal` is spelled with a lowercase `legal` by CVM. The name is
preserved verbatim; it is not normalised to match its siblings.

⚠️ `Data_Composicao_Capital_Social` arrived **entirely blank** in 2025, so the column is all
`NaT`; `Data_Ultima_Alteracao` is about half blank. Both are dates by contract.

`Quantidade_*` and `Percentual_*` are counts and percentages that stay exact text — never a binary
float; convert downstream.

Download/unzip/parse is inherited from the private `_BaseFreReader`; this module only declares
which member it reads and how it is typed.
"""

from __future__ import annotations

from typing import ClassVar

from filings_cvm._internal.config.contracts.fre_cia_aberta import FRE_CIA_ABERTA_POSICAO_ACIONARIA
from filings_cvm._internal.utils.tabular_reader import FileContract
from filings_cvm.ingestion.cia_aberta.doc.fre._base_fre_reader import _BaseFreReader


class FreCiaAbertaPosicaoAcionariaReader(_BaseFreReader):
	"""Read the FRE CIA_ABERTA `posição acionária` member into a typed DataFrame.

	Methods
	-------
	read(int_timeout_s)
		Download, unzip, and parse the reference year's member (inherited).
	"""

	_MEMBER_STEM: ClassVar[str] = "fre_cia_aberta_posicao_acionaria"
	_CONTRACT: ClassVar[FileContract] = FRE_CIA_ABERTA_POSICAO_ACIONARIA
	_DATE_COLS: ClassVar[tuple[str, ...]] = (
		"Data_Referencia",
		"Data_Composicao_Capital_Social",
		"Data_Ultima_Alteracao",
	)
	_LABEL: ClassVar[str] = "posição acionária"
