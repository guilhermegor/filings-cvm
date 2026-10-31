# Work ledger — #29 Informe Mensal INR submission writer

Branch `feat/inr-mensal-writer-29`. Spec: `PadraoXMLInfoMensalINR.asp` (fetched 2026-10-31).

- [x] Confirmed no INR writer on `origin/main`.
- [x] Schema `_internal/config/schemas/inr_mensal.py` (models only; validators in `_internal/utils/inr_mensal_fields.py`).
- [x] Writer `submission/inr_mensal.py` (`InrMensal`, encodes to bytes before touching the target file).
- [x] Names registered in `submission/__init__.py` and `schemas/__init__.py` (sorted `__all__`).
- [x] Unit tests: XML of every block, every rule below, failed export leaves target intact.
- [x] `docs/submission/inr_mensal.md`, `mkdocs.yml` nav, `docs/api.md`, `CLAUDE.md` catalog.
- [ ] PR (`Closes #29`).

## What the page leaves unsettled (stated on the docs page and in the PR)

- Conflict: the notes say "vírgula separa casas decimais" but every amount is "numérico e inteiro".
  Chose whole numbers (`int`); a fractional value is refused, never truncated.
- Conflict: the sample shows `COD_DOC` 477 while the tag list says "deve ser 'XX'". Used 477.
- Sign of amounts is not stated: flows, transfers and notionals are non-negative; market value
  and net worth may be negative.
- `VL_NOCION_APLIC` is required for Tabela A codes 15-24 and refused otherwise (page: "APENAS").
- Participant code check digit: algorithm unpublished, checked only as one digit.
- Assumed: a participant code appears once per file; the `AAAAA` of a code is not forced to equal
  `CD_CVM`; empty optional containers are refused (the page says to omit them).
- No CVM validator (the page links a syntax tester) was run.
