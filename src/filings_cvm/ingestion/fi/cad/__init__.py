"""CVM open-data **cadastro** readers (`FI/CAD`).

The fund registry: the legacy current-state snapshot (`cad_fi.csv`), the post-RCVM 175
registry (:mod:`filings_cvm.ingestion.fi.cad.registro`), and the change-log
(:mod:`filings_cvm.ingestion.fi.cad.cad_fi_hist`). Re-exported from `filings_cvm.ingestion`.
"""

from filings_cvm.ingestion.fi.cad.cadastro_fi import CadastroFiReader, MetaCadastroFiReader


__all__ = ["CadastroFiReader", "MetaCadastroFiReader"]
