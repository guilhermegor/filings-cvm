"""CVM Informe Mensal FII — membro *complemento* reader.

The ``inf_mensal_fii_complemento`` member of ``inf_mensal_fii_AAAA.zip``: the shareholder
breakdown by investor type, the fund's net worth and share value, and the month's expense and
return percentages (rentabilidade efetiva/patrimonial, *dividend yield*, amortização).

See ``_base_inf_mensal_fii_reader`` for the shared behaviour — in particular that the dump is
partitioned by **year**, so ``date_ref`` selects the year, not the month.
"""

from __future__ import annotations

from typing import ClassVar

from filings_cvm._internal.config.contracts import INF_MENSAL_FII_COMPLEMENTO, FileContract
from filings_cvm.ingestion.fii.doc.inf_mensal._base_inf_mensal_fii_reader import (
	_BaseInfMensalFiiReader,
)


class InfMensalFiiComplementoReader(_BaseInfMensalFiiReader):
	"""Read the Informe Mensal FII *complemento* member into a typed DataFrame."""

	_MEMBER_STEM: ClassVar[str] = "inf_mensal_fii_complemento"
	_CONTRACT: ClassVar[FileContract] = INF_MENSAL_FII_COMPLEMENTO
	_DATE_COLS: ClassVar[tuple[str, ...]] = (
		"Data_Referencia",
		"Data_Informacao_Numero_Cotistas",
	)
	_LABEL: ClassVar[str] = "complemento"
