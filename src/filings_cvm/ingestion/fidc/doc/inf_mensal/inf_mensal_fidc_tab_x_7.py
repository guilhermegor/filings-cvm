"""CVM Informe Mensal FIDC — tabela X.7 (garantias dos direitos creditórios) reader.

The ``inf_mensal_fidc_tab_X_7`` member of ``inf_mensal_fidc_AAAAMM.zip``: garantias dos direitos
creditórios (valor e percentual). See ``_base_inf_mensal_fidc_reader`` for the shared behaviour
(monthly ``date_ref``, ``DT_COMPTC`` date column, shared archive, ``path_raw``).
"""

from __future__ import annotations

from typing import ClassVar

from filings_cvm._internal.config.contracts import INF_MENSAL_FIDC_TAB_X_7, FileContract
from filings_cvm._internal.utils.retry import RetryPolicy
from filings_cvm.ingestion.fidc.doc.inf_mensal._base_inf_mensal_fidc_reader import (
	_DEFAULT_RETRY_POLICY,
	_BaseInfMensalFidcReader,
)


class InfMensalFidcTabX7Reader(_BaseInfMensalFidcReader):
	"""Read the Informe Mensal FIDC tabela X.7 (garantias) into a typed DataFrame."""

	_MEMBER_STEM: ClassVar[str] = "inf_mensal_fidc_tab_X_7"
	_CONTRACT: ClassVar[FileContract] = INF_MENSAL_FIDC_TAB_X_7
	_LABEL: ClassVar[str] = "tabela X.7"
	_RETRY_POLICY: ClassVar[RetryPolicy | None] = _DEFAULT_RETRY_POLICY
