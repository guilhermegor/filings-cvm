"""CVM Informe Mensal CRA — fluxo de caixa reader.

The ``inf_mensal_cra_fluxo_caixa`` member of ``inf_mensal_cra_AAAA.zip``: the operation's cash-flow
section — inflows from receivables, acquisitions, amortisations and distributions. **21 columns.**

⚠️ Unlike OTS, the inflow columns are named ``Recebimentos_Direitos_Creditorios`` and
``Aquisicao_Novos_Direitos_Creditorios`` (OTS spells them ``*_Creditos``).

See ``_base_inf_mensal_cra_reader`` for the shared behaviour (yearly ``date_ref``, shared archive,
``path_raw``).
"""

from __future__ import annotations

from typing import ClassVar

from filings_cvm._internal.config.contracts import INF_MENSAL_CRA_FLUXO_CAIXA, FileContract
from filings_cvm._internal.utils.retry import RetryPolicy
from filings_cvm.ingestion.securit.doc.inf_mensal_cra._base_inf_mensal_cra_reader import (
	_DEFAULT_RETRY_POLICY,
	_BaseInfMensalCraReader,
)


class InfMensalCraFluxoCaixaReader(_BaseInfMensalCraReader):
	"""Read the Informe Mensal CRA fluxo de caixa into a typed DataFrame."""

	_MEMBER_STEM: ClassVar[str] = "inf_mensal_cra_fluxo_caixa"
	_CONTRACT: ClassVar[FileContract] = INF_MENSAL_CRA_FLUXO_CAIXA
	_LABEL: ClassVar[str] = "fluxo de caixa"
	_DATE_COLS: ClassVar[tuple[str, ...]] = ("Data_Referencia",)
	_RETRY_POLICY: ClassVar[RetryPolicy | None] = _DEFAULT_RETRY_POLICY
