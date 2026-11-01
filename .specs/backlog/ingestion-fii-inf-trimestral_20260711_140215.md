# Work ledger — FII INF_TRIMESTRAL readers (issue #58)

Branch: `feat/58-fii-inf-trimestral-readers`. **Third of 4 FII datasets** in Wave 1 of the #41
portal sweep; the largest (16 members).

FII queue (one artifact = one PR): #56 INF_MENSAL ✅ → #57 DFIN ✅ → **#58 INF_TRIMESTRAL (16)** →
#59 INF_ANUAL (12).

## Done

- [x] Grounded all 16 contracts in the **real artifact** (META-first): fetched
      `meta_inf_trimestral_fii.zip` (16 META txts) + `inf_trimestral_fii_2025.zip`. Row grains vary
      hugely (27 → 49,717) — most members are long. All-ASCII column names.
- [x] 16 `FileContract`s in `_internal/config/contracts/inf_trimestral_fii.py` (single file, same
      deliberate deviation as the other multi-member dumps), generated from the manifest so column
      names/order are **exactly** as published.
- [x] **CVM typo preserved verbatim**: `Outras_Receitas_Depesas_Contabil`/`_Financeiro` (missing
      the 's' of *Despesas*) in `resultado_contabil_financeiro`. Documented + a test asserts it
      survives (do not "fix" it — the read would break).
- [x] `CNPJ_Fundo_Classe` is the only CNPJ-validated column; `CNPJ_Emissor` (ativo) /
      `CNPJ_Administrador` (geral) are counterparty IDs read as text (registro pattern).
- [x] Private base `_base_inf_trimestral_fii_reader.py` (yearly `{yyyy}` URL, per-subclass
      `_DATE_COLS`) + 16 thin readers; `_RETRY_POLICY` per the #53 standard.
- [x] ⚠️ **Year-partitioned** (`inf_trimestral_fii_AAAA.zip`), not quarter — `date_ref` selects the
      year (locked by a test: two quarters → one yearly URL).
- [x] Wiring at every level (inf_trimestral → doc → fii → ingestion → public API) + contracts
      aggregator.
- [x] Tests `tests/unit/test_inf_trimestral_fii_ingestion.py` (69) — parametrized family (member
      selection, date coercion, year-not-quarter partition, absent-year ValueError, contract error,
      path_raw, money-as-str, CVM typo verbatim, retry standard).
- [x] Docs: new mkdocs page (16-member table, year-partition + typo callouts), nav, ingestion
      index, `api.md` section, `CLAUDE.md` catalog (Trimestral ✅ + layout note).
- [x] Gates: ruff, format, `check_typing`, `check_provenance`, mypy (126 files),
      `pytest tests/unit` (**661 passed**) — green under pandas 3.0.3; pandas 2.x via CI matrix.

## Open / next

- [ ] `mkdocs build --strict` + final full-gate re-run before commit.
- [ ] User review of the PR (approval gate).
- [ ] After merge: release (minor bump → 0.17.0) Test PyPI → verify by install → PyPI → verify.
- [ ] Then **#59 INF_ANUAL** (12 members) — completes the `fii/` root (4/4 datasets).

## Notes

- Two key-prefix families (like FIDC): `geral` is `Tipo_Fundo_Classe`-first; the other 15 are
  `CNPJ_Fundo_Classe`-first. The base handles both — the CNPJ column is the same everywhere.
- `resultado_contabil_financeiro` is the widest member (~95 cols): the quarter's income statement,
  contábil × financeiro side by side.
