# Work ledger — #19 Informe Sintético submission writers

Branch `feat/informe-sintetico-writer-19`. Specs fetched 2026-10-31: `PadraoXMLSint{FCCE,FITVM,FIC,Outros}.asp`.

- [x] Confirmed no Informe Sintético writer on `origin/main`; surface posted on the issue.
- [x] Schema `_internal/config/schemas/informe_sintetico.py` (models only), one block set per variant.
- [x] `_internal/utils/xml_fields.py` copied verbatim from #291 (identical file, so the merge is a no-op whichever lands first).
- [x] Writers `submission/informe_sintetico_{fcce,fitvm,fic,outros}.py` over private `_informe_sintetico_xml.py` (bytes encoded before the target is opened).
- [x] Names registered in `submission/__init__.py` (sorted `__all__`).
- [x] Unit tests: tag order typed from each spec sample, values per tag, validation rules.
- [x] `docs/submission/informe_sintetico.md`, nav, `docs/api.md`, `CLAUDE.md` catalog.
- [ ] PR (`Closes #19`).

## What the pages leave unsettled (stated on the docs page and in the PR)

- `VL_QUOTA_ULT_DIA_MES` "(decimal)" with no scale: money policy, 2 places, truncated. A quota usually has more places.
- FIC page: tag list omits `VL_QUOTA_ULT_DIA_MES`, sample has it. Followed the sample.
- Outros page: tag list omits the `APLICACOES`/`OUTRAS` wrappers, sample has them. Followed the sample.
- CNPJ: "zeros a esquerda devem ser omitidos" taken literally on output.
- Negative values: only `PATRIM_LIQ` may be negative (assumption).
- No CVM validator was run.
