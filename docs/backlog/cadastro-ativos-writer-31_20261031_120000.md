# Cadastro de Ativos submission writer (#31)

Spec: `PadraoXMLAtivos.asp` (`COD_DOC=2`, no namespace, windows-1252).

- [x] Read the CVM page and derive the tag tree, tables 1/2 and cardinalities
- [x] Schema `_internal/config/schemas/cadastro_ativos.py`
- [x] Writer `submission/cadastro_ativos.py`
- [x] Unit tests `tests/unit/test_cadastro_ativos_submission.py`
- [x] Re-export from `submission/__init__.py` (sorted `__all__`)
- [x] `docs/submission/cadastro_ativos.md`, mkdocs nav, `docs/api.md`, CLAUDE.md catalog
- [ ] Merge `origin/main`, push, open PR (`Closes #31`)
