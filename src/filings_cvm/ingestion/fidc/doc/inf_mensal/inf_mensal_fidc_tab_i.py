"""CVM Informe Mensal FIDC — tabela I (composição do ativo) reader.

The ``inf_mensal_fidc_tab_I`` member of ``inf_mensal_fidc_AAAAMM.zip``: composição do ativo
(disponibilidades, carteira de direitos creditórios com/sem risco, valores mobiliários, posição
em derivativos, outros ativos). See ``_base_inf_mensal_fidc_reader`` for the shared behaviour
(monthly ``date_ref``, ``DT_COMPTC`` date column, shared archive, ``path_raw``).
"""

from __future__ import annotations

from typing import ClassVar

from filings_cvm._internal.config.contracts import INF_MENSAL_FIDC_TAB_I, FileContract
from filings_cvm._internal.utils.retry import RetryPolicy
from filings_cvm.ingestion.fidc.doc.inf_mensal._base_inf_mensal_fidc_reader import (
	_DEFAULT_RETRY_POLICY,
	_BaseInfMensalFidcReader,
)


class InfMensalFidcTabIReader(_BaseInfMensalFidcReader):
	"""Read the Informe Mensal FIDC tabela I (composição do ativo) into a typed DataFrame."""

	_MEMBER_STEM: ClassVar[str] = "inf_mensal_fidc_tab_I"
	_CONTRACT: ClassVar[FileContract] = INF_MENSAL_FIDC_TAB_I
	_LABEL: ClassVar[str] = "tabela I"
	_RETRY_POLICY: ClassVar[RetryPolicy | None] = _DEFAULT_RETRY_POLICY
