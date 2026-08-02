"""CVM FRE CIA_ABERTA (remuneração baseada em ações) — ingestion (leitura) reader.

Share-based compensation: potential dilution and weighted-average option prices.

⚠️ **Same width as `acao_entregue` and `remuneracao_maxima_minima_media` (14 columns), same first
ten, different last four.** Copying either sibling would ship a wrong column list that only the
pinned header catches.

`Diluicao_Potencial`, the `Preco_Medio_Ponderado_*` and `Quantidade_*` columns stay **exact source
text**; convert to `Decimal` downstream.

Download/unzip/parse is inherited from the private `_BaseFreReader`; this module only declares
which member it reads and how it is typed.
"""

from __future__ import annotations

from typing import ClassVar

from filings_cvm._internal.config.contracts.fre_cia_aberta import (
	FRE_CIA_ABERTA_REMUNERACAO_ACAO,
)
from filings_cvm._internal.utils.tabular_reader import FileContract
from filings_cvm.ingestion.cia_aberta.doc.fre._base_fre_reader import _BaseFreReader


class FreCiaAbertaRemuneracaoAcaoReader(_BaseFreReader):
	"""Read this FRE CIA_ABERTA remuneração/valores-mobiliários member into a typed DataFrame.

	Covers `remuneração baseada em ações`.

	Methods
	-------
	read(int_timeout_s)
		Download, unzip, and parse the reference year's member (inherited).
	"""

	_MEMBER_STEM: ClassVar[str] = "fre_cia_aberta_remuneracao_acao"
	_CONTRACT: ClassVar[FileContract] = FRE_CIA_ABERTA_REMUNERACAO_ACAO
	_DATE_COLS: ClassVar[tuple[str, ...]] = (
		"Data_Referencia",
		"Data_Inicio_Exercicio_Social",
		"Data_Fim_Exercicio_Social",
	)
	_LABEL: ClassVar[str] = "remuneração baseada em ações"
