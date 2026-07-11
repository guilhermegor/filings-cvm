"""CVM Informe Mensal FIDC — tabela IX (taxas de negociação) reader.

The ``inf_mensal_fidc_tab_IX`` member of ``inf_mensal_fidc_AAAAMM.zip``: taxas de negociação de
direitos creditórios (compra e venda; mínima, média, máxima) por faixa. See
``_base_inf_mensal_fidc_reader`` for the shared behaviour (monthly ``date_ref``, ``DT_COMPTC``
date column, shared archive, ``path_raw``).
"""

from __future__ import annotations

from typing import ClassVar

from filings_cvm._internal.config.contracts import INF_MENSAL_FIDC_TAB_IX, FileContract
from filings_cvm._internal.utils.retry import RetryPolicy
from filings_cvm.ingestion.fidc.doc.inf_mensal._base_inf_mensal_fidc_reader import (
	_DEFAULT_RETRY_POLICY,
	_BaseInfMensalFidcReader,
)


class InfMensalFidcTabIXReader(_BaseInfMensalFidcReader):
	"""Read the Informe Mensal FIDC tabela IX (taxas de negociação) into a typed DataFrame."""

	_MEMBER_STEM: ClassVar[str] = "inf_mensal_fidc_tab_IX"
	_CONTRACT: ClassVar[FileContract] = INF_MENSAL_FIDC_TAB_IX
	_LABEL: ClassVar[str] = "tabela IX"
	_RETRY_POLICY: ClassVar[RetryPolicy | None] = _DEFAULT_RETRY_POLICY
