"""CVM FRE CIA_ABERTA (distribuição por classe) — ingestion (leitura) reader.

Free float broken down by preferential share class.

Download/unzip/parse is inherited from the private `_BaseFreReader`; this module only declares
which member it reads and how it is typed.
"""

from __future__ import annotations

from typing import ClassVar

from filings_cvm._internal.config.contracts.fre_cia_aberta import (
	FRE_CIA_ABERTA_DISTRIBUICAO_CAPITAL_CLASSE_ACAO,
)
from filings_cvm._internal.utils.tabular_reader import FileContract
from filings_cvm.ingestion.cia_aberta.doc.fre._base_fre_reader import _BaseFreReader


class FreCiaAbertaDistribuicaoCapitalClasseAcaoReader(_BaseFreReader):
	"""Read the FRE CIA_ABERTA `distribuição por classe` member into a typed DataFrame.

	Methods
	-------
	read(int_timeout_s)
		Download, unzip, and parse the reference year's member (inherited).
	"""

	_MEMBER_STEM: ClassVar[str] = "fre_cia_aberta_distribuicao_capital_classe_acao"
	_CONTRACT: ClassVar[FileContract] = FRE_CIA_ABERTA_DISTRIBUICAO_CAPITAL_CLASSE_ACAO
	_DATE_COLS: ClassVar[tuple[str, ...]] = ("Data_Referencia",)
	_LABEL: ClassVar[str] = "distribuição por classe"
