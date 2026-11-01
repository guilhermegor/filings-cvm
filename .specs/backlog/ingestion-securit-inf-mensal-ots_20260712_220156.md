# Work ledger — SECURIT INF_MENSAL_OTS readers (#89, Wave 2 PR 2/4)

Issue **#89** · branch `feat/ingestion-securit-inf-mensal-ots-89`. Second slice of Wave 2 of #41
(Securitização): the 8-member `INF_MENSAL_OTS` yearly ZIP. Grounded in the real `2025` artifact
(META + bytes, 2026-07-12).

Excluded from the docs site (`backlog/`). Never deleted — tick the last box on completion.

## Shape

⚠️ **Yearly-partitioned ZIP despite a monthly report** (`inf_mensal_ots_AAAA.zip`, members
`inf_mensal_ots_<section>_AAAA.csv`) → `date_ref` selects the **year** (FII pattern, not FIDC). 8
members share the 4-col key prefix (`CNPJ_Securitizadora`, `Codigo_Identificacao_Certificado`,
`Data_Referencia`, `Versao`) → private base + 8 thin subclasses (FIDC INF_MENSAL template).

| Reader | Member | Cols | Rows (2025) |
|---|---|---|---|
| `InfMensalOtsGeralReader` | geral | 36 | 1793 |
| `InfMensalOtsAtivoPassivoReader` | ativo_passivo | 30 | 1793 |
| `InfMensalOtsClasseReader` | classe | 23 | 6821 (long) |
| `InfMensalOtsDireitosCreditoriosReader` | direitos_creditorios | 43 | 1793 |
| `InfMensalOtsDesembolsoReader` | desembolso | 22 | 1793 |
| `InfMensalOtsFluxoCaixaReader` | fluxo_caixa | 21 | 1793 |
| `InfMensalOtsDerivativosReader` | derivativos | 20 | 1793 |
| `InfMensalOtsCedenteDevedorReader` | cedente_devedor | 7 | 1650 (long) |

## Three traps found by grounding + LIVE-verified (all honoured)

1. **`cedente_devedor.CNPJ` holds a CPF on 257/1650 rows** — NOT declared a CNPJ column (would fail
   a valid file — `cad_fi.CPF_CNPJ_GESTOR` trap); only `CNPJ_Securitizadora` is validated. PII →
   verbatim text. Live: all 257 CPF rows parsed without ContractError.
2. **`Indice_Subordinacao_Data_Base` (in `classe`) is NOT a date** despite the name — numeric values.
   Absent from `_DATE_COLS`; stays `str`. Live-confirmed.
3. **CVM typo verbatim:** `Outras_Contigencias_Relevantes` in `geral` (missing *n*) vs correct
   `Contingencias_Principais_Fatos` in the same file. Live-confirmed present.

Date columns are **per-member** (FIAGRO pattern): all have `Data_Referencia`; `geral` +3, `classe`
+`Data_Vencimento`.

## Done

- [x] Contract module `inf_mensal_ots.py` (8 constants, deliberate `inf_mensal_fidc.py` deviation) +
  re-exports. **All 8 tuples programmatically verified equal to the real headers** (0 drift).
- [x] Private base `_base_inf_mensal_ots_reader.py` (yearly `date_ref`, per-member `_DATE_COLS`,
  exact-name member selection) + 8 thin readers; `inf_mensal_ots/` `__init__`.
- [x] Public API wired: `securit/doc` + `securit` + `ingestion/__init__` + root `__init__`.
- [x] Docs: page `inf_mensal_ots.md`, mkdocs nav, `api.md` section, ingestion index bullet, root
  `CLAUDE.md` catalog + Layout; #41 survey ledger.
- [x] Tests `test_inf_mensal_ots_ingestion.py` (41, incl. 3 trap regressions). Full suite **1010
  pass BOTH pandas majors**; ruff/format/typing/provenance/mypy/codespell all clean.
- [x] **Live-verified** all 8 against real 2025 bytes (row counts 1793/6821/1650 etc.; dates coerced;
  money `str`; provenance stamped; 3 traps behave).
- [x] Kanban: #89 → In progress (manual; hook not deployed).

## Remaining

- [ ] Open PR (`Closes #89`); wait for approval + merge. `risk:src` → human review.
- [ ] After merge: release **PATCH** (0.25.2 → **0.25.3**; both indices aligned at 0.25.2).
- [ ] Wave 2 PRs 3–4: `INF_MENSAL_CRA` (8 members), `INF_MENSAL_CRI` (11) — same base+subclass
  template; CRI adds `carteira`, `carteira_modificacao`, `creditos`, `responsavel` vs CRA/OTS.
