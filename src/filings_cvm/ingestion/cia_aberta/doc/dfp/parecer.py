"""CVM DFP CIA_ABERTA (parecer e declarações) — ingestion (leitura) reader.

The auditor's report type and the statements the directors signed, one row per
item.

⚠️ `TP_RELAT_AUD` arrives **partially empty** — a declaration row carries no audit opinion. Blank
stays blank, never a placeholder.

Download/unzip/parse is inherited from the private `_BaseDfpReader`; this module only declares
which member it reads and how it is typed.
"""

from __future__ import annotations

from typing import ClassVar

from filings_cvm._internal.config.contracts.dfp_cia_aberta import (
	DFP_CIA_ABERTA_PARECER,
)
from filings_cvm._internal.utils.tabular_reader import FileContract
from filings_cvm.ingestion.cia_aberta.doc.dfp._base_dfp_reader import _BaseDfpReader


class DfpCiaAbertaParecerReader(_BaseDfpReader):
	"""Read this DFP CIA_ABERTA member into a typed DataFrame.

	Covers `parecer e declarações`.

	Methods
	-------
	read(int_timeout_s)
		Download, unzip, and parse the reference year's member (inherited).
	"""

	_MEMBER_STEM: ClassVar[str] = "dfp_cia_aberta_parecer"
	_CONTRACT: ClassVar[FileContract] = DFP_CIA_ABERTA_PARECER
	_DATE_COLS: ClassVar[tuple[str, ...]] = ("DT_REFER",)
	_LABEL: ClassVar[str] = "parecer e declarações"
