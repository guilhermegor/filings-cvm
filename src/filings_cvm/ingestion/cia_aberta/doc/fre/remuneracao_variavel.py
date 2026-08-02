"""CVM FRE CIA_ABERTA (remuneração variável) — ingestion (leitura) reader.

Variable compensation: bonus and profit-sharing, each as minimum / maximum / on-target /
actually paid, per company and organ.

The eight `Bonus_Valor_*` and `Participacao_Valor_*` columns stay **exact source text** — money,
never a binary float; convert to `Decimal` downstream.

Download/unzip/parse is inherited from the private `_BaseFreReader`; this module only declares
which member it reads and how it is typed.
"""

from __future__ import annotations

from typing import ClassVar

from filings_cvm._internal.config.contracts.fre_cia_aberta import (
	FRE_CIA_ABERTA_REMUNERACAO_VARIAVEL,
)
from filings_cvm._internal.utils.tabular_reader import FileContract
from filings_cvm.ingestion.cia_aberta.doc.fre._base_fre_reader import _BaseFreReader


class FreCiaAbertaRemuneracaoVariavelReader(_BaseFreReader):
	"""Read this FRE CIA_ABERTA remuneração/valores-mobiliários member into a typed DataFrame.

	Covers `remuneração variável`.

	Methods
	-------
	read(int_timeout_s)
		Download, unzip, and parse the reference year's member (inherited).
	"""

	_MEMBER_STEM: ClassVar[str] = "fre_cia_aberta_remuneracao_variavel"
	_CONTRACT: ClassVar[FileContract] = FRE_CIA_ABERTA_REMUNERACAO_VARIAVEL
	_DATE_COLS: ClassVar[tuple[str, ...]] = (
		"Data_Referencia",
		"Data_Inicio_Exercicio_Social",
		"Data_Fim_Exercicio_Social",
	)
	_LABEL: ClassVar[str] = "remuneração variável"
