"""CVM open-data **Companhias Abertas** readers (`CIA_ABERTA/`).

Mirrors the `dados.cvm.gov.br/dados/CIA_ABERTA/` portal branch — the last and largest root of the
#41 sweep. The portal branch holds three sub-roots: `CAD` (the company registry, implemented here
via :mod:`filings_cvm.ingestion.cia_aberta.cad`), `DOC` (seven financial-statement datasets —
CGVN / DFP / FCA / FRE / IPE / ITR / VLMO) and `EVENTOS` (share buybacks). This slice ships the
`CAD` registry; the `DOC` and `EVENTOS` datasets land as their own readers. Every reader is
re-exported flat from `filings_cvm.ingestion`.
"""

from filings_cvm.ingestion.cia_aberta.cad import (
	CadastroCiaAbertaReader,
	MetaCadCiaAbertaReader,
)


__all__ = [
	"CadastroCiaAbertaReader",
	"MetaCadCiaAbertaReader",
]
