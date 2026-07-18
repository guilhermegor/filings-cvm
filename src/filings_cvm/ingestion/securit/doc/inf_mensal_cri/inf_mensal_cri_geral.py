"""CVM Informe Mensal CRI — geral reader.

The ``inf_mensal_cri_geral`` member of ``inf_mensal_cri_AAAA.zip``: the operation's registry —
issuing company, fiduciary agent, custodian, lastro, LTV and risk
rating. **44 columns.** This is the member with the **most date columns**.

⚠️ Three columns are **100% blank** in 2025 — ``CNPJ_Agente_Fiduciario``,
``CNPJ_Custodiante`` and ``CNPJ_Agencia_Classificadora``. Published, so part of the contract,
but deliberately **not** declared as CNPJ columns (nothing to validate today). ``Data_LTV`` is
**100% empty** across the year, so it stays ``str`` rather than being coerced on an unverified
name (the ``Indice_Subordinacao_Data_Base`` lesson). Its ``Outras_Contigencias_Relevantes``
keeps CVM's misspelling **verbatim** (unlike CRA, which drops the contingency block).

See ``_base_inf_mensal_cri_reader`` for the shared behaviour (yearly ``date_ref``, shared archive,
``path_raw``).
"""

from __future__ import annotations

from typing import ClassVar

from filings_cvm._internal.config.contracts import INF_MENSAL_CRI_GERAL, FileContract
from filings_cvm._internal.utils.retry import RetryPolicy
from filings_cvm.ingestion.securit.doc.inf_mensal_cri._base_inf_mensal_cri_reader import (
	_DEFAULT_RETRY_POLICY,
	_BaseInfMensalCriReader,
)


class InfMensalCriGeralReader(_BaseInfMensalCriReader):
	"""Read the Informe Mensal CRI geral into a typed DataFrame."""

	_MEMBER_STEM: ClassVar[str] = "inf_mensal_cri_geral"
	_CONTRACT: ClassVar[FileContract] = INF_MENSAL_CRI_GERAL
	_LABEL: ClassVar[str] = "geral"
	_DATE_COLS: ClassVar[tuple[str, ...]] = (
		"Data_Referencia",
		"Data_Entrega",
		"Data_Emissao",
		"Data_Ultima_Classificacao",
	)
	_RETRY_POLICY: ClassVar[RetryPolicy | None] = _DEFAULT_RETRY_POLICY
