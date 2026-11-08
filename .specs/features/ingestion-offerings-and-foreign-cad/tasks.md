## ingestion-cia-estrang-cad_20260721_220540

# Work ledger — CIA_ESTRANG/CAD ingestion reader (#143)

Branch `feat/143-cia-estrang-cad-reader`. Adds `CadastroCiaEstrangReader` over `cad_cia_estrang.csv`
(`CIA_ESTRANG/CAD`), inaugurating the `cia_estrang/` portal root. **Opens Wave 4 of #41**
(companhias/ofertas).

A flat-CSV snapshot molded on `CadastroAdmFiiReader` / `CadastroEmissorCepacReader` — but wide
enough (49 cols) that the contract is **pinned to a verbatim header fixture** (the anti-tautology
oracle), unlike the narrower flat cadastros.

## Grounding (real bytes)

- `cad_cia_estrang.csv`: ISO-8859-1, CRLF, `;`-delimited, **49 columns**, 26 data rows (tiny —
  foreign issuers), fixed URL (snapshot — **no `date_ref`**).
- 7 date cols: `DT_REG`, `DT_CONST`, `DT_CANCEL`, `DT_INI_SIT`, `DT_INI_CATEG`,
  `DT_INI_SIT_EMISSOR`, `DT_INI_RESP`. ⚠️ `MOTIVO_CANCEL` is **free text**, not a date.
- **Two CNPJ cols**: `CNPJ` (issuer, masked, 25/26 valid) + `CNPJ_AUDITOR` (auditor, 25/25 valid) →
  `tuple_cnpj_cols = ("CNPJ", "CNPJ_AUDITOR")`. `RESP` carries a person's name but **no CPF col**.
- `CD_CVM`/`CEP`/`TEL`/`FAX`/`DDD_*`/`CD_PAIS_*` are `numeric`/`char` in META but kept `str`.
- META `meta_cad_cia_estrang.txt` exists (flat `.txt`, 49 fields). 32nd Meta reader.

## Wave 4 portal grounding (for the next slices)

- CIA_ESTRANG/CAD → `cad_cia_estrang.csv` (flat CSV) ✅ this PR
- CIA_INCENT/CAD → `cad_cia_incent.csv` (flat CSV)
- COORD_OFERTA/CAD → `cad_coord_oferta.zip` (multi-member ZIP)
- CROWDFUNDING/CAD → `cad_crowdfunding.zip` (multi-member ZIP)
- OFERTA → DISTRIB; CIA_ABERTA → big multi-dataset (7 DOC + CAD + EVENTOS), do last.

## Done

- [x] Header fixture `tests/fixtures/cad_cia_estrang/cad_cia_estrang_header.csv` (generated from real
      bytes, verbatim CRLF, header-only).
- [x] Contract `cad_cia_estrang.py` (`CAD_CIA_ESTRANG`, 49 cols, generated from + pinned to fixture)
      + re-export in `contracts/__init__.py`.
- [x] `META_CAD_CIA_ESTRANG` in `contracts/meta.py` + re-export.
- [x] Reader `ingestion/cia_estrang/cad/cadastro/cadastro.py` (`CadastroCiaEstrangReader`).
- [x] `MetaCadCiaEstrangReader` — 32nd Meta reader.
- [x] 3 nested `__init__.py` + flat re-export in `ingestion/__init__.py` and top
      `filings_cvm/__init__.py` (imports + `__all__`).
- [x] Drift registry `bin/check_contract_drift.py`: import, `_UNEXPOSED_CONTRACTS`, `_META_MEMBERS`.
- [x] Tests: **generalized the flat-CSV `FlatCase` harness** — dropped the single `str_cnpj_col`
      field; `_value_for` now derives CNPJ cols from `cls_contract.tuple_cnpj_cols` (supports N CNPJ
      columns). Added the CIA_ESTRANG case + an **anti-tautology test** reading the header fixture.
      Bumped `test_meta_readers.py` 31 → 32.
- [x] Docs: `docs/ingestion/cia_estrang.md` + mkdocs nav + `docs/api.md` (new section + Meta 31→32)
      + `docs/ingestion/index.md` + root `CLAUDE.md` catalog + Layout tree + META count 31→32.
- [x] Gates: ruff, mypy (314 files), check_typing, check_provenance, **full unit suite 1690 passed**.
- [x] Live-verified vs real CVM bytes: 26 rows, 49 source + 6 provenance cols, `DT_REG`→date,
      `CNPJ_AUDITOR` 25 valid, META 49 fields keyed `meta_cad_cia_estrang`.

## Remaining

- [ ] Full pre-commit run + `mkdocs --strict` + codespell.
- [ ] Commit → PR `Closes #143` → wait for approval + merge.
- [ ] After merge: release PATCH; continue Wave 4 (CIA_INCENT next — also flat CSV).

## ingestion-cia-incent-cad_20260722_121003

# Work ledger — CIA_INCENT/CAD ingestion reader (#145)

