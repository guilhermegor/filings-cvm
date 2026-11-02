# Perfil Mensal ICVM 739 writer (#343)

Branch `feat/343-perfil-mensal-739-writer`. Spec: `PadraoXMLPerfil739.asp` (fetched 2026-11-01).

- [x] Confirmed no 739 writer on `origin/main` (only the catalog line in CLAUDE.md).
- [x] Fetched the 739, V3 and V4 pages and diffed tag sample, tag table and question table.
- [x] Schema `perfil_mensal_739.py` reusing V4 models; writer `PerfilMensal739` reusing the V4 serializer.
- [x] V4 writer: the sensitivity scale became a class attribute (`_sensitivity_places`, default 4).
- [x] Unit tests: exact page tag order, VERSAO, 2-decimal tags, mandatory block, absent tags, cp1252.
- [x] Docs page, api/index/README/mkdocs/CLAUDE.md catalog.
- [ ] PR (`Closes #343`).

## Measured on the page (739 vs V3 and V4)

- XML sample tag order: identical to V3/V4 except the sample ends at `VAL_COTA_FUNDO` (no `MONTANTE_DISTRIB`, no `INF_COMPL_PERFIL`).
- `VERSAO` is `1.0`; `COD_DOC` 40; namespace `urn:perf`; encoding windows-1252.
- Q13-Q16 and `VAL_PERCENT_OUTROS`: two decimals (V3/V4: four).
- `DISTR_PATRIM`: mandatory, as in V3.
- The tag table says `CNPJ_FUNDO`, the sample says `CNPJ_FDO`; the writer follows the sample.
- No CVM validator was run.

## Review follow-up (CodeRabbit, 2026-11-02)

- [x] `COD_DOC` pinned to 40: new `PerfilMensal739Header` (`cod_doc: Literal[40]`), so `cod_doc=7` is refused at construction.
- [x] XML-forbidden control characters (NUL etc.) refused at export, in the shared V4 writer's `_escape`, so V4 and 739 are both covered.
