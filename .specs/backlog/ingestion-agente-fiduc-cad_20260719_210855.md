# Work ledger — AGENTE_FIDUC/CAD reader (#129)

Issue **#129**. Branch `feat/129-agente-fiduc-cad-reader`. Second PR of **Wave 3** of #41
(service-provider CAD snapshots), tracked in #122. Ships the `agente_fiduc/` portal root.

## Grounding (real 2026 bytes)

- `cad_agente_fiduc.zip` = **2 members**: `cad_agente_fiduc_pf.csv` (5 cols, 47 rows),
  `cad_agente_fiduc_pj.csv` (15 cols, 70 rows). Snapshot at a fixed URL → **no `date_ref`**.
- **pf** = `AGENTE_FIDUC;DT_REG;DT_CANCEL;SIT;DT_INI_SIT` — **no CPF, no `CD_CVM`**, identifies a
  person agent by **name alone** → `tuple_cnpj_cols=()`.
- **pj** = `CNPJ;DENOM_SOCIAL;DT_REG;DT_CANCEL;SIT;DT_INI_SIT;LOGRADOURO;COMPL;BAIRRO;MUN;UF;PAIS;CEP;DDD_TEL;TEL`.
  `CNPJ` **masked** (`00.271.457/0001-30`) → validates via `br_identifiers`; `tuple_cnpj_cols=("CNPJ",)`.
- ⚠️ **NOT a copy of AUDITOR**: **3 date cols** (`DT_REG`, `DT_CANCEL`, `DT_INI_SIT`) vs 1; no
  `CD_CVM`; pj adds `PAIS`/`DDD_TEL`/`TEL`. `DT_CANCEL` blank for active records. Contracts generated
  from the header, pinned to fixtures — never derived from the sibling.
- META = `meta_cad_agente_fiduc.zip`, 2 members (pf/pj) → one `MetaAgenteFiducReader` (25th),
  `_MEMBER_STEM="cad_agente_fiduc"`.
- Live-verified: pf=47, pj=70 rows; 3 dates coerce; masked CNPJ validates; META=20 field rows
  (sections pf/pj); provenance stamped.

## Done

- [x] Contracts `_internal/config/contracts/cad_agente_fiduc.py` (`CAD_AGENTE_FIDUC_PF/PJ`),
      generated from + pinned to `tests/fixtures/cad_agente_fiduc/*_header.csv` (verbatim, header-only).
- [x] `_base_agente_fiduc_reader.py` + `agente_fiduc_pf.py`, `agente_fiduc_pj.py`, `meta.py`
      (`MetaAgenteFiducReader`, the 25th Meta reader).
- [x] `META_CAD_AGENTE_FIDUC` in `contracts/meta.py`; `MetaAgenteFiducReader` registered in
      `bin/check_contract_drift.py` `_META_MEMBERS`.
- [x] Wiring: `agente_fiduc/__init__.py` + `agente_fiduc/cad/__init__.py`; flat re-exports in
      `ingestion/__init__.py` and top `filings_cvm/__init__.py` (+ `__all__`); `contracts/__init__.py`.
- [x] Tests `tests/unit/test_agente_fiduc_ingestion.py` (mirrors AUDITOR, incl. the anti-tautology
      header test). Bumped `test_meta_readers.py` 24→25.
- [x] Docs: `docs/ingestion/agente_fiduc.md` + mkdocs nav + `api.md` (new section, Meta 24→25) +
      ingestion index + `meta.md` (24→25 + row) + root `CLAUDE.md` catalog & layout.
- [x] Gates: ruff + mypy clean; `check_typing` + `check_provenance` pass; new + meta + drift unit
      tests green (62). Live-verified against real CVM bytes.

## Remaining

- [ ] Full unit suite; codespell; `mkdocs --strict`; all pre-commit hooks.
- [ ] Commit → PR `Closes #129` → CodeQL (may need the `--allow-empty` push re-trigger — see the
      `codeql-default-setup-drops-a-pr-dispatch` lesson) → admin-merge → release PATCH.
- [ ] Next Wave 3 roots: AGENTE_AUTON, INVNR, INTERMED (2-member), then ADM_CART, CONSULTOR_VLMOB
      (5-member), ADM_FII (flat). ⚠️ Their `pf` members likely DO carry CPF — keep out of
      `tuple_cnpj_cols`, header-only fixtures.
