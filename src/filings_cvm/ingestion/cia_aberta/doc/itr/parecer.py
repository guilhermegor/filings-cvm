"""CVM ITR CIA_ABERTA (relatório de revisão especial e declarações) — ingestion (leitura) reader.

The reviewer's report type and the statements the directors signed, one row per
item.

⚠️⚠️ **This is the one member whose header differs from DFP's.** A quarterly filing gets a *revisão
especial*, not a full audit, so the fifth column is `TP_RELAT_ESP` here and `TP_RELAT_AUD` there —
same width, same position, seven of eight names shared. The contract is generated from this
dataset's own header for exactly that reason.

⚠️ `TP_RELAT_ESP` arrives **partially empty** (4.844 of 7.051 rows in 2025) — a declaration row
carries no review opinion. Blank stays blank, never a placeholder.

Download/unzip/parse is inherited from the private `_BaseItrReader`; this module only declares
which member it reads and how it is typed.
"""

from __future__ import annotations

from typing import ClassVar

from filings_cvm._internal.config.contracts.itr_cia_aberta import (
	ITR_CIA_ABERTA_PARECER,
)
from filings_cvm._internal.utils.tabular_reader import FileContract
from filings_cvm.ingestion.cia_aberta.doc.itr._base_itr_reader import _BaseItrReader


class ItrCiaAbertaParecerReader(_BaseItrReader):
	"""Read this ITR CIA_ABERTA member into a typed DataFrame.

	Covers `relatório de revisão especial e declarações`.

	Methods
	-------
	read(int_timeout_s)
		Download, unzip, and parse the reference year's member (inherited).
	"""

	_MEMBER_STEM: ClassVar[str] = "itr_cia_aberta_parecer"
	_CONTRACT: ClassVar[FileContract] = ITR_CIA_ABERTA_PARECER
	_DATE_COLS: ClassVar[tuple[str, ...]] = ("DT_REFER",)
	_LABEL: ClassVar[str] = "relatório de revisão especial e declarações"
