"""CVM Informe Mensal FIDC — tabela VIII reader.

The ``inf_mensal_fidc_tab_VIII`` member of ``inf_mensal_fidc_AAAAMM.zip``. Unlike its wide
siblings it is **long**: one row per fund × ``SEQUENCIAL`` (1–25 in 202506), each carrying a
single ``VALOR`` (META: ``numeric(20,2)``, kept as exact text). CVM's META leaves the description
of both columns blank, so this reader asserts no meaning beyond the published shape. See
``_base_inf_mensal_fidc_reader`` for the shared behaviour (monthly ``date_ref``, ``DT_COMPTC``
date column, shared archive, ``path_raw``).
"""

from __future__ import annotations

from typing import ClassVar

from filings_cvm._internal.config.contracts import INF_MENSAL_FIDC_TAB_VIII, FileContract
from filings_cvm._internal.utils.retry import RetryPolicy
from filings_cvm.ingestion.fidc.doc.inf_mensal._base_inf_mensal_fidc_reader import (
	_DEFAULT_RETRY_POLICY,
	_BaseInfMensalFidcReader,
)


class InfMensalFidcTabVIIIReader(_BaseInfMensalFidcReader):
	"""Read the Informe Mensal FIDC tabela VIII (sequenced values) into a typed DataFrame."""

	_MEMBER_STEM: ClassVar[str] = "inf_mensal_fidc_tab_VIII"
	_CONTRACT: ClassVar[FileContract] = INF_MENSAL_FIDC_TAB_VIII
	_LABEL: ClassVar[str] = "tabela VIII"
	_RETRY_POLICY: ClassVar[RetryPolicy | None] = _DEFAULT_RETRY_POLICY
