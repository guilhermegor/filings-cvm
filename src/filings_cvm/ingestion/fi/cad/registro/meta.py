"""CVM **META** for the FI Registro RCVM 175 dataset (`FI/CAD`, `registro_fundo_classe.zip`).

The spec CVM publishes for the fundo/classe/subclasse members of `registro_fundo_classe.zip` — the
declared description, type and size of every field.
"""

from __future__ import annotations

from typing import ClassVar

from filings_cvm._internal.config.contracts.meta import META_REGISTRO_FUNDO_CLASSE
from filings_cvm._internal.utils.tabular_reader import FileContract
from filings_cvm.ingestion._base_meta_reader import BaseMetaReader


class MetaRegistroReader(BaseMetaReader):
	"""Read the META of the CVM FI Registro RCVM 175 dataset.

	Methods
	-------
	read(int_timeout_s)
		Download and parse the META into a validated DataFrame (inherited).
	"""

	_META_URL: ClassVar[str] = (
		"https://dados.cvm.gov.br/dados/FI/CAD/META/meta_registro_fundo_classe.zip"
	)
	_CONTRACT: ClassVar[FileContract] = META_REGISTRO_FUNDO_CLASSE
	_MEMBER_STEM: ClassVar[str] = "registro"
