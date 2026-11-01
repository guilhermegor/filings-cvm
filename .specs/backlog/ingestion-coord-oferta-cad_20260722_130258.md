# Work ledger — COORD_OFERTA/CAD ingestion readers (#147)

Branch `feat/147-coord-oferta-cad-reader`. Adds `CoordOfertaReader` + `CoordOfertaRespReader` over
`cad_coord_oferta.zip` (`COORD_OFERTA/CAD`), inaugurating the `coord_oferta/` portal root.
**Third slice of Wave 4 of #41 — the first multi-member ZIP of the wave**, so it returns to the
INTERMED mould (private base + N members) after two flat-CSV slices.

## Grounding (real bytes)

- `cad_coord_oferta.zip`: **2 members**, ISO-8859-1, CRLF, `;`, fixed URL (snapshot — **no
  `date_ref`**).
  - `cad_coord_oferta.csv` — registry, **25 cols**, 121 rows, 4 date cols (`DT_REG`, `DT_CANCEL`,
    `DT_INI_SIT`, `DT_PATRIM_LIQ`). `CNPJ` 121/121 valid.
  - `cad_coord_oferta_resp.csv` — officers, **6 cols**, 262 rows, 2 date cols (`DT_REG`,
    `DT_INI_RESP`). `CNPJ` 262/262 valid.
- ⚠️ **NOT a `pf`/`pj` split** — two related tables of one registry, **both keyed by the
  coordinator's `CNPJ`** (the INTERMED shape). `resp` carries `RESP` (a person's name) but the
  source publishes **no CPF column** → `tuple_cnpj_cols=("CNPJ",)` on both.
- `MOTIVO_CANCEL` is free text, not a date. `CD_CVM`/`CEP`/`TEL`/`FAX`/`DDD_*` are `numeric`/`char`
  in META but kept `str`.
- ⚠️ **The META is a `.zip`** (`meta_cad_coord_oferta.zip`, 2 members) — `meta_cad_coord_oferta.txt`
  **404s**. The URL is a per-dataset constant, never derived from a sibling's shape. Its two
  `section` labels come back **asymmetric** (`cad_coord_oferta` + `resp`) because one member is the
  bare stem — the documented `_section_of` fallback, same as INTERMED. **Predicted from the
  checkpoint before writing, then confirmed on live-verify and pinned by test.** 34th Meta reader.

## Done

- [x] Header fixtures `tests/fixtures/cad_coord_oferta/{cad_coord_oferta,cad_coord_oferta_resp}_header.csv`
      (generated from the real bytes, verbatim CRLF, header-only).
- [x] Contracts `cad_coord_oferta.py` (`CAD_COORD_OFERTA` 25 cols + `CAD_COORD_OFERTA_RESP` 6 cols,
      generated from + pinned to the fixtures) + re-exports.
- [x] `META_CAD_COORD_OFERTA` in `contracts/meta.py` + re-export.
- [x] Private base `_base_coord_oferta_reader.py` + 2 thin subclasses (`coord_oferta.py`,
      `coord_oferta_resp.py`).
- [x] `MetaCoordOfertaReader` (`.zip` URL, `_MEMBER_STEM = "cad_coord_oferta"`) — 34th Meta reader.
- [x] 2 nested `__init__.py` + flat re-export in `ingestion/__init__.py` and top
      `filings_cvm/__init__.py` (imports + `__all__`).
- [x] Drift registry `bin/check_contract_drift.py`: `_META_MEMBERS` entry (both readers expose
      `_CONTRACT`, so no `_UNEXPOSED_CONTRACTS` entry is needed).
- [x] Tests `tests/unit/test_coord_oferta_ingestion.py` (mirrors INTERMED): anti-tautology header
      test per member, distinct-columns anti-copy test, member selection, date coercion, no
      `date_ref`, `path_raw` persistence, missing member/column, `CEP` text, **plus two pinned
      source facts** — the META URL is the `.zip`, and the section labels are asymmetric. Bumped
      `test_meta_readers.py` 33 → 34.
- [x] Docs: `docs/ingestion/coord_oferta.md` + mkdocs nav + `docs/api.md` (new section + Meta 33→34)
      + `docs/ingestion/index.md` + root `CLAUDE.md` catalog + Layout tree + META count 33→34.
- [x] Gates: ruff, mypy (327 files), check_typing, check_provenance, **full unit suite 1736 passed**.
- [x] Live-verified vs real CVM bytes: registry 121 rows/25 cols, resp 262 rows/6 cols, META 31
      fields with sections `['cad_coord_oferta', 'resp']`, key `meta_cad_coord_oferta`.

## Remaining

- [ ] Full pre-commit run + `mkdocs --strict` + codespell.
- [ ] Commit → PR `Closes #147` → wait for approval + merge.
- [ ] After merge: release PATCH; continue Wave 4 (CROWDFUNDING next — also a multi-member ZIP).
