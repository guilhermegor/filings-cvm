# Work ledger — #337 Informe Diário V3 submission writer

Branch `feat/337-informe-diario-v3-writer`. Spec: `PadraoXMLInfoDiarioNetV3.asp` (fetched 2026-10-31).

- [x] Page fetched and diffed against V4: only `VERSAO` 3.0 and no `COD_SUBCLASSE`.
- [x] Schema extends V4; writer is its own `SubmissionWriter` adapter delegating to the V4 writer's public `export` (composition, not a V4 subclass).
- [x] Tests, docs page, nav, api.md, index.md, README, CLAUDE.md.
- [ ] PR (`Closes #337`).

Note: the file write is atomic, inherited through the V4 writer's `atomic_write_bytes`.
