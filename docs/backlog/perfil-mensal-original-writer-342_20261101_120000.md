# Perfil Mensal original writer (#342)

- [x] Fetch `PadraoXMLPerfil.asp` and diff against V4: 53-tag sample vs 92, 36 tag names in common, 14-tag `NR_CLIENT`/`DISTR_PATRIM` with `_NAC` suffixes, own row body, no `VERSAO` in the header.
- [x] Schema `perfil_mensal_original.py` (own blocks, `PercentField` reused from V4) and writer `PerfilMensalOriginal` (generic model walk, `atomic_write_bytes`, windows-1252).
- [x] Unit tests: tag order typed from the page sample, no `VERSAO`, scales, rejections, windows-1252 file output.
- [x] Docs page, mkdocs nav, api.md, index.md, README, CLAUDE.md catalog.
- [ ] Follow-up: V4 `AvgTermField` / `VarPercentPlField` use `Field(max_digits=...)`, which pydantic evaluates after dropping trailing zeros and which has no separate integer bound, so `12345.0` passes `max_digits=8`. Out of scope here (V4 writer behaviour); worth its own issue.

Open note: the page's tag table says `CNPJ_FUNDO`, its XML sample says `CNPJ_FDO`; the writer follows the sample (as V4 does).
