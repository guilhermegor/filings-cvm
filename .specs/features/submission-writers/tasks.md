## cadastro-ativos-writer-31_20261031_120000

# Cadastro de Ativos submission writer (#31)

Spec: `PadraoXMLAtivos.asp` (`COD_DOC=2`, no namespace, windows-1252).

- [x] Read the CVM page and derive the tag tree, tables 1/2 and cardinalities
- [x] Schema `_internal/config/schemas/cadastro_ativos.py`
- [x] Writer `submission/cadastro_ativos.py`
- [x] Unit tests `tests/unit/test_cadastro_ativos_submission.py`
- [x] Re-export from `submission/__init__.py` (sorted `__all__`)
- [x] `docs/submission/cadastro_ativos.md`, mkdocs nav, `docs/api.md`, CLAUDE.md catalog
- [ ] Merge `origin/main`, push, open PR (`Closes #31`)

## cda-v4-writer-20_20261030_202420

# CDA V4 submission writer (#20)

- [x] Read the CVM spec page (PadraoXMLCDANetV4.aspx) — tags, scales, Tables A-D, F
- [x] Schema `_internal/config/schemas/cda.py` (Pydantic, Decimal scales, Table A/B rules)
- [x] Writer `submission/cda.py` (`Cda`), re-exports in `submission/__init__.py`
- [x] Tests `tests/unit/test_cda_submission.py` (serialisation + negative cases)
- [x] Docs `docs/submission/cda.md`, `mkdocs.yml` nav, root `CLAUDE.md` catalog line
- [ ] Open: Table E (swap codes), G (countries) and H (exchanges) are not enumerated; only
  the `SWP`+3 shape is checked for COD_SWAP
- [ ] Open: QTDE_DIAS_CONFID cap is 90; the 30-day cap for "curto prazo"/"referenciado"
  classes needs the fund class, which the document does not carry
- [ ] Open: V3/V2 writers remain pending
- [x] PR #277 review: encode-before-open + cp1252/XML-legal text, real-calendar dates, float
  refusal (VALOR_AT_EXT kept exact: page gives no scale), SWAP MERC_POS_FIM nested in POS_FIM,
  ATIVO_EXT only in INV_EXT, empty NEGOC and negative traded quantities rejected, fullmatch
  regexes, XML tests for TIT_PUB/COTAS/DEP_PRAZO_TIT_IF/TIT_AGRO_CRED_PRIV/INV_EXT/SWAP
- [ ] Open (page silent): TP_NEGOC rules vs Table F, max length of code fields, empty
  LISTA_INFORM/LISTA_ATIV

## feat-extrato-v3-writer-27_20261031_130000

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

## feat-inf-fundo-157-writer-18_20261031_130000

# Work ledger — #18 Informe de Fundo 157 submission writer

Branch `feat/inf-fundo-157-writer-18`. Spec: `PadraoXMLInf157.asp` (fetched 2026-10-31).

