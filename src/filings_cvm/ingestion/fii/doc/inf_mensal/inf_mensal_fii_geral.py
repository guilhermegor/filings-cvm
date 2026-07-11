"""CVM Informe Mensal FII — membro *geral* (cadastro e administrador) reader.

The ``inf_mensal_fii_geral`` member of ``inf_mensal_fii_AAAA.zip``: the fund's identification,
mandate, trading venues and administrator (name, CNPJ, address, contacts). See
``_base_inf_mensal_fii_reader`` for the shared behaviour — in particular that the dump is
partitioned by **year**, so ``date_ref`` selects the year, not the month.
"""

from __future__ import annotations

from typing import ClassVar

from filings_cvm._internal.config.contracts import INF_MENSAL_FII_GERAL, FileContract
from filings_cvm.ingestion.fii.doc.inf_mensal._base_inf_mensal_fii_reader import (
	_BaseInfMensalFiiReader,
)


class InfMensalFiiGeralReader(_BaseInfMensalFiiReader):
	"""Read the Informe Mensal FII *geral* member into a typed DataFrame."""

	_MEMBER_STEM: ClassVar[str] = "inf_mensal_fii_geral"
	_CONTRACT: ClassVar[FileContract] = INF_MENSAL_FII_GERAL
	_DATE_COLS: ClassVar[tuple[str, ...]] = (
		"Data_Referencia",
		"Data_Entrega",
		"Data_Funcionamento",
		"Data_Prazo_Duracao",
	)
	_LABEL: ClassVar[str] = "geral"
