# Informe Mensal FIDC submission writer (#25)

Spec: `PadraoXMLMensalFIDC576.asp` (ICVM 576, from 2019-11-01; `urn:fidc`).

- [x] Read the CVM page and derive the tag tree, scales and cardinalities
- [x] Schema `_internal/config/schemas/inf_mensal_fidc.py` (SOMATORIO items 1-30 enforced)
- [x] Writer `submission/inf_mensal_fidc.py` (schema-driven, windows-1252)
- [x] Unit tests incl. negative cases
- [x] Re-export from `submission/__init__.py` (sorted `__all__`)
- [x] codespell: `passiv` (CVM tag PASSIV) added to ignore list
- [x] Merge `origin/main`; satisfy `check-schemas` and `check-docs-sections`
- [x] `docs/submission/inf_mensal_fidc.md` + `mkdocs.yml` nav
- [x] Root `CLAUDE.md` catalog: FIDC submission pending -> done
- [ ] Push, open PR (`Closes #25`)