Branch `feat/145-cia-incent-cad-reader`. Adds `CadastroCiaIncentReader` over `cad_cia_incent.csv`
(`CIA_INCENT/CAD`), inaugurating the `cia_incent/` portal root. **Second slice of Wave 4 of #41**.

Flat-CSV snapshot molded on `CadastroCiaEstrangReader`, contract pinned to a verbatim header fixture
(47 cols → transcription risk).

## Grounding (real bytes)

- `cad_cia_incent.csv`: ISO-8859-1, CRLF, `;`, **47 columns**, ~3.570 data rows, fixed URL
  (snapshot — **no `date_ref`**).
- ⚠️ **NOT a copy of CIA_ESTRANG**: adds `ST_CIA_INCENT_REG`, drops `PAIS_ORIGEM`/`CD_PAIS_*`, uses
  `MUN`/`UF` (domestic) instead of `CIDADE`/`ESTADO`. Separate contract + fixture.
- 7 date cols: `DT_REG`, `DT_CONST`, `DT_CANCEL`, `DT_INI_SIT`, `DT_INI_CATEG`,
  `DT_INI_SIT_EMISSOR`, `DT_INI_RESP`. ⚠️ `DT_INI_CATEG` is **100% empty** in the current snapshot
  but is a date column by contract (META declares it, CIA_ESTRANG populates it) → coerces to all
  `NaT`. `MOTIVO_CANCEL` is free text, not a date.
- **Two CNPJ cols**: `CNPJ` (3570/3570 valid) + `CNPJ_AUDITOR` (2062 nonempty, 1781 valid) →
  `tuple_cnpj_cols = ("CNPJ", "CNPJ_AUDITOR")`. `RESP` carries a person's name but **no CPF col**.
- `CD_CVM`/`CEP`/`TEL`/`FAX`/`DDD_*` are `numeric`/`char` in META but kept `str`.
- META `meta_cad_cia_incent.txt` exists (flat `.txt`, 47 fields). 33rd Meta reader.

## Done

- [x] Header fixture `tests/fixtures/cad_cia_incent/cad_cia_incent_header.csv` (generated from real
      bytes, verbatim CRLF, header-only).
- [x] Contract `cad_cia_incent.py` (`CAD_CIA_INCENT`, 47 cols, generated from + pinned to fixture) +
      re-export.
- [x] `META_CAD_CIA_INCENT` in `contracts/meta.py` + re-export.
- [x] Reader `ingestion/cia_incent/cad/cadastro/cadastro.py` (`CadastroCiaIncentReader`).
- [x] `MetaCadCiaIncentReader` — 33rd Meta reader.
- [x] 3 nested `__init__.py` + flat re-export in `ingestion/__init__.py` and top
      `filings_cvm/__init__.py` (imports + `__all__`).
- [x] Drift registry `bin/check_contract_drift.py`: import, `_UNEXPOSED_CONTRACTS`, `_META_MEMBERS`.
- [x] Tests: added the CIA_INCENT `FlatCase` (harness already multi-CNPJ-aware) + an anti-tautology
      test reading the header fixture. Bumped `test_meta_readers.py` 32 → 33.
- [x] Docs: `docs/ingestion/cia_incent.md` + mkdocs nav + `docs/api.md` (new section + Meta 32→33) +
      `docs/ingestion/index.md` + root `CLAUDE.md` catalog + Layout tree + META count 32→33.
- [x] Gates: ruff, mypy (320 files), check_typing, check_provenance, **full unit suite 1705 passed**.
- [x] Live-verified vs real CVM bytes: 3570 rows, 47 source + 6 provenance cols, `DT_REG`→date,
      `DT_INI_CATEG` all `NaT`, `CNPJ_AUDITOR` 2062 nonempty, META 47 fields keyed
      `meta_cad_cia_incent`.

## Remaining

- [ ] Full pre-commit run + `mkdocs --strict` + codespell.
- [ ] Commit → PR `Closes #145` → wait for approval + merge.
- [ ] After merge: release PATCH; continue Wave 4 (COORD_OFERTA next — multi-member ZIP).

## ingestion-coord-oferta-cad_20260722_130258

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

## ingestion-crowdfunding-cad_20260722_133803

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

## ingestion-oferta-distrib_20260722_154919

# Work ledger — OFERTA/DISTRIB ingestion readers (#151, closes #14)

Branch `feat/151-oferta-distrib-reader`. Adds `OfertaDistribuicaoReader` + `OfertaResolucao160Reader`
over `oferta_distribuicao.zip` (`OFERTA/DISTRIB`), inaugurating the `oferta/` portal root.
**Fifth slice of Wave 4 of #41; closes the old #14** (Ofertas de Distribuição reader).

The widest tables in the portal so far — two offering registers keyed by regulatory regime, on the
COORD_OFERTA mould (private base + members), but NOT a registry+satellite pair.

## Grounding (real bytes)

