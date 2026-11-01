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
