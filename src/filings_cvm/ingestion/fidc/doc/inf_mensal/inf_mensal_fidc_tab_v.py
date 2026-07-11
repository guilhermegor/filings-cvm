"""CVM Informe Mensal FIDC — tabela V (prazos dos direitos creditórios a adquirir) reader.

The ``inf_mensal_fidc_tab_V`` member of ``inf_mensal_fidc_AAAAMM.zip``: direitos creditórios a
adquirir por faixa de prazo de vencimento (a vencer, inadimplentes, antecipados). See
``_base_inf_mensal_fidc_reader`` for the shared behaviour (monthly ``date_ref``, ``DT_COMPTC``
date column, shared archive, ``path_raw``).
"""

from __future__ import annotations

from typing import ClassVar

from filings_cvm._internal.config.contracts import INF_MENSAL_FIDC_TAB_V, FileContract
from filings_cvm._internal.utils.retry import RetryPolicy
from filings_cvm.ingestion.fidc.doc.inf_mensal._base_inf_mensal_fidc_reader import (
	_DEFAULT_RETRY_POLICY,
	_BaseInfMensalFidcReader,
)


class InfMensalFidcTabVReader(_BaseInfMensalFidcReader):
	"""Read the Informe Mensal FIDC tabela V (prazos a adquirir) into a typed DataFrame."""

	_MEMBER_STEM: ClassVar[str] = "inf_mensal_fidc_tab_V"
	_CONTRACT: ClassVar[FileContract] = INF_MENSAL_FIDC_TAB_V
	_LABEL: ClassVar[str] = "tabela V"
	_RETRY_POLICY: ClassVar[RetryPolicy | None] = _DEFAULT_RETRY_POLICY
