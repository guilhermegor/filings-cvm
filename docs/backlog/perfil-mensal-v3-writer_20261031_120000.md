# Perfil Mensal V3 writer (#344)

- [x] Fetch `PadraoXMLPerfilV3.asp` and diff against V4 (91-tag sample sequence identical; only `VERSAO` value differs; `DISTR_PATRIM` mandatory in V3).
- [x] Schema `perfil_mensal_v3.py` reusing V4 models; writer `PerfilMensalV3` reusing the V4 serializer.
- [x] Unit tests pinned to the page's tag order and PR_* scale.
- [x] Docs page, api/index/README/mkdocs/CLAUDE.md catalog.
- [ ] Output is written the V4 way (`write_text`); migrate to `atomic_write_bytes` once PR #330 lands.

Open note: the V3 tag table says `CNPJ_FUNDO`, the XML sample says `CNPJ_FDO`; the writer follows the sample.
