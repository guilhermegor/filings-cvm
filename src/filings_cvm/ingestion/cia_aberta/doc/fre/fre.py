"""CVM FRE CIA_ABERTA (índice) — ingestion (leitura) reader.

The **index** member: one row per *Formulário de Referência* filed, with a ``LINK_DOC``
returned as text and never followed.

⚠️ This member uses the uppercase, abbreviated ``CNPJ_CIA`` / ``DT_REFER`` / ``DT_RECEB`` /
``DENOM_CIA`` style — **not** the ``CNPJ_Companhia`` / ``Data_Referencia`` of its 35 satellites.
FCA's index does the same; CGVN's does not.

Download/unzip/parse is inherited from the private `_BaseFreReader`; this module only declares
which member it reads and how it is typed.
"""

from __future__ import annotations

from typing import ClassVar

from filings_cvm._internal.config.contracts.fre_cia_aberta import FRE_CIA_ABERTA
from filings_cvm._internal.utils.tabular_reader import FileContract
from filings_cvm.ingestion.cia_aberta.doc.fre._base_fre_reader import _BaseFreReader


class FreCiaAbertaReader(_BaseFreReader):
	"""Read the FRE CIA_ABERTA `índice` member into a typed DataFrame.

	Methods
	-------
	read(int_timeout_s)
		Download, unzip, and parse the reference year's member (inherited).
	"""

	_MEMBER_STEM: ClassVar[str] = "fre_cia_aberta"
	_CONTRACT: ClassVar[FileContract] = FRE_CIA_ABERTA
	_DATE_COLS: ClassVar[tuple[str, ...]] = (
		"DT_REFER",
		"DT_RECEB",
	)
	_LABEL: ClassVar[str] = "índice"
