# Work ledger — #338 Informe Trimestral V1 submission writer

Branch `feat/338-informe-trimestral-v1-writer`. Spec: `PadraoXMLInfoTrim.asp` (fetched 2026-11-01).

- [x] Fetched the page (200); measured tags, scales, COD_DOC 51, VERSAO, 100-fund cap.
- [x] Schema `_internal/config/schemas/informe_trimestral_v1.py` (own models; V2 shares only the serialiser).
- [x] Writer `submission/informe_trimestral_v1.py` (reuses V2's serialiser; temp file + `os.replace`).
- [x] Unit tests, one assertion each.
- [x] Docs page, nav, api.md, index.md, CLAUDE.md catalog, registries.
- [ ] PR (`Closes #338`); #330 migrates the file write to `atomic_write_bytes`.

## What the page leaves unsettled (stated on the docs page and in the PR)

- Sample says `VERSAO` 1.0; the field note says 2.0 (V2 leftover): used 1.0.
- No integer width stated: 18 integer digits for decimals, 999999999999 for counts.
- Negative net worth not addressed: allowed.
- No CVM validator was run.
