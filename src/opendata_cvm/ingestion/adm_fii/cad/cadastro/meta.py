"""CVM **META** for the Administrador de FII Cadastro dataset (`ADM_FII/CAD`).

The spec CVM publishes for `cad_adm_fii.csv` — the declared description, type and size of each
field. A flat `.txt`, so the whole document is one section.
"""

from __future__ import annotations

from typing import ClassVar

from opendata_cvm._internal.config.contracts.meta import META_CAD_ADM_FII
from opendata_cvm._internal.utils.tabular_reader import FileContract
from opendata_cvm.ingestion._base_meta_reader import BaseMetaReader


class MetaCadAdmFiiReader(BaseMetaReader):
	"""Read the META of the CVM Administrador de FII Cadastro dataset.

	Methods
	-------
	read(int_timeout_s)
		Download and parse the META into a validated DataFrame (inherited).
	"""

	_META_URL: ClassVar[str] = (
		"https://dados.cvm.gov.br/dados/ADM_FII/CAD/META/meta_cad_adm_fii.txt"
	)
	_CONTRACT: ClassVar[FileContract] = META_CAD_ADM_FII
