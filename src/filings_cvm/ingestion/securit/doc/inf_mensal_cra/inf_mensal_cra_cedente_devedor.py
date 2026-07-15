"""CVM Informe Mensal CRA — cedente/devedor reader.

The ``inf_mensal_cra_cedente_devedor`` member of ``inf_mensal_cra_AAAA.zip``: the assignors
(*cedentes*) and debtors (*devedores*) behind the receivables, with each one's share
(``Percentual``). **7 columns.** Naturally **long** — many rows per cert, two ``Tipo`` values
(``Cedente``, ``Devedor``) — so no grain is asserted.

⚠️ **``CNPJ`` here is NOT a CNPJ column** — it is a dirty free-text identifier field, and it is the
reason ``tuple_cnpj_cols`` names only ``CNPJ_Emissora``. Across the 2025 file it holds 14-digit
CNPJs (7090), **11-digit CPFs (327 — a cedente/devedor may be a natural person)**, a ``'0'``
placeholder (2352), a bare ``','`` (103), a malformed 15-digit value (72), and **two ids in a
single cell** (12). It is read as exact text and never validated.

⚠️ **Personal data.** A CPF is personal data (LGPD): it is kept **verbatim** in bronze — the raw
bytes are the point — and any minimisation, hashing or access control belongs downstream, never in
this reader.

See ``_base_inf_mensal_cra_reader`` for the shared behaviour (yearly ``date_ref``, shared archive,
``path_raw``).
"""

from __future__ import annotations

from typing import ClassVar

from filings_cvm._internal.config.contracts import INF_MENSAL_CRA_CEDENTE_DEVEDOR, FileContract
from filings_cvm._internal.utils.retry import RetryPolicy
from filings_cvm.ingestion.securit.doc.inf_mensal_cra._base_inf_mensal_cra_reader import (
	_DEFAULT_RETRY_POLICY,
	_BaseInfMensalCraReader,
)


class InfMensalCraCedenteDevedorReader(_BaseInfMensalCraReader):
	"""Read the Informe Mensal CRA cedente/devedor into a typed DataFrame."""

	_MEMBER_STEM: ClassVar[str] = "inf_mensal_cra_cedente_devedor"
	_CONTRACT: ClassVar[FileContract] = INF_MENSAL_CRA_CEDENTE_DEVEDOR
	_LABEL: ClassVar[str] = "cedente/devedor"
	_DATE_COLS: ClassVar[tuple[str, ...]] = ("Data_Referencia",)
	_RETRY_POLICY: ClassVar[RetryPolicy | None] = _DEFAULT_RETRY_POLICY
