"""CVM Informe Mensal CRA — derivativos reader.

The ``inf_mensal_cra_derivativos`` member of ``inf_mensal_cra_AAAA.zip``: the derivative positions
held by the segregated estate. **20 columns.**

⚠️ The commodity columns are ``*_Commodities_Agricolas`` here (``Mercado_Termo``, ``Futuros``,
``Opcoes``, ``Swap``) — OTS spells them plain ``*_Commodities``.

See ``_base_inf_mensal_cra_reader`` for the shared behaviour (yearly ``date_ref``, shared archive,
``path_raw``).
"""

from __future__ import annotations

from typing import ClassVar

from filings_cvm._internal.config.contracts import INF_MENSAL_CRA_DERIVATIVOS, FileContract
from filings_cvm._internal.utils.retry import RetryPolicy
from filings_cvm.ingestion.securit.doc.inf_mensal_cra._base_inf_mensal_cra_reader import (
	_DEFAULT_RETRY_POLICY,
	_BaseInfMensalCraReader,
)


class InfMensalCraDerivativosReader(_BaseInfMensalCraReader):
	"""Read the Informe Mensal CRA derivativos into a typed DataFrame."""

	_MEMBER_STEM: ClassVar[str] = "inf_mensal_cra_derivativos"
	_CONTRACT: ClassVar[FileContract] = INF_MENSAL_CRA_DERIVATIVOS
	_LABEL: ClassVar[str] = "derivativos"
	_DATE_COLS: ClassVar[tuple[str, ...]] = ("Data_Referencia",)
	_RETRY_POLICY: ClassVar[RetryPolicy | None] = _DEFAULT_RETRY_POLICY
