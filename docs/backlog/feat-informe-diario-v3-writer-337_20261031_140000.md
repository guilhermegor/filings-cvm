# Work ledger — #337 Informe Diário V3 submission writer

Branch `feat/337-informe-diario-v3-writer`. Spec: `PadraoXMLInfoDiarioNetV3.asp` (fetched 2026-10-31).

- [x] Page fetched and diffed against V4: only `VERSAO` 3.0 and no `COD_SUBCLASSE`.
- [x] Schema extends V4; writer subclasses V4 writer.
- [x] Tests, docs page, nav, api.md, index.md, README, CLAUDE.md.
- [ ] PR (`Closes #337`).

Note: no `atomic_write_bytes` on base; #330 will migrate the file write.
