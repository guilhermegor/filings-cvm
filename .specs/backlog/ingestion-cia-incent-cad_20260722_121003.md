# Work ledger — CIA_INCENT/CAD ingestion reader (#145)

Branch `feat/145-cia-incent-cad-reader`. Adds `CadastroCiaIncentReader` over `cad_cia_incent.csv`
(`CIA_INCENT/CAD`), inaugurating the `cia_incent/` portal root. **Second slice of Wave 4 of #41**.

Flat-CSV snapshot molded on `CadastroCiaEstrangReader`, contract pinned to a verbatim header fixture
(47 cols → transcription risk).

## Grounding (real bytes)

- `cad_cia_incent.csv`: ISO-8859-1, CRLF, `;`, **47 columns**, ~3.570 data rows, fixed URL
  (snapshot — **no `date_ref`**).
- ⚠️ **NOT a copy of CIA_ESTRANG**: adds `ST_CIA_INCENT_REG`, drops `PAIS_ORIGEM`/`CD_PAIS_*`, uses
  `MUN`/`UF` (domestic) instead of `CIDADE`/`ESTADO`. Separate contract + fixture.
- 7 date cols: `DT_REG`, `DT_CONST`, `DT_CANCEL`, `DT_INI_SIT`, `DT_INI_CATEG`,
  `DT_INI_SIT_EMISSOR`, `DT_INI_RESP`. ⚠️ `DT_INI_CATEG` is **100% empty** in the current snapshot
  but is a date column by contract (META declares it, CIA_ESTRANG populates it) → coerces to all
  `NaT`. `MOTIVO_CANCEL` is free text, not a date.
- **Two CNPJ cols**: `CNPJ` (3570/3570 valid) + `CNPJ_AUDITOR` (2062 nonempty, 1781 valid) →
  `tuple_cnpj_cols = ("CNPJ", "CNPJ_AUDITOR")`. `RESP` carries a person's name but **no CPF col**.
- `CD_CVM`/`CEP`/`TEL`/`FAX`/`DDD_*` are `numeric`/`char` in META but kept `str`.
- META `meta_cad_cia_incent.txt` exists (flat `.txt`, 47 fields). 33rd Meta reader.

## Done

- [x] Header fixture `tests/fixtures/cad_cia_incent/cad_cia_incent_header.csv` (generated from real
      bytes, verbatim CRLF, header-only).
- [x] Contract `cad_cia_incent.py` (`CAD_CIA_INCENT`, 47 cols, generated from + pinned to fixture) +
      re-export.
- [x] `META_CAD_CIA_INCENT` in `contracts/meta.py` + re-export.
- [x] Reader `ingestion/cia_incent/cad/cadastro/cadastro.py` (`CadastroCiaIncentReader`).
- [x] `MetaCadCiaIncentReader` — 33rd Meta reader.
- [x] 3 nested `__init__.py` + flat re-export in `ingestion/__init__.py` and top
      `filings_cvm/__init__.py` (imports + `__all__`).
- [x] Drift registry `bin/check_contract_drift.py`: import, `_UNEXPOSED_CONTRACTS`, `_META_MEMBERS`.
- [x] Tests: added the CIA_INCENT `FlatCase` (harness already multi-CNPJ-aware) + an anti-tautology
      test reading the header fixture. Bumped `test_meta_readers.py` 32 → 33.
- [x] Docs: `docs/ingestion/cia_incent.md` + mkdocs nav + `docs/api.md` (new section + Meta 32→33) +
      `docs/ingestion/index.md` + root `CLAUDE.md` catalog + Layout tree + META count 32→33.
- [x] Gates: ruff, mypy (320 files), check_typing, check_provenance, **full unit suite 1705 passed**.
- [x] Live-verified vs real CVM bytes: 3570 rows, 47 source + 6 provenance cols, `DT_REG`→date,
      `DT_INI_CATEG` all `NaT`, `CNPJ_AUDITOR` 2062 nonempty, META 47 fields keyed
      `meta_cad_cia_incent`.

## Remaining

- [ ] Full pre-commit run + `mkdocs --strict` + codespell.
- [ ] Commit → PR `Closes #145` → wait for approval + merge.
- [ ] After merge: release PATCH; continue Wave 4 (COORD_OFERTA next — multi-member ZIP).
