# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this template is

A **PyPI-ready Python library starter**. A clean, importable package with CI, pre-commit,
tests, docs, and PyPI + Test-PyPI release workflows ready to go. It is scaffolded by
BlueprintX into a new project directory; the scaffold replaces the `<project_name>` package
directory and the `pyproject.toml` placeholders via `envsubst`.

## CVM Sources of Truth — one per direction

The library implements the CVM regulatory file standards in two directions, and **each
direction has its own authoritative CVM source.** Do not cross them.

**Submission (`submission/`, envio → CVM) — the XML-standards catalog page:**

> https://cvmweb.cvm.gov.br/SWB/Sistemas/SCW/PadroesXML/PadroesXML.asp

Each catalog entry below links to a `PadraoXML*.asp` page (relative to that base URL) describing
one XML standard. When implementing or updating a **writer**, treat the linked CVM page as
authoritative — field names, decimal scales, and cardinalities come from there, not from this
file.

**Ingestion (`ingestion/`, leitura ← CVM) — the open-data portal:**

> https://dados.cvm.gov.br/dados/

The **readers** consume the flat open-data dumps published under this portal, **not** the
submission XML specs. Nearly every ingestion artifact comes from here, each with its own dataset
page — e.g. Perfil Mensal ingestion is <https://dados.cvm.gov.br/dataset/fi-doc-perfil_mensal>,
and the implemented readers pull from `FI/DOC/INF_DIARIO`, `FI/DOC/CDA`, `FI/DOC/LAMINA`,
`FI/CAD`, … When implementing or updating a **reader**, ground its `FileContract` in the real
downloaded artifact from the relevant dataset page (per "Standing decisions" in the sweep ledger).

