"""CVM FRE CIA_ABERTA (capital social por classe) — ingestion (leitura) reader.

Share capital broken down by preferential share class, keyed to its parent by
``ID_Capital_Social``.

Download/unzip/parse is inherited from the private `_BaseFreReader`; this module only declares
which member it reads and how it is typed.
"""

from __future__ import annotations

from typing import ClassVar

from filings_cvm._internal.config.contracts.fre_cia_aberta import (
	FRE_CIA_ABERTA_CAPITAL_SOCIAL_CLASSE_ACAO,
)
from filings_cvm._internal.utils.tabular_reader import FileContract
from filings_cvm.ingestion.cia_aberta.doc.fre._base_fre_reader import _BaseFreReader


class FreCiaAbertaCapitalSocialClasseAcaoReader(_BaseFreReader):
	"""Read the FRE CIA_ABERTA `capital social por classe` member into a typed DataFrame.

	Methods
	-------
	read(int_timeout_s)
		Download, unzip, and parse the reference year's member (inherited).
	"""

	_MEMBER_STEM: ClassVar[str] = "fre_cia_aberta_capital_social_classe_acao"
	_CONTRACT: ClassVar[FileContract] = FRE_CIA_ABERTA_CAPITAL_SOCIAL_CLASSE_ACAO
	_DATE_COLS: ClassVar[tuple[str, ...]] = ("Data_Referencia",)
	_LABEL: ClassVar[str] = "capital social por classe"
