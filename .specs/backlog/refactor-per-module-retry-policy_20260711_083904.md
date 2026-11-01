# Work ledger — per-module `_RETRY_POLICY` as the project standard (issue #53)

Branch: `refactor/53-per-module-retry-policy`. Generalizes the pattern proven by the FIDC
readers (#52 / PR #54) to **every** ingestion reader.

## Done

- [x] Retrofitted the **9 constructor-bearing** reader modules with the pattern (module
      `_DEFAULT_RETRY_POLICY` literal → `_RETRY_POLICY` ClassVar → ctor fallback):
      `informe_diario`, `cda`, `lamina`, `lamina_carteira`, `cadastro_fi`,
      `registro_{fundo,classe,subclasse}`, and `_base_cad_fi_hist_reader` (which covers its 19
      change-log subclasses). FIDC's 17 already had it.
- [x] **Per-family literal** chosen over one shared library-wide constant (user decision): each
      family declares its own `_DEFAULT_RETRY_POLICY`, mirroring FIDC exactly. Keeps the patience
      co-located with the dataset; no change to FIDC or to `http_downloader`'s own fallback.
- [x] Ctor docstrings updated — the old "by default the seam's throttle-tolerant policy" wording
      was inaccurate once the reader owns the default.
- [x] **Structural test** `tests/unit/test_reader_retry_policy.py` — cross-cutting and
      **introspective**: it discovers readers from `ingestion.__all__` rather than listing them, so
      a *future* reader that forgets `_RETRY_POLICY` fails automatically. Asserts, per reader:
      declares a `RetryPolicy`, exposes `retry_policy`, defaults to the module policy, and lets a
      per-instance policy override. 177 tests over all 44 readers.
- [x] Docs: fixed the **`api.md` signature drift** (7 reader ctors omitted `retry_policy`) and added
      a `retry_policy` row to each param table; documented the standard in `ingestion/index.md`
      (new "Política de retry" section beside provenance / `path_raw`).
- [x] Gates: ruff, ruff format, `check_typing`, `check_provenance`, mypy (97 files),
      `pytest tests/unit` (**482 passed**), `mkdocs build --strict` — all green (pandas 3.0.3;
      pandas 2.x via CI matrix).
- [x] Ticked the #52 ledger's remaining boxes (PR #54 merged, 0.13.0 released) — carried here.

## Open / next

- [ ] User review of the PR (approval gate — do not start the next task until merged).
- [ ] After merge: release (minor bump → 0.14.0) Test PyPI → verify by install → PyPI → verify.
- [ ] Then resume Wave 1 of the #41 sweep: FII → FIP → FIAGRO → FIE, then Waves 2–5.

## Notes

- The introspective test is the thing that makes this a *standard* rather than a convention nine
  files happen to follow — it is the structural guard, analogous to `bin/check_provenance.py`.
- Related but separate: the pending dotfiles-dev lesson `autowrap-commit-body-pretooluse-hook.md`
  (auto-wrap commit bodies ≤72 before gitlint) — toolchain, not this repo.
