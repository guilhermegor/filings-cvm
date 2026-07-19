# Work ledger — AUDITOR/CAD reader (#127)

Issue **#127**. Branch `feat/127-auditor-cad-reader`. First PR of **Wave 3** of #41 (service-provider
CAD snapshots), tracked in #122. Ships the `auditor/` portal root.

## Grounding (real 2026 bytes)

- `cad_auditor.zip` = **2 members** (not a flat CSV): `cad_auditor_pf.csv` (4 cols), `cad_auditor_pj.csv`
  (12 cols). Snapshot at a fixed URL, so **no `date_ref`** (the `CadastroFiReader` mould).
- **pf has no CPF column** — `CD_CVM;AUDITOR;SIT;DT_INI_SIT`. Identifies a person auditor by code +
  name, so `tuple_cnpj_cols=()`.
- **pj**: `CD_CVM;CNPJ;DENOM_SOCIAL;SIT;DT_INI_SIT;TP_ENDER;LOGRADOURO;COMPL;BAIRRO;MUN;UF;CEP`.
  `CNPJ` is **masked** (`36.348.092/0001-42`) → validates via `br_identifiers`; `tuple_cnpj_cols=("CNPJ",)`.
- Only date column: `DT_INI_SIT` (META type=`date`, confirmed). `CD_CVM`/`CEP` numeric-in-META but
  kept as **text** (leading zeros).
- META = `meta_cad_auditor.zip`, 2 members (`meta_cad_auditor_pf.txt`, `_pj.txt`), ISO-8859-1+CRLF →
  one `MetaAuditorReader`, `_MEMBER_STEM="cad_auditor"`.
- Live-verified: pf=30 rows, pj=491 rows, dates coerce, provenance stamped, META=16 field rows
  (sections `pf`/`pj`).

## Done

- [x] Contracts `_internal/config/contracts/cad_auditor.py` (`CAD_AUDITOR_PF`, `CAD_AUDITOR_PJ`),
      generated from + pinned to `tests/fixtures/cad_auditor/*_header.csv` (verbatim, header-only).
- [x] `_base_auditor_reader.py` (mirrors `_base_cad_fi_hist_reader.py`) + `auditor_pf.py`,
      `auditor_pj.py`, `meta.py` (`MetaAuditorReader`, the 24th Meta reader).
- [x] `META_CAD_AUDITOR` in `contracts/meta.py`; `MetaAuditorReader` registered in
      `bin/check_contract_drift.py` `_META_MEMBERS` (multi-member readers expose `_CONTRACT`, so no
      `_UNEXPOSED` entry needed).
- [x] Wiring: `auditor/__init__.py` + `auditor/cad/__init__.py`; flat re-exports in
      `ingestion/__init__.py` and top `filings_cvm/__init__.py` (+ `__all__`); `contracts/__init__.py`.
- [x] Tests `tests/unit/test_auditor_ingestion.py` (mirrors `test_cad_fi_hist_ingestion.py`) incl. the
      anti-tautology `test_contract_matches_the_published_header`. Bumped `test_meta_readers.py` 23→24.
- [x] Docs: `docs/ingestion/auditor.md` + mkdocs nav + `api.md` (new section, Meta 23→24) + ingestion
      index + root `CLAUDE.md` catalog & layout. **Also fixed pre-existing meta.md drift**: it under-
      counted (22) and was missing the CRI row (the #114 PR omitted it) → now 24 with CRI + AUDITOR
      rows and the stale "CRI ainda não tem readers" note removed.
- [x] Gates: ruff + mypy clean on new files; `check_typing` + `check_provenance` pass; AUDITOR + meta
      + drift unit tests green (62). Live-verified against real CVM bytes.

## Remaining

- [ ] Full unit suite under pandas 3.x **and** 2.x; codespell; `mkdocs --strict`; all pre-commit hooks.
- [ ] Commit → PR `Closes #127` → wait approval+merge → release **PATCH**.
- [ ] Next Wave 3 roots (copy this mould): AGENTE_FIDUC, AGENTE_AUTON, INVNR, INTERMED (2-member),
      then ADM_CART, CONSULTOR_VLMOB (5-member), ADM_FII (flat). Some `pf` members **do** carry CPF —
      keep it out of `tuple_cnpj_cols`, header-only fixtures.
