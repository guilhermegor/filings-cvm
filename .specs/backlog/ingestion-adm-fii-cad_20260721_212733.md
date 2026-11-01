# Work ledger — ADM_FII/CAD ingestion reader (#141)

Branch `feat/141-adm-fii-cad-reader`. Adds `CadastroAdmFiiReader` over `cad_adm_fii.csv`
(`ADM_FII/CAD`), inaugurating the `adm_fii/` portal root. **Eighth and final slice of Wave 3 of
#41 — closes Wave 3 (8/8 service-provider registries).**

The only Wave 3 member that is a **flat CSV** (not a multi-member ZIP): one reader, molded on
`CadastroFiReader` / `CadastroEmissorCepacReader`, not the `_base_*_reader.py` sibling pattern.

## Grounding (real bytes)

- `cad_adm_fii.csv`: ISO-8859-1, CRLF, `;`-delimited, **18 columns**, 135 data rows, fixed URL
  (snapshot — CVM overwrites in place, so **no `date_ref`**).
- Columns: `CNPJ;DENOM_SOCIAL;DENOM_COMERC;DT_REG;DT_CANCEL;MOTIVO_CANCEL;SIT;DT_INI_SIT;TP_ENDER;`
  `LOGRADOURO;COMPL;BAIRRO;MUN;UF;CEP;DDD;TEL;EMAIL`.
- 3 date cols: `DT_REG`, `DT_CANCEL`, `DT_INI_SIT`. ⚠️ `MOTIVO_CANCEL` is **free text**, not a date.
- Keyed by `CNPJ` (masked, institution); **no CPF column** — no personal data.
- `CEP`/`DDD`/`TEL` are `numeric` in META but kept `str` (identifiers). Uses `DDD` (not `DDD_TEL`).
- META `meta_cad_adm_fii.txt` exists (flat `.txt`, 18 fields, alphabetical order — the known
  "META order ≠ file order"). 31st Meta reader.

## Done

- [x] Contract `_internal/config/contracts/cad_adm_fii.py` (`CAD_ADM_FII`, 18 cols, verified vs real
      bytes) + re-export in `contracts/__init__.py`.
- [x] `META_CAD_ADM_FII` in `contracts/meta.py` + re-export.
- [x] Reader `ingestion/adm_fii/cad/cadastro/cadastro.py` (`CadastroAdmFiiReader`).
- [x] `MetaCadAdmFiiReader` (`ingestion/adm_fii/cad/cadastro/meta.py`) — 31st Meta reader.
- [x] 3 nested `__init__.py` (cadastro / cad / adm_fii) + flat re-export in `ingestion/__init__.py`
      and top `filings_cvm/__init__.py` (imports + `__all__`).
- [x] Drift registry `bin/check_contract_drift.py`: `CAD_ADM_FII` import,
      `_UNEXPOSED_CONTRACTS["CadastroAdmFiiReader"]`, `_META_MEMBERS["MetaCadAdmFiiReader"]`.
- [x] Tests: added `CadastroAdmFiiReader` `FlatCase` to `tests/unit/test_securit_cepac_flat_ingestion.py`
      (reuses the flat-CSV harness — 6 parametrized tests); bumped `test_meta_readers.py` 30 → 31.
- [x] Docs: `docs/ingestion/adm_fii.md` + mkdocs nav + `docs/api.md` (new section + Meta list 30→31)
      + `docs/ingestion/index.md` + root `CLAUDE.md` catalog + Layout tree + META count 30→31.
- [x] Gates: ruff format+check, mypy (308 files), check_typing, check_provenance, **full unit suite
      1675 passed**.
- [x] Live-verified vs real CVM bytes: 135 rows, 18 source + 6 provenance cols, `DT_REG`→date,
      `MOTIVO_CANCEL`→str, META 18 fields keyed `meta_cad_adm_fii`.

## Remaining

- [ ] Full pre-commit run on changed files + `mkdocs --strict`.
- [ ] Commit → PR `Closes #141` → wait for approval + merge.
- [ ] After merge: release PATCH; update sweep checkpoint memory (Wave 3 → **8/8 DONE**).
