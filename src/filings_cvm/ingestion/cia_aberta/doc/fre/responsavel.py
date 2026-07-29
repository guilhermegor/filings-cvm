"""CVM FRE CIA_ABERTA (responsáveis) — ingestion (leitura) reader.

The people who signed off the form — name and role.

``Nome_Responsavel`` is an individual's name, but this member carries **no CPF**; the CPF-bearing
members of FRE are all in the administração/pessoas slice.

Download/unzip/parse is inherited from the private `_BaseFreReader`; this module only declares
which member it reads and how it is typed.
"""

from __future__ import annotations

from typing import ClassVar

from filings_cvm._internal.config.contracts.fre_cia_aberta import FRE_CIA_ABERTA_RESPONSAVEL
from filings_cvm._internal.utils.tabular_reader import FileContract
from filings_cvm.ingestion.cia_aberta.doc.fre._base_fre_reader import _BaseFreReader


class FreCiaAbertaResponsavelReader(_BaseFreReader):
	"""Read the FRE CIA_ABERTA `responsáveis` member into a typed DataFrame.

	Methods
	-------
	read(int_timeout_s)
		Download, unzip, and parse the reference year's member (inherited).
	"""

	_MEMBER_STEM: ClassVar[str] = "fre_cia_aberta_responsavel"
	_CONTRACT: ClassVar[FileContract] = FRE_CIA_ABERTA_RESPONSAVEL
	_DATE_COLS: ClassVar[tuple[str, ...]] = ("Data_Referencia",)
	_LABEL: ClassVar[str] = "responsáveis"
