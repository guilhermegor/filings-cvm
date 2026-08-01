# FRE CIA_ABERTA — fatia 2 de 4 (administração/pessoas, os 7 membros com CPF) — #179

Branch: `feat/179-fre-readers-2-4-administracao-pessoas` · Issue: #179 · Fatia anterior: #172 / PR #173

## Feito

- [x] Grounding contra os bytes reais de `fre_cia_aberta_2025.zip` (8,5 MB) — cols **e** linhas por
      membro, validade de CNPJ/CPF por coluna, presença de header-only, campos com aspas.
- [x] 7 fixtures **header-only** verbatim (ISO-8859-1) em `tests/fixtures/fre_cia_aberta/`.
- [x] 7 contracts **gerados dos headers pinados**, nunca transcritos.
- [x] 7 readers sobre a base privada `_base_fre_reader.py` (zero infraestrutura nova).
- [x] Registro nos 5 `__init__` + contracts `__init__`; **contagem exportada conferida** (222 nomes,
      216 readers, 42 Meta, 15 FRE readers = 15 FRE contracts).
- [x] Testes: 73 no arquivo do FRE (era 45).
- [x] **Controles negativos rodados** (3 mutações) — ver abaixo.
- [x] Docs: `docs/ingestion/fre_cia_aberta.md`, `docs/api.md`, `CLAUDE.md` (catálogo + Layout).

## Medições que contrariaram o plano da issue

O plano dizia "CPF fora de `tuple_cnpj_cols`, fixtures header-only" — isso valeu. Três coisas **não**
estavam no plano e só apareceram por medir:

- [x] **`auditor` tem 2 colunas de CNPJ**, não 1: `CNPJ_Auditor` (1.096/1.096 válidos) além do
      `CNPJ_Companhia`. E as duas **têm máscaras diferentes na mesma linha** — a da companhia é
      pontuada, a do auditor vem em dígitos crus (`49928567000111`).
- [x] **`relacao_familiar` tem 3 colunas de CNPJ** (`CNPJ_Emissor`, `CNPJ_Emissor_Pessoa_Relacionada`
      além da companhia). O plano só mencionava as 2 de CPF.
- [x] **`relacao_subordinacao.Documento_Pessoa_Relacionada` guarda CNPJ *e* CPF** (8.462 × 34) e o
      nome **não diz nem um nem outro**. Uma varredura que só olha colunas com "CNPJ"/"CPF" no nome
      passa direto por ela. Fica **fora** de `tuple_cnpj_cols`.

Consequência de método: a asserção da fatia 1 `todo satélite == ("CNPJ_Companhia",)` **deixou de ser
verdade** e foi substituída por um mapa medido por membro. Uma regra derivada de 8 membros não
sobreviveu ao 9º.

## Controles negativos (todos rodados, todos vermelhos antes do fix)

- [x] **Declarar `CPF_Auditor` como coluna de CNPJ** → 7 testes falham, incluindo `ContractError` em
      runtime (`holds no valid CNPJ`). Duas defesas independentes.
- [x] **Dar a `membro_comite` as colunas de `administrador_membro_conselho_fiscal`** (os dois têm
      **21 colunas**) → falha o header pinado **e** o teste anti-cópia. Sem o header pinado, o
      contrato errado passaria.
- [x] ⚠️ **Tirar `Data_Fim_Contratacao` de `_DATE_COLS` → PASSOU (73 verdes).** Meu teste usava
      `isna().all()`, e **pandas transforma branco em NA sob `dtype="str"` também** — a asserção era
      verdadeira nos dois mundos. Medido: `datetime64[ns]`/`NaT` × `string`/`<NA>`. Reescrito para
      asserir o **dtype**; a mutação passou a falhar. **Um teste sobre uma coluna 100% vazia não pode
      asserir vazio — só o tipo distingue.**

## Aberto / próximo

- [ ] **Fatia 3 de 4** — diversidade, 11 membros (contagens **agregadas**, não PII).
- [ ] **Fatia 4 de 4** — remuneração + valores mobiliários + transações, 10 membros.
- [ ] Estender `_META_MEMBERS` do drift conforme as fatias 3–4 entrarem.
- [ ] **#91** (slim top-level `__all__`) — acordado com o user para **depois deste PR**, antes das
      fatias 3–4, para não colidir. O `__all__` plano já está em **216 readers** (a issue foi escrita
      com 94).

## Release

`src/` muda → releasa. PATCH sobre 0.25.26 → **0.25.27** (feat, pré-1.0).
