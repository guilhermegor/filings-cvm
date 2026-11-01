# Work ledger — CIA_ESTRANG/CAD ingestion reader (#143)

Branch `feat/143-cia-estrang-cad-reader`. Adds `CadastroCiaEstrangReader` over `cad_cia_estrang.csv`
(`CIA_ESTRANG/CAD`), inaugurating the `cia_estrang/` portal root. **Opens Wave 4 of #41**
(companhias/ofertas).

A flat-CSV snapshot molded on `CadastroAdmFiiReader` / `CadastroEmissorCepacReader` — but wide
enough (49 cols) that the contract is **pinned to a verbatim header fixture** (the anti-tautology
oracle), unlike the narrower flat cadastros.

## Grounding (real bytes)

- `cad_cia_estrang.csv`: ISO-8859-1, CRLF, `;`-delimited, **49 columns**, 26 data rows (tiny —
  foreign issuers), fixed URL (snapshot — **no `date_ref`**).
- 7 date cols: `DT_REG`, `DT_CONST`, `DT_CANCEL`, `DT_INI_SIT`, `DT_INI_CATEG`,
  `DT_INI_SIT_EMISSOR`, `DT_INI_RESP`. ⚠️ `MOTIVO_CANCEL` is **free text**, not a date.
- **Two CNPJ cols**: `CNPJ` (issuer, masked, 25/26 valid) + `CNPJ_AUDITOR` (auditor, 25/25 valid) →
  `tuple_cnpj_cols = ("CNPJ", "CNPJ_AUDITOR")`. `RESP` carries a person's name but **no CPF col**.
- `CD_CVM`/`CEP`/`TEL`/`FAX`/`DDD_*`/`CD_PAIS_*` are `numeric`/`char` in META but kept `str`.
- META `meta_cad_cia_estrang.txt` exists (flat `.txt`, 49 fields). 32nd Meta reader.

## Wave 4 portal grounding (for the next slices)

- CIA_ESTRANG/CAD → `cad_cia_estrang.csv` (flat CSV) ✅ this PR
- CIA_INCENT/CAD → `cad_cia_incent.csv` (flat CSV)
- COORD_OFERTA/CAD → `cad_coord_oferta.zip` (multi-member ZIP)
- CROWDFUNDING/CAD → `cad_crowdfunding.zip` (multi-member ZIP)
- OFERTA → DISTRIB; CIA_ABERTA → big multi-dataset (7 DOC + CAD + EVENTOS), do last.

## Done

- [x] Header fixture `tests/fixtures/cad_cia_estrang/cad_cia_estrang_header.csv` (generated from real
      bytes, verbatim CRLF, header-only).
- [x] Contract `cad_cia_estrang.py` (`CAD_CIA_ESTRANG`, 49 cols, generated from + pinned to fixture)
      + re-export in `contracts/__init__.py`.
- [x] `META_CAD_CIA_ESTRANG` in `contracts/meta.py` + re-export.
- [x] Reader `ingestion/cia_estrang/cad/cadastro/cadastro.py` (`CadastroCiaEstrangReader`).
- [x] `MetaCadCiaEstrangReader` — 32nd Meta reader.
- [x] 3 nested `__init__.py` + flat re-export in `ingestion/__init__.py` and top
      `filings_cvm/__init__.py` (imports + `__all__`).
- [x] Drift registry `bin/check_contract_drift.py`: import, `_UNEXPOSED_CONTRACTS`, `_META_MEMBERS`.
- [x] Tests: **generalized the flat-CSV `FlatCase` harness** — dropped the single `str_cnpj_col`
      field; `_value_for` now derives CNPJ cols from `cls_contract.tuple_cnpj_cols` (supports N CNPJ
      columns). Added the CIA_ESTRANG case + an **anti-tautology test** reading the header fixture.
      Bumped `test_meta_readers.py` 31 → 32.
- [x] Docs: `docs/ingestion/cia_estrang.md` + mkdocs nav + `docs/api.md` (new section + Meta 31→32)
      + `docs/ingestion/index.md` + root `CLAUDE.md` catalog + Layout tree + META count 31→32.
- [x] Gates: ruff, mypy (314 files), check_typing, check_provenance, **full unit suite 1690 passed**.
- [x] Live-verified vs real CVM bytes: 26 rows, 49 source + 6 provenance cols, `DT_REG`→date,
      `CNPJ_AUDITOR` 25 valid, META 49 fields keyed `meta_cad_cia_estrang`.

## Remaining

- [ ] Full pre-commit run + `mkdocs --strict` + codespell.
- [ ] Commit → PR `Closes #143` → wait for approval + merge.
- [ ] After merge: release PATCH; continue Wave 4 (CIA_INCENT next — also flat CSV).
