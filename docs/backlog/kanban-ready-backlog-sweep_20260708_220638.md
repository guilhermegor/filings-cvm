# Work ledger — kanban Ready + Backlog sweep (one branch/PR per issue)

Master ledger for the sweep of every kanban issue in **Ready** (#6–#14, ingestion readers)
and **Backlog** (#18–#33, submission XML writers). One branch and one PR per issue.

Excluded from the docs site (`backlog/`). **Never deleted** — on completion the last box is
ticked and a "Completed — kept as a record" note added, per `docs/CLAUDE.md`.

This file is the **resume point**: if a session drops, read the checkboxes below to see what
landed, then continue from the first `- [ ]`.

## Workflow gate — ONE PR at a time, user approves before the next starts

**Hard rule. Do not violate.** The sweep is strictly sequential and gated on the user's
approval. Claude must **never** start the next issue's branch/PR while a PR is still open and
unapproved. The per-issue lifecycle, in order:

1. Implement the issue on its branch; open the PR (closes the issue).
2. **STOP. Wait for the user to review and approve/merge the PR.** Do not branch, do not touch
   the next issue, do not run `git checkout main` — nothing.
3. Once the user has approved and the PR is **merged** (which closes it), delete the merged
   branch (`git branch -d <branch>` local + `git push origin --delete <branch>` remote, or the
   `gh pr merge --delete-branch` that did it).
4. Sync `main` (`git checkout main && git pull --ff-only`) so the next branch forks from the
   merged state.
5. Only **then** start the next issue's branch/PR.

Rationale: the user is the reviewer/approver. A second PR opened before the first is approved
buries feedback, risks building later work on an approach the user may still change, and makes
the branch/main state ambiguous. **When a PR is open, the default action is to wait, not to
proceed.**

## Release gate — every merge to `main` ships, Test PyPI first

**Standing instruction from the user (2026-07-09). Applies after *every* PR merge in this
sweep**, not just at the end. It slots between step 4 (sync `main`) and step 5 (start the next
issue) of the lifecycle above:

4a. Compute the next version: a **minor** semver bump of the currently published version
    (`0.4.0` → `0.5.0` → `0.6.0` …). The version is **not** in `pyproject.toml` (it is a
    `0.0.0` stub; `poetry-dynamic-versioning` derives it from the `vX.Y.Z` git tag), so read
    the truth from the index, not the repo:

    ```bash
    python3 -c "import json,urllib.request as u; \
      print(json.load(u.urlopen('https://pypi.org/pypi/filings-cvm/json'))['info']['version'])"
    ```

4b. Run **`release-test-pypi.yaml`** (`workflow_dispatch`, input `version`) with that version.
    Both release workflows call `tests.yaml` as a hard gate, so a red suite blocks the publish.

    ```bash
    rtk gh workflow run release-test-pypi.yaml -f version=X.Y.0
    ```

4c. **Verify it actually landed on Test PyPI** before going further — the workflow going green
    is not the same as the artifact being installable:

    ```bash
    python3 -c "import json,urllib.request as u; \
      print(json.load(u.urlopen('https://test.pypi.org/pypi/filings-cvm/json'))['info']['version'])"
    ```

4d. Only once Test PyPI holds that version, run **`release-pypi.yaml`** with the **same**
    version (never a different one — Test PyPI is a rehearsal of the exact artifact, and PyPI
    versions are immutable once taken):

    ```bash
    rtk gh workflow run release-pypi.yaml -f version=X.Y.0
    ```

4e. Confirm the version on PyPI, then — and only then — start the next backlog issue.

Rationale: Test PyPI is the only place a bad wheel is still recoverable. A PyPI version number
can never be reused or overwritten, so a broken publish burns that version permanently. Bumping
minor (not patch) on every merge is deliberate: each merged issue adds a new public reader or
writer to `__all__`, which is a feature addition, not a fix.

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

- [x] **#6** CDA — Composição e Diversificação das Aplicações reader ·
  `feat/ingestion-cda-reader` · **PR #35** —
  - Shape: concat `BLC_1…BLC_8` tagged with a `BLOCO` column, then **left-join** `PL`'s
    `VL_PATRIM_LIQ` on `(TP_FUNDO_CLASSE, CNPJ_FUNDO_CLASSE, DT_COMPTC)` (`validate="many_to_one"`).
    Single grain: fund × date × asset. `cda_fie_*.csv` out of scope — see follow-up.
  - Rejected: stacking all ten members (mixed grain — `groupby().sum()` double-counts).
  - Also shipped the `path_raw` raw-artifact seam (`_internal/utils/raw_workspace.py`),
    retrofitted onto `InformeDiarioReader`. Warn-not-raise policy for funds absent from PL.
  - 49 tests green; docs + catalog updated. **Merged** (commit `89454bf`).
- [x] **#7** Carteira / Portfolio composition reader · `feat/ingestion-carteira-reader` · PR _pending_ —
  - Ledger: [`ingestion-lamina-carteira-reader_20260709_194646.md`](ingestion-lamina-carteira-reader_20260709_194646.md)
  - **Not a duplicate of #6.** The issue's stpstone reference `CvmFIFPortfolio` downloads
    `lamina_fi_AAAAMM.zip`, not CDA — #7 is the **Lâmina's allocation-by-asset-type** table.
    Shipped as `LaminaCarteiraReader` (`ingestion/lamina_carteira.py`), not `CarteiraReader`:
    "carteira" alone collides with CDA and with #8's `LaminaReader`.
  - Grounded in the real `lamina_fi_202504.zip`: 7 columns, grain unique, `ID_SUBCLASSE` empty
    on all 4,474 rows. **`PR_PL_ATIVO` does not sum to 100** (per-fund -37.08 → 1123.00, median
    100.03 — leverage/shorts), so no "totals 100%" invariant is asserted.
  - 13 new tests (58 total green); verified end-to-end against the live CVM file, not just mocks.
    Docs + catalog updated. Merged? _pending review._
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
- [x] *Resolved 2026-07-09:* the PyPI release that ran after the #35 merge was **`0.4.0`**, and
  it was intentional — the user has since made publishing a standing post-merge step (see
  "Release gate" above). Local tags lag the published versions; `git fetch --tags` before
  reasoning about the current version, or just query the index.
