"""CVM FRE CIA_ABERTA (relações familiares) — ingestion (leitura) reader.

Family ties between a company's administrators and other administrators or controlling
shareholders — who is related to whom, in which issuer, and how.

⚠️ **Contains personal data, and it is the densest member for it in this dataset.** Two names and
**two CPF columns** (`CPF_Administrador`, `CPF_Pessoa_Relacionada`) describe the individuals on
both sides of the relationship. Neither CPF column is declared a CNPJ column, and neither is
altered: `CPF_Administrador` even carries a 14-digit placeholder in 2025, which is returned as
published rather than blanked.

⚠️ **Three CNPJ columns**, not one: the filing company plus the issuer of each side
(`CNPJ_Emissor`, `CNPJ_Emissor_Pessoa_Relacionada`). The last of these carries a handful of
`00.000.000/0000-00` placeholders alongside thousands of real values; it stays declared because
the contract requires **at least one** valid CNPJ, not all of them.

Download/unzip/parse is inherited from the private `_BaseFreReader`; this module only declares
which member it reads and how it is typed.
"""

from __future__ import annotations

from typing import ClassVar

from filings_cvm._internal.config.contracts.fre_cia_aberta import FRE_CIA_ABERTA_RELACAO_FAMILIAR
from filings_cvm._internal.utils.tabular_reader import FileContract
from filings_cvm.ingestion.cia_aberta.doc.fre._base_fre_reader import _BaseFreReader


class FreCiaAbertaRelacaoFamiliarReader(_BaseFreReader):
	"""Read the FRE CIA_ABERTA `relações familiares` member into a typed DataFrame.

	Methods
	-------
	read(int_timeout_s)
		Download, unzip, and parse the reference year's member (inherited).
	"""

	_MEMBER_STEM: ClassVar[str] = "fre_cia_aberta_relacao_familiar"
	_CONTRACT: ClassVar[FileContract] = FRE_CIA_ABERTA_RELACAO_FAMILIAR
	_DATE_COLS: ClassVar[tuple[str, ...]] = ("Data_Referencia",)
	_LABEL: ClassVar[str] = "relações familiares"
