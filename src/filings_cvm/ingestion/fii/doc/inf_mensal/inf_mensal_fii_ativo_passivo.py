"""CVM Informe Mensal FII — membro *ativo e passivo* reader.

The ``inf_mensal_fii_ativo_passivo`` member of ``inf_mensal_fii_AAAA.zip``: the fund's balance
sheet for the month — liquidity needs, invested assets (imóveis, valores mobiliários, cotas de
fundos), receivables, and the liabilities that make up ``Total_Passivo``. Every value column keeps
CVM's exact decimal text; convert to ``Decimal`` where you compute.

See ``_base_inf_mensal_fii_reader`` for the shared behaviour — in particular that the dump is
partitioned by **year**, so ``date_ref`` selects the year, not the month.
"""

from __future__ import annotations

from typing import ClassVar

from filings_cvm._internal.config.contracts import INF_MENSAL_FII_ATIVO_PASSIVO, FileContract
from filings_cvm.ingestion.fii.doc.inf_mensal._base_inf_mensal_fii_reader import (
	_BaseInfMensalFiiReader,
)


class InfMensalFiiAtivoPassivoReader(_BaseInfMensalFiiReader):
	"""Read the Informe Mensal FII *ativo e passivo* member into a typed DataFrame."""

	_MEMBER_STEM: ClassVar[str] = "inf_mensal_fii_ativo_passivo"
	_CONTRACT: ClassVar[FileContract] = INF_MENSAL_FII_ATIVO_PASSIVO
	_DATE_COLS: ClassVar[tuple[str, ...]] = ("Data_Referencia",)
	_LABEL: ClassVar[str] = "ativo e passivo"
