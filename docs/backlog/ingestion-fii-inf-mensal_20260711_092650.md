# Work ledger — FII INF_MENSAL readers (issue #56)

Branch: `feat/56-fii-inf-mensal-readers`. **First of 4 FII datasets** in Wave 1 of the #41 portal
sweep; launches the **`fii/` portal root** (sibling of `fi/` and `fidc/`).

FII queue (one artifact = one PR): **#56 INF_MENSAL (3)** → #57 DFIN (1) → #58 INF_TRIMESTRAL (16)
→ #59 INF_ANUAL (12).

## Done

- [x] Surveyed the whole `FII/` root first: only `DOC/` exists (no `FII/CAD`), with 4 datasets —
      DFIN, INF_MENSAL, INF_ANUAL, INF_TRIMESTRAL. Filed one issue per dataset (#56–#59).
- [x] Grounded the contracts in the **real artifact** (META-first): fetched
      `meta_inf_mensal_fii.zip` + `inf_mensal_fii_2025.zip`; 3 members, 13,677 rows each, ISO dates.
- [x] **⚠️ Key finding — the dump is partitioned by YEAR, not month**, despite being the *monthly*
      report: `inf_mensal_fii_2025.zip` holds all twelve months (`Data_Referencia` = month's first
      day). `date_ref` therefore selects the **year**. Every reader so far (FI, FIDC) partitions by
      `AAAAMM`, so this is a genuine trap — documented in the base reader, the contracts module, the
      docs page, `api.md`, and locked by a dedicated test.
- [x] 3 `FileContract`s in `_internal/config/contracts/inf_mensal_fii.py`, column names **verbatim**
      including CVM's own defects: accented `…Previdência_Complementar`, and the misspellings
      `Outros_Valores_Mobliarios` / `Provisoes_Contigencias`. A test asserts they are preserved —
      "fixing" them would silently break the read.
- [x] Private base `_base_inf_mensal_fii_reader.py` (yearly `{yyyy}` URL, per-subclass `_DATE_COLS`)
      + 3 thin readers; `_RETRY_POLICY` per the #53 standard.
- [x] Wiring: `fii/__init__`, `fii/doc/__init__`, `inf_mensal/__init__`, `ingestion/__init__`,
      public API, contracts aggregator.
- [x] Tests `tests/unit/test_inf_mensal_fii_ingestion.py` (17) — member selection, date coercion,
      **year-not-month partition** (two months → same yearly URL), absent-year ValueError, contract
      error, `path_raw`, money-as-str, CVM column quirks, retry-policy standard.
- [x] Docs: new mkdocs page (leads with the year-partition warning), nav, ingestion index, `api.md`
      section, `CLAUDE.md` catalog (new FII section + layout tree).
- [x] Gates: ruff, format, `check_typing`, `check_provenance`, mypy (105 files),
      `pytest tests/unit` (**511 passed**) — green under pandas 3.0.3; pandas 2.x via CI matrix.

## Open / next

- [ ] `mkdocs build --strict` + final full-gate re-run before commit.
- [ ] User review of the PR (approval gate).
- [ ] After merge: release (minor bump → 0.15.0) Test PyPI → verify by install → PyPI → verify.
- [ ] Then **#57 DFIN**, **#58 INF_TRIMESTRAL**, **#59 INF_ANUAL** (in that order).

## Notes

- No unique key: the grain is (fundo, mês, versão) — a refiled month repeats. Readers stay thin and
  do not de-duplicate; that is the consumer's `Versao` filter (bedrock gold layer).
- DFIN (#57) is a plain **CSV**, not a ZIP, and is an *index* of financial statements carrying a
  `Link_Download` column — the reader will return the index and **not** follow the link.
