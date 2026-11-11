## Unreleased

### BREAKING CHANGE

- **rename**: the import package is now `opendata_cvm` (was `filings_cvm`) and the family name
  is `opendata-*` (#418). There is no compatibility shim: `import filings_cvm` no longer works;
  use `import opendata_cvm`. Every runtime string that embedded the old package name (logger
  names, cache directories, user-agent) follows the rename.

- **submission**: the whole submission section is removed (#389) — `opendata_cvm.submission`
  (all 15 XML writers and their document models), the Pydantic schemas, the `SubmissionWriter`
  port, the atomic-write and XML field helpers and the submission docs. It lives on in the
  separate `layouts-cvm` package; there is no shim, no re-export and no dependency on it.
  Migration: `from opendata_cvm.submission import X` becomes `from layouts_cvm import X`
  (e.g. `from layouts_cvm import PerfilMensal, InformeDiario`; `pip install layouts-cvm`).
  Document-model migration guide: <https://guilhermegor.github.io/layouts-cvm/>.
  The `pydantic` dependency is dropped.

### Feat

- **ingestion**: FII INF_ANUAL readers (12 members) — fii/ root complete (#63)
- **ingestion**: FII INF_TRIMESTRAL readers (16 members) (#62)
- **ingestion**: FII DFIN index reader (#61)
- **ingestion**: FII INF_MENSAL readers (3 members) — launch fii/ portal root (#60)
- **ingestion**: FIDC INF_MENSAL open-data readers (17 members) (#54)
- **retry**: recover per-reader RetryPolicy + downloader wiring (post-#49) (#50)
- **retry**: pluggable backoff strategy (linear/constant) + wait cap (#49)
- **ingestion**: stamp provenance columns, enforced with read_table (#47)
- **ingestion**: CAD/FI histórico readers (19 change-logs) (#43)
- **ingestion**: Registro RCVM 175 readers (fundo, classe, subclasse) (#40)
- **ingestion**: Cadastro de Fundos (CAD/FI) reader (#38)
- **ingestion**: Lâmina FIF fact-sheet reader (#37)
- **ingestion**: Lâmina carteira FIF reader (#36)
- **ingestion**: CDA FIF reader + raw-artifact persistence seam (#35)
- **ingestion**: add Informe Diário FIF reader and section ports (#34)
- **submission**: Informe Diário V4 XML writer (#3)
- **submission**: Perfil Mensal XML writer + submission/ingestion sections (#1)
- first commit

### Fix

- gerar e versionar coverage.svg para o badge do README (#17)

### Refactor

- **ingestion**: per-module _RETRY_POLICY for every reader (#55)
- **ingestion**: nest readers by CVM portal path (option A) (#48)
- **_internal**: consolidate ports and schemas under config/ (#39)
