"""CVM FCA CIA_ABERTA (geral) — ingestion (leitura) reader.

The company's general registration data — incorporation, CVM registry status, sector, control.

The member with the most date columns (**nine**), most of them partly blank; blanks become ``NaT``.

Download/unzip/parse is inherited from the private `_BaseFcaReader`; this module only declares
which member it reads and how it is typed.
"""

from __future__ import annotations

from typing import ClassVar

from filings_cvm._internal.config.contracts.fca_cia_aberta import FCA_CIA_ABERTA_GERAL
from filings_cvm._internal.utils.tabular_reader import FileContract
from filings_cvm.ingestion.cia_aberta.doc.fca._base_fca_reader import _BaseFcaReader


class FcaCiaAbertaGeralReader(_BaseFcaReader):
	"""Read the FCA CIA_ABERTA `geral` member into a typed DataFrame.

	Methods
	-------
	read(int_timeout_s)
		Download, unzip, and parse the reference year's member (inherited).
	"""

	_MEMBER_STEM: ClassVar[str] = "fca_cia_aberta_geral"
	_CONTRACT: ClassVar[FileContract] = FCA_CIA_ABERTA_GERAL
	_DATE_COLS: ClassVar[tuple[str, ...]] = (
		"Data_Referencia",
		"Data_Nome_Empresarial",
		"Data_Constituicao",
		"Data_Registro_CVM",
		"Data_Categoria_Registro_CVM",
		"Data_Situacao_Registro_CVM",
		"Data_Situacao_Emissor",
		"Data_Especie_Controle_Acionario",
		"Data_Alteracao_Exercicio_Social",
	)
	_LABEL: ClassVar[str] = "geral"
