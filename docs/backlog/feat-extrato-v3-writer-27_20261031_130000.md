# Work ledger — #27 Extrato V3 submission writer

Branch `feat/extrato-v3-writer-27`. Spec: `PadraoXMLInfExtratoV3.asp` (fetched 2026-10-31).

- [x] Confirmed no Extrato writer on `origin/main` (only the ingestion contracts).
- [x] Schema `_internal/config/schemas/extrato.py` (models only; validators in `_internal/utils/xml_fields.py`).
- [x] Writer `submission/extrato.py` (`Extrato`, encodes to bytes before touching the target file, 1 MB cap).
- [x] Names registered in `submission/__init__.py` and `schemas/__init__.py` (sorted `__all__`).
- [x] Unit tests: XML of every block, every rule below, failed export leaves target intact.
- [x] `docs/submission/extrato.md`, `mkdocs.yml` nav, `docs/api.md`, `CLAUDE.md` catalog.
- [ ] PR (`Closes #27`).

## What the page leaves unsettled (stated on the docs page and in the PR)

- The page holds two generations of the form. The sample file is followed for structure; the tag list supplies optionality and code tables. Tags only in the tag list (`COTA_MERC_SECUND`, `COTISTA_EXCV`, `SERV_ATEND_COTISTA`, `LIM_*`, ...) are not modelled.
- Namespace: sample `urn:extr`, tag list `urn:perf`. Used `urn:extr`.
- CNPJ tag: sample `CNPJ_FDO`, tag list `CNPJ_FUNDO`. Used `CNPJ_FDO`; the CNPJ is sent as 14 bare characters (leading zeros kept, since dropping them would corrupt it).
- Exit fee: the sample reuses the tag `TP_VL_FIXO_TX_INGRESSO` inside `TX_SAIDA`. Emitted as written.
- Investment policy code: table C lists 1-3, the questionnaire adds 4 (Enhanced). Accepted 1-4.
- `LISTA_MERC_BLOQUEIO`: modelled as one market code 1-4.
- Performance-fee detail depends on the investor (tag list); the sample says all fields mandatory. Followed the tag list.
- Decimal scales: 2 places where the page says so (limits, minimum application, credit limit), 6 for custody fee, otherwise percentages 4 places; truncated toward zero, `float` refused.
- Day counts and free-text bounds not stated: days 0-9999, `PRAZO_ATUALIZACAO` 1-200 characters.
- No CVM validator (the page links a syntax tester) was run.