- [x] Confirmed no writer on `origin/main`; file surface appended to the issue.
- [x] Schema `_internal/config/schemas/inf_fundo_157.py` (models only; validators in `xml_fields.py`, copied verbatim from PR #291 so the two merge cleanly).
- [x] Writer `submission/inf_fundo_157.py` (encodes to bytes before touching the target file).
- [x] Names registered (sorted `__all__`), 29 unit tests.
- [x] Docs page, nav, `api.md`, `CLAUDE.md` catalog.
- [x] PR #301 (`Closes #18`).
- [x] Review: `cotistas` made a tuple (a list could be cleared past `min_length`), two test
  names made descriptive, docs state the alphanumeric CNPJ shape apart from the CPF one.

## Assumptions (stated on the docs page and in the PR)

- `DT_FIM` format not stated: `DD/MM/AAAA`.
- `COTST` cardinality not stated: at least one, no ceiling.
- CPF: 11 digits plus check digits. No decimals on the page.
- No CVM validator was run.

Completed — kept as a record.

## feat-informe-quadrimestral-v2-writer-24_20261031_130000

# Work ledger — #24 Informe Quadrimestral V2 submission writer

Branch `feat/informe-quadrimestral-v2-writer-24`. Spec: `PadraoXMLInfoTrimV2.asp` (fetched 2026-10-31).

- [x] Confirmed no Informe Quadrimestral writer on `origin/main`.
- [x] File surface appended to the issue.
- [x] Schema `_internal/config/schemas/informe_quadrimestral.py` (models only).
- [x] Writer `submission/informe_quadrimestral.py` (encodes to bytes before touching the target).
- [x] Validators `_internal/utils/xml_fields.py` (copied verbatim from #291; identical content merges cleanly).
- [x] Unit tests for every block and rule.
- [x] Docs page, nav, api.md, index.md, CLAUDE.md catalog.
- [ ] PR (`Closes #24`).

## What the page leaves unsettled (stated on the docs page and in the PR)

- Text bans zero fillers but Tabela I prints `001`..`015`: used 3-digit codes.
- Decimal shape is stated (12 integer / 8 decimal digits): 8 places, truncated toward zero.
- The two list blocks are not marked mandatory: treated as mandatory, at least one item.
- Totals are not reconciled with the items (relation not defined by the page).
- No CVM validator was run.

## feat-lamina-v3-writer-26_20261031_120000

# Work ledger — #26 Lâmina V3 submission writer

Branch `feat/lamina-v3-writer-26`. Spec: `PadraoXMLLaminaV3.asp` (fetched 2026-10-31).

- [x] Confirmed no Lâmina writer on `origin/main` (only the ingestion contracts).
- [x] Schema `_internal/config/schemas/lamina.py` (models only; validators in `_internal/utils/xml_fields.py`).
- [x] Writer `submission/lamina.py` (`Lamina`, encodes to bytes before touching the target file).
- [x] Names registered in `submission/__init__.py` and `schemas/__init__.py` (sorted `__all__`).
- [x] Unit tests: XML of every block, every rule below, failed export leaves target intact.
- [x] `docs/submission/lamina.md`, `mkdocs.yml` nav, `docs/api.md`, `CLAUDE.md` catalog.
- [ ] PR (`Closes #26`).

## What the page leaves unsettled (stated on the docs page and in the PR)

- Namespace: the sample says `urn:lamina`, the tag list says `urn:infdiario` (copy-paste). Used `urn:lamina`.
- Monthly row tag: the sample says `MES`, the tag list says `MES_RENT`. Used `MES`.
- Every number is "float" with no scale: money 2 places, percentages 4, truncated toward zero.
- Subclass code: no format or length given; assumed 1 to 50 characters.
- Which blocks a fund under one year may omit is marked, but fund age is not in the file, so those
  blocks are optional and never enforced.
- No CVM validator (the page links a syntax tester) was run.

## inf-mensal-fidc-writer-25_20261030_120000

# Informe Mensal FIDC submission writer (#25)

Spec: `PadraoXMLMensalFIDC576.asp` (ICVM 576, from 2019-11-01; `urn:fidc`).

- [x] Read the CVM page and derive the tag tree, scales and cardinalities
- [x] Schema `_internal/config/schemas/inf_mensal_fidc.py` (SOMATORIO items 1-30 enforced)
- [x] Writer `submission/inf_mensal_fidc.py` (schema-driven, windows-1252)
- [x] Unit tests incl. negative cases
- [x] Re-export from `submission/__init__.py` (sorted `__all__`)
- [x] codespell: `passiv` (CVM tag PASSIV) added to ignore list
- [x] Merge `origin/main`; satisfy `check-schemas` and `check-docs-sections`
- [x] `docs/submission/inf_mensal_fidc.md` + `mkdocs.yml` nav
- [x] Root `CLAUDE.md` catalog: FIDC submission pending -> done
- [ ] Push, open PR (`Closes #25`)

## submission-atomic-write-298_20261031_120000

# Write every submission writer's output atomically (#298)

- [x] `_internal/utils/atomic_write.py`: temp file in the target directory, fsync, `os.replace`, cleanup on failure
- [x] Nine writers on main routed through it (cadastro_ativos, cda, extrato, inf_fundo_157, informe_quadrimestral, lamina, informe_diario, perfil_mensal, inf_mensal_fidc); bytes and windows-1252 encoding unchanged
- [x] `tests/unit/test_atomic_write.py`: success, failure keeps old file, no temp left, same-directory temp, guard sweeping every public writer module
- [x] `docs/api.md` notes atomic output
- [ ] Writers still in open PRs adopt `atomic_write_bytes` when they merge main (the guard test fails them until they do)

## atomic-write-mode-before-write-361_20261101_120000

# Work ledger — #361 `atomic_write_bytes` narrows the mode before writing, not after

Branch `fix/361-atomic-write-mode-before-write`. Fecha **#361**. **Release** (toca `src/`; fix → PATCH).

- [x] Teste vermelho primeiro: `test_atomic_write_bytes_never_exposes_payload_under_wider_mode`
  (destino `0o600`, umask `022`, modo do temp lido no `fsync`) falhava com `0o644`.
- [x] `atomic_write.py`: o modo do destino existente é lido antes do `os.open` e aplicado ao temp
  (`os.chmod`) antes de qualquer byte escrito; destino novo segue `0o666 & ~umask`, sem tocar o umask.
- [x] Docstring declara a garantia de permissão.
- [x] ruff, mypy e `tests/unit/test_atomic_write.py` verdes.
- [x] Completed — kept as a record.

## feat-informe-diario-v3-writer-337_20261031_140000

# Work ledger — #337 Informe Diário V3 submission writer

Branch `feat/337-informe-diario-v3-writer`. Spec: `PadraoXMLInfoDiarioNetV3.asp` (fetched 2026-10-31).

- [x] Page fetched and diffed against V4: only `VERSAO` 3.0 and no `COD_SUBCLASSE`.
- [x] Schema extends V4; writer is its own `SubmissionWriter` adapter delegating to the V4 writer's public `export` (composition, not a V4 subclass).
- [x] Tests, docs page, nav, api.md, index.md, README, CLAUDE.md.
- [ ] PR (`Closes #337`).

Note: the file write is atomic, inherited through the V4 writer's `atomic_write_bytes`.

## feat-informe-portabilidade-writer-33_20261031_130000

# Work ledger — #33 Informe de Portabilidade submission writer

Branch `feat/informe-portabilidade-writer-33`. Spec: `PadraoXMLInfoPortabilidade.asp` (fetched 2026-10-31).

- [x] Confirmed no Informe de Portabilidade writer on `origin/main`.
- [x] File surface appended to the issue body.
- [x] Schema `_internal/config/schemas/informe_portabilidade.py` (models only).
- [x] Writer `submission/informe_portabilidade.py` (`InformePortabilidade`, encodes to bytes before touching the target file).
- [x] Names registered in `submission/__init__.py` (sorted `__all__`).
- [x] Unit tests: XML of header and INFORM blocks against spec-typed tag lists, every rule below.
- [x] `docs/submission/informe_portabilidade.md`, `mkdocs.yml` nav, `docs/api.md`, `docs/index.md`, `CLAUDE.md` catalog.
- [ ] PR (`Closes #33`).

## What the page leaves unsettled (stated on the docs page and in the PR)

- No decimal field exists: every quantity is a request count, modelled as a strict non-negative
  `int` (no money/percentage scale needed).
- `DT_EVENT` ("mês das solicitações") has no stated format: assumed `MM/AAAA`, like `DT_COMPT`.
- Cardinality of `INFORM` is not stated: at least one, no upper bound.
- No relation between the counts (e.g. canceled <= requested) is stated, so none is enforced.
- No CVM validator (the page of the sibling standards links a syntax tester) was run.

## feat-informe-trimestral-v1-writer-338_20261101_000000

# Work ledger — #338 Informe Trimestral V1 submission writer

Branch `feat/338-informe-trimestral-v1-writer`. Spec: `PadraoXMLInfoTrim.asp` (fetched 2026-11-01).

- [x] Fetched the page (200); measured tags, scales, COD_DOC 51, VERSAO, 100-fund cap.
- [x] Schema `_internal/config/schemas/informe_trimestral_v1.py` (own models; V2 shares only the serialiser).
- [x] Writer `submission/informe_trimestral_v1.py` (reuses V2's serialiser; temp file + `os.replace`).
- [x] Unit tests, one assertion each.
- [x] Docs page, nav, api.md, index.md, CLAUDE.md catalog, registries.
- [ ] PR (`Closes #338`); #330 migrates the file write to `atomic_write_bytes`.

## What the page leaves unsettled (stated on the docs page and in the PR)

- Sample says `VERSAO` 1.0; the field note says 2.0 (V2 leftover): used 1.0.
- No integer width stated: 18 integer digits for decimals, 999999999999 for counts.
- Negative net worth not addressed: allowed.
- No CVM validator was run.

## feat-inr-mensal-writer-29_20261031_130000

# Work ledger — #29 Informe Mensal INR submission writer

Branch `feat/inr-mensal-writer-29`. Spec: `PadraoXMLInfoMensalINR.asp` (fetched 2026-10-31).

- [x] Confirmed no INR writer on `origin/main`.
- [x] Schema `_internal/config/schemas/inr_mensal.py` (models only; validators in `_internal/utils/inr_mensal_fields.py`).
- [x] Writer `submission/inr_mensal.py` (`InrMensal`, encodes to bytes before touching the target file).
- [x] Names registered in `submission/__init__.py` and `schemas/__init__.py` (sorted `__all__`).
- [x] Unit tests: XML of every block, every rule below, failed export leaves target intact.
- [x] `docs/submission/inr_mensal.md`, `mkdocs.yml` nav, `docs/api.md`, `CLAUDE.md` catalog.
- [ ] PR (`Closes #29`).

## What the page leaves unsettled (stated on the docs page and in the PR)

- Conflict: the notes say "vírgula separa casas decimais" but every amount is "numérico e inteiro".
  Chose whole numbers (`int`); a fractional value is refused, never truncated.
- Conflict: the sample shows `COD_DOC` 477 while the tag list says "deve ser 'XX'". Used 477.
- Sign of amounts is not stated: flows, transfers and notionals are non-negative; market value
  and net worth may be negative.
- `VL_NOCION_APLIC` is required for Tabela A codes 15-24 and refused otherwise (page: "APENAS").
- Participant code check digit: algorithm unpublished, checked only as one digit.
- Assumed: a participant code appears once per file; the `AAAAA` of every `COD_PARTIC` must equal
  `CD_CVM` (the page defines both as the representative's CVM code); empty optional containers are refused (the page says to omit them).
- No CVM validator (the page links a syntax tester) was run.

## perfil-mensal-original-writer-342_20261101_120000

# Perfil Mensal original writer (#342)

- [x] Fetch `PadraoXMLPerfil.asp` and diff against V4: 53-tag sample vs 92, 36 tag names in common, 14-tag `NR_CLIENT`/`DISTR_PATRIM` with `_NAC` suffixes, own row body, no `VERSAO` in the header.
- [x] Schema `perfil_mensal_original.py` (own blocks, `PercentField` reused from V4) and writer `PerfilMensalOriginal` (generic model walk, `atomic_write_bytes`, windows-1252).
- [x] Unit tests: tag order typed from the page sample, no `VERSAO`, scales, rejections, windows-1252 file output.
- [x] Docs page, mkdocs nav, api.md, index.md, README, CLAUDE.md catalog.
- [ ] Follow-up: V4 `AvgTermField` / `VarPercentPlField` use `Field(max_digits=...)`, which pydantic evaluates after dropping trailing zeros and which has no separate integer bound, so `12345.0` passes `max_digits=8`. Out of scope here (V4 writer behaviour); worth its own issue.

Open note: the page's tag table says `CNPJ_FUNDO`, its XML sample says `CNPJ_FDO`; the writer follows the sample (as V4 does).
