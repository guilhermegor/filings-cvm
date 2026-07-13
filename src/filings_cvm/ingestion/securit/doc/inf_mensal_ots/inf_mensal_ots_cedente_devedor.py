"""CVM Informe Mensal OTS — cedente/devedor reader.

The ``inf_mensal_ots_cedente_devedor`` member of ``inf_mensal_ots_AAAA.zip``: the concentration of
the operation's assignors (``Tipo == "Cedente"``) and debtors (``Tipo == "Devedor"``) — one row per
counterparty per certificate, with its share (``Percentual``). Naturally **long**. See
``_base_inf_mensal_ots_reader`` for the shared behaviour.

⚠️ **The ``CNPJ`` column holds a CPF on 257 of 1650 real rows** — an assignor or debtor may be a
natural person. It is therefore **not** declared a CNPJ column on the contract (a CNPJ check would
reject a valid file — the ``cad_fi`` ``CPF_CNPJ_GESTOR`` trap): only ``CNPJ_Securitizadora`` is
validated. Being a CPF, it is **personal data** — kept as exact source text in the bronze layer,
never parsed or validated here; LGPD handling is a downstream concern.
"""

from __future__ import annotations

from typing import ClassVar

from filings_cvm._internal.config.contracts import INF_MENSAL_OTS_CEDENTE_DEVEDOR, FileContract
from filings_cvm._internal.utils.retry import RetryPolicy
from filings_cvm.ingestion.securit.doc.inf_mensal_ots._base_inf_mensal_ots_reader import (
	_DEFAULT_RETRY_POLICY,
	_BaseInfMensalOtsReader,
)


class InfMensalOtsCedenteDevedorReader(_BaseInfMensalOtsReader):
	"""Read the Informe Mensal OTS cedente/devedor concentration into a typed DataFrame."""

	_MEMBER_STEM: ClassVar[str] = "inf_mensal_ots_cedente_devedor"
	_CONTRACT: ClassVar[FileContract] = INF_MENSAL_OTS_CEDENTE_DEVEDOR
	_LABEL: ClassVar[str] = "cedente/devedor"
	_DATE_COLS: ClassVar[tuple[str, ...]] = ("Data_Referencia",)
	_RETRY_POLICY: ClassVar[RetryPolicy | None] = _DEFAULT_RETRY_POLICY
