# Ledger — #114 SECURIT INF_MENSAL_CRI readers (11 members)

Branch: `feat/114-inf-mensal-cri` · Issue: #114 · Class: **src (feat)** → PATCH release (0.25.6)

## Goal

Ingestion readers for `SECURIT/DOC/INF_MENSAL_CRI` (`inf_mensal_cri_AAAA.zip`, 11 members). Wave 2
PR 4/4 — **closes the `securit/` root (4/4)** and ends Wave 2 of #41.

## Work

- [x] 11 verbatim header fixtures generated from the real 2025 zip — `tests/fixtures/inf_mensal_cri/`
      (the pinned oracle; header-only, no PII).
- [x] `contracts/inf_mensal_cri.py` — 11 contracts **generated from the fixtures**, source key
      `inf_mensal_cri_<section>`, cnpj/date cols verified against real 2025 values.
- [x] `_base_inf_mensal_cri_reader.py` + 11 thin subclasses (CRA template; yearly `date_ref`).
- [x] `meta.py` = **23rd Meta reader** `MetaInfMensalCriReader` + `META_INF_MENSAL_CRI` in the
      `contracts/meta.py` factory list. META live-verified (URL, 11 members, `Data_LTV`=varchar,
      `Indice_Subordinacao_Data_Base`=numeric).
- [x] Registered CRI in `bin/check_contract_drift.py` `_META_MEMBERS` (#98 structural test — CI
      would fail otherwise). Registry re-closes: **113 readers, 113 members, 0 gaps**.
- [x] Wired all 5 `__init__` layers (package → securit/doc → securit → ingestion → top
      `filings_cvm`) + `contracts/__init__`. `test_meta_readers.py` 22→23.
- [x] Tests `test_inf_mensal_cri_ingestion.py` (mirrors CRA anti-tautology + traps + a header-only
      regression). Full unit suite green.
- [x] **Live-verified against real 2025 bytes**: geral 26,689×44, creditos ×51, classe 51,914×28,
      cedente_devedor 38,953×7, responsavel 0 rows (header-only reads clean).
- [x] Docs: `docs/ingestion/inf_mensal_cri.md` + mkdocs nav + api.md (+ Meta count 23) + ingestion
      index + root CLAUDE.md catalog (securit COMPLETE 4/4) + #41 survey ledger.

## Findings from the real bytes (honoured, not "fixed")

- [x] CRI is **not** a CRA copy: no `direitos_creditorios` (has `creditos`, 51 cols); +4 members.
- [x] `desembolso` (22) and `cedente_devedor` (7) are **column-identical to CRA** — generic
      structures; the coincidence is the source's, proven by the pinned headers (not a copy error).
      Anti-copy test asserts only the 5 asset-class sections differ.
- [x] `carteira_modificacao` + `responsavel` are **header-only** in 2025 → `tuple_cnpj_cols=()`
      (else a legitimately empty member fails the contract). Caught by live-verify, not unit tests.
- [x] `cedente_devedor.CNPJ` may be CPF (excluded from cnpj cols); `Indice_Subordinacao_Data_Base`
      and `Data_LTV` (varchar per META) are not dates; `Outras_Contigencias_Relevantes` typo kept.

## Remaining before PR

- [ ] codespell (pt-BR words), mkdocs --strict, pre-commit on changed files.
- [ ] pytest under **both** pandas 3.0.3 and 2.3.3.
- [ ] Commit → PR `Closes #114` → wait approval+merge → release PATCH 0.25.6.
