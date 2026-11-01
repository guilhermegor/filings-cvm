# Work ledger — CIA_ABERTA/CAD ingestion reader (#153)

Branch `feat/153-cia-aberta-cad-reader`. Adds `CadastroCiaAbertaReader` over `cad_cia_aberta.csv`
(`CIA_ABERTA/CAD`), inaugurating the `cia_aberta/` portal root — **the last and largest root of the
#41 sweep**. Sixth slice of Wave 4.

⚠️ **This PR is the `CAD` slice only.** `CIA_ABERTA` holds nine datasets: `CAD` (here), the seven
`DOC` financial-statement datasets (`CGVN`, `DFP`, `FCA`, `FRE`, `IPE`, `ITR`, `VLMO`) and
`EVENTOS`. Each needs its own grounding against real bytes and its own PR — the root is too big for
one slice, and the sibling roots have repeatedly proven that shape is not inheritable.

## Grounding (real bytes)

- `cad_cia_aberta.csv`: **bare CSV** (not a ZIP), ISO-8859-1, CRLF, `;`, **fixed URL** → snapshot,
  **no `date_ref`**. Mould = `CadastroCiaEstrangReader` / `CadastroCiaIncentReader`, not the
  multi-member ZIP readers of COORD_OFERTA / CROWDFUNDING / OFERTA.
- **47 columns, 2 677 rows** (live-verified). Returned frame = 53 cols (47 source + 6 provenance).
- ⚠️ **NOT a copy of its CIA_* siblings** — the issuer key is **`CNPJ_CIA`** (the others use plain
  `CNPJ`), and it adds **`TP_MERC`** (`BOLSA` / `BALCÃO ORGANIZADO` / `BALCÃO NÃO ORGANIZADO`),
  which neither CIA_ESTRANG (49 cols) nor CIA_INCENT (47 cols) has. Same column *count* as
  CIA_INCENT — a coincidence, not a shared shape; transcribing the sibling would have shipped a
  wrong contract green.
- **7 date columns** (`DT_REG`, `DT_CONST`, `DT_CANCEL`, `DT_INI_SIT`, `DT_INI_CATEG`,
  `DT_INI_SIT_EMISSOR`, `DT_INI_RESP`). ⚠️ `MOTIVO_CANCEL` is **free text**, not a date — verified
  live (`CANCELAMENTO VOLUNTÁRIO`, `ELISÃO POR INCORPORAÇÃO`).
- **Two CNPJ columns** → `tuple_cnpj_cols = ("CNPJ_CIA", "CNPJ_AUDITOR")`; live counts 2 677 / 2 577
  non-blank. `RESP` carries a legal representative's name but there is **no CPF column**.
- `CD_CVM` / `CEP` / `TEL` / `FAX` / `DDD_*` are `numeric`/`char` in the META but stay `str` — they
  are identifiers, not quantities (`CD_CVM` arrives as `'25224'`).
- ⚠️ **META is a bare `.txt`** (`meta_cad_cia_aberta.txt`, 47 fields, single section
  `cad_cia_aberta`) — unlike the `.zip` METAs of the three preceding Wave 4 slices. The URL is
  constant per dataset and never derived.

## Done

- [x] Header fixture `tests/fixtures/cad_cia_aberta/cad_cia_aberta_header.csv` (verbatim real bytes,
      header-only — no PII). The pinned oracle the contract is generated **from**.
- [x] Contract `_internal/config/contracts/cad_cia_aberta.py` (`CAD_CIA_ABERTA`, 47 cols generated
      from the fixture) + re-exports in `contracts/__init__.py`.
- [x] `META_CAD_CIA_ABERTA` in `contracts/meta.py` + re-export.
- [x] `CadastroCiaAbertaReader` (`cia_aberta/cad/cadastro/cadastro.py`) + `MetaCadCiaAbertaReader`
      (`meta.py`) — **37th Meta reader**.
- [x] Nested `__init__.py` (`cia_aberta/`, `cad/`, `cad/cadastro/`) + flat re-exports in
      `ingestion/__init__.py` and top `filings_cvm/__init__.py` (imports + `__all__`).
- [x] Drift registry `bin/check_contract_drift.py`: `_UNEXPOSED_CONTRACTS` +`_META_MEMBERS` entries.
- [x] Tests: new `FlatCase` in `tests/unit/test_securit_cepac_flat_ingestion.py` (the shared flat-CSV
      harness — reused, not duplicated) + anti-tautology header test reading the fixture. Bumped
      `test_meta_readers.py` 36 → 37.
- [x] Docs: `docs/ingestion/cia_aberta_cad.md` + mkdocs nav + `docs/api.md` + `docs/ingestion/index.md`
      + root `CLAUDE.md` catalog + Layout tree + META count 36 → 37 (and corrected the stale
      `.txt`/`.zip` split to the measured 15/22).
- [x] Live-verified vs real CVM bytes: 2 677 rows × 53 cols, 7 date cols coerced, `MOTIVO_CANCEL`
      text, `CNPJ_CIA` 2 677 / `CNPJ_AUDITOR` 2 577 non-blank, all 6 provenance columns stamped,
      META 47 fields / section `cad_cia_aberta` / key `meta_cad_cia_aberta`.

## Remaining

- [ ] Gates: ruff, mypy, full unit suite, `mkdocs --strict`, codespell, full pre-commit.
- [ ] Commit → PR `Closes #153` → wait for approval + merge.
- [ ] After merge: release PATCH. Then the rest of `cia_aberta/`: the 7 `DOC` datasets + `EVENTOS`,
      **grounded one at a time**.
