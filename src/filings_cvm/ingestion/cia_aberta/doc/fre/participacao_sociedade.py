"""CVM FRE CIA_ABERTA (participações em sociedades) — ingestion (leitura) reader.

Equity stakes the company holds in other companies.

⚠️ **The only member of this slice with two CNPJ columns** — `CNPJ_Companhia` (the filer) and
`CNPJ` (the invested company). 792 of the 6.511 `CNPJ` values in 2025 are the literal placeholder
`00000000000000`, which is what the CVM publishes for **subsidiaries abroad with no Brazilian
CNPJ**; none is malformed and none is blank. They are returned **as published**, and the column
stays declared because the contract requires *at least one* valid CNPJ, not all of them.

⚠️ **`Data_Valor_Mercado` and `Data_Valor_Contabil` arrive 100% empty in 2025 and are still dates
by contract** (the dataset's META types both `date`), so every value becomes `NaT` rather than an
empty string. Twelve of this member's columns are empty in 2025; emptiness is a property of the
year, not of the schema.

`Valor_Mercado`, `Valor_Contabil` and `Participacao_Emissor` stay **exact source text**.

Download/unzip/parse is inherited from the private `_BaseFreReader`; this module only declares
which member it reads and how it is typed.
"""

from __future__ import annotations

from typing import ClassVar

from filings_cvm._internal.config.contracts.fre_cia_aberta import (
	FRE_CIA_ABERTA_PARTICIPACAO_SOCIEDADE,
)
from filings_cvm._internal.utils.tabular_reader import FileContract
from filings_cvm.ingestion.cia_aberta.doc.fre._base_fre_reader import _BaseFreReader


class FreCiaAbertaParticipacaoSociedadeReader(_BaseFreReader):
	"""Read this FRE CIA_ABERTA remuneração/valores-mobiliários member into a typed DataFrame.

	Covers `participações em sociedades`.

	Methods
	-------
	read(int_timeout_s)
		Download, unzip, and parse the reference year's member (inherited).
	"""

	_MEMBER_STEM: ClassVar[str] = "fre_cia_aberta_participacao_sociedade"
	_CONTRACT: ClassVar[FileContract] = FRE_CIA_ABERTA_PARTICIPACAO_SOCIEDADE
	_DATE_COLS: ClassVar[tuple[str, ...]] = (
		"Data_Referencia",
		"Data_Valor_Mercado",
		"Data_Valor_Contabil",
	)
	_LABEL: ClassVar[str] = "participações em sociedades"
