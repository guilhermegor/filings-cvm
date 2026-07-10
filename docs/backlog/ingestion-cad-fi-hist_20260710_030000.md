# Work ledger — CAD/FI histórico readers (19 change-logs)

Branch `feat/ingestion-cad-fi-hist-reader` · **user-prioritised follow-up** · part of the
[kanban sweep](kanban-ready-backlog-sweep_20260708_220638.md).

## Scope

`cad_fi_hist.zip` ships **19 members**, one per mutable attribute of the legacy CAD/FI registry —
each a per-attribute **change-log** (`CNPJ_FUNDO`, `DT_REG`, value column(s), `DT_INI_*`/`DT_FIM_*`).
Where `CadastroFiReader` gives the current snapshot, these give the history.

## Design decisions (user-approved)

- **19 separate reader classes** (user chose "19 separate readers" over a parameterized reader or a
  curated subset), one public class per file per repo convention → 19 `CadastroFiHist*Reader`.
- **Private shared base `_base_cad_fi_hist_reader.py`** holds the download → unzip → find_member →
  read_table logic once (DRY); each public reader is a ~10-line subclass setting `_MEMBER`,
  `_CONTRACT`, `_DATE_COLS`, `_LABEL`. This is the first reader in the repo to use a shared base —
  justified because 19 near-identical readers would otherwise duplicate the same body 19×.
- **Contracts consolidated into ONE module** `_internal/config/contracts/cad_fi_hist.py` (19
  `FileContract` constants). **Deliberate deviation** from the "one contract per file" convention:
  the 19 are members of a *single* input artifact (one ZIP, one dataset page) and a uniform family;
  19 one-constant modules would be sprawl. Noted in the module docstring. **Flag for review** — the
  registro readers used one file per member (3 files); this diverges because 19 ≫ 3 and they are
  attributes of one entity, not distinct entities.
- Snapshot (no `AAAAMM`) → **no `date_ref`**; a change-log has many rows per fund → **no grain**.

## Findings from the real artifact

- [x] 19 members, all fixed-width under `QUOTE_NONE` (safe, not load-bearing here).
- [x] Uniform prefix `CNPJ_FUNDO; DT_REG; …`; every `DT_*` column parses; `CNPJ_FUNDO` never null.
- [x] Row counts range from 42,984 (`publico_alvo`) to 489,195 (`exerc_social`).
- [x] `taxa_adm` / `taxa_perfm` have an opening date but **no** `DT_FIM_*`; `exerc_social` has no
  non-date value column beyond the keys. Contracts capture these per-member shapes exactly.
- [x] `gestor.CPF_CNPJ_GESTOR` holds a CPF for PF managers → excluded from CNPJ validation.

## Shipped

- [x] `_internal/config/contracts/cad_fi_hist.py` — 19 `FileContract`s; re-exported from `__init__`
- [x] `ingestion/_base_cad_fi_hist_reader.py` — private base
- [x] 19 `ingestion/cad_fi_hist_*.py` readers; exported from `ingestion/__init__` + package `__all__`
- [x] `tests/unit/test_cad_fi_hist_ingestion.py` — one parameterized module, 81 tests over all 19
- [x] Docs: combined `docs/ingestion/cad_fi_hist.md`, `ingestion/index.md`, `api.md`, `mkdocs.yml`
- [x] Root `CLAUDE.md` catalog: `cad_fi_hist.zip` marked ✅

## Verification

- [x] 204 unit tests green under **pandas 3.0.3 and 2.3.3**. Ruff check + format,
  `bin/check_typing.py` clean.
- [x] **End-to-end against the live archive:** `sit` 143,392×5, `gestor` 98,567×7 (CPF present),
  `taxa_adm` 87,757×5 (str), `exerc_social` 489,195×4; dates coerced; a single `path_raw` kept the
  ZIP + all 19 CSVs.

## Open

- [ ] PR opened; awaiting user review/merge, then the single release with any co-merged work.
- [ ] **Next to-do is #42** (provenance `url` + `updated_at` on every reader) — will retrofit these
  19 too.
