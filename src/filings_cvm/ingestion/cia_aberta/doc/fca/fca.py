"""CVM FCA CIA_ABERTA (índice) — ingestion (leitura) reader.

The **index** member: one row per *Formulário Cadastral* filed, with a ``LINK_DOC`` returned as
text and never followed.

⚠️ This member does **not** share its nine satellites' naming convention — it uses the uppercase,
abbreviated ``CNPJ_CIA`` / ``DT_REFER`` / ``DT_RECEB`` / ``DENOM_CIA`` style of
``cad_cia_aberta.csv``, while every satellite uses ``CNPJ_Companhia`` / ``Data_Referencia``.
Writing the ten from one template silently breaks this one.

Download/unzip/parse is inherited from the private `_BaseFcaReader`; this module only declares
which member it reads and how it is typed.
"""

from __future__ import annotations

from typing import ClassVar

from filings_cvm._internal.config.contracts.fca_cia_aberta import FCA_CIA_ABERTA
from filings_cvm._internal.utils.tabular_reader import FileContract
from filings_cvm.ingestion.cia_aberta.doc.fca._base_fca_reader import _BaseFcaReader


class FcaCiaAbertaReader(_BaseFcaReader):
	"""Read the FCA CIA_ABERTA `índice` member into a typed DataFrame.

	Methods
	-------
	read(int_timeout_s)
		Download, unzip, and parse the reference year's member (inherited).
	"""

	_MEMBER_STEM: ClassVar[str] = "fca_cia_aberta"
	_CONTRACT: ClassVar[FileContract] = FCA_CIA_ABERTA
	_DATE_COLS: ClassVar[tuple[str, ...]] = (
		"DT_REFER",
		"DT_RECEB",
	)
	_LABEL: ClassVar[str] = "índice"
