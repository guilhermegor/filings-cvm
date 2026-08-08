"""CVM Perfil Mensal FI (post-RCVM 175) — ingestion (leitura) reader.

Reads `perfil_mensal_fi_AAAAMM.csv` (dataset `FI/DOC/PERFIL_MENSAL`) for the **post-RCVM 175**
regime — `202312` onward, **107 columns**, keyed by `TP_FUNDO_CLASSE` + `CNPJ_FUNDO_CLASSE`. For
`201901`–`202311` use :class:`PerfilMensalPre175Reader`, whose 106-column header predates the
fund/class split.

This is the reading side of the `PerfilMensal` submission writer: the same regulatory standard, a
**different artifact** (CVM's flat open-data dump, not the submission XML), so it declares its own
`FileContract` rather than reusing the writer's Pydantic schema.

⚠️ Only `CNPJ_FUNDO_CLASSE` is a CNPJ column. The six `CPF_CNPJ_*` fields
(`COMITENTE_1..3`, `EMISSOR_1..3`) hold a **CPF or a CNPJ** — each has a sibling `PF_PJ_*` column
whose domain is `PF`/`PJ`, and the `PF` case occurs in practice — so they are personal data and
stay out of the contract's CNPJ columns.
"""

from __future__ import annotations

from typing import ClassVar

from filings_cvm._internal.config.contracts.perfil_mensal_fi import PERFIL_MENSAL_FI
from filings_cvm._internal.utils.tabular_reader import FileContract
from filings_cvm.ingestion.fi.doc.perfil_mensal._base_perfil_mensal_reader import (
	_BasePerfilMensalReader,
)


class PerfilMensalReader(_BasePerfilMensalReader):
	"""Read the post-RCVM 175 CVM Perfil Mensal FI monthly dump into a typed DataFrame.

	Concrete :class:`IngestionReader` for `perfil_mensal_fi_AAAAMM.csv` from `202312` onward — one
	row per fund/class per competency month.

	Methods
	-------
	read(int_timeout_s)
		Download and parse the reference month's profile into a validated DataFrame (inherited).
	"""

	_CONTRACT: ClassVar[FileContract] = PERFIL_MENSAL_FI
	_LABEL: ClassVar[str] = "post-RCVM 175"
	_SIBLING: ClassVar[str] = "PerfilMensalPre175Reader"

	# RCVM 175's fund/class split lands in the ``202312`` file — measured by binary search over the
	# published headers, not inferred from the regulation's date.
	_FIRST_YM: ClassVar[int | None] = 202312
	_LAST_YM: ClassVar[int | None] = None
