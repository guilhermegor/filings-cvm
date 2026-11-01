# INTERMED/CAD reader — `cad_intermed.zip` (intermed + resp) — issue #135

Branch `feat/135-intermed-cad-reader`. Wave 3 slice **5/8** of #41. Inaugurates the portal root
`intermed/`. Mould: AUDITOR (#127) → AGENTE_FIDUC (#129) → AGENTE_AUTON (#131) → INVNR (#133).

## Grounding (verified against the real 2026-07-20 artifact)

- Snapshot ZIP, fixed URL, **no `date_ref`**.
- ⚠️ **The 2 members are NOT a `pf`/`pj` split** — the first departure from the mould:
  `cad_intermed.csv` (28 cols, 2.352 rows, the registry) + `cad_intermed_resp.csv` (8 cols, 5.545
  rows, responsible officers), **both keyed by the intermediary's `CNPJ`** (masked, 100% filled).
- Date cols: registry **4** (`DT_REG`/`DT_CANCEL`/`DT_INI_SIT`/`DT_PATRIM_LIQ`), resp **2**
  (`DT_REG`/`DT_INI_RESP`). `MOTIVO_CANCEL` is text (`varchar` in META), not a date.
- ⚠️ `resp` carries **personal data** (`RESP` name, `EMAIL_RESP`) but **no CPF column** → both
  members get `tuple_cnpj_cols=("CNPJ",)` (the intermediary's), fixtures header-only (LGPD).
- ⚠️ `CEP`/`TEL`/`FAX`/`DDD_TEL`/`DDD_FAX`/`CD_CVM` declared `numeric`/`char` in META → kept `str`
  (identifiers; `DDD_TEL` already arrives `'051'`, leading zero intact only as text).
- META URL confirmed `INTERMED/CAD/META/meta_cad_intermed.zip` (2 members, alphabetical order).
- `find_member` verified exact-match, so `cad_intermed.csv` cannot collide with the longer
  `cad_intermed_resp.csv` — covered by a test.
- ⚠️ **META `section` labels are asymmetric: `cad_intermed` + `resp`** (not a tidy pair). Surfaced
  on live-verify. `meta_cad_intermed.txt` is the bare `_MEMBER_STEM` with no `<stem>_` suffix to
  strip, so the base's `_section_of` falls back to the whole stem; the sibling reduces to `resp`.
  That fallback is the base's **documented** behaviour and both labels stay distinct — so it is
  honoured and pinned by a test, **not** "fixed" by special-casing the shared base.

## Done

- [x] Grounded against the real artifact + META (URL probed, types read, values sampled)
- [x] Header fixtures pinned verbatim (`tests/fixtures/cad_intermed/*_header.csv`, ISO-8859-1/CRLF)
- [x] Contracts generated from + pinned to headers (`_internal/config/contracts/cad_intermed.py`)
- [x] `_base_intermed_reader.py` + `IntermedReader` + `IntermedRespReader`
- [x] `MetaIntermedReader` (28th) + `META_CAD_INTERMED` in contracts/meta.py
- [x] Registered in `bin/check_contract_drift.py` `_META_MEMBERS`
- [x] Wired all `__init__` layers (nested + flat) + `__all__` (157 public names, 28 Meta readers)
- [x] Tests `tests/unit/test_intermed_ingestion.py` (incl. distinct-columns anti-copy test +
      exact-member-selection test) + `test_meta_readers.py` count 27→28
- [x] Docs: page + mkdocs nav + api.md + ingestion index + meta.md + root CLAUDE.md (catalog + layout)
- [x] #41 survey ledger ticked (INTERMED ✅ #135; also ticked INVNR ✅ #133, whose line was left open)

- [x] Gates: ruff ✅ · mypy (281 files) ✅ · check_typing ✅ · check_provenance ✅ · unit suite
      **1541 green** ✅ · mkdocs --strict ✅ · codespell ✅
- [x] Live-verified against the real bytes: intermed 2.352 rows, resp 5.545; `DDD_TEL` keeps its
      leading zero (`'051'`, `str`); CNPJ masked and identical across both members; no CPF column
      in `resp`; META 2 sections; provenance stamped

## Remaining

- [ ] All pre-commit hooks (run at commit time)
- [ ] Commit → PR `Closes #135` → wait approval + merge → release PATCH
- [ ] AFTER merge: update sweep checkpoint memory (Wave 3 → 5/8), NEXT = ADM_CART (5 membros)
