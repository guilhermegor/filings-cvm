"""CVM **Registro RCVM 175** readers — the three members of `registro_fundo_classe.zip`.

The post-Resolução CVM 175 fund → class → subclass hierarchy (where the live funds are).
Re-exported from `filings_cvm.ingestion`.
"""

from filings_cvm.ingestion.cad.registro.registro_classe import RegistroClasseReader
from filings_cvm.ingestion.cad.registro.registro_fundo import RegistroFundoReader
from filings_cvm.ingestion.cad.registro.registro_subclasse import RegistroSubclasseReader


__all__ = ["RegistroClasseReader", "RegistroFundoReader", "RegistroSubclasseReader"]
