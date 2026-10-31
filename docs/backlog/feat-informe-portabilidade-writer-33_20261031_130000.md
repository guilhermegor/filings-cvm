# Work ledger — #33 Informe de Portabilidade submission writer

Branch `feat/informe-portabilidade-writer-33`. Spec: `PadraoXMLInfoPortabilidade.asp` (fetched 2026-10-31).

- [x] Confirmed no Informe de Portabilidade writer on `origin/main`.
- [x] File surface appended to the issue body.
- [x] Schema `_internal/config/schemas/informe_portabilidade.py` (models only).
- [x] Writer `submission/informe_portabilidade.py` (`InformePortabilidade`, encodes to bytes before touching the target file).
- [x] Names registered in `submission/__init__.py` (sorted `__all__`).
- [x] Unit tests: XML of header and INFORM blocks against spec-typed tag lists, every rule below.
- [x] `docs/submission/informe_portabilidade.md`, `mkdocs.yml` nav, `docs/api.md`, `docs/index.md`, `CLAUDE.md` catalog.
- [ ] PR (`Closes #33`).

## What the page leaves unsettled (stated on the docs page and in the PR)

- No decimal field exists: every quantity is a request count, modelled as a strict non-negative
  `int` (no money/percentage scale needed).
- `DT_EVENT` ("mês das solicitações") has no stated format: assumed `MM/AAAA`, like `DT_COMPT`.
- Cardinality of `INFORM` is not stated: at least one, no upper bound.
- No relation between the counts (e.g. canceled <= requested) is stated, so none is enforced.
- No CVM validator (the page of the sibling standards links a syntax tester) was run.