- `oferta_distribuicao.zip`: **2 members**, ISO-8859-1, CRLF, `;`, fixed URL (snapshot — **no
  `date_ref`**). OFERTA has exactly one dataset (`DISTRIB`); no other subfolders.
  - `oferta_distribuicao.csv` — historical register (pre-RCVM 160), **76 cols**, ~48.9k rows, 9 ISO
    date cols. CNPJ cols: `CNPJ_Emissor` (31498 valid), `CNPJ_Lider` (35189), `CNPJ_Ofertante`
    (45734).
  - `oferta_resolucao_160.csv` — RCVM 160 requests, **71 cols**, ~13.9k rows, 3 ISO date cols. CNPJ
    cols: `CNPJ_Emissor` (13864 valid), `CNPJ_Lider` (13858).
- ⚠️ **NOT a registry+satellite pair** — two offering tables of **different regimes** with disjoint
  columns (`Numero_Requerimento`/`Status_Requerimento` in RCVM 160; `Numero_Registro_Oferta` in the
  historical one). Copying one onto the other ships the wrong contract green → anti-copy test.
- ⚠️ **Numeric convention (checked, not assumed):** every value-heavy ingestion reader in the repo
  keeps monetary/quantity/percent fields as `str` (exact CVM decimal text; consumer casts to
  `Decimal`). So all `Valor_*`/`Preco_*`/`Nr_*`/`Num_*`/`Qtd_*`/`Qtde_*` columns stay `str` — no user
  decision needed.
- ⚠️ **`oferta_resolucao_160.Data_deliberacao_aprovou_oferta` is `DD/MM/YYYY`** (e.g. `02/01/2023`),
  not ISO. The shared coercion is `pd.to_datetime(errors="raise").dt.date` — **ISO-only, no
  `dayfirst`** — so treating it as a date would silently swap day/month. Kept **`str`** (out of
  `_DATE_COLS`); consumer parses with `dayfirst=True`. Pinned by 2 tests.
- ⚠️ **META is a `.zip`** of 2 members (`meta_oferta_distribuicao.txt` **404s**). Both share the
  `oferta_` prefix → `_MEMBER_STEM="oferta"` yields **symmetric** sections `distribuicao` /
  `resolucao_160` (unlike INTERMED/COORD_OFERTA's asymmetric fallback). 36th Meta reader.

## Done

- [x] 2 header fixtures `tests/fixtures/oferta_distribuicao/*_header.csv` (generated from real bytes,
      verbatim CRLF, header-only). 147 col names — generated into a scratch file, never hand-typed.
- [x] Contracts `oferta_distribuicao.py` (`OFERTA_DISTRIBUICAO` 76 + `OFERTA_RESOLUCAO_160` 71,
      generated from + pinned to fixtures) + re-exports.
- [x] `META_OFERTA_DISTRIBUICAO` in `contracts/meta.py` + re-export.
- [x] Private base `_base_oferta_reader.py` + 2 thin subclasses.
- [x] `MetaOfertaReader` (`.zip` URL, `_MEMBER_STEM="oferta"`) — 36th Meta reader.
- [x] 2 nested `__init__.py` (`oferta/` + `oferta/distrib/`) + flat re-export in
      `ingestion/__init__.py` and top `filings_cvm/__init__.py` (imports + `__all__`).
- [x] Drift registry `bin/check_contract_drift.py`: `_META_MEMBERS` entry (both expose `_CONTRACT`).
- [x] Tests `tests/unit/test_oferta_distrib_ingestion.py`: anti-tautology header test per member,
      two-regime anti-copy test, **BR-date-as-str** pins (2 tests), CNPJ-cols-per-member, member
      selection, date coercion, no `date_ref`, `path_raw`, missing member/column, monetary-as-text,
      META-is-`.zip`, META symmetric sections. Bumped `test_meta_readers.py` 35 → 36.
- [x] Docs: `docs/ingestion/oferta_distrib.md` + mkdocs nav + `docs/api.md` (new section + Meta
      35→36) + `docs/ingestion/index.md` + root `CLAUDE.md` catalog + Layout tree + META count 35→36.
- [x] Gates: ruff, mypy (342 files), check_typing, check_provenance, **full unit suite 1813 passed**.
- [x] Live-verified vs real CVM bytes: distribuicao 48947 rows/76 cols, resolucao_160 13864/71,
      `Data_deliberacao_aprovou_oferta` returned as `'02/01/2023'` (str), META 147 fields with
      symmetric sections `['distribuicao', 'resolucao_160']`, key `meta_oferta_distribuicao`.

## Remaining

- [ ] Full pre-commit run + `mkdocs --strict` + codespell.
- [ ] Commit → PR `Closes #151` (mention it also resolves #14) → wait for approval + merge.
- [ ] After merge: release PATCH; **CIA_ABERTA** is the last Wave 4 slice (big — 7 DOC datasets
      {CGVN,DFP,FCA,FRE,IPE,ITR,VLMO} + CAD + EVENTOS; ground each sub-dataset separately).
