"""CVM Informe Trimestral FII — membro *ativo* reader.

The ``inf_trimestral_fii_ativo`` member of ``inf_trimestral_fii_AAAA.zip``: the fund's securities
and other assets — one row per asset (issuer, emission/série, quantity, value, maturity). A
**long** table. ``CNPJ_Emissor`` is the counterparty's CNPJ, read as text and not validated as the
fund's CNPJ. See ``_base_inf_trimestral_fii_reader`` for the shared behaviour — in particular that
the dump is partitioned by **year**, so ``date_ref`` selects the year, not the quarter.
"""

from __future__ import annotations

from typing import ClassVar

from filings_cvm._internal.config.contracts import INF_TRIMESTRAL_FII_ATIVO, FileContract
from filings_cvm.ingestion.fii.doc.inf_trimestral._base_inf_trimestral_fii_reader import (
	_BaseInfTrimestralFiiReader,
)


class InfTrimestralFiiAtivoReader(_BaseInfTrimestralFiiReader):
	"""Read the Informe Trimestral FII *ativo* member into a typed DataFrame."""

	_MEMBER_STEM: ClassVar[str] = "inf_trimestral_fii_ativo"
	_CONTRACT: ClassVar[FileContract] = INF_TRIMESTRAL_FII_ATIVO
	_DATE_COLS: ClassVar[tuple[str, ...]] = ("Data_Referencia", "Data_Vencimento")
	_LABEL: ClassVar[str] = "ativo"
