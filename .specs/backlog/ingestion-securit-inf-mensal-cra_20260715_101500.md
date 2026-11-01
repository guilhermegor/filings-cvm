# Work ledger — #96 SECURIT INF_MENSAL_CRA (8 membros) — Wave 2 PR 3/4

Branch `feat/ingestion-securit-inf-mensal-cra-96`. Fecha **#96**. Release: `feat` em `src/` →
**PATCH** → **0.25.4**.

## O achado que define esta PR

O `INF_MENSAL_CRA` tem **os mesmos 8 nomes de seção** do `INF_MENSAL_OTS` (já embarcado) e a mesma
forma de reader. Parecia trabalho de copiar/colar. **Não era: os 8 diferem.** O CRA é *agro*; o OTS é
o residual genérico.

| membro | OTS | CRA |
|---|---|---|
| todos os 8 | `CNPJ_Securitizadora` | **`CNPJ_Emissora`** |
| `direitos_creditorios` | 43 | **56** (13 baldes agro) |
| `geral` | 36 | 31 (+`Cadeia_Producao`/`Tipo_Segmento`; **sem** bloco de contingências) |
| `derivativos` | `*_Commodities` | `*_Commodities_Agricolas` |
| `classe` | `Codigo_Negociacao_Mercado_Secundario`, `Total_Integralizado` | `Codigo_CETIP`, `Valor_Total_Integralizado` |
| `fluxo_caixa` | `Recebimentos_Creditos` | `Recebimentos_Direitos_Creditorios` |

**Copiar os contracts do OTS embarcaria os 8 errados com a suíte inteira verde** — porque os testes
afirmam o contract que foi escrito. Corolário: a typo `Outras_Contigencias_Relevantes` do OTS **não
tem contrapartida aqui** — quirk é fato de artefato, não de família.

## Feito

- [x] **Grounding nos bytes reais** — `inf_mensal_cra_2025.zip` (1.360.247 bytes) + `meta_*.zip`
  baixados do portal. 8 membros confirmados: geral 31, ativo_passivo 31, classe 23,
  direitos_creditorios 56, desembolso 22, fluxo_caixa 21, derivativos 20, cedente_devedor 7.
- [x] **Contracts gerados do header publicado**, nunca transcritos, e **verificados
  programaticamente** (`tuple_required == header` nos 8 → 0 drift).
- [x] **Fixtures de header pinados** (`tests/fixtures/inf_mensal_cra/*_header.csv`) — os bytes
  verbatim do header da CVM. **Só header, ZERO linhas de dados**: `cedente_devedor` guarda **CPF
  real** e commitar linhas publicaria dado pessoal. O ganho anti-tautologia é o mesmo.
- [x] **`test_contract_matches_the_published_header`** — o único teste do arquivo cujo valor esperado
  **não** veio de nós. **Mutation-testado** (prova de que falha mesmo):
  - `CNPJ_Emissora`→`CNPJ_Securitizadora` em `geral` (**o erro de cópia exato**) → **2 testes falham**;
  - remover 1 coluna (`Cadeia_Producao`) → **falha**;
  - restaurado → 44 passam.
- [x] `test_cra_contracts_are_not_the_ots_contracts` — guarda explícita contra uma cópia futura.
- [x] Base privada `_base_inf_mensal_cra_reader.py` + **8 readers finos** (`_MEMBER_STEM`,
  `_CONTRACT`, `_LABEL`, `_DATE_COLS`, `_RETRY_POLICY`), padrão OTS/FIDC.
- [x] Re-export flat nos 4 níveis (`securit/doc` → `securit` → `ingestion` → `filings_cvm`); 8 nomes
  no `__all__` público.
- [x] **Live-verificado contra os bytes reais**, os 8: 8093/8093/14073/8093/8093/8093/8093/10691
  linhas, contagem de colunas exata, proveniência (6 colunas) em todos.

### Armadilhas auditadas nos valores reais (não presumidas)

- [x] **`classe.Indice_Subordinacao_Data_Base` NÃO é data** — valores `'0.00'`. Fora do `_DATE_COLS`
  (mesma trap do OTS). Teste trava.
- [x] **`cedente_devedor.CNPJ` NÃO é coluna de CNPJ** — campo livre e sujo. Arquivo 2025 inteiro:
  14 díg = 7.090 (CNPJ), **11 díg = 327 (CPF, dado pessoal)**, 1 díg = 2.352 (`'0'`), 0 díg = 103
  (`','`), 15 díg = 72 (malformado), **33 díg = 12 (dois identificadores na mesma célula)**. Só
  `CNPJ_Emissora` em `tuple_cnpj_cols`; teste cobre as 5 formas sujas.
- [x] **`geral` tem 3 colunas `CNPJ_*` 100% vazias** (`CNPJ_Agente_Fiduciario`, `CNPJ_Custodiante`,
  `CNPJ_Agencia_Classificadora`) — entram no contract, **ficam fora** de `tuple_cnpj_cols` (nada a
  validar hoje; declará-las falharia um arquivo válido no dia em que a CVM as preencher com texto
  livre). Teste trava.
- [x] `_DATE_COLS` por membro auditado contra os valores reais: `geral` 4, `classe` 2, os outros 6
  só `Data_Referencia`.

## Gates

- [ ] ruff check + format · mypy · codespell · check_typing · check_provenance · check_docstrings
- [ ] **pytest nos DOIS pandas majors** (3.0.3 e 2.3.3)
- [ ] `mkdocs build --strict`
- [x] 44 testes novos passam; live-verify OK; mutation-test do guard OK

## Docs

- [x] Página `docs/ingestion/inf_mensal_cra.md` + nav no `mkdocs.yml`
- [x] `docs/api.md` (secção `InfMensalCra*Reader`), `docs/ingestion/index.md`
- [x] Catálogo do `CLAUDE.md` raiz (entrada CRA + layout `securit/`)
- [ ] Ledger do #41 (survey) — marcar CRA feito, CRI a seguir

## Aberto / próximo

- [ ] PR → aprovação do usuário → merge → **release PATCH 0.25.4** (Test PyPI → verify → PyPI →
  verify). ⚠️ **Primeiro release depois do #79** (bumps `upload-artifact@v7`/`download-artifact@v8`/
  `gh-release@v3`, que **nenhuma PR exercita** — os workflows de release são `workflow_dispatch`).
  **Não pular o Test PyPI**; conferir `gh run view --json jobs` → `test_pypi: success`, não `skipped`
  (lição do #86).
- [ ] **Depois: #97 (módulo público de META) → #98 (job semanal de drift) → CRI (11 membros,
  META-first).** Sequência escolhida com o usuário: o CRI é o maior alvo de "copiar do irmão" que
  resta, então é o primeiro cliente ideal do seam.
- [x] Lição BlueprintX capturada: `pin-contracts-to-a-source-published-oracle.md` (store global +
  mirror do repo). É a lição-mãe do #97/#98.
