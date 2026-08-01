"""CVM FRE CIA_ABERTA (auditores independentes) — ingestion (leitura) reader.

The independent auditor each company contracted, with the engagement dates and the fees paid.

⚠️ **Contains personal data.** `CPF_Auditor` identifies an individual auditor and is returned as
exact published text; it is **never** declared a CNPJ column, even in a year whose only value
happens to pass a CNPJ check.

⚠️ **The two CNPJ columns do not share a mask style.** `CNPJ_Companhia` arrives punctuated
(`00.000.000/0001-91`) while `CNPJ_Auditor`, on the same row, arrives as bare digits
(`49928567000111`). Both are declared as CNPJ columns — the validator normalises punctuation —
and both are returned exactly as published.

⚠️ `Data_Fim_Contratacao` arrived **entirely blank** in 2025, so the column is all `NaT`. It is a
date by contract regardless; an open engagement simply has no end date.

`Remuneracao_Auditor` is free text describing the fees (it embeds control characters CVM uses as
bullet markers), not a number — it stays exact text and is not parsed.

Download/unzip/parse is inherited from the private `_BaseFreReader`; this module only declares
which member it reads and how it is typed.
"""

from __future__ import annotations

from typing import ClassVar

from filings_cvm._internal.config.contracts.fre_cia_aberta import FRE_CIA_ABERTA_AUDITOR
from filings_cvm._internal.utils.tabular_reader import FileContract
from filings_cvm.ingestion.cia_aberta.doc.fre._base_fre_reader import _BaseFreReader


class FreCiaAbertaAuditorReader(_BaseFreReader):
	"""Read the FRE CIA_ABERTA `auditores` member into a typed DataFrame.

	Methods
	-------
	read(int_timeout_s)
		Download, unzip, and parse the reference year's member (inherited).
	"""

	_MEMBER_STEM: ClassVar[str] = "fre_cia_aberta_auditor"
	_CONTRACT: ClassVar[FileContract] = FRE_CIA_ABERTA_AUDITOR
	_DATE_COLS: ClassVar[tuple[str, ...]] = (
		"Data_Referencia",
		"Data_Inicio_Contratacao",
		"Data_Fim_Contratacao",
		"Data_Inicio_Prestacao_Servico",
	)
	_LABEL: ClassVar[str] = "auditores"
