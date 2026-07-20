"""CVM **META** for the AGENTE_AUTON Cadastro dataset (`AGENTE_AUTON/CAD`, `cad_agente_auton.zip`).

The spec CVM publishes for the autonomous-agent registry — the declared description, type and size
of each field. A ZIP of two members (`meta_cad_agente_auton_pf.txt`,
`meta_cad_agente_auton_pj.txt`), so the parsed frame comes back as one long frame with each
member's section in ``section``.
"""

from __future__ import annotations

from typing import ClassVar

from filings_cvm._internal.config.contracts.meta import META_CAD_AGENTE_AUTON
from filings_cvm._internal.utils.tabular_reader import FileContract
from filings_cvm.ingestion._base_meta_reader import BaseMetaReader


class MetaAgenteAutonReader(BaseMetaReader):
	"""Read the META of the CVM AGENTE_AUTON Cadastro dataset.

	Methods
	-------
	read(int_timeout_s)
		Download and parse the META into a validated DataFrame (inherited).
	"""

	_META_URL: ClassVar[str] = (
		"https://dados.cvm.gov.br/dados/AGENTE_AUTON/CAD/META/meta_cad_agente_auton.zip"
	)
	_CONTRACT: ClassVar[FileContract] = META_CAD_AGENTE_AUTON
	_MEMBER_STEM: ClassVar[str] = "cad_agente_auton"
