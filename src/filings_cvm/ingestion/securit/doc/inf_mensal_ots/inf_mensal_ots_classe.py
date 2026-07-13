"""CVM Informe Mensal OTS — classe (séries/classes emitidas) reader.

The ``inf_mensal_ots_classe`` member of ``inf_mensal_ots_AAAA.zip``: one row per class/série of the
operation — offer type, ISIN and trading code, maturity, integralised total, interest rate, payment
schedule, quantity and value, yields, amortisations, rating and subordination index. Naturally
**long**: many rows per certificate (6821 rows against 1793 in the single-row-per-certificate
sections). See ``_base_inf_mensal_ots_reader`` for the shared behaviour.

⚠️ **``Indice_Subordinacao_Data_Base`` is NOT a date**, despite its name — the real values are
numeric (``0.00000000000000000000``). It is deliberately **absent** from :attr:`_DATE_COLS` and
stays exact source text; coercing it by name would corrupt the column. Only ``Data_Referencia`` and
``Data_Vencimento`` are dates here.
"""

from __future__ import annotations

from typing import ClassVar

from filings_cvm._internal.config.contracts import INF_MENSAL_OTS_CLASSE, FileContract
from filings_cvm._internal.utils.retry import RetryPolicy
from filings_cvm.ingestion.securit.doc.inf_mensal_ots._base_inf_mensal_ots_reader import (
	_DEFAULT_RETRY_POLICY,
	_BaseInfMensalOtsReader,
)


class InfMensalOtsClasseReader(_BaseInfMensalOtsReader):
	"""Read the Informe Mensal OTS classe (séries/classes) into a typed DataFrame."""

	_MEMBER_STEM: ClassVar[str] = "inf_mensal_ots_classe"
	_CONTRACT: ClassVar[FileContract] = INF_MENSAL_OTS_CLASSE
	_LABEL: ClassVar[str] = "classe"
	# NOT Indice_Subordinacao_Data_Base — see the module docstring; it is numeric, not a date.
	_DATE_COLS: ClassVar[tuple[str, ...]] = ("Data_Referencia", "Data_Vencimento")
	_RETRY_POLICY: ClassVar[RetryPolicy | None] = _DEFAULT_RETRY_POLICY
