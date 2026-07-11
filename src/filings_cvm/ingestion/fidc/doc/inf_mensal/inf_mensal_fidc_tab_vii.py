"""CVM Informe Mensal FIDC — tabela VII (direitos creditórios por origem) reader.

The ``inf_mensal_fidc_tab_VII`` member of ``inf_mensal_fidc_AAAAMM.zip``: quantidade e valor de
direitos creditórios por origem (cedente, prestador, terceiro, substituição, recompra). See
``_base_inf_mensal_fidc_reader`` for the shared behaviour (monthly ``date_ref``, ``DT_COMPTC``
date column, shared archive, ``path_raw``).
"""

from __future__ import annotations

from typing import ClassVar

from filings_cvm._internal.config.contracts import INF_MENSAL_FIDC_TAB_VII, FileContract
from filings_cvm._internal.utils.retry import RetryPolicy
from filings_cvm.ingestion.fidc.doc.inf_mensal._base_inf_mensal_fidc_reader import (
	_DEFAULT_RETRY_POLICY,
	_BaseInfMensalFidcReader,
)


class InfMensalFidcTabVIIReader(_BaseInfMensalFidcReader):
	"""Read the Informe Mensal FIDC tabela VII (direitos por origem) into a typed DataFrame."""

	_MEMBER_STEM: ClassVar[str] = "inf_mensal_fidc_tab_VII"
	_CONTRACT: ClassVar[FileContract] = INF_MENSAL_FIDC_TAB_VII
	_LABEL: ClassVar[str] = "tabela VII"
	_RETRY_POLICY: ClassVar[RetryPolicy | None] = _DEFAULT_RETRY_POLICY
