# CONSULTOR_VLMOB/CAD reader — `cad_consultor_vlmob.zip` (5 membros) — issue #139

Branch `feat/139-consultor-vlmob-cad-reader`. Wave 3 slice **7/8** of #41. Inaugurates the portal
root `consultor_vlmob/`. Same 5-member shape as ADM_CART (#137). **Closes the 5-member roots** —
only ADM_FII (flat CSV) remains to end Wave 3.

## Grounding (verified against the real 2026-07-20 artifact)

- Snapshot ZIP, fixed URL, **no `date_ref`**. 5 members:
  | member | cols | rows | date cols | CNPJ |
  |---|---|---|---|---|
  | `pf` | 7 | 3.743 | 3 | no column |
  | `pj` | 20 | 1.031 | 3 | 1031/1031 valid |
  | `diretor` | 3 | 725 | **0** | 725/725 |
  | `resp` | 3 | 1.557 | **0** | 1557/1557 |
  | `socios` | 2 | 1.862 | **0** | 1862/1862 |
- Same dateless-member shape as ADM_CART (`diretor`/`resp`/`socios` → `_DATE_COLS=()`); META
  confirms those three declare no `date` field.
- ⚠️ **NOT a copy of ADM_CART** — each contract generated from its own header:
  - `pf` keyed by **`NOME`** (not `ADMIN`); 7th column **`SITE_ADMIN`** (not `CATEG_REG`).
  - `pj` has **20 cols** (ADM_CART 24): no `CATEG_REG`/`SUBCATEG_REG`/`VL_PATRIM_LIQ`/
    `DT_PATRIM_LIQ` → **only 3 date cols**, not 4. Pinned by
    `test_pj_has_three_date_columns_not_four`.
- `pf` has **no CNPJ nor CPF** → `tuple_cnpj_cols=()`. Satellites carry personal data but **no CPF**
  → keyed on the consultant's CNPJ. **All CNPJ 100% valid** (no malformed value like ADM_CART's).
- `CEP`/`TEL` `numeric` in META → kept `str`. `pj` uses `DDD` (not `DDD_TEL`).
- META URL confirmed `CONSULTOR_VLMOB/CAD/META/meta_cad_consultor_vlmob.zip` (5 members,
  alphabetical). All members carry the `<stem>_` suffix → section labels **symmetric**.

## Done

- [x] Grounded against the real artifact + META (URL probed, types read, CNPJ validity checked)
- [x] Header fixtures pinned verbatim (`tests/fixtures/cad_consultor_vlmob/*_header.csv`)
- [x] Contracts generated from + pinned to headers (`_internal/config/contracts/cad_consultor_vlmob.py`)
- [x] `_base_consultor_vlmob_reader.py` + 5 readers (pf/pj/diretor/resp/socios)
- [x] `MetaConsultorVlmobReader` (30th) + `META_CAD_CONSULTOR_VLMOB` in contracts/meta.py
- [x] Registered in `bin/check_contract_drift.py` `_META_MEMBERS`
- [x] Wired all `__init__` layers (nested + flat) + `__all__` (169 public names, 30 Meta readers)
- [x] Tests `tests/unit/test_consultor_vlmob_ingestion.py` (incl. dateless-member + pj-3-date-cols
      anti-copy + no-CPF tests) + `test_meta_readers.py` count 29→30
- [x] Docs: page + mkdocs nav + api.md + ingestion index + meta.md + root CLAUDE.md (catalog + layout)
- [x] #41 survey ledger ticked (CONSULTOR_VLMOB ✅ #139)

- [x] Gates: ruff ✅ · ruff format ✅ · mypy (301 files) ✅ · check_typing ✅ · check_provenance ✅ ·
      unit suite **1661 green** ✅ · mkdocs --strict ✅ · codespell ✅
- [x] Live-verified: pf 3.743, pj 1.031 (no `DT_PATRIM_LIQ` column), diretor 725, resp 1.557,
      socios 1.862; dateless members all-text; `CEP` `str`; META 5 symmetric sections; provenance
      stamped

## Remaining

- [ ] All pre-commit hooks (run at commit time)
- [ ] Commit → PR `Closes #139` → wait approval + merge → release PATCH
- [ ] AFTER merge: update sweep checkpoint memory (Wave 3 → 7/8), NEXT = **ADM_FII** (flat CSV,
      18 cols) which **closes Wave 3**
