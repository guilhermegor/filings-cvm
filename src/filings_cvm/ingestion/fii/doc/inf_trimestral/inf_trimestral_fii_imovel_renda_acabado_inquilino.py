"""CVM Informe Trimestral FII — membro *inquilino de imóvel de renda acabado* reader.

The ``inf_trimestral_fii_imovel_renda_acabado_inquilino`` member of
``inf_trimestral_fii_AAAA.zip``: the tenants of each finished income-producing property — one row
per inquilino (sector, share of the property's and the FII's revenue). The largest member (tens of
thousands of rows). See ``_base_inf_trimestral_fii_reader`` for the shared behaviour — in
particular that the dump is partitioned by **year**, so ``date_ref`` selects the year, not the
quarter.
"""

from __future__ import annotations

from typing import ClassVar

from filings_cvm._internal.config.contracts import (
	INF_TRIMESTRAL_FII_IMOVEL_RENDA_ACABADO_INQUILINO,
	FileContract,
)
from filings_cvm.ingestion.fii.doc.inf_trimestral._base_inf_trimestral_fii_reader import (
	_BaseInfTrimestralFiiReader,
)


class InfTrimestralFiiImovelRendaAcabadoInquilinoReader(_BaseInfTrimestralFiiReader):
	"""Read the Informe Trimestral FII *inquilino de imóvel de renda acabado* member."""

	_MEMBER_STEM: ClassVar[str] = "inf_trimestral_fii_imovel_renda_acabado_inquilino"
	_CONTRACT: ClassVar[FileContract] = INF_TRIMESTRAL_FII_IMOVEL_RENDA_ACABADO_INQUILINO
	_DATE_COLS: ClassVar[tuple[str, ...]] = ("Data_Referencia",)
	_LABEL: ClassVar[str] = "inquilino de imóvel de renda acabado"
