"""CVM Informe Mensal OTS — derivativos reader.

The ``inf_mensal_ots_derivativos`` member of ``inf_mensal_ots_AAAA.zip``: the operation's
derivative exposure, as a 4×4 grid — market (termo, futuros, opções, swap) × risk factor (juros,
commodities, câmbio, outros). One row per certificate per reference month. See
``_base_inf_mensal_ots_reader`` for the shared behaviour.
"""

from __future__ import annotations

from typing import ClassVar

from filings_cvm._internal.config.contracts import INF_MENSAL_OTS_DERIVATIVOS, FileContract
from filings_cvm._internal.utils.retry import RetryPolicy
from filings_cvm.ingestion.securit.doc.inf_mensal_ots._base_inf_mensal_ots_reader import (
	_DEFAULT_RETRY_POLICY,
	_BaseInfMensalOtsReader,
)


class InfMensalOtsDerivativosReader(_BaseInfMensalOtsReader):
	"""Read the Informe Mensal OTS derivativos section into a typed DataFrame."""

	_MEMBER_STEM: ClassVar[str] = "inf_mensal_ots_derivativos"
	_CONTRACT: ClassVar[FileContract] = INF_MENSAL_OTS_DERIVATIVOS
	_LABEL: ClassVar[str] = "derivativos"
	_DATE_COLS: ClassVar[tuple[str, ...]] = ("Data_Referencia",)
	_RETRY_POLICY: ClassVar[RetryPolicy | None] = _DEFAULT_RETRY_POLICY
