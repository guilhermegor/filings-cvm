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
- The `Link_Download` → fnet document is the natural first thing a downstream (bedrock-fm) gold
  layer would fetch; keeping the reader from following it is what preserves the thin-reader
  boundary (fetching + parsing PDFs belongs downstream, per the bedrock-fm design notes).
