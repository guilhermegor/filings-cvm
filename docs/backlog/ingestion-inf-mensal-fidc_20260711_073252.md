# Work ledger — FIDC INF_MENSAL ingestion readers (issue #52)

Branch: `feat/52-fidc-inf-mensal-readers` · Wave 1 of the #41 portal sweep.
Launches the **`fidc/` portal root** (sibling of `fi/`).

## Done

- [x] Grounded the contract in the **real artifact** (META-first): downloaded
      `meta_inf_mensal_fidc_txt.zip` + `inf_mensal_fidc_202506.zip`, extracted the 17 members,
      confirmed the shared 4-col key prefix and `DT_COMPTC` as the only date column.
- [x] 17 `FileContract`s in `_internal/config/contracts/inf_mensal_fidc.py` (single file, same
      deliberate deviation as `cad_fi_hist.py`), column lists verified against `202506`.
- [x] Private base `_base_inf_mensal_fidc_reader.py` — monthly `{ym}` URL + `date_ref` (like
      `informe_diario`) fused with multi-member `_MEMBER_STEM`/`_CONTRACT` subclassing (like
      `cad_fi_hist`). `DT_COMPTC` shared on the base; all other columns kept `str`.
- [x] 17 thin readers `InfMensalFidcTab*Reader` under `ingestion/fidc/doc/inf_mensal/`.
- [x] **Per-table retry policy** (user request): shared `_DEFAULT_RETRY_POLICY` in the base module
      (5 attempts, capped exponential ~2/4/8/10 s); each reader declares
      `_RETRY_POLICY: ClassVar[RetryPolicy | None] = _DEFAULT_RETRY_POLICY`; ctor falls back to it,
      per-instance `retry_policy=` overrides. Tunable per table.
- [x] Wiring at every level: `fidc/__init__`, `fidc/doc/__init__`, `inf_mensal/__init__`,
      `ingestion/__init__`, top-level `filings_cvm/__init__`, contracts `__init__`.
- [x] Tests `tests/unit/test_inf_mensal_fidc_ingestion.py` — parametrized family (member selection,
      `DT_COMPTC` coercion, `date_ref` presence, month-in-member-name, contract error, member
      absent, `path_raw` persistence, money-as-str, wrong-arg-type, per-module retry default,
      per-instance override). Mock `download_file` only.
- [x] Docs (mkdocs): new page `docs/ingestion/inf_mensal_fidc.md` with a dedicated **retry policy /
      per-table patience** section; registered in `mkdocs.yml` nav; bullet in `ingestion/index.md`;
      compact section + "Veja também" link in `api.md`. `mkdocs build --strict` green.
- [x] `CLAUDE.md` catalog updated (Informe Mensal FIDC ingestion + new `fidc/` root).
- [x] Gates: ruff, ruff format, `bin/check_typing.py`, `bin/check_provenance.py`, mypy (97 files),
      `pytest tests/unit` (305 passed) — all green under pandas 3.0.3. pandas 2.x covered by CI matrix.

## Open / next

- [ ] User review of the open PR (approval gate — do not start the next task until merged).
- [ ] After merge: release (minor bump) Test PyPI → verify by install → PyPI → verify.
- [ ] Then Wave 1 continues: FII → FIP → FIAGRO → FIE (see portal-survey-41 ledger), then Waves 2–5.

## Notes

- `api.md` reader ctors for the existing FI readers still omit `retry_policy` (pre-existing doc
  drift from #49/#50); the new FIDC section documents it correctly. Not fixed here to keep the diff
  scoped — candidate follow-up.
- The `202501+`-only DADOS window reflects the post-RCVM-175 structure; older FIDC monthly layouts
  (`PadraoXMLMensalFIDC489/576`) are the submission direction, out of scope for this reader.
