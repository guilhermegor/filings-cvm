"""CVM Informe Mensal OTS — fluxo de caixa reader.

The ``inf_mensal_ots_fluxo_caixa`` member of ``inf_mensal_ots_AAAA.zip``: the operation's cash
flow — credit receipts, expense payments, payments to each class (senior / subordinada mezanino /
subordinada junior, each split into principal amortisation and interest), cash acquisitions and
disposals, and the net cash variation. One row per certificate per reference month. See
``_base_inf_mensal_ots_reader`` for the shared behaviour.
"""

from __future__ import annotations

from typing import ClassVar

from filings_cvm._internal.config.contracts import INF_MENSAL_OTS_FLUXO_CAIXA, FileContract
from filings_cvm._internal.utils.retry import RetryPolicy
from filings_cvm.ingestion.securit.doc.inf_mensal_ots._base_inf_mensal_ots_reader import (
	_DEFAULT_RETRY_POLICY,
	_BaseInfMensalOtsReader,
)


class InfMensalOtsFluxoCaixaReader(_BaseInfMensalOtsReader):
	"""Read the Informe Mensal OTS fluxo de caixa section into a typed DataFrame."""

	_MEMBER_STEM: ClassVar[str] = "inf_mensal_ots_fluxo_caixa"
	_CONTRACT: ClassVar[FileContract] = INF_MENSAL_OTS_FLUXO_CAIXA
	_LABEL: ClassVar[str] = "fluxo de caixa"
	_DATE_COLS: ClassVar[tuple[str, ...]] = ("Data_Referencia",)
	_RETRY_POLICY: ClassVar[RetryPolicy | None] = _DEFAULT_RETRY_POLICY
