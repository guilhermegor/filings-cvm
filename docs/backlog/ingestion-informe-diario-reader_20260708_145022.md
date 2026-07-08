# Work ledger — ingestion: Informe Diário FIF reader (issue #5)

Branch: `feat/ingestion-informe-diario-reader`. Excluded from the docs site (`backlog/`).

## Done

- **First ingestion reader** — `ingestion/informe_diario.py` (`InformeDiarioReader`): downloads
  the monthly CVM open-data dump (`inf_diario_fi_AAAAMM`), extracts the CSV, validates the
  contract, returns a typed `DataFrame`. Built on this repo's own seams (`download_file`,
  `zip_extractor`, `read_table`, `LogEmitter`), not stpstone's framework. Money kept as `str`
  (exact), `NR_COTST` as `Int64`, `DT_COMPTC` as `date`.
- **Contract** — `_internal/config/contracts/informe_diario_fif.py` (`INFORME_DIARIO_FIF`),
  re-exported from `contracts/__init__.py`.
- **Macro-section ports** (user request) — `_internal/ports/` (renamed from `interfaces/` per
  user; hexagonal ports-and-adapters): `SubmissionWriter[TDoc]` (abstract `export`) and
  `IngestionReader` (abstract `read`). Both private ABCs (`ABCTypeCheckerMeta`), not in any public
  `__all__`.
- **Submission generalised** (user request) — `to_xml` → `export` on `InformeDiario` /
  `PerfilMensal`; both now inherit `SubmissionWriter[...]` and drop the explicit
  `metaclass=TypeChecker` (inherited). Existing submission tests updated.
- **Root-cause seam fix** — `tabular_reader.read_table` now reads files as text (`dtype=str`) and
  lets `apply_dtypes` do all coercion, instead of inferring-then-casting (which lost zero-padding
  and decimal precision). Regression test in `tests/unit/test_tabular_reader.py`.
- **Tests** — `tests/unit/test_informe_diario_ingestion.py` (boundary-mocked download; contract +
  typing exercised for real), `tests/unit/test_tabular_reader.py`. 23 unit tests pass; ruff,
  ruff-format, and `bin/check_typing.py` clean.
- **Docs** — `docs/ingestion/informe_diario.md` (new page) + `ingestion/index.md`, `usage.md`,
  `api.md`, `README.md`, `mkdocs.yml` nav, and `CLAUDE.md` (catalog + layout + ports note)
  updated. `to_xml`→`export` across all docs.
- **BlueprintX lessons** captured (global store + this repo's `docs/blueprintx-lessons.md`):
  `tabular-reader-read-as-text-not-infer`, `ports-package-for-section-interfaces`.

## Open / follow-up

- **BlueprintX template backport** (NOT done here — guarded): apply both lessons to
  `~/github/blueprintx/templates/` in their own dotfiles/blueprintx PRs — the `read_table`
  read-as-text fix and the `_internal/ports/` package + `example_port.py`.
- Remaining kanban "Ready" ingestion readers #6–#14, one PR each, after this PR is closed.

## Delete when

Every item above is merged and the follow-ups are queued as their own issues/PRs.
