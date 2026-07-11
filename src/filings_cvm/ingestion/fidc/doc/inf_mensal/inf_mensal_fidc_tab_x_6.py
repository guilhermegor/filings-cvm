"""CVM Informe Mensal FIDC — tabela X.6 (desempenho esperado × realizado) reader.

The ``inf_mensal_fidc_tab_X_6`` member of ``inf_mensal_fidc_AAAAMM.zip``: desempenho esperado ×
realizado por classe/série (percentuais). A **long** table — many rows per fund (one per
classe/série). See ``_base_inf_mensal_fidc_reader`` for the shared behaviour (monthly
``date_ref``, ``DT_COMPTC`` date column, shared archive, ``path_raw``).
"""

from __future__ import annotations

from typing import ClassVar

from filings_cvm._internal.config.contracts import INF_MENSAL_FIDC_TAB_X_6, FileContract
from filings_cvm._internal.utils.retry import RetryPolicy
from filings_cvm.ingestion.fidc.doc.inf_mensal._base_inf_mensal_fidc_reader import (
	_DEFAULT_RETRY_POLICY,
	_BaseInfMensalFidcReader,
)


class InfMensalFidcTabX6Reader(_BaseInfMensalFidcReader):
	"""Read the Informe Mensal FIDC tabela X.6 (desempenho esperado × realizado)."""

	_MEMBER_STEM: ClassVar[str] = "inf_mensal_fidc_tab_X_6"
	_CONTRACT: ClassVar[FileContract] = INF_MENSAL_FIDC_TAB_X_6
	_LABEL: ClassVar[str] = "tabela X.6"
	_RETRY_POLICY: ClassVar[RetryPolicy | None] = _DEFAULT_RETRY_POLICY
