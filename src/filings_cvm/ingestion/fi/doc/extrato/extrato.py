"""CVM Extrato FI (2020 onward) — ingestion (leitura) reader.

Reads `extrato_fi_AAAA.csv` (dataset `FI/DOC/EXTRATO`) for the current schema — **117 columns**,
keyed by `TP_FUNDO_CLASSE` + `CNPJ_FUNDO_CLASSE`, years **2020** onward. For `2015`–`2019` use
:class:`ExtratoFiPre2020Reader`, whose 116-column header predates the split.

⚠️ The file holds **every extrato delivered in that year**, so a fund appears once per filing — the
grain is the *filing*, not the fund. For one row per fund (its latest filing) use
:class:`ExtratoFiSnapshotReader`, which reads a different artifact.
"""

from __future__ import annotations

from typing import ClassVar

from filings_cvm._internal.config.contracts.extrato_fi import EXTRATO_FI
from filings_cvm._internal.utils.tabular_reader import FileContract
from filings_cvm.ingestion.fi.doc.extrato._base_extrato_reader import _BaseExtratoYearlyReader


class ExtratoFiReader(_BaseExtratoYearlyReader):
	"""Read a year of CVM Extrato FI filings (2020 onward) into a typed DataFrame.

	Concrete :class:`IngestionReader` for `extrato_fi_AAAA.csv` from 2020 — one row per extrato
	delivered in the reference year.

	Methods
	-------
	read(int_timeout_s)
		Download and parse the reference year's filings into a validated DataFrame (inherited).
	"""

	_CONTRACT: ClassVar[FileContract] = EXTRATO_FI
	_LABEL: ClassVar[str] = "2020 onward"
	_SIBLING: ClassVar[str] = "ExtratoFiPre2020Reader"

	# Where the header gains its extra column, measured across the published years rather than
	# inferred from a regulation, since Resolução CVM 175 postdates this change by years.
	_FIRST_YEAR: ClassVar[int | None] = 2020
	_LAST_YEAR: ClassVar[int | None] = None
