"""filings-cvm — typed access to CVM regulatory XML file standards.

Two macro-sections organise every solution:

- ``filings_cvm.submission`` — build and serialise files to *send* to CVM (envio).
- ``filings_cvm.ingestion`` — parse and interpret files *received* from CVM (leitura).

See the CVM XML Standards catalog in ``CLAUDE.md`` for the full source of truth.
"""

from importlib.metadata import PackageNotFoundError, version

from filings_cvm.ingestion import CdaReader, InformeDiarioReader
from filings_cvm.submission import (
	InformeDiario,
	InformeDiarioDocument,
	PerfilMensal,
	PerfilMensalDocument,
)


try:
	__version__ = version("filings-cvm")
except PackageNotFoundError:  # pragma: no cover - source tree without an installed dist
	__version__ = "0.0.0"


__all__ = [
	"CdaReader",
	"InformeDiario",
	"InformeDiarioDocument",
	"InformeDiarioReader",
	"PerfilMensal",
	"PerfilMensalDocument",
	"__version__",
]
