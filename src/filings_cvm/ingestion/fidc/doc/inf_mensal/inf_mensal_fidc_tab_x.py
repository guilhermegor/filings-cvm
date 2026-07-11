"""CVM Informe Mensal FIDC — tabela X (classificação de risco SCR) reader.

The ``inf_mensal_fidc_tab_X`` member of ``inf_mensal_fidc_AAAAMM.zip``: classificação de risco
(SCR) por devedor e por operação (níveis AA–H) e débito tributário. See
``_base_inf_mensal_fidc_reader`` for the shared behaviour (monthly ``date_ref``, ``DT_COMPTC``
date column, shared archive, ``path_raw``).
"""

from __future__ import annotations

from typing import ClassVar

from filings_cvm._internal.config.contracts import INF_MENSAL_FIDC_TAB_X, FileContract
from filings_cvm._internal.utils.retry import RetryPolicy
from filings_cvm.ingestion.fidc.doc.inf_mensal._base_inf_mensal_fidc_reader import (
	_DEFAULT_RETRY_POLICY,
	_BaseInfMensalFidcReader,
)


class InfMensalFidcTabXReader(_BaseInfMensalFidcReader):
	"""Read the Informe Mensal FIDC tabela X (classificação de risco) into a typed DataFrame."""

	_MEMBER_STEM: ClassVar[str] = "inf_mensal_fidc_tab_X"
	_CONTRACT: ClassVar[FileContract] = INF_MENSAL_FIDC_TAB_X
	_LABEL: ClassVar[str] = "tabela X"
	_RETRY_POLICY: ClassVar[RetryPolicy | None] = _DEFAULT_RETRY_POLICY
