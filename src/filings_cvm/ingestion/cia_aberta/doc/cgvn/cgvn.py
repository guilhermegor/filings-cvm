"""CVM CGVN CIA_ABERTA (índice) — ingestion (leitura) reader.

The **index** member: one row per *Informe sobre o Código Brasileiro de Governança
Corporativa* a listed company filed in the year, with a ``Link_Download`` returned as text
and **never followed**.

It carries **four** date columns — the reference and delivery dates plus the fiscal year's
start and end (``Data_Inicio_Exercicio_Social`` / ``Data_Fim_Exercicio_Social``), all 100%
ISO in the real file. ``Motivo_Reapresentacao`` is mostly blank (13 of 382 rows in 2025).

⚠️ Unlike the sibling FCA's index, this one uses the ordinary CamelCase naming
(``CNPJ_Companhia`` / ``Data_Referencia``) — FCA's uppercase ``CNPJ_CIA`` / ``DT_REFER`` index is
the exception in this sub-root, not the pattern.

⚠️ ``Link_Download`` here uses plain ``http`` against ``http://www.rad.cvm.gov.br`` under an
``ENETCONSULTA`` path — where IPE and VLMO use ``https`` under ``ENET``. It is returned
**exactly as published**: the reader normalises neither scheme nor path, and never follows it.

Download/unzip/parse is inherited from the private `_BaseCgvnReader`.
"""

from __future__ import annotations

from typing import ClassVar

from filings_cvm._internal.config.contracts.cgvn_cia_aberta import CGVN_CIA_ABERTA
from filings_cvm._internal.utils.tabular_reader import FileContract
from filings_cvm.ingestion.cia_aberta.doc.cgvn._base_cgvn_reader import _BaseCgvnReader


class CgvnCiaAbertaReader(_BaseCgvnReader):
	"""Read the CGVN CIA_ABERTA index member into a typed DataFrame.

	Methods
	-------
	read(int_timeout_s)
		Download, unzip, and parse the reference year's index (inherited).
	"""

	_MEMBER_STEM: ClassVar[str] = "cgvn_cia_aberta"
	_CONTRACT: ClassVar[FileContract] = CGVN_CIA_ABERTA
	_DATE_COLS: ClassVar[tuple[str, ...]] = (
		"Data_Referencia",
		"Data_Entrega",
		"Data_Inicio_Exercicio_Social",
		"Data_Fim_Exercicio_Social",
	)
	_LABEL: ClassVar[str] = "índice"
