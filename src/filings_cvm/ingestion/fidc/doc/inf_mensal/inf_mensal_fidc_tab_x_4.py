"""CVM Informe Mensal FIDC — tabela X.4 (movimentações de cotas) reader.

The ``inf_mensal_fidc_tab_X_4`` member of ``inf_mensal_fidc_AAAAMM.zip``: movimentações de cotas
por tipo de operação e classe/série (valor total e quantidade). A **long** table — many rows per
fund (one per tipo de operação × classe/série). See ``_base_inf_mensal_fidc_reader`` for the
shared behaviour (monthly ``date_ref``, ``DT_COMPTC`` date column, shared archive, ``path_raw``).
"""

from __future__ import annotations

from typing import ClassVar

from filings_cvm._internal.config.contracts import INF_MENSAL_FIDC_TAB_X_4, FileContract
from filings_cvm._internal.utils.retry import RetryPolicy
from filings_cvm.ingestion.fidc.doc.inf_mensal._base_inf_mensal_fidc_reader import (
	_DEFAULT_RETRY_POLICY,
	_BaseInfMensalFidcReader,
)


class InfMensalFidcTabX4Reader(_BaseInfMensalFidcReader):
	"""Read the Informe Mensal FIDC tabela X.4 (movimentações de cotas) into a DataFrame."""

	_MEMBER_STEM: ClassVar[str] = "inf_mensal_fidc_tab_X_4"
	_CONTRACT: ClassVar[FileContract] = INF_MENSAL_FIDC_TAB_X_4
	_LABEL: ClassVar[str] = "tabela X.4"
	_RETRY_POLICY: ClassVar[RetryPolicy | None] = _DEFAULT_RETRY_POLICY
