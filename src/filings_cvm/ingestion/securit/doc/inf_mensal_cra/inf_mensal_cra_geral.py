"""CVM Informe Mensal CRA — geral (cadastro da operação) reader.

The ``inf_mensal_cra_geral`` member of ``inf_mensal_cra_AAAA.zip``: the operation's registry
section — issuing company, fiduciary agent, custodian, issue/lastro details, the agro production
chain and segment, and the risk rating. **31 columns.**

This is the member with the **most date columns**: besides the shared ``Data_Referencia`` it has
``Data_Entrega``, ``Data_Emissao`` and ``Data_Ultima_Classificacao``.

⚠️ Three columns are **100% blank** in the 2025 file — ``CNPJ_Agente_Fiduciario``,
``CNPJ_Custodiante`` and ``CNPJ_Agencia_Classificadora``. Published, so they are part of the
contract, but deliberately **not** declared as CNPJ columns (nothing to validate today, and
declaring them would fail a valid file the day CVM fills them with free text).

⚠️ Unlike OTS's ``geral``, this member has **no contingency block** — so OTS's
``Outras_Contigencias_Relevantes`` typo has no counterpart here. It adds the agro-specific
``Cadeia_Producao``, ``Tipo_Segmento`` and ``Especificacao_Tipo_Segmento`` instead.

See ``_base_inf_mensal_cra_reader`` for the shared behaviour (yearly ``date_ref``, shared archive,
``path_raw``).
"""

from __future__ import annotations

from typing import ClassVar

from filings_cvm._internal.config.contracts import INF_MENSAL_CRA_GERAL, FileContract
from filings_cvm._internal.utils.retry import RetryPolicy
from filings_cvm.ingestion.securit.doc.inf_mensal_cra._base_inf_mensal_cra_reader import (
	_DEFAULT_RETRY_POLICY,
	_BaseInfMensalCraReader,
)


class InfMensalCraGeralReader(_BaseInfMensalCraReader):
	"""Read the Informe Mensal CRA geral (cadastro da operação) into a typed DataFrame."""

	_MEMBER_STEM: ClassVar[str] = "inf_mensal_cra_geral"
	_CONTRACT: ClassVar[FileContract] = INF_MENSAL_CRA_GERAL
	_LABEL: ClassVar[str] = "geral"
	_DATE_COLS: ClassVar[tuple[str, ...]] = (
		"Data_Referencia",
		"Data_Entrega",
		"Data_Emissao",
		"Data_Ultima_Classificacao",
	)
	_RETRY_POLICY: ClassVar[RetryPolicy | None] = _DEFAULT_RETRY_POLICY
