# INVNR/CAD reader — `cad_invnr_repres.zip` (pf + pj) — issue #133

Branch `feat/133-invnr-cad-reader`. Wave 3 slice **4/8** of #41. Inaugurates the portal root
`invnr/`. Mould: AUDITOR (#127) → AGENTE_FIDUC (#129) → AGENTE_AUTON (#131).

## Grounding (verified against the real 2026-07-20 artifact)

- Snapshot ZIP, fixed URL, **no `date_ref`**. `pf` = 6 cols / 1.370 rows, `pj` = 23 cols / 887 rows.
- `pf` has **no CPF** (key = `NOME`); `pj.CNPJ` masked (`76.621.457/0001-85`, 887/887 filled).
- `pj` adds `CONTROLE_ACIONARIO`, `DDD_FAX`/`FAX`, `VL_PATRIM_LIQ`, `DT_PATRIM_LIQ` → **4 date cols**
  vs pf's 3. Uses `DDD_TEL` (not AGENTE_AUTON's `DDD`).
- META URL confirmed `INVNR/CAD/META/meta_cad_invnr_repres.zip` (2 members, alphabetical order).
  META declares `CEP`/`TEL`/`FAX` `numeric` → kept `str` (identifiers; `CEP` already arrives with
  leading zero dropped). `MOTIVO_CANCEL` = `varchar` (text, not date); `DT_PATRIM_LIQ` = `date`.

## Done

- [x] Grounded against the real artifact + META (URL probed, types read)
- [x] Header fixtures pinned verbatim (`tests/fixtures/cad_invnr_repres/*_header.csv`, ISO-8859-1/CRLF)
- [x] Contracts generated from + pinned to headers (`_internal/config/contracts/cad_invnr_repres.py`)
- [x] `_base_invnr_repres_reader.py` + `InvnrRepresPfReader` + `InvnrRepresPjReader`
- [x] `MetaInvnrRepresReader` (27th) + `META_CAD_INVNR_REPRES` in contracts/meta.py
- [x] Registered in `bin/check_contract_drift.py` `_META_MEMBERS`
- [x] Wired all `__init__` layers (nested + flat) + `__all__` (154 public names, 27 Meta readers)
- [x] Tests `tests/unit/test_invnr_repres_ingestion.py` + `test_meta_readers.py` count 26→27
- [x] Docs: page + mkdocs nav + api.md + ingestion index + meta.md + root CLAUDE.md (catalog + layout)
- [x] #41 survey ledger ticked (INVNR ✅ #133)

## Remaining

- [ ] Gates: ruff + mypy + check_typing + check_provenance + full unit suite + mkdocs --strict +
      all pre-commit hooks
- [ ] Live-verify readers against the real bytes (download boundary real)
- [ ] Commit → PR `Closes #133` → wait approval + merge → release PATCH
- [ ] AFTER merge: update sweep checkpoint memory (Wave 3 → 4/8), NEXT = INTERMED
