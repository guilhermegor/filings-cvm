"""CVM Informe Mensal CRI — carteira reader.

The ``inf_mensal_cri_carteira`` member of ``inf_mensal_cri_AAAA.zip``: the linked-credits
portfolio, bucketed by maturity, default and payment horizon. **29 columns.**
A **CRI-only** member (absent from CRA/OTS).

See ``_base_inf_mensal_cri_reader`` for the shared behaviour (yearly ``date_ref``, shared archive,
``path_raw``).
"""

from __future__ import annotations

from typing import ClassVar

from filings_cvm._internal.config.contracts import INF_MENSAL_CRI_CARTEIRA, FileContract
from filings_cvm._internal.utils.retry import RetryPolicy
from filings_cvm.ingestion.securit.doc.inf_mensal_cri._base_inf_mensal_cri_reader import (
	_DEFAULT_RETRY_POLICY,
	_BaseInfMensalCriReader,
)


class InfMensalCriCarteiraReader(_BaseInfMensalCriReader):
	"""Read the Informe Mensal CRI carteira into a typed DataFrame."""

	_MEMBER_STEM: ClassVar[str] = "inf_mensal_cri_carteira"
	_CONTRACT: ClassVar[FileContract] = INF_MENSAL_CRI_CARTEIRA
	_LABEL: ClassVar[str] = "carteira"
	_DATE_COLS: ClassVar[tuple[str, ...]] = ("Data_Referencia",)
	_RETRY_POLICY: ClassVar[RetryPolicy | None] = _DEFAULT_RETRY_POLICY
