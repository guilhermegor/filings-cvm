"""CVM Informe Anual FII — membro *complemento* reader.

The ``inf_anual_fii_complemento`` member of ``inf_anual_fii_AAAA.zip``: the fund's service
providers (gestor, custodiante, auditor, formador de mercado, distribuidor, consultor, empresa de
locação), the year's narrative sections (resultado, conjuntura, perspectivas, políticas) and a
``Link_Download_Anexo``.

**The ``Link_Download_Anexo`` is returned as text and never followed** — fetching the annex is a
downstream concern, exactly as ``DfinFiiReader`` treats its ``Link_Download``. The counterparty
CNPJs are read as text and not validated as the fund's CNPJ.

See ``_base_inf_anual_fii_reader`` for the shared behaviour.
"""

from __future__ import annotations

from typing import ClassVar

from filings_cvm._internal.config.contracts import INF_ANUAL_FII_COMPLEMENTO, FileContract
from filings_cvm.ingestion.fii.doc.inf_anual._base_inf_anual_fii_reader import (
	_BaseInfAnualFiiReader,
)


class InfAnualFiiComplementoReader(_BaseInfAnualFiiReader):
	"""Read the Informe Anual FII *complemento* member into a typed DataFrame."""

	_MEMBER_STEM: ClassVar[str] = "inf_anual_fii_complemento"
	_CONTRACT: ClassVar[FileContract] = INF_ANUAL_FII_COMPLEMENTO
	_DATE_COLS: ClassVar[tuple[str, ...]] = ("Data_Referencia",)
	_LABEL: ClassVar[str] = "complemento"
