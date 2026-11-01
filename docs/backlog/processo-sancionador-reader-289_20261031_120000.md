# Work ledger — Processo Sancionador reader (#289)

- [x] Measure `processo_sancionador.zip` (2 members, ISO-8859-1, `;`, CRLF, snapshot) and the META zip
- [x] No CNPJ/CPF column in either member; `Nome_Acusado` is PII, so header-only fixtures
- [x] Contracts generated from the real headers and pinned to verbatim fixtures
- [x] Readers `ProcessoSancionadorReader`, `ProcessoSancionadorAcusadoReader`, `MetaProcessoSancionadorReader`; new root `processo/`
- [x] Registered in `ingestion/__init__.py`, contracts `__init__`, `_META_MEMBERS`, `_IMPLEMENTED_PACKAGES` (`processo-sancionador`)
- [x] Re-measured counts from code: 23 roots, 293 readers, 49 META readers (19 txt + 30 zip, 49 contracts)
- [x] Docs page, nav, api.md, index.md, meta.md, CLAUDE.md catalog and layout
- [x] Unit tests; real artifact read end to end with the download mocked to the real bytes (581 + 2070 rows)
- [ ] PR merged (orchestrator); counts conflict with #282/#283/#287/#288 resolved at merge
