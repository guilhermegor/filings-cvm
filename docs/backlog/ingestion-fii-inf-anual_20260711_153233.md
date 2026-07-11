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
        downstream (bedrock-fm) layer.
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
  bedrock-fm: bronze keeps it verbatim (it is what CVM published), but the gold layer / any API
  surface must treat it as PII (LGPD).
