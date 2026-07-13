# Work ledger — SECURIT DFIN (CRA/CRI) + EMISSOR_CEPAC CAD (#87, Wave 2 PR 1/4)

Issue **#87** · branch `feat/ingestion-securit-cepac-flat-87`. First slice of Wave 2 of #41
(Securitização): the three **flat-CSV** datasets, grouped into one PR (maintainer's chosen
decomposition). Inaugurates the `securit/` **and** `emissor_cepac/` portal roots. Grounded in the
real artifacts (META + bytes, 2026-07-12).

Excluded from the docs site (`backlog/`). Never deleted — tick the last box on completion.

## 3 readers, 2 new roots

| Reader | Dataset | Artifact | Precedent |
|---|---|---|---|
| `DfinCraReader` | `SECURIT/DOC/DFIN_CRA` | `dfin_cra_AAAA.csv` (flat, yearly) | `DfinFiiReader` |
| `DfinCriReader` | `SECURIT/DOC/DFIN_CRI` | `dfin_cri_AAAA.csv` (flat, yearly) | `DfinFiiReader` |
| `CadastroEmissorCepacReader` | `EMISSOR_CEPAC/CAD` | `cad_emissor_cepac.csv` (snapshot, fixed URL) | `CadastroFiReader` |

- **DFIN CRA/CRI** — identical 9-col index of financial statements (one row per document). Year-
  partitioned; `Link_Download` returned as text, **not followed**. Dates `Data_Referencia`,
  `Data_Entrega`; CNPJ `CNPJ_Emissora`; no unique key. Live: 681 / 2300 rows on 2025.
- **cad_emissor_cepac** — 20-col registry snapshot (municipalities; 3 rows), fixed URL → **no
  `date_ref`**. Dates `DT_REG`/`DT_CANCEL`/`DT_INI_SIT`; CNPJ `CNPJ`.

## Done

- [x] 3 contracts (`dfin_cra`, `dfin_cri`, `cad_emissor_cepac`) + re-exports in `contracts/__init__`.
- [x] 3 readers under new `securit/doc/` + `emissor_cepac/cad/` packages; `__init__` chains for both
  roots. All carry `raw_workspace` + `hash_artifact` + `stamp_provenance` + `_RETRY_POLICY`.
- [x] Public API wired: `ingestion/__init__` + root `filings_cvm/__init__` (imports + `__all__`).
- [x] Docs: page `securit_cepac_flat.md`, mkdocs nav, `api.md` section, ingestion `index.md` bullet,
  root `CLAUDE.md` catalog (2 new roots + Layout) + #41 survey ledger (SECURIT 🟡 partial, CEPAC ✅).
- [x] Tests `test_securit_cepac_flat_ingestion.py` (22, config-driven; CEPAC's absent `date_ref`
  handled by a `_build` helper). Full suite **937 pass BOTH pandas majors**; all gates + mypy clean.
- [x] **Live-verified** against real bytes (DFIN 681/2300 rows, CEPAC 3; dates coerced; Link_Download
  kept as `str`, not followed; provenance stamped).
- [x] Kanban: #87 moved to **In progress** (had to fix manually — raw `gh` left it in Backlog; the
  deterministic branch-name-keyed hook is captured in dotfiles `issue-command-drives-kanban-lifecycle`).

## Remaining

- [ ] Open PR (`Closes #87`); wait for approval + merge. `risk:src` → human review.
- [ ] After merge: **release** — `feat` in `src/` → **PATCH** bump. PyPI 0.24.0, Test-PyPI floor
  0.25.1 → next likely **0.25.2** (compute vs max of both indices).
- [ ] Wave 2 PRs 2–4: `INF_MENSAL_OTS` (8 members), `INF_MENSAL_CRA` (8), `INF_MENSAL_CRI` (11) —
  multi-member yearly zips, one reader per member over a private base (FIDC INF_MENSAL template).
