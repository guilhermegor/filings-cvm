"""CVM Informe Mensal FIDC — tabela X.5 (liquidez por faixa de prazo) reader.

The ``inf_mensal_fidc_tab_X_5`` member of ``inf_mensal_fidc_AAAAMM.zip``: liquidez do fundo por
faixa de prazo (0, 30, 60, 90, 180, 360, >360 dias). See ``_base_inf_mensal_fidc_reader`` for the
shared behaviour (monthly ``date_ref``, ``DT_COMPTC`` date column, shared archive, ``path_raw``).
"""

from __future__ import annotations

from typing import ClassVar

from filings_cvm._internal.config.contracts import INF_MENSAL_FIDC_TAB_X_5, FileContract
from filings_cvm._internal.utils.retry import RetryPolicy
from filings_cvm.ingestion.fidc.doc.inf_mensal._base_inf_mensal_fidc_reader import (
	_DEFAULT_RETRY_POLICY,
	_BaseInfMensalFidcReader,
)


class InfMensalFidcTabX5Reader(_BaseInfMensalFidcReader):
	"""Read the Informe Mensal FIDC tabela X.5 (liquidez por prazo) into a typed DataFrame."""

	_MEMBER_STEM: ClassVar[str] = "inf_mensal_fidc_tab_X_5"
	_CONTRACT: ClassVar[FileContract] = INF_MENSAL_FIDC_TAB_X_5
	_LABEL: ClassVar[str] = "tabela X.5"
	_RETRY_POLICY: ClassVar[RetryPolicy | None] = _DEFAULT_RETRY_POLICY
