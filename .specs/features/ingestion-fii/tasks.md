## ingestion-fii-dfin_20260711_124631

# Work ledger — FII DFIN reader (issue #57)

Branch: `feat/57-fii-dfin-reader`. **Second of 4 FII datasets** in Wave 1 of the #41 portal sweep
(the `fii/` root was launched by #56).

FII queue (one artifact = one PR): #56 INF_MENSAL ✅ → **#57 DFIN (1)** → #58 INF_TRIMESTRAL (16)
→ #59 INF_ANUAL (12).

## Done

- [x] Grounded the contract in the **real artifact** (META-first): fetched `meta_dfin_fii.txt` +
      `dfin_fii_2025.csv` (8 cols, 1,178 rows, ISO dates).
- [x] 1 `FileContract` in `_internal/config/contracts/dfin_fii.py`.
- [x] `ingestion/fii/doc/dfin.py` (`DfinFiiReader`) — a **standalone** reader (single member, so no
      base+subclass). Two shape notes it handles:
      - **Plain CSV, not a ZIP** → downloads and reads the file directly (no extract/find_member),
        like the CAD/FI snapshot.
      - **Year-partitioned** (`dfin_fii_AAAA.csv`) → `date_ref` selects the year, like the FII
        monthly readers.
- [x] **`Link_Download` is returned as text and NOT followed** — the reader indexes documents, it
      does not fetch the linked statements (stays thin). Locked by a test asserting the only URL
      requested is the DFIN CSV itself (`not any("fnet" in url)`).
- [x] `_RETRY_POLICY` per the #53 standard; `Data_Referencia`/`Data_Entrega` → `date`; everything
      else (incl. `Versao`) exact text.
- [x] Wiring: `fii/doc/__init__`, `fii/__init__`, `ingestion/__init__`, public API, contracts
      aggregator.
- [x] Tests `tests/unit/test_dfin_fii_ingestion.py` (9) — columns, both date coercions,
      link-not-followed, year partition, `Versao`-as-text, contract error, `path_raw`, retry
      standard, wrong-arg-type.
- [x] Docs: new mkdocs page (leads with "this is an index, not a statement"), nav, ingestion index,
      `api.md` section, `CLAUDE.md` catalog (DFIN ✅ + layout note).
- [x] Gates: ruff, format, `check_typing`, `check_provenance`, mypy (107 files),
      `pytest tests/unit` (**528 passed**) — green under pandas 3.0.3; pandas 2.x via CI matrix.

## Open / next

- [ ] `mkdocs build --strict` + final full-gate re-run before commit.
- [ ] User review of the PR (approval gate).
- [ ] After merge: release (minor bump → 0.16.0) Test PyPI → verify by install → PyPI → verify.
- [ ] Then **#58 INF_TRIMESTRAL** (16 members), **#59 INF_ANUAL** (12 members).

## Notes

- DFIN is the only FII dataset that is a bare CSV; the other three are multi-member ZIPs.
- The `Link_Download` → fnet document is the natural first thing a downstream (marketdata-fm) gold
  layer would fetch; keeping the reader from following it is what preserves the thin-reader
  boundary (fetching + parsing PDFs belongs downstream, per the marketdata-fm design notes).

## ingestion-fii-inf-anual_20260711_153233

# Work ledger — FII INF_ANUAL readers (issue #59)

Branch: `feat/59-fii-inf-anual-readers`. **Last of the 4 FII datasets** — with this the **`fii/`
portal root is COMPLETE (4/4)**.

FII queue: #56 INF_MENSAL ✅ (0.15.0) → #57 DFIN ✅ (0.16.0) → #58 INF_TRIMESTRAL ✅ (0.17.0) →
**#59 INF_ANUAL (12)**.

## Done

- [x] Grounded all 12 contracts in the **real artifact** (META-first): fetched
      `meta_inf_anual_fii.zip` + `inf_anual_fii_2025.zip`. All-ASCII column names, no CVM typos in
      this dump. Row grains vary (3 → 46,627) — most members are long.
- [x] 12 `FileContract`s in `_internal/config/contracts/inf_anual_fii.py` (single file, same
      deliberate deviation as the other multi-member dumps), generated from the manifest.
- [x] Private base `_base_inf_anual_fii_reader.py` (yearly `{yyyy}` URL, per-subclass `_DATE_COLS`)
      + 12 thin readers; `_RETRY_POLICY` per the #53 standard.
- [x] **Year partition is NATURAL here** (it *is* the annual report) — unlike the FII monthly and
      quarterly dumps, where the yearly archive is the trap. Documented as such.
- [x] ⚠️ **Two dataset-specific guarantees, both tested:**
      - `complemento` carries a **`Link_Download_Anexo`** (external URL to the filed annex) — the
        reader returns it as **text and does not follow it**, same rule as `DfinFiiReader`. Test
        asserts no `fnet` URL is ever requested.
      - `diretor_responsavel` and `representante_cotista` carry a **`CPF`** — a natural person's id.
        Read as exact text, **never** CNPJ-validated. Test asserts the value survives and that
        `CPF` is not in the contract's `tuple_cnpj_cols`. **Personal data** — flag for the
        downstream (marketdata-fm) layer.
- [x] `CNPJ_Fundo_Classe` is the only CNPJ-validated column; `CNPJ_Prestador`,
      `CNPJ_Administrador` and the `complemento` counterparty CNPJs are read as text.
- [x] Wiring at every level (inf_anual → doc → fii → ingestion → public API) + contracts aggregator.
- [x] Tests `tests/unit/test_inf_anual_fii_ingestion.py` (55) — parametrized family + the two
      guarantees above + year partition, absent-year ValueError, contract error, path_raw,
      money-as-str, retry standard.
- [x] Docs: new mkdocs page, nav, ingestion index, `api.md` section, `CLAUDE.md` catalog (Anual ✅,
      FII root marked **COMPLETO 4/4**, layout tree updated).
- [x] Gates: ruff, format, `check_typing`, `check_provenance`, mypy (141 files),
      `pytest tests/unit` (**764 passed**) — green under pandas 3.0.3; pandas 2.x via CI matrix.
- [x] **32 FII readers** total exported (3 + 1 + 16 + 12).

## Open / next

- [ ] `mkdocs build --strict` + final full-gate re-run before commit.
- [ ] User review of the PR (approval gate).
- [ ] After merge: release (minor bump → 0.18.0) Test PyPI → verify by install → PyPI → verify.
- [ ] **FII done.** Wave 1 of #41 continues: **FIP → FIAGRO → FIE**, then Waves 2–5.

## Notes

- The `CPF` columns are the first personal data the library ingests. Worth a standing note for
  marketdata-fm: bronze keeps it verbatim (it is what CVM published), but the gold layer / any API
  surface must treat it as PII (LGPD).

## ingestion-fii-inf-mensal_20260711_092650

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
  do not de-duplicate; that is the consumer's `Versao` filter (marketdata-fm gold layer).
- DFIN (#57) is a plain **CSV**, not a ZIP, and is an *index* of financial statements carrying a
  `Link_Download` column — the reader will return the index and **not** follow the link.

## ingestion-fii-inf-trimestral_20260711_140215

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
