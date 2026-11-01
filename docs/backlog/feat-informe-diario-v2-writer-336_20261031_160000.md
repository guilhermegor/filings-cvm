# Work ledger — #336 Informe Diário V2 submission writer

Branch `feat/336-informe-diario-v2-writer`. Spec: `PadraoXMLInfoDiarioNet739.asp` (fetched 2026-10-31).

- [x] Page measured: VERSAO 2.0, `CNPJ_FDO` only, no `DATA_PROX_PL`, tag order, scales (2 / 12 / 4).
- [x] Schema `_internal/config/schemas/informe_diario_v2.py` reusing V4 field types and shareholder block.
- [x] Writer `submission/informe_diario_v2.py` (reuses V4 formatting helpers).
- [x] Registered in `submission/__init__.py`; docs page, nav, api.md, index.md, README, CLAUDE.md.
- [ ] PR (`Closes #336`).

Note: `atomic_write_bytes` (#330) is not on main; output is written like the V4 writer and #330 will migrate it.
