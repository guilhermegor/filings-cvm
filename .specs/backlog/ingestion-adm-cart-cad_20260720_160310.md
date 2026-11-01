# ADM_CART/CAD reader — `cad_adm_cart.zip` (5 membros) — issue #137

Branch `feat/137-adm-cart-cad-reader`. Wave 3 slice **6/8** of #41. Inaugurates the portal root
`adm_cart/`. **First 5-member root** — step up from the 2-member mould (AUDITOR #127 → INTERMED
#135).

## Grounding (verified against the real 2026-07-20 artifact)

- Snapshot ZIP, fixed URL, **no `date_ref`**. 5 members:
  | member | cols | rows | date cols | CNPJ |
  |---|---|---|---|---|
  | `pf` | 7 | 6.776 | 3 | no column |
  | `pj` | 24 | 3.033 | 4 | 3032/3033 valid |
  | `diretor` | 3 | 1.718 | **0** | 1718/1718 |
  | `resp` | 3 | 6.637 | **0** | 6636/6637 |
  | `socios` | 2 | 7.942 | **0** | 7942/7942 |
- ⚠️ **NEW SHAPE — 3 of 5 members have no date column at all** (`diretor`/`resp`/`socios`), the
  first in the library → `_DATE_COLS=()`. Proven `apply_dtypes(..., list_date_cols=())` works before
  writing; META confirms those three declare no `date` field.
- `pf` keyed by `ADMIN` (name), **no CNPJ nor CPF** → `tuple_cnpj_cols=()`.
- Satellites carry personal data (`DIRETOR`/`RESP`/`SOCIOS`, `SOCIOS` mixes PF+PJ) but **no CPF
  column** → `tuple_cnpj_cols=("CNPJ",)` (the manager's), fixtures header-only (LGPD).
- ⚠️ **One genuinely malformed source CNPJ**: `00.010.354/1901-72` in `pj` and `resp`, fails mod-11.
  `tuple_cnpj_cols` requires *at least one* valid → contracts pass, value honoured as published
  (pinned by `test_read_tolerates_a_malformed_cnpj_among_valid_ones`).
- `pj` uses `DDD` (like AGENTE_AUTON), not `DDD_TEL`. `CEP`/`TEL` `numeric` in META → kept `str`.
- META URL confirmed `ADM_CART/CAD/META/meta_cad_adm_cart.zip` (5 members, alphabetical). All 5
  members carry the `<stem>_` suffix → section labels **symmetric** (no INTERMED-style asymmetry).

## Done

- [x] Grounded against the real artifact + META (URL probed, types read, CNPJ validity checked)
- [x] Header fixtures pinned verbatim (`tests/fixtures/cad_adm_cart/*_header.csv`, ISO-8859-1/CRLF)
- [x] Contracts generated from + pinned to headers (`_internal/config/contracts/cad_adm_cart.py`)
- [x] `_base_adm_cart_reader.py` + 5 readers (pf/pj/diretor/resp/socios)
- [x] `MetaAdmCartReader` (29th) + `META_CAD_ADM_CART` in contracts/meta.py
- [x] Registered in `bin/check_contract_drift.py` `_META_MEMBERS`
- [x] Wired all `__init__` layers (nested + flat) + `__all__` (163 public names, 29 Meta readers)
- [x] Tests `tests/unit/test_adm_cart_ingestion.py` (incl. dateless-member + malformed-CNPJ +
      no-CPF tests) + `test_meta_readers.py` count 28→29
- [x] Docs: page + mkdocs nav + api.md + ingestion index + meta.md + root CLAUDE.md (catalog + layout)
- [x] #41 survey ledger ticked (ADM_CART ✅ #137)

- [x] Gates: ruff ✅ · mypy (291 files) ✅ · check_typing ✅ · check_provenance ✅ · unit suite
      **1601 green** ✅ · mkdocs --strict ✅ · codespell ✅
- [x] Live-verified: pf 6.776, pj 3.033, diretor 1.718, resp 6.637, socios 7.942; dateless members
      all-text; `CEP` `str`; malformed CNPJ present in `resp`; META 5 symmetric sections; provenance
      stamped

## Remaining

- [ ] All pre-commit hooks (run at commit time)
- [ ] Commit → PR `Closes #137` → wait approval + merge → release PATCH
- [ ] AFTER merge: update sweep checkpoint memory (Wave 3 → 6/8), NEXT = CONSULTOR_VLMOB (5 membros)
