"""CVM Informe Trimestral FII — membro *contrato de imóvel de renda acabado* reader.

The ``inf_trimestral_fii_imovel_renda_acabado_contrato`` member of ``inf_trimestral_fii_AAAA.zip``:
the contractual characteristics of each finished income-producing property. A **long** table. See
``_base_inf_trimestral_fii_reader`` for the shared behaviour — in particular that the dump is
partitioned by **year**, so ``date_ref`` selects the year, not the quarter.
"""

from __future__ import annotations

from typing import ClassVar

from filings_cvm._internal.config.contracts import (
	INF_TRIMESTRAL_FII_IMOVEL_RENDA_ACABADO_CONTRATO,
	FileContract,
)
from filings_cvm.ingestion.fii.doc.inf_trimestral._base_inf_trimestral_fii_reader import (
	_BaseInfTrimestralFiiReader,
)


class InfTrimestralFiiImovelRendaAcabadoContratoReader(_BaseInfTrimestralFiiReader):
	"""Read the Informe Trimestral FII *contrato de imóvel de renda acabado* member."""

	_MEMBER_STEM: ClassVar[str] = "inf_trimestral_fii_imovel_renda_acabado_contrato"
	_CONTRACT: ClassVar[FileContract] = INF_TRIMESTRAL_FII_IMOVEL_RENDA_ACABADO_CONTRATO
	_DATE_COLS: ClassVar[tuple[str, ...]] = ("Data_Referencia",)
	_LABEL: ClassVar[str] = "contrato de imóvel de renda acabado"
