# Work ledger — #9 Cadastro de Fundos (CAD/FI) ingestion reader

Branch `feat/ingestion-cadastro-fi-reader` · issue **#9** · part of the
[kanban sweep](kanban-ready-backlog-sweep_20260708_220638.md).

## Scope

`CadastroFiReader` reads `cad_fi.csv` — the CVM fund registry — into a typed, contract-validated
DataFrame. 46,809 rows × 41 columns.

Issue #9 points at stpstone's `CvmFIFCADFI`. Per the "class names lie, read the URL" rule its URL
was checked first: `https://dados.cvm.gov.br/dados/FI/CAD/DADOS/cad_fi.csv` — matching the issue.

## Findings from the real artifact

- [x] **Not a ZIP, not month-partitioned.** A bare 18 MB `.csv` at a fixed URL. CVM overwrites it
  in place. → the reader takes **no `date_ref`**, the first in this library not to.
- [x] Header read off the real file: **41 columns**, 46,809 data rows.
- [x] **No unique key, at any combination tried:**

  | Key | Duplicated rows |
  |---|---|
  | `CNPJ_FUNDO` | 10,947 |
  | `(CNPJ_FUNDO, TP_FUNDO)` | 1,027 |
  | `(CNPJ_FUNDO, CD_CVM)` | 843 |
  | `(CNPJ_FUNDO, TP_FUNDO, DT_REG)` | 851 |
  | `CD_CVM` | 18,535 |

  Cause: a fund **keeps its CNPJ** across regulatory-regime migrations and is re-registered under a
  new `TP_FUNDO` with a fresh `CD_CVM`. Confirmed on `00.000.432/0001-00`: a `FIF` registered
  2003-04-30 and an `FI` registered 2005-03-31, both `CANCELADA`. 46,809 rows ↔ 41,106 distinct
  CNPJs.
- [x] **99.5% historical.** `SIT == "CANCELADA"` on 46,569 rows; 46,570 carry a `DT_CANCEL`; only
  22 are `EM FUNCIONAMENTO NORMAL`. `TP_FUNDO` is full of legacy types (`FACFIF`, `FITVM`, `FIF`).
  Sanity-checked against a raw row to rule out a column-misalignment misparse — it is real. The
  live funds live in `registro_fundo_classe.zip` (post-RCVM 175).
- [x] `CPF_CNPJ_GESTOR` holds a **CPF** on the 47 rows where `PF_PJ_GESTOR == "PF"`.
- [x] All nine `DT_*` columns parse cleanly; blanks (20,282 for `DT_INI_ATIV`) become `NaT`.
- [x] `QUOTE_MINIMAL` and `QUOTE_NONE` agree here (both 41 fields on all 46,810 lines) — unlike
  `lamina_fi_*.csv`. `QUOTE_NONE` is kept for consistency with the sibling readers, but it is not
  load-bearing on this file.

## Decisions

- [x] **No `date_ref` in the constructor**, and a test asserts passing one raises `TypeError`
  rather than being silently ignored — a caller who thinks they are selecting a month would
  otherwise get today's registry and never know.
- [x] **Assert no grain, do not de-duplicate.** Choosing the "current" row per CNPJ (latest
  `DT_REG`? `SIT != "CANCELADA"`?) is a domain decision for the consumer. A reader's job is to
  return what CVM published. Documented loudly, because `set_index("CNPJ_FUNDO")` or a merge on
  that column alone silently fans out rows.
- [x] **`CPF_CNPJ_GESTOR` is not declared a CNPJ column.** A CNPJ check would reject a valid
  registry. The counterparty columns (`CNPJ_ADMIN`, `CNPJ_AUDITOR`, …) are likewise excluded:
  validating them would conflate a defect in *this* file with a defect in a counterparty's
  registration.
- [x] Contract declares all 41 columns required; dtype map derived from it, so the names live in
  one place.
- [x] Default `int_timeout_s=60` (vs 30 for the monthly readers) — the file is ~18 MB, unzipped.
- [x] Scope held to `cad_fi.csv`. `cad_fi_hist.zip` and `registro_fundo_classe.zip` filed as
  follow-ups, as #6 did with `cda_fie`.

## Shipped

- [x] `_internal/config/contracts/cad_fi.py` — `CAD_FI` (41 required columns)
- [x] `contracts/__init__.py` re-export
- [x] `ingestion/cadastro_fi.py` — `CadastroFiReader`
- [x] Exported from `ingestion/__init__.py` and the package `__all__`
- [x] `tests/unit/test_cadastro_fi_ingestion.py` — 12 tests
- [x] Docs: `docs/ingestion/cadastro_fi.md`, `ingestion/index.md`, `api.md`, `mkdocs.yml` nav
- [x] Root `CLAUDE.md` catalog: new CAD/FI entry (open-data only, no submission XML standard)

## Verification

- [x] 89 unit tests green under **pandas 3.0.3 and pandas 2.3.3**. Ruff check + format,
  `bin/check_typing.py` clean.
- [x] **End-to-end against the live CVM file:** 46,809 × 41 and 41,106 distinct CNPJs, both
  matching independent raw counts; `DT_REG` → `date`; 20,282 null `DT_INI_ATIV`; no fabricated
  `"nan"`; `path_raw` kept `cad_fi.csv`.

## Open

- [ ] PR opened; awaiting user review/merge.
- [ ] `registro_fundo_classe.zip` is likely the artifact consumers actually want for live funds —
  worth raising with the user as a priority follow-up, not just a backlog line.
