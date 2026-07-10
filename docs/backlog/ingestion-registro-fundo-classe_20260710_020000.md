# Work ledger — Registro RCVM 175 readers (fundo / classe / subclasse)

Branch `feat/ingestion-registro-fundo-classe-reader` · **user-prioritised follow-up** (not a
numbered backlog issue) · part of the [kanban sweep](kanban-ready-backlog-sweep_20260708_220638.md).

## Scope

Three readers for the three members of `registro_fundo_classe.zip`, the post-**Resolução CVM 175**
fund → class → subclass registry. Raised as a #9 follow-up and pulled forward by the user because
it is where the **live** funds are (`cad_fi.csv` is ~99.5% cancelled).

- `RegistroFundoReader` — `registro_fundo.csv` (21 cols), key `ID_Registro_Fundo`.
- `RegistroClasseReader` — `registro_classe.csv` (30 cols), FK `ID_Registro_Fundo`.
- `RegistroSubclasseReader` — `registro_subclasse.csv` (14 cols), FK `ID_Registro_Classe`.

## Design decisions (user-approved)

- **Three separate readers, one per member** (user chose "all three now" over "fundo first"). One
  public class per file, per repo convention.
- **Not joined into one frame.** The hierarchy is one-to-many, so a join fans the fund's rows out —
  the CDA grain-mixing trap. Consumers join on the surrogate keys themselves; documented with an
  example. FK integrity is 100% on the real file, so the join is safe when the consumer chooses the
  grain.
- **No shared base class.** The four existing readers all repeat the download→extract→read_table
  pattern inline; introducing a base just for these three would break that consistency. Each reader
  is self-contained (reuses `find_member` + `raw_workspace`, already shared seams).
- **Single combined doc page** (`docs/ingestion/registro.md`) rather than three near-duplicate
  pages — the trio shares one archive and one hierarchy, explained once.

## Findings from the real artifact

- [x] Three members, fixed field counts under both quotings (`QUOTE_NONE` safe, not load-bearing).
- [x] Columns are **Title_Case** (`Denominacao_Social`), not the UPPER_SNAKE of `cad_fi.csv`.
- [x] CNPJs are **bare digits** (`00016999000167`), not masked like `cad_fi.csv`.
- [x] **34,176 funds `Em Funcionamento Normal`** (vs 22 in `cad_fi.csv`) — confirms this is the
  live registry.
- [x] `ID_Registro_Fundo` not strictly unique (1,121 dup); `ID_Registro_Classe` 3 dup;
  `ID_Subclasse` 0 dup. FK class→fund and subclass→class both resolve **100%**. No grain asserted.
- [x] `CPF_CNPJ_Gestor` holds a CPF on `Tipo_Pessoa_Gestor == "PF"` rows → excluded from CNPJ check.
  `registro_subclasse` has **no CNPJ column** → empty `tuple_cnpj_cols` (a test pins this path).
- [x] Snapshot (fixed URL, no `AAAAMM`) → readers take **no `date_ref`**; a test asserts passing
  one raises.

## Sat on the reorg (PR #39)

Implementation was written, then **stashed** while PR #39 (move ports/schemas under `config/`)
landed. Resumed on the reorged `main`: the three readers' `_internal.ports` imports were rewritten
to `_internal.config.ports`. Per the user, this work **rides PR #39's release** — a single `0.8.0`,
not a release each.

## Shipped

- [x] 3 contracts `_internal/config/contracts/registro_{fundo,classe,subclasse}.py`
- [x] 3 readers `ingestion/registro_{fundo,classe,subclasse}.py`
- [x] Exports (`ingestion/__init__`, package `__all__`, `contracts/__init__`)
- [x] 3 test files — 34 tests
- [x] Docs: combined `docs/ingestion/registro.md`, `ingestion/index.md`, `api.md`, `mkdocs.yml` nav
- [x] Root `CLAUDE.md` catalog: `registro_fundo_classe.zip` marked ✅

## Verification

- [x] 123 unit tests green under **pandas 3.0.3 and 2.3.3**. Ruff check + format,
  `bin/check_typing.py` clean.
- [x] **End-to-end against the live archive:** fundo 89,139 × 21 (34,176 active), classe
  36,398 × 30 (FK→fundo 100%), subclasse 8,865 × 14 (FK→classe 100%); dates coerced; `path_raw`
  kept the ZIP and all three CSVs from a single download.

## Open

- [ ] PR opened; awaiting user review/merge, then the single `0.8.0` release.
- [ ] `cad_fi_hist.zip` (CAD/FI change log) remains the last unread member of the CAD directory.
