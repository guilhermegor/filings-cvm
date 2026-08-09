"""CVM Perfil Mensal FI (pre-RCVM 175) — ingestion (leitura) reader.

Reads `perfil_mensal_fi_AAAAMM.csv` (dataset `FI/DOC/PERFIL_MENSAL`) for the **pre-RCVM 175**
regime — `201901` through `202311`, **106 columns**, keyed by a single `CNPJ_FUNDO`. From `202312`
CVM's fund/class split replaced that one column with `TP_FUNDO_CLASSE` + `CNPJ_FUNDO_CLASSE`; use
:class:`PerfilMensalReader` for those months.

⚠️ The other **105 columns are identical** between the two regimes (measured). The whole
difference is that leading key block — which is exactly why each contract is generated from, and
pinned to, its own published header rather than derived from its sibling.
"""

from __future__ import annotations

from typing import ClassVar

from filings_cvm._internal.config.contracts.perfil_mensal_fi import PERFIL_MENSAL_FI_PRE175
from filings_cvm._internal.utils.tabular_reader import FileContract
from filings_cvm.ingestion.fi.doc.perfil_mensal._base_perfil_mensal_reader import (
	_BasePerfilMensalReader,
)


class PerfilMensalPre175Reader(_BasePerfilMensalReader):
	"""Read the pre-RCVM 175 CVM Perfil Mensal FI monthly dump into a typed DataFrame.

	Concrete :class:`IngestionReader` for `perfil_mensal_fi_AAAAMM.csv` from `201901` through
	`202311` — one row per fund per competency month.

	Methods
	-------
	read(int_timeout_s)
		Download and parse the reference month's profile into a validated DataFrame (inherited).
	"""

	_CONTRACT: ClassVar[FileContract] = PERFIL_MENSAL_FI_PRE175
	_LABEL: ClassVar[str] = "pre-RCVM 175"
	_SIBLING: ClassVar[str] = "PerfilMensalReader"

	# The series starts at ``201901``; ``202311`` is the last 106-column month, measured.
	_FIRST_YM: ClassVar[int | None] = 201901
	_LAST_YM: ClassVar[int | None] = 202311