The portal holds far more than is implemented; a standing task (issue **#41**) is to survey it
once the current ingestion backlog is cleared and decide what else is worth scraping.

### Two macro-sections — every solution lives in one of them

- **`submission/` (envio → CVM)** — build, validate, and serialise a document to a
  CVM-compliant file *to send* to CVM. Takes schema models (or a filled spreadsheet) → XML.
- **`ingestion/` (leitura ← CVM)** — parse and interpret a file *received/downloaded* from
  CVM back into typed models / DataFrames.

The **shared, direction-neutral schema** (Pydantic models mirroring each XML standard) lives
under `_internal/config/schemas/<standard>.py`; both sections import it. `submission/` and
`ingestion/` re-export the public names consumers need.

Each section's classes implement a private **port** (hexagonal ports-and-adapters) in
`_internal/config/ports/`: submission writers are `SubmissionWriter[TDoc]` adapters exposing
`export(doc, output_path)`; ingestion readers are `IngestionReader` adapters exposing
`read() -> pd.DataFrame`. The ports are ABCs (`ABCTypeCheckerMeta`) and stay private — consumers
import the concrete writers/readers, never the port. An `ingestion` reader of a CVM open-data
CSV consumes a **different artifact** from the same standard's submission XML, so it declares its
own `FileContract` rather than reusing the submission Pydantic schema.

**Every ingestion reader takes an optional `path_raw: Path | None = None`** at construction.
`None` → the artifact is fetched into a `TemporaryDirectory` and destroyed on exit, so nothing
persists (note: the read still transiently touches disk and needs a writable temp dir — it is not
a zero-disk read); a path → the untouched raw artifact (`.zip`, `.csv`, `.html`, `.xlsx`, …) is
written there and **kept**, before any parsing. This is the reading-side mirror of the writers' `output_path`. It is
implemented once by the shared `_internal/utils/raw_workspace.py` context manager — never
re-branch on the tempdir inside a reader. Keeping the raw bytes is what makes a downstream
datalake's bronze layer authoritative: when CVM changes a data contract and a transform breaks,
the exact bytes that broke it stay on disk, replayable, instead of being lost to a re-fetch of an
already-changed source.

### Catalog (status: ✅ implemented · ⬜ pending)

Status marks the `submission` direction unless noted; `ingestion` is tracked as it grows.

**Fundos**
- Informe Diário — ✅ **V4** (`PadraoXMLInfoDiarioNetV4.asp`) — `submission/informe_diario.py` (`InformeDiario`); schema `_internal/config/schemas/informe_diario.py` · ✅ **ingestion** FIF open-data CSV — `ingestion/fi/doc/informe_diario.py` (`InformeDiarioReader`); contract `_internal/config/contracts/informe_diario_fif.py` · ⬜ V3 (`PadraoXMLInfoDiarioNetV3.asp`) · V2 (`PadraoXMLInfoDiarioNet739.asp`) · V1 (`PadraoXMLInfoDiarioNet.asp`)
- ⬜ Informe de Fundo 157 (`PadraoXMLInf157.asp`)
- ⬜ Informe Sintético — FCCE (`PadraoXMLSintFCCE.asp`) · FITVM/FMP-FGTS CL/FIIM (`PadraoXMLSintFITVM.asp`) · FIC-FITVM (`PadraoXMLSintFIC.asp`) · FMP-FGTS/FMAI (`PadraoXMLSintOutros.asp`)
- Demonstrativo de Composição e Diversificação das Aplicações (CDA) — ✅ **ingestion** FIF open-data CSV — `ingestion/fi/doc/cda.py` (`CdaReader`); contract `_internal/config/contracts/cda_fif.py` · ⬜ **submission** V2 (`PadraoXMLCDANet.aspx`) · V3 (`PadraoXMLCDANetV3.aspx`) · V4 (`PadraoXMLCDANetV4.aspx`)
- ⬜ Demonstrativo de Fontes e Aplicações de Recursos — FAR (`PadraoXMLFAR.asp`)
- ⬜ Balanço (`PadraoXMLBalanco.asp`)
- ⬜ Balancete (`PadraoXMLBalancete.asp`)
- ⬜ Informe Quadrimestral V2 (`PadraoXMLInfoTrimV2.asp`, antigo Informe Trimestral) · Informe Trimestral V1 (`PadraoXMLInfoTrim.asp`)
- Informe Mensal FIDC — ✅ **ingestion** FIDC open-data dump (`inf_mensal_fidc_AAAAMM.zip`, **17
  membros**: Tabelas I–X + sub-tabelas X.1/X.1.1/X.2…X.7) — `ingestion/fidc/doc/inf_mensal/*`
  (`InfMensalFidcTab*Reader`, base privada `_base_inf_mensal_fidc_reader.py`); contracts
  `_internal/config/contracts/inf_mensal_fidc.py`. Inaugura o portal root `fidc/` (irmão de `fi/`)
  · ⬜ **submission** até 2019-11-01 (`PadraoXMLMensalFIDC489.asp`) · a partir de 2019-11-01 (`PadraoXMLMensalFIDC576.asp`)
- Cadastro de Fundos (CAD/FI) — **open-data only, sem padrão XML de envio** — ✅ **ingestion**
  snapshot `cad_fi.csv` — `ingestion/fi/cad/cadastro_fi.py` (`CadastroFiReader`); contract
  `_internal/config/contracts/cad_fi.py`. Sem `date_ref` (retrato do estado atual) e **sem chave
  única** (o CNPJ se repete entre regimes) · ✅ **ingestion** `cad_fi_hist.zip` (log de alterações,
  19 membros/atributos) — `ingestion/fi/cad/cad_fi_hist/cad_fi_hist_*.py` (`CadastroFiHist*Reader`, base privada
  `_base_cad_fi_hist_reader.py`); contracts em `_internal/config/contracts/cad_fi_hist.py`
  · ✅ **ingestion** `registro_fundo_classe.zip` (cadastro pós-RCVM 175, onde estão os fundos vivos) —
  `ingestion/fi/cad/registro/registro_fundo.py`, `registro_classe.py`, `registro_subclasse.py`
  (`RegistroFundoReader`, `RegistroClasseReader`, `RegistroSubclasseReader`); contracts
  `_internal/config/contracts/registro_{fundo,classe,subclasse}.py`

**Fundos Imobiliários (FII)** — portal root `fii/`; **open-data only** (a CVM não publica padrão XML
de envio para estes informes). O portal tem 4 datasets sob `FII/DOC/`:
- Informe Mensal FII — ✅ **ingestion** `inf_mensal_fii_AAAA.zip` (**3 membros**: `geral`,
  `ativo_passivo`, `complemento`) — `ingestion/fii/doc/inf_mensal/*` (`InfMensalFii*Reader`, base
  privada `_base_inf_mensal_fii_reader.py`); contracts `_internal/config/contracts/inf_mensal_fii.py`.
  Inaugura o portal root `fii/`. ⚠️ **Particionado por ANO** (`_AAAA`), apesar de mensal — o
  `date_ref` seleciona o ano
- ⬜ **ingestion** DFIN (`dfin_fii_AAAA.csv`, índice das demonstrações financeiras) — issue #57
- ⬜ **ingestion** Informe Trimestral (`inf_trimestral_fii_AAAA.zip`, 16 membros) — issue #58
- ⬜ **ingestion** Informe Anual (`inf_anual_fii_AAAA.zip`, 12 membros) — issue #59

**Lâmina de Fundos**
- Lâmina — ✅ **ingestion** carteira FIF open-data CSV (`lamina_fi_carteira_*`, o membro de alocação
  por tipo de ativo do dump `lamina_fi_AAAAMM.zip`) — `ingestion/fi/doc/lamina/lamina_carteira.py`
  (`LaminaCarteiraReader`); contract `_internal/config/contracts/lamina_carteira_fif.py` ·
  ✅ **ingestion** lâmina proper (`lamina_fi_*`, 78 colunas) — `ingestion/fi/doc/lamina/lamina.py`
  (`LaminaReader`); contract `_internal/config/contracts/lamina_fif.py` ·
  ⬜ **ingestion** `rentab_ano_*` / `rentab_mes_*` (membros irmãos do mesmo ZIP) ·
  ⬜ **submission** V3 (`PadraoXMLLaminaV3.asp`) · V2 (`PadraoXMLLaminaV2.asp`) · V1 (`PadraoXMLLamina.asp`)

**Perfil Mensal e Extrato das Informações sobre o Fundo**
- ✅ **Perfil Mensal — V4** (`PadraoXMLPerfilV4.asp`) — `submission/perfil_mensal.py` (`PerfilMensal`); schema `_internal/config/schemas/perfil_mensal.py`
- ⬜ Perfil Mensal — V3 (`PadraoXMLPerfilV3.asp`) · 739 (`PadraoXMLPerfil739.asp`) · original (`PadraoXMLPerfil.asp`)
- ⬜ Extrato das Informações sobre o Fundo — V3 (`PadraoXMLInfExtratoV3.asp`) · V2 (`PadraoXMLInfExtratoV2.asp`) · V1/450 (`PadraoXMLInfExtrato450.asp`)

**Auditores**
- ⬜ Informe Anual de Auditor (`PadraoXMLAuditorAnual.asp`)

**Investidores Não Residentes**
- ⬜ Informe Mensal de Investidor não Residente (`PadraoXMLInfoMensalINR.asp`)
- ⬜ Informe Semestral de Investidor não Residente (`PadraoXMLInfoSemestralINR.asp`)

**Mercados de Negociação**
- ⬜ Atualização do Cadastro de Ativos (`PadraoXMLAtivos.asp`)

**Escriturador de Valores Mobiliários**
- ⬜ Informe Art. 12 Resolução CVM 33 (`PadraoXMLPrest.asp`)
- ⬜ Informe de Portabilidade (`PadraoXMLInfoPortabilidade.asp`)

## Layout

```
src/filings_cvm/
    __init__.py            # the public API surface (control it with __all__)
    submission/            # envio → CVM: SubmissionWriter adapters (validated model → XML)
    ingestion/             # leitura ← CVM: IngestionReader adapters (CVM file → typed DataFrame)
                           #   nested by CVM portal path (dados/<ROOT>/…); __init__ FLAT public API
        fi/                #   FI/ — Fundos de Investimento (one portal root; FIDC/, FII/, … as siblings)
            doc/           #     FI/DOC/* — informe_diario, cda, lamina/ (lamina + lamina_carteira)
            cad/           #     FI/CAD — cadastro_fi, registro/ (fundo/classe/subclasse),
                           #       cad_fi_hist/ (19 change-log readers + private base)
        fidc/              #   FIDC/ — inf_mensal/ (17 table readers + private base)
        fii/               #   FII/ — inf_mensal/ (3 readers + private base); DFIN/trimestral/anual pending
    _internal/             # PRIVATE — ships in the wheel, but not a public API
        utils/             # vendored helpers (dtypes, tabular_reader, retry, http_downloader,
                           #   text, zip_extractor, br_identifiers, typing/)
        config/            # private structural declarations (shapes + interfaces, not machinery)
            contracts/     # FileContract declarations (one per input source)
            schemas/       # shared, direction-neutral Pydantic models (one per XML standard)
            ports/         # private behavioural ABCs (SubmissionWriter, IngestionReader)
tests/
    unit/  integration/  performance/
```

**Public vs private.** Consumers import `<project_name>` (your core). Everything under
`<project_name>._internal` is vendored support code: it ships inside the wheel (so imports
resolve after `pip install`), but the leading underscore marks it off-limits — keep it out
of your public `__all__`. The internal imports are package-qualified
(`from <project_name>._internal.utils.dtypes import …`).

## Architecture

- **One public class per module/file.** The public class is named after the file
  (`user_service.py` → `UserService`). When helpers share no state and need no lifecycle,
  prefer **module-level functions** over a utility class. A private/shared base class gets
  its **own** `_`-prefixed file (`_base_reader.py`) — never share a module with a public
  class.
- **Separate I/O from logic**: pure functions in the core, side effects at the edges.
- Reach for a class only when there is **state + lifecycle**, **interface conformance**, or
  **dependency injection** — otherwise a module of functions is the right shape.
- **No redundant package-name subfolder.** When the package's whole purpose is one domain
  (e.g. `calendars`), do **not** nest a subfolder that repeats the package name
  (`src/<project_name>/<project_name>-ish/`) — the package name already conveys the scope. Keep
  public modules **flat** at `src/<project_name>/` (`src/<project_name>/calendar_br.py`), and put
  non-exported abstract bases / internals under `_internal/`.
- **On migration, reuse the target's own implementation.** When lifting code in from another
  repo, if this project already has an equivalent module (its own `_internal` typing engine, a
  helper), rewrite the imports to **this** project's version and discard the source's duplicate —
  never vendor a second copy (DRY). The scaffold's own `rewrite_internal_imports` embodies this.

## Conventions (inherited from `templates/python-common/`)

- **Ruff**: linter + formatter. Line-length 99, tab indent, double quotes, NumPy docstrings.
- **Pre-commit**: ruff, pydocstyle, codespell, commitizen, gitlint, unit + integration
  tests, coverage badge.
- **Gate parity — every lint/static/test gate lives in BOTH `.pre-commit-config.yaml` and
  `.github/workflows/tests.yaml`.** CI runs its gates as explicit steps (not `pre-commit run`),
  so adding a hook does not cover CI — add the matching step in the same commit, or a
  hook-skipping contributor (or branch-protection CI) bypasses it. Full rationale + canonical
  set + current open drift: `.github/CLAUDE.md` ("Gate parity").
- **Tests**: `pytest` — `make unit_tests` (`poetry run pytest tests/unit/`). Write
  pytest-style functions with fixtures, not `unittest.TestCase`.
- **Explicit column typing & Brazilian identifiers** — if the library touches pandas, type
  every DataFrame on load via `apply_dtypes` (`_internal.utils.dtypes`, never pandas'
  inference), route reads through `_internal.utils.tabular_reader`, and use
  `_internal.utils.br_identifiers` for CNPJ/CPF (alphanumeric-aware for the 2026 CNPJ).
- **Every ingested DataFrame is provenance-stamped.** A reader's returned frame carries, beside
  its source columns, the six `FileContract.PROVENANCE_COLUMNS` — `url`, `updated_at` (tz-aware
  UTC collection time), `source_key`, `package_version`, `ingestion_run_id`, `content_hash` —
  appended by the shared `_internal.utils.provenance.stamp_provenance` seam **after** contract
  validation (they are not in `tuple_required`; the source lacks them). `updated_at` stays
  tz-aware — a SQL sink that needs naive normalises at the warehouse load, never here. This is
  enforced structurally: `bin/check_provenance.py` (pre-commit + CI) fails any `src/` module that
  calls `read_table` without also calling `stamp_provenance`, so the contract read and the stamp
  ship together.
- **No `.env`** — a distributable library has no runtime env to seed (unlike the service
  tiers), so none is shipped.
- **Logging via dependency injection** — never hard-import a logging backend in a helper;
  inject a logger (stdlib default), as `_internal/utils/retry.py`'s `LogEmitter` shows. The
  in-repo `logs.py` helper is **opt-in** at scaffold time; see `_internal/utils/CLAUDE.md`.
- **Every imported package is a direct dependency.** If a module `import`s a package, declare
  it in `pyproject.toml` — even when it is already installed transitively via another dep. A
  transitive presence is an accident of another package's tree and breaks silently the day that
  package drops or version-caps it. Run `poetry add <pkg>` for anything you import.
- **Runtime type checking is mandatory everywhere in `src/`.** It complements — does not replace
  — ruff `ANN` + mypy: static checks miss what crosses runtime boundaries (deserialised data, DB
  rows), so honest signatures become enforced contracts that fail loudly. The rule is uniform, no
  by-layer and no public/private exemption: **every class** under `src/` declares a checker
  metaclass from `_internal.utils.typing` (`metaclass=TypeChecker`; `ABCTypeCheckerMeta` for ABCs,
  `ProtocolTypeCheckerMeta` for Protocols), and **every standalone function** uses `@type_checker`
  — private (`_`-prefixed) helpers included. The only exclusions:
  - **Pydantic `BaseModel` subclasses** — Pydantic owns the metaclass (conflict at import) and
    already validates at construction, so never add `metaclass=TypeChecker` to a model.
  - **The typing engine itself** (`_internal/utils/typing/`) — it is the machinery.
  - **Dunders** (`__x__`) — the `TypeChecker` metaclass leaves them untouched, so the hook
    skips them too; single-underscore private names are **not** exempt.
  - Metaclasses are **inherited**, so only a hierarchy root declares it — a subclass of a
    checker-metaclass class (e.g. `LogsEmitter(LogEmitter)`) is already checked.

  The `check-typing` pre-commit hook (`bin/check_typing.py`) enforces this across all of `src/`.

## Releasing to PyPI

Two workflows ship under `.github/workflows/` (present only when a GitHub remote is set up):

- `release-test-pypi.yaml` — publish to **Test PyPI** first (`workflow_dispatch`).
- `release-pypi.yaml` — publish to **PyPI** and cut a GitHub release.

Both gate on the version being greater than what is already published, build with Poetry,
and fall back to `twine` if `poetry publish` is unavailable. Configure these repository
secrets and a GitHub Environment named **`release`**:

- `PYPI_TOKEN` — a PyPI API token.
- `TEST_PYPI_TOKEN` — a Test PyPI API token.

## Extending this template

- Keep `src/<project_name>/` as the importable package root; grow the public API there.
- Add sub-packages as the project grows — do not dump everything into `main.py`.
- Mirror the test folder hierarchy to match the package structure.
- Drop `_internal/config/contracts` (and the pandas deps) if the library never reads
  tabular inputs.
