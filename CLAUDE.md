# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this template is

A **PyPI-ready Python library starter**. A clean, importable package with CI, pre-commit,
tests, docs, and PyPI + Test-PyPI release workflows ready to go. It is scaffolded by
BlueprintX into a new project directory; the scaffold replaces the `<project_name>` package
directory and the `pyproject.toml` placeholders via `envsubst`.

## CVM XML Standards — Source of Truth

The library implements the CVM regulatory file standards. **The single source of truth for
every standard, version, and its official spec is the CVM catalog page:**

> https://cvmweb.cvm.gov.br/SWB/Sistemas/SCW/PadroesXML/PadroesXML.asp

Each entry below links to a `PadraoXML*.asp` page (relative to that base URL) describing one
XML standard. When implementing or updating a standard, treat the linked CVM page as
authoritative — field names, decimal scales, and cardinalities come from there, not from
this file.

### Two macro-sections — every solution lives in one of them

- **`submission/` (envio → CVM)** — build, validate, and serialise a document to a
  CVM-compliant file *to send* to CVM. Takes schema models (or a filled spreadsheet) → XML.
- **`ingestion/` (leitura ← CVM)** — parse and interpret a file *received/downloaded* from
  CVM back into typed models / DataFrames.

The **shared, direction-neutral schema** (Pydantic models mirroring each XML standard) lives
under `_internal/schemas/<standard>.py`; both sections import it. `submission/` and
`ingestion/` re-export the public names consumers need. `ingestion/` is created when its
first reading pattern lands (not scaffolded empty).

### Catalog (status: ✅ implemented · ⬜ pending)

Status marks the `submission` direction unless noted; `ingestion` is tracked as it grows.

**Fundos**
- Informe Diário — ✅ **V4** (`PadraoXMLInfoDiarioNetV4.asp`) — `submission/informe_diario.py` (`InformeDiario`); schema `_internal/schemas/informe_diario.py` · ⬜ V3 (`PadraoXMLInfoDiarioNetV3.asp`) · V2 (`PadraoXMLInfoDiarioNet739.asp`) · V1 (`PadraoXMLInfoDiarioNet.asp`)
- ⬜ Informe de Fundo 157 (`PadraoXMLInf157.asp`)
- ⬜ Informe Sintético — FCCE (`PadraoXMLSintFCCE.asp`) · FITVM/FMP-FGTS CL/FIIM (`PadraoXMLSintFITVM.asp`) · FIC-FITVM (`PadraoXMLSintFIC.asp`) · FMP-FGTS/FMAI (`PadraoXMLSintOutros.asp`)
- ⬜ Demonstrativo de Composição e Diversificação das Aplicações (CDA) — V2 (`PadraoXMLCDANet.aspx`) · V3 (`PadraoXMLCDANetV3.aspx`) · V4 (`PadraoXMLCDANetV4.aspx`)
- ⬜ Demonstrativo de Fontes e Aplicações de Recursos — FAR (`PadraoXMLFAR.asp`)
- ⬜ Balanço (`PadraoXMLBalanco.asp`)
- ⬜ Balancete (`PadraoXMLBalancete.asp`)
- ⬜ Informe Quadrimestral V2 (`PadraoXMLInfoTrimV2.asp`, antigo Informe Trimestral) · Informe Trimestral V1 (`PadraoXMLInfoTrim.asp`)
- ⬜ Informe Mensal FIDC — até 2019-11-01 (`PadraoXMLMensalFIDC489.asp`) · a partir de 2019-11-01 (`PadraoXMLMensalFIDC576.asp`)

**Lâmina de Fundos**
- ⬜ Lâmina — V3 (`PadraoXMLLaminaV3.asp`) · V2 (`PadraoXMLLaminaV2.asp`) · V1 (`PadraoXMLLamina.asp`)

**Perfil Mensal e Extrato das Informações sobre o Fundo**
- ✅ **Perfil Mensal — V4** (`PadraoXMLPerfilV4.asp`) — `submission/perfil_mensal.py` (`PerfilMensal`); schema `_internal/schemas/perfil_mensal.py`
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
src/<project_name>/
    __init__.py            # the public API surface (control it with __all__)
    main.py                # library core / entry point — rename or split as it grows
    _internal/             # PRIVATE — ships in the wheel, but not a public API
        utils/             # vendored helpers (dtypes, tabular_reader, retry, http_downloader,
                           #   text, zip_extractor, br_identifiers, typing/)
        config/
            contracts/     # FileContract declarations (one per input source)
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
- **Tests**: `pytest` — `make unit_tests` (`poetry run pytest tests/unit/`). Write
  pytest-style functions with fixtures, not `unittest.TestCase`.
- **Explicit column typing & Brazilian identifiers** — if the library touches pandas, type
  every DataFrame on load via `apply_dtypes` (`_internal.utils.dtypes`, never pandas'
  inference), route reads through `_internal.utils.tabular_reader`, and use
  `_internal.utils.br_identifiers` for CNPJ/CPF (alphanumeric-aware for the 2026 CNPJ).
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
