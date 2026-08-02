"""CVM FRE CIA_ABERTA (remuneração máxima, mínima e média) — ingestion (leitura) reader.

Highest, lowest and average individual compensation paid by each organ.

⚠️ **No individual is identified.** The row is a per-organ statistic, so the largest salary in a
company appears without the person who received it — this member carries **no personal data**
despite reporting individual-level amounts.

⚠️ Third of the three 14-column members of this slice (with `acao_entregue` and
`remuneracao_acao`); its own header is the only source of its column list.

`Valor_*` and `Numero_*` stay **exact source text**; convert to `Decimal` downstream.

Download/unzip/parse is inherited from the private `_BaseFreReader`; this module only declares
which member it reads and how it is typed.
"""

from __future__ import annotations

from typing import ClassVar

from filings_cvm._internal.config.contracts.fre_cia_aberta import (
	FRE_CIA_ABERTA_REMUNERACAO_MAXIMA_MINIMA_MEDIA,
)
from filings_cvm._internal.utils.tabular_reader import FileContract
from filings_cvm.ingestion.cia_aberta.doc.fre._base_fre_reader import _BaseFreReader


class FreCiaAbertaRemuneracaoMaximaMinimaMediaReader(_BaseFreReader):
	"""Read this FRE CIA_ABERTA remuneração/valores-mobiliários member into a typed DataFrame.

	Covers `remuneração máxima, mínima e média`.

	Methods
	-------
	read(int_timeout_s)
		Download, unzip, and parse the reference year's member (inherited).
	"""

	_MEMBER_STEM: ClassVar[str] = "fre_cia_aberta_remuneracao_maxima_minima_media"
	_CONTRACT: ClassVar[FileContract] = FRE_CIA_ABERTA_REMUNERACAO_MAXIMA_MINIMA_MEDIA
	_DATE_COLS: ClassVar[tuple[str, ...]] = (
		"Data_Referencia",
		"Data_Inicio_Exercicio_Social",
		"Data_Fim_Exercicio_Social",
	)
	_LABEL: ClassVar[str] = "remuneração máxima, mínima e média"
