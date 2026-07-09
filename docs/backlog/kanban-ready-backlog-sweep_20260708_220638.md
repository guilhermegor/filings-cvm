# Work ledger — kanban Ready + Backlog sweep (one branch/PR per issue)

Master ledger for the sweep of every kanban issue in **Ready** (#6–#14, ingestion readers)
and **Backlog** (#18–#33, submission XML writers). One branch and one PR per issue.

Excluded from the docs site (`backlog/`). **Never deleted** — on completion the last box is
ticked and a "Completed — kept as a record" note added, per `docs/CLAUDE.md`.

This file is the **resume point**: if a session drops, read the checkboxes below to see what
landed, then continue from the first `- [ ]`.

## Standing decisions (apply to every issue in this sweep)

- **Ground every schema in the real artifact.** Before declaring a `FileContract` or a dtype
  map, download the actual CVM file and read its real header. Never write column names from
  memory. (This caught a missing `DENOM_SOCIAL` in the #6 contract on 2026-07-08.)
- **Every ingestion reader takes an optional `path_raw: Path | None = None`.** `None` → the
  artifact is fetched into a temporary directory and discarded (pure in-memory read, returning
  only the DataFrame). A path → the **untouched raw artifact** (`.zip`, `.csv`, `.html`,
  `.xlsx`, `.txt`, …) is written there and kept, *before* any parsing. Implemented once as the
  shared `_internal/utils/raw_workspace.py` context manager — never re-branch on the tempdir
  inside a reader. Applies to **#6–#14 without exception**, and is retrofitted onto the already
  -merged `InformeDiarioReader` (#5) in the same PR that introduces the seam.

  *Why:* these packages feed the future **bedrock** financial-markets datalake (raw, myriad
  formats) + medallion warehouse (bronze/silver/gold), scraped on an Airflow schedule. When an
  upstream contract changes and a transform breaks, the raw artifact on disk makes the failure
  replayable from the exact bytes; a log-sniffing agent can then open an issue via `/issue`,
  add it to the kanban, and a fix starts — none of which works if the bytes were memory-only.
  The seam yields a local `Path`; raw files are destined for S3-compatible object storage
  (rustfs is under consideration), reached today via a mounted/synced directory. An `s3://`
  upgrade would land inside `raw_workspace` alone, touching no reader.

  This convention is **not** `filings-*`-specific: it governs every scraping/ingestion package
  in the family (`bcb`, `investingcom`, `yahii`, `debentures-com-br`, `mais-retorno`, `fmp_*`,
  `global-rates`, `trading-econ`, `world-gov-bonds`, …). Captured as the BlueprintX
  python-common lesson `ingestion-reader-persists-raw-artifact.md`.
- **Writers (#18–#33) take field names, decimal scales, and cardinalities from the linked
  `PadraoXML*.asp` CVM spec page**, never from recall — per the root `CLAUDE.md`.
- Money/quantity columns stay `str` (exact CVM decimal text). Never `float`. Consumers convert
  to `Decimal` at the point of computation.
- One PR per issue, branched from an up-to-date `main`; PR body closes the issue.
- Each issue gets its own per-branch ledger under `docs/backlog/` too; this file is the index.

## Ready — ingestion readers (#6–#14)

- [ ] **#6** CDA — Composição e Diversificação das Aplicações reader ·
  `feat/ingestion-cda-reader` · PR —
  - Shape decided 2026-07-08: concat `BLC_1…BLC_8` tagged with a `BLOCO` column, then
    **left-join** `PL`'s `VL_PATRIM_LIQ` on `(TP_FUNDO_CLASSE, CNPJ_FUNDO_CLASSE, DT_COMPTC)`.
    Single grain: fund × date × asset. `cda_fie_*.csv` (a distinct FIE layout carrying its own
    `ID_DOC`/`VL_PATRIM_LIQ`) is **out of scope** — see follow-up below.
  - Rejected: stacking all ten members (mixed grain — `groupby().sum()` double-counts).
- [ ] **#7** Carteira / Portfolio composition reader · `feat/ingestion-carteira-reader` · PR —
- [ ] **#8** Lâmina (fact sheet) reader · `feat/ingestion-lamina-reader` · PR —
- [ ] **#9** Cadastro de Fundos (CAD/FI) reader · `feat/ingestion-cadastro-fi-reader` · PR —
- [ ] **#10** Registro de Intermediários Financeiros reader ·
  `feat/ingestion-registro-intermediarios-reader` · PR —
- [ ] **#11** Perfil Mensal FI (funds) reader · `feat/ingestion-perfil-mensal-fi-reader` · PR —
- [ ] **#12** Extrato (statement) reader · `feat/ingestion-extrato-reader` · PR —
- [ ] **#13** Perfil Mensal FIF reader · `feat/ingestion-perfil-mensal-fif-reader` · PR —
- [ ] **#14** Ofertas de Distribuição de Valores Mobiliários reader ·
  `feat/ingestion-ofertas-distribuicao-reader` · PR —

## Backlog — submission XML writers (#18–#33)

Each needs its `PadraoXML*.asp` spec page fetched first; the CVM catalog page is the index:
<https://cvmweb.cvm.gov.br/SWB/Sistemas/SCW/PadroesXML/PadroesXML.asp>

- [ ] **#18** Informe de Fundo 157 (`PadraoXMLInf157.asp`) · `feat/submission-informe-157`
- [ ] **#19** Informe Sintético (`PadraoXMLSintFCCE.asp` + 3 sibling layouts) ·
  `feat/submission-informe-sintetico`
- [ ] **#20** CDA V4 (`PadraoXMLCDANetV4.aspx`) · `feat/submission-cda-v4`
- [ ] **#21** Demonstrativo de Fontes e Aplicações de Recursos — FAR (`PadraoXMLFAR.asp`) ·
  `feat/submission-far`
- [ ] **#22** Balanço (`PadraoXMLBalanco.asp`) · `feat/submission-balanco`
- [ ] **#23** Balancete (`PadraoXMLBalancete.asp`) · `feat/submission-balancete`
- [ ] **#24** Informe Quadrimestral V2 (`PadraoXMLInfoTrimV2.asp`) ·
  `feat/submission-informe-quadrimestral-v2`
- [ ] **#25** Informe Mensal FIDC (`PadraoXMLMensalFIDC576.asp`) · `feat/submission-fidc-mensal`
- [ ] **#26** Lâmina V3 (`PadraoXMLLaminaV3.asp`) · `feat/submission-lamina-v3`
- [ ] **#27** Extrato das Informações sobre o Fundo V3 (`PadraoXMLInfExtratoV3.asp`) ·
  `feat/submission-extrato-v3`
- [ ] **#28** Informe Anual de Auditor (`PadraoXMLAuditorAnual.asp`) ·
  `feat/submission-auditor-anual`
- [ ] **#29** Informe Mensal de Investidor não Residente (`PadraoXMLInfoMensalINR.asp`) ·
  `feat/submission-inr-mensal`
- [ ] **#30** Informe Semestral de Investidor não Residente (`PadraoXMLInfoSemestralINR.asp`) ·
  `feat/submission-inr-semestral`
- [ ] **#31** Atualização do Cadastro de Ativos (`PadraoXMLAtivos.asp`) ·
  `feat/submission-cadastro-ativos`
- [ ] **#32** Informe Art. 12 Resolução CVM 33 (`PadraoXMLPrest.asp`) · `feat/submission-art12-rcvm33`
- [ ] **#33** Informe de Portabilidade (`PadraoXMLInfoPortabilidade.asp`) ·
  `feat/submission-portabilidade`

## Open / follow-up

- [ ] `cda_fie_*.csv` — the CDA dump also ships a **FIE** member with a distinct layout
  (`ID_DOC`, inline `VL_PATRIM_LIQ`, exterior-asset columns). Deliberately excluded from #6.
  Worth its own issue + reader rather than forcing it into the FIF frame.
- [ ] Writers cannot be fully verified without a CVM validation round-trip; field names and
  decimal scales carry residual risk even when taken from the spec page. Flag any writer PR
  that could not be checked against a real CVM-accepted document.
