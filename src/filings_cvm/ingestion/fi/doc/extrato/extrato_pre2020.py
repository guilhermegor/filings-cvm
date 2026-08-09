"""CVM Extrato FI (pre-2020) — ingestion (leitura) reader.

Reads `extrato_fi_AAAA.csv` (dataset `FI/DOC/EXTRATO`) for the legacy schema — **116 columns**,
keyed by a single `CNPJ_FUNDO`, years **2015** through **2019**. From 2020 CVM replaced that one
column with `TP_FUNDO_CLASSE` + `CNPJ_FUNDO_CLASSE`; use :class:`ExtratoFiReader` for those years.

⚠️ **The name says `Pre2020`, not `Pre175`, and that is deliberate.** The column change is the same
one the Perfil Mensal underwent, but there it lands at `202312` and here at **2020** — and
Resolução CVM 175 dates from December 2022, so it cannot be the cause here. A reader name is an
assertion; this one is named for the year that was **measured** in the published headers.

⚠️ The other **115 columns are identical** to the current regime (measured, position for position),
so deriving one contract from the other is right about 115 of 116 names — which is exactly why each
is pinned to its own published header.
"""

from __future__ import annotations

from typing import ClassVar

from filings_cvm._internal.config.contracts.extrato_fi import EXTRATO_FI_PRE2020
from filings_cvm._internal.utils.tabular_reader import FileContract
from filings_cvm.ingestion.fi.doc.extrato._base_extrato_reader import _BaseExtratoYearlyReader


class ExtratoFiPre2020Reader(_BaseExtratoYearlyReader):
	"""Read a year of legacy CVM Extrato FI filings (2015-2019) into a typed DataFrame.

	Concrete :class:`IngestionReader` for `extrato_fi_AAAA.csv` through 2019 — one row per extrato
	delivered in the reference year.

	Methods
	-------
	read(int_timeout_s)
		Download and parse the reference year's filings into a validated DataFrame (inherited).
	"""

	_CONTRACT: ClassVar[FileContract] = EXTRATO_FI_PRE2020
	_LABEL: ClassVar[str] = "pre-2020"
	_SIBLING: ClassVar[str] = "ExtratoFiReader"

	# The published series starts at ``2015``; ``2019`` is the last 116-column year, measured.
	_FIRST_YEAR: ClassVar[int | None] = 2015
	_LAST_YEAR: ClassVar[int | None] = 2019
