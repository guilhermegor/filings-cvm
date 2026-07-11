"""CVM Informe Anual FII — membro *prestador de serviço* reader.

The ``inf_anual_fii_prestador_servico`` member of ``inf_anual_fii_AAAA.zip``: the fund's service
providers — one row per prestador (nome, CNPJ, endereço, telefone). ``CNPJ_Prestador`` is a
counterparty id, read as text and not validated as the fund's CNPJ. See
``_base_inf_anual_fii_reader`` for the shared behaviour.
"""

from __future__ import annotations

from typing import ClassVar

from filings_cvm._internal.config.contracts import INF_ANUAL_FII_PRESTADOR_SERVICO, FileContract
from filings_cvm.ingestion.fii.doc.inf_anual._base_inf_anual_fii_reader import (
	_BaseInfAnualFiiReader,
)


class InfAnualFiiPrestadorServicoReader(_BaseInfAnualFiiReader):
	"""Read the Informe Anual FII *prestador de serviço* member into a typed DataFrame."""

	_MEMBER_STEM: ClassVar[str] = "inf_anual_fii_prestador_servico"
	_CONTRACT: ClassVar[FileContract] = INF_ANUAL_FII_PRESTADOR_SERVICO
	_DATE_COLS: ClassVar[tuple[str, ...]] = ("Data_Referencia",)
	_LABEL: ClassVar[str] = "prestador de serviço"
