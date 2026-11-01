# Work ledger — #317 CNPJ check on empty partitions

Branch `fix/317-cnpj-empty-partition`. Closes **#317**. Release: `fix` touching `src/` → PATCH.

## Done

- [x] Reproduced on `origin/main` (`8171df8`): a header-only `DFP_CIA_ABERTA_DFC_MD_CON` frame
  returned `["Column 'CNPJ_CIA' ... holds no valid CNPJ (unexpected data type)"]`.
- [x] Regression tests first (`tests/unit/test_tabular_reader.py`): 7 of 8 red before the fix
  (header-only DFP/ITR `DFC_MD_con`/`_ind`; all-NaN/blank/whitespace column). The guard
  "non-empty values with no valid CNPJ still fail" was green before and after.
- [x] `find_contract_problems` drops NaN and blank cells before the CNPJ check; nothing present
  → pass. No existing test expectation changed (IPE "only placeholders raises" still holds).
- [x] Live check against CVM: DFP `DFC_MD_con`/`_ind` 2026 read as 0 rows, no error; ITR
  `DFC_MD_con`/`_ind` 2026 have rows (810/948) and read fine.

## ⚠️ Finding — Complemento FI is NOT an empty-column case

`ComplFiReader` at 2019-04 still raises, and correctly under the rule this issue keeps:
`CNPJ_AG_RISCO` is **not empty** there — 199 × `00.000.000/0000-00` + 1 × `11.111.111/1111-11`.
Measured over the whole series (201801–201904): the column holds sentinels
(`00.000.000/0000-00`, `99.999.999/0001-99`, `11.111.111/1111-11`) and has **one** valid CNPJ in
16 months (201808). So `ComplFiReader` raises on 15 of 16 partitions on `main`, and the
`compl_fi.py` docstring ("well-formed otherwise") is wrong.

- [x] Coordinator extended the surface and decided to fix it here: `CNPJ_AG_RISCO` dropped
  from `COMPL_FI.tuple_cnpj_cols`, docstring and `docs/ingestion/compl_fi.md` corrected,
  `test_compl_fi_ingestion.py` expectation changed (data disproves it) plus a placeholder-only
  test (red under the old contract). Live: `ComplFiReader` 2019-04 reads 200 rows.

Completed — kept as a record.
