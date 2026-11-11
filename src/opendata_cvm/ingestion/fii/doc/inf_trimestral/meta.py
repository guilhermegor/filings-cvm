"""CVM **META** for the FII Informe Trimestral dataset (`FII/DOC/INF_TRIMESTRAL`).

The spec CVM publishes for the 16 members of `inf_trimestral_fii_AAAA.zip` — the declared
description, type and size of every field.
"""

from __future__ import annotations

from typing import ClassVar

from opendata_cvm._internal.config.contracts.meta import META_INF_TRIMESTRAL_FII
from opendata_cvm._internal.utils.tabular_reader import FileContract
from opendata_cvm.ingestion._base_meta_reader import BaseMetaReader


class MetaInfTrimestralFiiReader(BaseMetaReader):
	"""Read the META of the CVM FII Informe Trimestral dataset.

	Methods
	-------
	read(int_timeout_s)
		Download and parse the META into a validated DataFrame (inherited).
	"""

	_META_URL: ClassVar[str] = (
		"https://dados.cvm.gov.br/dados/FII/DOC/INF_TRIMESTRAL/META/meta_inf_trimestral_fii.zip"
	)
	_CONTRACT: ClassVar[FileContract] = META_INF_TRIMESTRAL_FII
	_MEMBER_STEM: ClassVar[str] = "inf_trimestral_fii"
