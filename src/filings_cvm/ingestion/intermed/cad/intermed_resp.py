"""CVM INTERMED/CAD — responsible-officer table reader.

The ``cad_intermed_resp.csv`` member of ``cad_intermed.zip``: one row per responsible officer of a
market intermediary (the intermediary's `TP_PARTIC`/`CNPJ`/`DENOM_SOCIAL` and registration date,
plus the officer's role, name, start date and e-mail). ⚠️ Carries personal data (`RESP`,
`EMAIL_RESP`) but **no CPF column** — the only CNPJ is the intermediary's. See
``_base_intermed_reader`` for the shared behaviour.
"""

from __future__ import annotations

from typing import ClassVar

from filings_cvm._internal.config.contracts import CAD_INTERMED_RESP, FileContract
from filings_cvm.ingestion.intermed.cad._base_intermed_reader import _BaseIntermedReader


class IntermedRespReader(_BaseIntermedReader):
	"""Read the INTERMED/CAD responsible-officer table into a typed DataFrame."""

	_MEMBER: ClassVar[str] = "cad_intermed_resp.csv"
	_CONTRACT: ClassVar[FileContract] = CAD_INTERMED_RESP
	_DATE_COLS: ClassVar[tuple[str, ...]] = ("DT_REG", "DT_INI_RESP")
	_LABEL: ClassVar[str] = "responsável"
