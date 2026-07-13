"""CVM Informe Mensal OTS — ativo/passivo reader.

The ``inf_mensal_ots_ativo_passivo`` member of ``inf_mensal_ots_AAAA.zip``: the operation's
balance — assets (direitos creditórios by ageing, cash and equivalents, derivative positions, other
assets) and liabilities (derivatives, updated issue value, others). One row per certificate
per reference month. See ``_base_inf_mensal_ots_reader`` for the shared behaviour (yearly
``date_ref``, shared archive, ``path_raw``).
"""

from __future__ import annotations

from typing import ClassVar

from filings_cvm._internal.config.contracts import INF_MENSAL_OTS_ATIVO_PASSIVO, FileContract
from filings_cvm._internal.utils.retry import RetryPolicy
from filings_cvm.ingestion.securit.doc.inf_mensal_ots._base_inf_mensal_ots_reader import (
	_DEFAULT_RETRY_POLICY,
	_BaseInfMensalOtsReader,
)


class InfMensalOtsAtivoPassivoReader(_BaseInfMensalOtsReader):
	"""Read the Informe Mensal OTS ativo/passivo section into a typed DataFrame."""

	_MEMBER_STEM: ClassVar[str] = "inf_mensal_ots_ativo_passivo"
	_CONTRACT: ClassVar[FileContract] = INF_MENSAL_OTS_ATIVO_PASSIVO
	_LABEL: ClassVar[str] = "ativo/passivo"
	_DATE_COLS: ClassVar[tuple[str, ...]] = ("Data_Referencia",)
	_RETRY_POLICY: ClassVar[RetryPolicy | None] = _DEFAULT_RETRY_POLICY
