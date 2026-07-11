"""CVM Informe Trimestral FII — membro *resultado contábil e financeiro* reader.

The ``inf_trimestral_fii_resultado_contabil_financeiro`` member of ``inf_trimestral_fii_AAAA.zip``:
the quarter's income statement, contábil and financeiro side by side across ~95 columns
(receitas/despesas by category, taxes, and the declared/paid income). See
``_base_inf_trimestral_fii_reader`` for the shared behaviour — in particular that the dump is
partitioned by **year**, so ``date_ref`` selects the year, not the quarter.
"""

from __future__ import annotations

from typing import ClassVar

from filings_cvm._internal.config.contracts import (
	INF_TRIMESTRAL_FII_RESULTADO_CONTABIL_FINANCEIRO,
	FileContract,
)
from filings_cvm.ingestion.fii.doc.inf_trimestral._base_inf_trimestral_fii_reader import (
	_BaseInfTrimestralFiiReader,
)


class InfTrimestralFiiResultadoContabilFinanceiroReader(_BaseInfTrimestralFiiReader):
	"""Read the Informe Trimestral FII *resultado contábil e financeiro* member."""

	_MEMBER_STEM: ClassVar[str] = "inf_trimestral_fii_resultado_contabil_financeiro"
	_CONTRACT: ClassVar[FileContract] = INF_TRIMESTRAL_FII_RESULTADO_CONTABIL_FINANCEIRO
	_DATE_COLS: ClassVar[tuple[str, ...]] = ("Data_Referencia",)
	_LABEL: ClassVar[str] = "resultado contábil e financeiro"
