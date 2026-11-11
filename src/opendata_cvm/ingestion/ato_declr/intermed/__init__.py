"""CVM open-data **Atos Declaratórios** reader (`ATO_DECLR/INTERMED`).

Snapshot list of the acts that suspend irregular intermediation, plus its META reader.
"""

from opendata_cvm.ingestion.ato_declr.intermed.ato_declr import AtoDeclrReader
from opendata_cvm.ingestion.ato_declr.intermed.meta import MetaAtoDeclrReader


__all__ = ["AtoDeclrReader", "MetaAtoDeclrReader"]
