"""CVM FRE CIA_ABERTA (capital social) — ingestion (leitura) reader.

The company's share capital: type, authorised value, paid-up deadline and the ordinary /
preferential / total share counts.

``Valor_Capital`` and every ``Quantidade_*`` column stay **exact source text** — money and counts
are never binary floats here.

Download/unzip/parse is inherited from the private `_BaseFreReader`; this module only declares
which member it reads and how it is typed.
"""

from __future__ import annotations

from typing import ClassVar

from filings_cvm._internal.config.contracts.fre_cia_aberta import FRE_CIA_ABERTA_CAPITAL_SOCIAL
from filings_cvm._internal.utils.tabular_reader import FileContract
from filings_cvm.ingestion.cia_aberta.doc.fre._base_fre_reader import _BaseFreReader


class FreCiaAbertaCapitalSocialReader(_BaseFreReader):
	"""Read the FRE CIA_ABERTA `capital social` member into a typed DataFrame.

	Methods
	-------
	read(int_timeout_s)
		Download, unzip, and parse the reference year's member (inherited).
	"""

	_MEMBER_STEM: ClassVar[str] = "fre_cia_aberta_capital_social"
	_CONTRACT: ClassVar[FileContract] = FRE_CIA_ABERTA_CAPITAL_SOCIAL
	_DATE_COLS: ClassVar[tuple[str, ...]] = (
		"Data_Referencia",
		"Data_Autorizacao_Aprovacao",
	)
	_LABEL: ClassVar[str] = "capital social"
