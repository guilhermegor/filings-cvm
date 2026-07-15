"""CVM Informe Mensal CRA — classe (série) reader.

The ``inf_mensal_cra_classe`` member of ``inf_mensal_cra_AAAA.zip``: one row per **class/series**
of the certificate — remuneration, subordination, amortisation and maturity. **23 columns.**
Naturally **long**: many rows per certificate, so no grain is asserted.

⚠️ **``Indice_Subordinacao_Data_Base`` is NOT a date** despite its name — real values are numeric
(``0.00``). It is deliberately absent from ``_DATE_COLS`` and stays ``str``. The only dates here
are ``Data_Referencia`` and ``Data_Vencimento``.

⚠️ Unlike OTS, this member carries ``Codigo_CETIP`` and ``Valor_Total_Integralizado`` (OTS spells
these ``Codigo_Negociacao_Mercado_Secundario`` and ``Total_Integralizado``).

See ``_base_inf_mensal_cra_reader`` for the shared behaviour (yearly ``date_ref``, shared archive,
``path_raw``).
"""

from __future__ import annotations

from typing import ClassVar

from filings_cvm._internal.config.contracts import INF_MENSAL_CRA_CLASSE, FileContract
from filings_cvm._internal.utils.retry import RetryPolicy
from filings_cvm.ingestion.securit.doc.inf_mensal_cra._base_inf_mensal_cra_reader import (
	_DEFAULT_RETRY_POLICY,
	_BaseInfMensalCraReader,
)


class InfMensalCraClasseReader(_BaseInfMensalCraReader):
	"""Read the Informe Mensal CRA classe (série) into a typed DataFrame."""

	_MEMBER_STEM: ClassVar[str] = "inf_mensal_cra_classe"
	_CONTRACT: ClassVar[FileContract] = INF_MENSAL_CRA_CLASSE
	_LABEL: ClassVar[str] = "classe"
	_DATE_COLS: ClassVar[tuple[str, ...]] = (
		"Data_Referencia",
		"Data_Vencimento",
	)
	_RETRY_POLICY: ClassVar[RetryPolicy | None] = _DEFAULT_RETRY_POLICY
