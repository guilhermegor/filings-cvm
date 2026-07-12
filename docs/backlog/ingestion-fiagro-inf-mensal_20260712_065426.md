# Work ledger — FIAGRO Informe Mensal readers (#74)

Issue **#74** · branch `feat/ingestion-fiagro-inf-mensal`. Wave 1 of the #41 portal sweep
(FIDC→FII→FIP→**FIAGRO**→FIE). Inaugurates the **`fiagro/` portal root** (sibling of
`fi/`/`fidc/`/`fii/`/`fip/`).

Excluded from the docs site (`backlog/`). Never deleted — on completion tick the last box and add
a "Completed — kept as a record" note, per `docs/CLAUDE.md`.

## Grounding (real `202506` artifact — META + bytes)

- Dataset `FIAGRO/DOC/INF_MENSAL`; dump `inf_mensal_fiagro_AAAAMM.zip`, **monthly-partitioned**
  (`_AAAAMM`), series starts **202505**. META shipped as a zip (`meta_inf_mensal_fiagro.zip`,
  2 `.txt` members).
- **2 members** → 2 readers over a private base (mirrors `fidc/doc/inf_mensal/`):
  - `inf_mensal_fiagro_AAAAMM.csv` — **133 cols**, informe proper. Grain: one row per class ×
    month (`CNPJ_Classe`, `Data_Referencia`) — 18 unique rows in `202506`. Date cols:
    `Data_Referencia`, `Data_Entrega`, `Data_Registro`. → `InfMensalFiagroReader`.
  - `inf_mensal_fiagro_subclasse_AAAAMM.csv` — **6 cols**, long (38 rows, one per subclasse).
    Date col: `Data_Referencia`. → `InfMensalFiagroSubclasseReader`.
- Post-RCVM 175 nomenclature (Classe/Subclasse). CNPJ key col: `CNPJ_Classe`.
- **CVM spellings preserved verbatim**: `Provisoes_Contigencias` (missing *n*) and asymmetric
  `A_Vencer_Acima1080_Dias` (extra `_`) vs `Vencidos_Acima1080Dias` (none). Column tuples
  generated from the real CSV headers, not hand-transcribed (per the FIP lesson).
- CSV member selection is by **exact name** — `inf_mensal_fiagro` is a strict prefix of
  `inf_mensal_fiagro_subclasse`, so exact-name selection is load-bearing (locked by a test).

## Done

- [x] Contract module `_internal/config/contracts/inf_mensal_fiagro.py` (2 `FileContract`, one-per-
  file deviation noted, as `inf_mensal_fidc.py`) + re-exports in `contracts/__init__`.
- [x] Private base `_base_inf_mensal_fiagro_reader.py` — `_DATE_COLS` is **per-subclass** here
  (members differ), unlike FIDC's shared date col. `raw_workspace` + `hash_artifact` +
  `stamp_provenance` + `_RETRY_POLICY` (`_DEFAULT_RETRY_POLICY`, 5-attempt patient default).
- [x] 2 thin readers; new `fiagro/`, `fiagro/doc/`, `fiagro/doc/inf_mensal/` `__init__` chain.
- [x] Public API: `ingestion/__init__` + root `filings_cvm/__init__` (imports + `__all__`).
- [x] Docs: page `docs/ingestion/inf_mensal_fiagro.md`, mkdocs nav, `api.md` section, ingestion
  `index.md` bullet, root `CLAUDE.md` catalog (new FIAGRO root + Layout line).
- [x] Tests `tests/unit/test_inf_mensal_fiagro_ingestion.py` (16). Full suite **849 passed under
  BOTH pandas 3.0.3 and 2.3.3**. ruff/format/check_typing/check_provenance/mypy all clean.
- [x] **Live-verified** end-to-end against the real `202506` bytes (both readers parse, 133/6
  source cols + 6 provenance, dates coerced, PL kept as exact `str`, both typos present).

## Remaining

- [ ] Open PR (`Closes #74`); wait for user approval + merge.
- [ ] After merge: release (minor bump `0.22.0`→`0.23.0`) Test PyPI → verify install → PyPI →
  verify. Then next Wave 1 item: **FIE** (`FIE/DOC/BALANCETE`, `BALANCO`, `FIE/CAD`).
