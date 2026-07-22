# Work ledger — CROWDFUNDING/CAD ingestion readers (#149)

Branch `feat/149-crowdfunding-cad-reader`. Adds `CrowdfundingReader` +
`CrowdfundingAdmRespReader` + `CrowdfundingSociosReader` over `cad_crowdfunding.zip`
(`CROWDFUNDING/CAD`), inaugurating the `crowdfunding/` portal root. **Fourth slice of Wave 4 of
#41.**

Combines two known shapes: the INTERMED/COORD_OFERTA keying (registry + satellites, all on the
platform's CNPJ) with the ADM_CART dateless satellites.

## Grounding (real bytes)

- `cad_crowdfunding.zip`: **3 members**, ISO-8859-1, CRLF, `;`, fixed URL (snapshot — **no
  `date_ref`**).
  - `cad_crowdfunding.csv` — registry, **17 cols**, 146 rows, 2 date cols (`DT_REG`, `DT_INI_SIT`).
  - `cad_crowdfunding_adm_resp.csv` — **2 cols**, 181 rows, **0 date cols**.
  - `cad_crowdfunding_socios.csv` — **2 cols**, 246 rows, **0 date cols**.
  - `CNPJ` 100% valid in all three (146/146, 181/181, 246/246).
- ⚠️ **NOT a `pf`/`pj` split** — registry + 2 satellites, all keyed by the platform's `CNPJ`.
- ⚠️ **The 2 satellites have no date column at all** (`_DATE_COLS=()`, the ADM_CART shape) → every
  column returns as exact text. They carry personal data (`ADM_RESP`; `SOCIO` mixes natural and
  legal persons — e.g. "Arco Participações S/A") but the source publishes **no CPF column**.
- ⚠️ **The registry is LEANER than its siblings** — **no** `DT_CANCEL` / `MOTIVO_CANCEL` / `CD_CVM`,
  and it spells `WEBSITE` (not COORD_OFERTA's `SITE_WEB`) and `DDD` (not `DDD_TEL`). Copying a
  sibling's contract would ship wrong columns with every test green → pinned by its own test.
- ⚠️ **META is a `.zip`** of 3 members (`meta_cad_crowdfunding.txt` **404s**), sections come back
  **asymmetric** (`cad_crowdfunding` + `adm_resp` + `socios`) — the documented `_section_of`
  fallback, as in INTERMED/COORD_OFERTA. **Predicted from the checkpoint before writing**, then
  confirmed on live-verify and pinned. 35th Meta reader.

## Done

- [x] 3 header fixtures `tests/fixtures/cad_crowdfunding/*_header.csv` (generated from the real
      bytes, verbatim CRLF, header-only).
- [x] Contracts `cad_crowdfunding.py` (3 contracts, generated from + pinned to the fixtures) +
      re-exports.
- [x] `META_CAD_CROWDFUNDING` in `contracts/meta.py` + re-export.
- [x] Private base `_base_crowdfunding_reader.py` + 3 thin subclasses.
- [x] `MetaCrowdfundingReader` (`.zip` URL, `_MEMBER_STEM = "cad_crowdfunding"`) — 35th Meta reader.
- [x] 2 nested `__init__.py` + flat re-export in `ingestion/__init__.py` and top
      `filings_cvm/__init__.py` (imports + `__all__`).
- [x] Drift registry `bin/check_contract_drift.py`: `_META_MEMBERS` entry (all three expose
      `_CONTRACT`, so no `_UNEXPOSED_CONTRACTS` entries needed).
- [x] Tests `tests/unit/test_crowdfunding_ingestion.py`: anti-tautology header test per member,
      **anti-copy test** (registry lacks `DT_CANCEL`/`MOTIVO_CANCEL`/`CD_CVM`/`SITE_WEB`/`DDD_TEL`,
      has `WEBSITE`/`DDD`), dateless-satellite test, all-text satellite test, member selection, date
      coercion, no `date_ref`, `path_raw`, missing member/column, `CEP` text, META-is-`.zip`, META
      section asymmetry. Bumped `test_meta_readers.py` 34 → 35.
- [x] Docs: `docs/ingestion/crowdfunding.md` + mkdocs nav + `docs/api.md` (new section + Meta 34→35)
      + `docs/ingestion/index.md` + root `CLAUDE.md` catalog + Layout tree + META count 34→35.
- [x] Gates: ruff, mypy (335 files), check_typing, check_provenance, **full unit suite 1779 passed**.
- [x] Live-verified vs real CVM bytes: 146/181/246 rows, 17/2/2 source cols, META 21 fields with
      sections `['adm_resp', 'cad_crowdfunding', 'socios']`, key `meta_cad_crowdfunding`.

## Remaining

- [ ] Full pre-commit run + `mkdocs --strict` + codespell.
- [ ] Commit → PR `Closes #149` → wait for approval + merge.
- [ ] After merge: release PATCH; continue Wave 4 (**OFERTA/DISTRIB** next, then **CIA_ABERTA** last
      — the big multi-dataset one).
