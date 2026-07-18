"""CVM Informe Mensal CRI — créditos reader.

The ``inf_mensal_cri_creditos`` member of ``inf_mensal_cri_AAAA.zip``: the receivables portfolio —
nature (incorporation, rents, acquisition, loteamento,
multipropriedade, home equity), aging, concentration and largest debtors/assignors.
**51 columns.** CRI's counterpart to CRA/OTS's ``direitos_creditorios`` — a different name and
shape (real-estate credits, not agro buckets).

See ``_base_inf_mensal_cri_reader`` for the shared behaviour (yearly ``date_ref``, shared archive,
``path_raw``).
"""

from __future__ import annotations

from typing import ClassVar

from filings_cvm._internal.config.contracts import INF_MENSAL_CRI_CREDITOS, FileContract
from filings_cvm._internal.utils.retry import RetryPolicy
from filings_cvm.ingestion.securit.doc.inf_mensal_cri._base_inf_mensal_cri_reader import (
	_DEFAULT_RETRY_POLICY,
	_BaseInfMensalCriReader,
)


class InfMensalCriCreditosReader(_BaseInfMensalCriReader):
	"""Read the Informe Mensal CRI créditos into a typed DataFrame."""

	_MEMBER_STEM: ClassVar[str] = "inf_mensal_cri_creditos"
	_CONTRACT: ClassVar[FileContract] = INF_MENSAL_CRI_CREDITOS
	_LABEL: ClassVar[str] = "créditos"
	_DATE_COLS: ClassVar[tuple[str, ...]] = ("Data_Referencia",)
	_RETRY_POLICY: ClassVar[RetryPolicy | None] = _DEFAULT_RETRY_POLICY
