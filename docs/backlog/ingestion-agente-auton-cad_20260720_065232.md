# Work ledger — AGENTE_AUTON/CAD reader (#131)

Issue **#131**. Branch `feat/131-agente-auton-cad-reader`. Third PR of **Wave 3** of #41
(service-provider CAD snapshots), tracked in #122. Ships the `agente_auton/` portal root.

## Grounding (real 2026 bytes)

- `cad_agente_auton.zip` = **2 members**: `cad_agente_auton_pf.csv` (6 cols, ~49,339 rows),
  `cad_agente_auton_pj.csv` (19 cols, ~4,794 rows). Snapshot at a fixed URL → **no `date_ref`**.
- **pf** = `NOME;DT_REG;DT_CANCEL;MOTIVO_CANCEL;SIT;DT_INI_SIT` — **no CPF**; keyed by `NOME`, which
  **can arrive blank** (no unique key) → `tuple_cnpj_cols=()`.
- **pj** = `CNPJ;DENOM_SOCIAL;DENOM_COMERC;DT_REG;DT_CANCEL;MOTIVO_CANCEL;SIT;DT_INI_SIT;TP_ENDER;LOGRADOURO;COMPL;BAIRRO;MUN;UF;CEP;DDD;TEL;EMAIL;SITE_ADMIN`.
  `CNPJ` **masked** (`49.270.551/0001-64`) → validates; `tuple_cnpj_cols=("CNPJ",)`.
- ⚠️ **NOT a copy of AUDITOR/AGENTE_FIDUC**: adds `MOTIVO_CANCEL`, `DENOM_COMERC`, `EMAIL`,
  `SITE_ADMIN`; uses `DDD` (not `DDD_TEL`). 3 date cols (`DT_REG`, `DT_CANCEL`, `DT_INI_SIT`);
  `MOTIVO_CANCEL` is free text, NOT a date. Contracts generated from the header, pinned to fixtures.
- META = `meta_cad_agente_auton.zip`, 2 members (pf/pj) → one `MetaAgenteAutonReader` (26th).
- Live-verified: pf=49,339, pj=4,794 rows; 3 dates coerce; masked CNPJ validates; META=25 field rows
  (sections pf/pj); provenance stamped.

## Done

- [x] Contracts `_internal/config/contracts/cad_agente_auton.py` (`CAD_AGENTE_AUTON_PF/PJ`),
      generated from + pinned to `tests/fixtures/cad_agente_auton/*_header.csv` (verbatim, header-only).
- [x] `_base_agente_auton_reader.py` + `agente_auton_pf.py`, `agente_auton_pj.py`, `meta.py`
      (`MetaAgenteAutonReader`, the 26th Meta reader).
- [x] `META_CAD_AGENTE_AUTON` in `contracts/meta.py`; `MetaAgenteAutonReader` registered in
      `bin/check_contract_drift.py` `_META_MEMBERS`.
- [x] Wiring: `agente_auton/__init__.py` + `agente_auton/cad/__init__.py`; flat re-exports in
      `ingestion/__init__.py` and top `filings_cvm/__init__.py` (+ `__all__`); `contracts/__init__.py`.
- [x] Tests `tests/unit/test_agente_auton_ingestion.py` (mirrors AGENTE_FIDUC). Bumped
      `test_meta_readers.py` 25→26.
- [x] Docs: `docs/ingestion/agente_auton.md` + mkdocs nav + `api.md` (new section, Meta 25→26) +
      ingestion index + `meta.md` (25→26 + row) + root `CLAUDE.md` catalog & layout.
- [x] Gates: ruff + mypy clean; `check_typing` + `check_provenance` pass; new + meta + drift unit
      tests green (62). Live-verified against real CVM bytes.

## Remaining

- [ ] Full unit suite; codespell; `mkdocs --strict`; all pre-commit hooks.
- [ ] Commit → PR `Closes #131` → CodeQL (empty-commit re-trigger only if it drops) → admin-merge →
      release PATCH (0.25.9).
- [ ] Next Wave 3 roots: INVNR, INTERMED (2-member), then ADM_CART, CONSULTOR_VLMOB (5-member),
      ADM_FII (flat). ⚠️ Check each `pf` for CPF (AUDITOR/AGENTE_FIDUC/AGENTE_AUTON had none, but
      others may) — keep out of `tuple_cnpj_cols`, header-only fixtures.
