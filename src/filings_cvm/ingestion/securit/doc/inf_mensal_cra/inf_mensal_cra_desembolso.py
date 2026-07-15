"""CVM Informe Mensal CRA — desembolso reader.

The ``inf_mensal_cra_desembolso`` member of ``inf_mensal_cra_AAAA.zip``: the operation's
disbursement section — expenses charged to the segregated estate. **22 columns.**

See ``_base_inf_mensal_cra_reader`` for the shared behaviour (yearly ``date_ref``, shared archive,
``path_raw``).
"""

from __future__ import annotations

from typing import ClassVar

from filings_cvm._internal.config.contracts import INF_MENSAL_CRA_DESEMBOLSO, FileContract
from filings_cvm._internal.utils.retry import RetryPolicy
from filings_cvm.ingestion.securit.doc.inf_mensal_cra._base_inf_mensal_cra_reader import (
	_DEFAULT_RETRY_POLICY,
	_BaseInfMensalCraReader,
)


class InfMensalCraDesembolsoReader(_BaseInfMensalCraReader):
	"""Read the Informe Mensal CRA desembolso into a typed DataFrame."""

	_MEMBER_STEM: ClassVar[str] = "inf_mensal_cra_desembolso"
	_CONTRACT: ClassVar[FileContract] = INF_MENSAL_CRA_DESEMBOLSO
	_LABEL: ClassVar[str] = "desembolso"
	_DATE_COLS: ClassVar[tuple[str, ...]] = ("Data_Referencia",)
	_RETRY_POLICY: ClassVar[RetryPolicy | None] = _DEFAULT_RETRY_POLICY
