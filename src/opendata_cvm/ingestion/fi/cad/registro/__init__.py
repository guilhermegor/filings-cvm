"""CVM **Registro RCVM 175** readers — the three members of `registro_fundo_classe.zip`.

The post-Resolução CVM 175 fund → class → subclass hierarchy (where the live funds are), plus its
META reader. Re-exported from `opendata_cvm.ingestion`.
"""

from opendata_cvm.ingestion.fi.cad.registro.meta import MetaRegistroReader
from opendata_cvm.ingestion.fi.cad.registro.registro_classe import RegistroClasseReader
from opendata_cvm.ingestion.fi.cad.registro.registro_fundo import RegistroFundoReader
from opendata_cvm.ingestion.fi.cad.registro.registro_subclasse import RegistroSubclasseReader


__all__ = [
	"MetaRegistroReader",
	"RegistroClasseReader",
	"RegistroFundoReader",
	"RegistroSubclasseReader",
]
