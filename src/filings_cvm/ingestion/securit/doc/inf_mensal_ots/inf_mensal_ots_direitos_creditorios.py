"""CVM Informe Mensal OTS — direitos creditórios reader.

The ``inf_mensal_ots_direitos_creditorios`` member of ``inf_mensal_ots_AAAA.zip``: the
credit-rights portfolio — amounts falling due and unpaid by ageing band, pre-payments, guarantees
and co-obligation percentages, duration, and the concentration of the largest debtors and
assignors. One row per certificate per reference month (43 columns, the widest section). See
``_base_inf_mensal_ots_reader`` for the shared behaviour.
"""

from __future__ import annotations

from typing import ClassVar

from filings_cvm._internal.config.contracts import (
	INF_MENSAL_OTS_DIREITOS_CREDITORIOS,
	FileContract,
)
from filings_cvm._internal.utils.retry import RetryPolicy
from filings_cvm.ingestion.securit.doc.inf_mensal_ots._base_inf_mensal_ots_reader import (
	_DEFAULT_RETRY_POLICY,
	_BaseInfMensalOtsReader,
)


class InfMensalOtsDireitosCreditoriosReader(_BaseInfMensalOtsReader):
	"""Read the Informe Mensal OTS direitos creditórios section into a typed DataFrame."""

	_MEMBER_STEM: ClassVar[str] = "inf_mensal_ots_direitos_creditorios"
	_CONTRACT: ClassVar[FileContract] = INF_MENSAL_OTS_DIREITOS_CREDITORIOS
	_LABEL: ClassVar[str] = "direitos creditórios"
	_DATE_COLS: ClassVar[tuple[str, ...]] = ("Data_Referencia",)
	_RETRY_POLICY: ClassVar[RetryPolicy | None] = _DEFAULT_RETRY_POLICY
