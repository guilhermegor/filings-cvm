"""filings-cvm — typed access to CVM regulatory file standards.

Every solution lives in ``filings_cvm.ingestion`` — parse and interpret files *received* from
CVM (leitura). Building the XML files to *send* to CVM (envio) moved to the separate
``layouts-cvm`` package.

See the catalog in ``AGENTS.md`` for the full source of truth.

**The ingestion readers are not re-exported here.** They are grouped by **CVM portal root** — the
portal's own division at <https://dados.cvm.gov.br/dados> — and each root package is the public
surface for its readers::

    from filings_cvm.ingestion.cia_aberta import FreCiaAbertaAuditorReader
    from filings_cvm.ingestion.fidc import InfMensalFidcTabIReader

There are 22 such roots. A single flat namespace would put 200+ reader names in one wall with no
division, and every new reader would widen it; the portal grouping is the division the data
already has.

So the ingestion section owns its names, and this top-level package keeps only what belongs to
none of them: the shared :class:`RetryPolicy` knob every reader accepts, and ``__version__``.
Importing a reader from here raises ``ImportError`` — see the changelog's migration note.
"""

from importlib.metadata import PackageNotFoundError, version

from filings_cvm._internal.utils.retry import RetryPolicy


try:
	__version__ = version("filings-cvm")
except PackageNotFoundError:  # pragma: no cover - source tree without an installed dist
	__version__ = "0.0.0"


__all__ = [
	"RetryPolicy",
	"__version__",
]
