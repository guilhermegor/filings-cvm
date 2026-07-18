"""CVM Informe Mensal CRI — fluxo de caixa reader.

The ``inf_mensal_cri_fluxo_caixa`` member of ``inf_mensal_cri_AAAA.zip``: the cash-flow statement —
receipts, expenses and the senior/mezzanine/junior payment tranches.
**21 columns.** Carries the 60-char
``Pagamentos_Classe_Subordinada_Mezanino_Amortizacao_Principal``
that CVM's META truncates to 50 (the reconciliation is truncation-aware).

See ``_base_inf_mensal_cri_reader`` for the shared behaviour (yearly ``date_ref``, shared archive,
``path_raw``).
"""

from __future__ import annotations

from typing import ClassVar

from filings_cvm._internal.config.contracts import INF_MENSAL_CRI_FLUXO_CAIXA, FileContract
from filings_cvm._internal.utils.retry import RetryPolicy
from filings_cvm.ingestion.securit.doc.inf_mensal_cri._base_inf_mensal_cri_reader import (
	_DEFAULT_RETRY_POLICY,
	_BaseInfMensalCriReader,
)


class InfMensalCriFluxoCaixaReader(_BaseInfMensalCriReader):
	"""Read the Informe Mensal CRI fluxo de caixa into a typed DataFrame."""

	_MEMBER_STEM: ClassVar[str] = "inf_mensal_cri_fluxo_caixa"
	_CONTRACT: ClassVar[FileContract] = INF_MENSAL_CRI_FLUXO_CAIXA
	_LABEL: ClassVar[str] = "fluxo de caixa"
	_DATE_COLS: ClassVar[tuple[str, ...]] = ("Data_Referencia",)
	_RETRY_POLICY: ClassVar[RetryPolicy | None] = _DEFAULT_RETRY_POLICY
