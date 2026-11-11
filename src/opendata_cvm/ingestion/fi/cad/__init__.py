"""CVM open-data **cadastro** readers (`FI/CAD`).

The fund registry: the legacy current-state snapshot (`cad_fi.csv`), the post-RCVM 175
registry (:mod:`opendata_cvm.ingestion.fi.cad.registro`), and the change-log
(:mod:`opendata_cvm.ingestion.fi.cad.cad_fi_hist`). Re-exported from `opendata_cvm.ingestion`.
"""

from opendata_cvm.ingestion.fi.cad.cadastro_fi import CadastroFiReader, MetaCadastroFiReader


__all__ = ["CadastroFiReader", "MetaCadastroFiReader"]
