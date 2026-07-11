"""CVM Informe Anual FII — membro *experiência profissional* reader.

The ``inf_anual_fii_experiencia_profissional`` member of ``inf_anual_fii_AAAA.zip``: the
professional history of each diretor/representante — one row per position held (empresa, período,
cargo, atividade principal). A **long** table. See ``_base_inf_anual_fii_reader`` for the shared
behaviour.
"""

from __future__ import annotations

from typing import ClassVar

from filings_cvm._internal.config.contracts import (
	INF_ANUAL_FII_EXPERIENCIA_PROFISSIONAL,
	FileContract,
)
from filings_cvm.ingestion.fii.doc.inf_anual._base_inf_anual_fii_reader import (
	_BaseInfAnualFiiReader,
)


class InfAnualFiiExperienciaProfissionalReader(_BaseInfAnualFiiReader):
	"""Read the Informe Anual FII *experiência profissional* member into a typed DataFrame."""

	_MEMBER_STEM: ClassVar[str] = "inf_anual_fii_experiencia_profissional"
	_CONTRACT: ClassVar[FileContract] = INF_ANUAL_FII_EXPERIENCIA_PROFISSIONAL
	_DATE_COLS: ClassVar[tuple[str, ...]] = ("Data_Referencia",)
	_LABEL: ClassVar[str] = "experiência profissional"
