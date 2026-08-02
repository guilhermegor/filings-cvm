"""CVM FRE CIA_ABERTA (remuneração total por órgão) — ingestion (leitura) reader.

Total compensation broken into its components, per company and administrative organ.

The widest member of this slice (27 columns): fixed pay (`Salario`,
`Beneficios_Diretos_Indiretos`, `Participacoes_Comites`), variable pay (`Bonus`,
`Participacao_Resultados`, `Comissoes`), post-employment and share-based amounts, each with its
own free-text description column.

Every monetary and count column stays **exact source text** — a binary float would silently
destroy the published scale; convert to `Decimal` downstream.

Download/unzip/parse is inherited from the private `_BaseFreReader`; this module only declares
which member it reads and how it is typed.
"""

from __future__ import annotations

from typing import ClassVar

from filings_cvm._internal.config.contracts.fre_cia_aberta import (
	FRE_CIA_ABERTA_REMUNERACAO_TOTAL_ORGAO,
)
from filings_cvm._internal.utils.tabular_reader import FileContract
from filings_cvm.ingestion.cia_aberta.doc.fre._base_fre_reader import _BaseFreReader


class FreCiaAbertaRemuneracaoTotalOrgaoReader(_BaseFreReader):
	"""Read this FRE CIA_ABERTA remuneração/valores-mobiliários member into a typed DataFrame.

	Covers `remuneração total por órgão`.

	Methods
	-------
	read(int_timeout_s)
		Download, unzip, and parse the reference year's member (inherited).
	"""

	_MEMBER_STEM: ClassVar[str] = "fre_cia_aberta_remuneracao_total_orgao"
	_CONTRACT: ClassVar[FileContract] = FRE_CIA_ABERTA_REMUNERACAO_TOTAL_ORGAO
	_DATE_COLS: ClassVar[tuple[str, ...]] = (
		"Data_Referencia",
		"Data_Inicio_Exercicio_Social",
		"Data_Fim_Exercicio_Social",
	)
	_LABEL: ClassVar[str] = "remuneração total por órgão"
