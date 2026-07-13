"""CVM Informe Mensal OTS — desembolso reader.

The ``inf_mensal_ots_desembolso`` member of ``inf_mensal_ots_AAAA.zip``: the operation's scheduled
disbursements — payments of expenses and payments to investors, each broken down by ageing band (up
to 30 days … above 361 days). One row per certificate per reference month. See
``_base_inf_mensal_ots_reader`` for the shared behaviour.
"""

from __future__ import annotations

from typing import ClassVar

from filings_cvm._internal.config.contracts import INF_MENSAL_OTS_DESEMBOLSO, FileContract
from filings_cvm._internal.utils.retry import RetryPolicy
from filings_cvm.ingestion.securit.doc.inf_mensal_ots._base_inf_mensal_ots_reader import (
	_DEFAULT_RETRY_POLICY,
	_BaseInfMensalOtsReader,
)


class InfMensalOtsDesembolsoReader(_BaseInfMensalOtsReader):
	"""Read the Informe Mensal OTS desembolso section into a typed DataFrame."""

	_MEMBER_STEM: ClassVar[str] = "inf_mensal_ots_desembolso"
	_CONTRACT: ClassVar[FileContract] = INF_MENSAL_OTS_DESEMBOLSO
	_LABEL: ClassVar[str] = "desembolso"
	_DATE_COLS: ClassVar[tuple[str, ...]] = ("Data_Referencia",)
	_RETRY_POLICY: ClassVar[RetryPolicy | None] = _DEFAULT_RETRY_POLICY
