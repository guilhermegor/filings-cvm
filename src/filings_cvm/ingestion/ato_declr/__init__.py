"""CVM open-data **Atos Declaratórios** readers (`ATO_DECLR/`).

Mirrors the `dados.cvm.gov.br/dados/ATO_DECLR/` portal branch, which publishes a single dataset,
`ATO_DECLR/INTERMED` (:mod:`filings_cvm.ingestion.ato_declr.intermed`), plus its META reader.
"""

from filings_cvm.ingestion.ato_declr.intermed import AtoDeclrReader, MetaAtoDeclrReader


__all__ = ["AtoDeclrReader", "MetaAtoDeclrReader"]
