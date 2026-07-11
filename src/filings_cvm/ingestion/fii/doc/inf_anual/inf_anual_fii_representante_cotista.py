"""CVM Informe Anual FII — membro *representante de cotistas* reader.

The ``inf_anual_fii_representante_cotista`` member of ``inf_anual_fii_AAAA.zip``: the
shareholders' elected representative — identity, remuneration, the fund shares they
hold/bought/sold, the election date and mandate end, and any criminal or CVM conviction.

**Carries a ``CPF``** (a natural person's id). It is read as exact text and **never** validated as
a CNPJ; treat it as personal data downstream. See ``_base_inf_anual_fii_reader`` for the shared
behaviour.
"""

from __future__ import annotations

from typing import ClassVar

from filings_cvm._internal.config.contracts import (
	INF_ANUAL_FII_REPRESENTANTE_COTISTA,
	FileContract,
)
from filings_cvm.ingestion.fii.doc.inf_anual._base_inf_anual_fii_reader import (
	_BaseInfAnualFiiReader,
)


class InfAnualFiiRepresentanteCotistaReader(_BaseInfAnualFiiReader):
	"""Read the Informe Anual FII *representante de cotistas* member into a typed DataFrame."""

	_MEMBER_STEM: ClassVar[str] = "inf_anual_fii_representante_cotista"
	_CONTRACT: ClassVar[FileContract] = INF_ANUAL_FII_REPRESENTANTE_COTISTA
	_DATE_COLS: ClassVar[tuple[str, ...]] = ("Data_Referencia", "Data_Eleicao")
	_LABEL: ClassVar[str] = "representante de cotistas"
