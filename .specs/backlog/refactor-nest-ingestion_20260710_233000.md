# Work ledger — nest the ingestion/ folder by CVM portal path (#44)

Branch `refactor/nest-ingestion-by-portal-path` · issue **#44**.

## Why

`ingestion/` had grown to 27 reader modules + 1 base flat (19 were the `cad_fi_hist_*` family).
User chose **option A (by CVM portal path) + per-dataset sub-folders** for multi-file datasets.

## Target tree (built)

The portal path is `dados.cvm.gov.br/dados/<ROOT>/…` where `FI/` is **one root among
siblings** (`FIDC/`, `FII/`, `AUDITOR/`, `INVNR/`, … — all pending in the catalog). So the
nesting carries the `fi/` root level; `doc/`/`cad/` are `FI/DOC` and `FI/CAD` beneath it, and
future roots become siblings of `fi/`, not name-collisions with it.

```
ingestion/
  __init__.py                 # FLAT public API — re-exports every reader (unchanged import path)
  fi/                         # FI/ — Fundos de Investimento (one portal root)
    __init__.py               #   aggregates all 28 FI readers
    doc/                      #   FI/DOC/*
      informe_diario.py
      cda.py
      lamina/                 #   FI/DOC/LAMINA (one ZIP, two members)
        lamina.py
        lamina_carteira.py
    cad/                      #   FI/CAD
      cadastro_fi.py          #   cad_fi.csv
      registro/               #   registro_fundo_classe.zip (3 members)
        registro_fundo.py  registro_classe.py  registro_subclasse.py
      cad_fi_hist/            #   cad_fi_hist.zip (19 members)
        _base_cad_fi_hist_reader.py
        cad_fi_hist_*.py  (19)
```

## Key property — public API unchanged

`from filings_cvm.ingestion import XReader` still works for all 28 readers. Each sub-package's
`__init__` re-exports its readers; `ingestion/__init__` imports from the sub-packages. Verified:
`filings_cvm.__all__` still 32 symbols. A **pure internal move** (like the PR #39 ports/schemas
reorg) — zero public API change.

## Execution

- [x] `git mv` 28 files into the tree (clean renames).
- [x] 5 new sub-package `__init__.py` (doc/, doc/lamina/, cad/, cad/registro/, cad/cad_fi_hist/),
  each re-exporting its readers.
- [x] Rewrote the 19 readers' base import to `…cad.cad_fi_hist._base_cad_fi_hist_reader` (+ the
  docstring `:mod:` refs, shortened to `` ``_base_cad_fi_hist_reader`` `` to stay under 99 cols).
- [x] Rewrote `ingestion/__init__` to import from the sub-packages.
- [x] Rewrote test internal module paths (monkeypatch targets + private imports) with anchored
  seds (name + delimiter, so substrings can't collide), verified by the suite.
- [x] Root `CLAUDE.md` catalog source paths + Layout tree updated to the nested structure.
- [x] **Review feedback (portal has many roots besides FI):** added the `fi/` root level above
  `doc/`/`cad/` so `doc/`/`cad/` are `FI/DOC`/`FI/CAD` and future roots (`FIDC/`, `AUDITOR/`, …)
  are siblings of `fi/`. New `fi/__init__.py` aggregates all 28; `ingestion/__init__` re-exports
  from `.fi`. Second commit on the same branch.

## Verification

- [x] 213 unit tests green under **pandas 3.0.3 and 2.3.3**.
- [x] ruff check + format, `bin/check_typing.py`, `bin/check_provenance.py`, `mypy` (70 files),
  `check_docstrings.py`, `mkdocs build --strict` — all clean.

## Open / follow-up

- [ ] PR opened; awaiting user review/merge + release.
- [ ] **Mirror the test-folder hierarchy** (`tests/unit/doc/…`, `tests/unit/cad/…`) to match the
  package structure, per the CLAUDE.md convention. Deferred: tests are already one-per-reader and
  clearly named; moving them is churn without functional value. Do it as a small follow-up if the
  mirror convention is to be enforced strictly.
