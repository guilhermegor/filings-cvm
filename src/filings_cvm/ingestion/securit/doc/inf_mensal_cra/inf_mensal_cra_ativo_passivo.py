"""CVM Informe Mensal CRA — ativo/passivo reader.

The ``inf_mensal_cra_ativo_passivo`` member of ``inf_mensal_cra_AAAA.zip``: the operation's
balance-sheet section — assets, liabilities and equity of the segregated estate. **31 columns.**

Every monetary column is exact source text (``str``), never a float: precision is preserved for a
downstream ``Decimal`` cast.

See ``_base_inf_mensal_cra_reader`` for the shared behaviour (yearly ``date_ref``, shared archive,
``path_raw``).
"""

from __future__ import annotations

from typing import ClassVar

from filings_cvm._internal.config.contracts import INF_MENSAL_CRA_ATIVO_PASSIVO, FileContract
from filings_cvm._internal.utils.retry import RetryPolicy
from filings_cvm.ingestion.securit.doc.inf_mensal_cra._base_inf_mensal_cra_reader import (
	_DEFAULT_RETRY_POLICY,
	_BaseInfMensalCraReader,
)


class InfMensalCraAtivoPassivoReader(_BaseInfMensalCraReader):
	"""Read the Informe Mensal CRA ativo/passivo into a typed DataFrame."""

	_MEMBER_STEM: ClassVar[str] = "inf_mensal_cra_ativo_passivo"
	_CONTRACT: ClassVar[FileContract] = INF_MENSAL_CRA_ATIVO_PASSIVO
	_LABEL: ClassVar[str] = "ativo/passivo"
	_DATE_COLS: ClassVar[tuple[str, ...]] = ("Data_Referencia",)
	_RETRY_POLICY: ClassVar[RetryPolicy | None] = _DEFAULT_RETRY_POLICY
