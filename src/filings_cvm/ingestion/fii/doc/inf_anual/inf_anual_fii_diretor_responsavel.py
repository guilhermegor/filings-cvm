"""CVM Informe Anual FII — membro *diretor responsável* reader.

The ``inf_anual_fii_diretor_responsavel`` member of ``inf_anual_fii_AAAA.zip``: the director
responsible for the fund — identity, education, the fund shares they hold/bought/sold, and any
criminal or CVM conviction.

**Carries a ``CPF``** (a natural person's id). It is read as exact text and **never** validated as
a CNPJ; treat it as personal data downstream. See ``_base_inf_anual_fii_reader`` for the shared
behaviour.
"""

from __future__ import annotations

from typing import ClassVar

from filings_cvm._internal.config.contracts import (
	INF_ANUAL_FII_DIRETOR_RESPONSAVEL,
	FileContract,
)
from filings_cvm.ingestion.fii.doc.inf_anual._base_inf_anual_fii_reader import (
	_BaseInfAnualFiiReader,
)


class InfAnualFiiDiretorResponsavelReader(_BaseInfAnualFiiReader):
	"""Read the Informe Anual FII *diretor responsável* member into a typed DataFrame."""

	_MEMBER_STEM: ClassVar[str] = "inf_anual_fii_diretor_responsavel"
	_CONTRACT: ClassVar[FileContract] = INF_ANUAL_FII_DIRETOR_RESPONSAVEL
	_DATE_COLS: ClassVar[tuple[str, ...]] = ("Data_Referencia", "Data_Inicio")
	_LABEL: ClassVar[str] = "diretor responsável"
