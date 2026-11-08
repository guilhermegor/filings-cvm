## fidc-tab-viii-318_20261031_150000

# FIDC monthly `tab_VIII` reader (#318)

Measured 2026-10-31 against `inf_mensal_fidc_202506.zip` (plus 202501, 202509, 202609 and
`HIST/inf_mensal_fidc_2013.zip`) and `META/meta_inf_mensal_fidc_txt.zip`.

## Findings

- The archive ships **18** members, not 17. `tab_VIII` is in every archive checked, from
  `HIST` 2013 to 202609, so the old count was wrong, not outdated. The META zip also has 18
  sections, `tab_VIII` included.
- Header: `TP_FUNDO_CLASSE;CNPJ_FUNDO_CLASSE;DENOM_SOCIAL;DT_COMPTC;SEQUENCIAL;VALOR` (6 cols,
  CRLF). The member is long: 39,984 rows in 202506, one per fund x `SEQUENCIAL` (1 to 25).
- META types: `VALOR` numeric(20,2), `SEQUENCIAL` bigint, `DT_COMPTC` date. CVM leaves both
  descriptions blank. `VALOR` has at most 2 decimals and no non-numeric value.
- `CNPJ_FUNDO_CLASSE`: 3,357 distinct values, all valid CNPJs. It is the only CNPJ column.

## To-do

- [x] Confirm on `origin/main` that no `tab_VIII` reader exists
- [x] Generate the contract from the real header and pin the verbatim bytes as a fixture
- [x] Add `InfMensalFidcTabVIIIReader` and register it up to the `fidc` root
- [x] Register the contract in `contracts/__init__.py`
- [x] Tests: family parametrisation, anti-tautology header test, exact-text `VALOR`
- [x] Read the real 202506 archive end to end through the new reader
- [x] Add the reader to `_META_MEMBERS`
- [x] Update `docs/ingestion/inf_mensal_fidc.md` and `docs/api.md`
- [x] Update the FIDC catalog line and member count in `CLAUDE.md`

Completed — kept as a record.

## ingestion-inf-mensal-fidc_20260711_073252

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

- [x] User review of the open PR (approval gate — do not start the next task until merged).
      PR #54 approved and squash-merged to main (`53e2e87`); content-verified post-merge.
- [x] After merge: release (minor bump) Test PyPI → verify by install → PyPI → verify.
      **0.13.0** released and install-verified on Test PyPI + PyPI (2026-07-11).
- [x] Next task started: **#53** (per-module `_RETRY_POLICY` standard) branched; Wave 1
      (FII → FIP → FIAGRO → FIE) resumes after #53. See portal-survey-41 ledger.

**Completed — kept as a record.** All boxes ticked 2026-07-11; PR #54 merged, 0.13.0 shipped.

## Notes

- `api.md` reader ctors for the existing FI readers still omit `retry_policy` (pre-existing doc
  drift from #49/#50); the new FIDC section documents it correctly. Not fixed here to keep the diff
  scoped — candidate follow-up.
- The `202501+`-only DADOS window reflects the post-RCVM-175 structure; older FIDC monthly layouts
  (`PadraoXMLMensalFIDC489/576`) are the submission direction, out of scope for this reader.
