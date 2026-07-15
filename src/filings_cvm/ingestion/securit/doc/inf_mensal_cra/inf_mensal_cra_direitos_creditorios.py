"""CVM Informe Mensal CRA — direitos creditórios reader.

The ``inf_mensal_cra_direitos_creditorios`` member of ``inf_mensal_cra_AAAA.zip``: the receivables
backing the operation — inadimplência, pré-pagamento, substitution and the agro receivable buckets.
**56 columns — the widest member, and 13 wider than OTS's counterpart.**

Those 13 extra columns are what makes CRA *agro*: ``Direitos_Creditorios_Receber`` split across
produção / comercialização / beneficiamento / industrialização, each also in an ``_Insumos`` and a
``_Maquinas`` variant. Copying OTS's 43-column contract here would be silently wrong.

See ``_base_inf_mensal_cra_reader`` for the shared behaviour (yearly ``date_ref``, shared archive,
``path_raw``).
"""

from __future__ import annotations

from typing import ClassVar

from filings_cvm._internal.config.contracts import (
	INF_MENSAL_CRA_DIREITOS_CREDITORIOS,
	FileContract,
)
from filings_cvm._internal.utils.retry import RetryPolicy
from filings_cvm.ingestion.securit.doc.inf_mensal_cra._base_inf_mensal_cra_reader import (
	_DEFAULT_RETRY_POLICY,
	_BaseInfMensalCraReader,
)


class InfMensalCraDireitosCreditoriosReader(_BaseInfMensalCraReader):
	"""Read the Informe Mensal CRA direitos creditórios into a typed DataFrame."""

	_MEMBER_STEM: ClassVar[str] = "inf_mensal_cra_direitos_creditorios"
	_CONTRACT: ClassVar[FileContract] = INF_MENSAL_CRA_DIREITOS_CREDITORIOS
	_LABEL: ClassVar[str] = "direitos creditórios"
	_DATE_COLS: ClassVar[tuple[str, ...]] = ("Data_Referencia",)
	_RETRY_POLICY: ClassVar[RetryPolicy | None] = _DEFAULT_RETRY_POLICY
