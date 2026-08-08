# Ledger — #204 registrar as Waves 3 e 4 em `_IMPLEMENTED_PACKAGES`

Branch: `chore/204-registrar-waves-3-4-implemented-packages` · Issue: #204 · Class: **ci**
(zero diff em `src/` → **sem release**)

## O problema, medido

`bin/check_portal_completeness.py` declara em `_IMPLEMENTED_PACKAGES` os slugs CKAN que a
biblioteca ingere. A lista ficou em **21** enquanto as Waves 3 e 4 entregavam **23** datasets
(`auditor-cad` … `cia_aberta-eventos-recompra_acoes`). O job semanal seguiu publicando o resultado
na issue #122: **33 pendentes de 54**, quando a verdade medida é **10 de 54** (44 implementados).

⚠️ **A omissão não tinha como ficar vermelha.** Ela só se manifesta no corpo de uma *issue*, que
nenhum teste lê. Os testes estruturais existentes conferem a **forma** dos slugs declarados, nunca
se algum **faltou** — a asserção `len >= 20` passava com folga em 21.

## Feito

- [x] Registrados os **23** slugs faltantes, em ordem alfabética, cada um com o comentário da
      família de readers no estilo do arquivo: `adm_cart-cad`, `adm_fii-cad`, `agente_auton-cad`,
      `agente_fiduc-cad`, `auditor-cad`, `cia_aberta-cad`, os **7** `cia_aberta-doc-*`,
      `cia_aberta-eventos-recompra_acoes`, `cia_estrang-cad`, `cia_incent-cad`,
      `consultor_vlmob-cad`, `coord_oferta-cad`, `crowdfunding-cad`, `fi-doc-eventual`,
      `intermed-cad`, `invnr-cad`, `oferta-distrib`.
- [x] Comentário de bloco `21 today` → `44 today`, mais a nota de por que a edição é fácil de
      esquecer e o que a defende agora.
- [x] `unregistered_roots(frozenset_roots, frozenset_implemented)` — lógica pura nova no script,
      no molde do `missing_packages`: devolve os roots que **nenhum** slug cobre, comparando o
      primeiro segmento do slug (`cia_aberta-doc-itr` → `cia_aberta`).
- [x] 3 testes em `tests/unit/test_check_portal_completeness.py`: o positivo sobre os roots reais
      (via `iter_root_packages()`, que **levanta** em vez de devolver vazio) e **2** controles da
      lógica pura — um root descoberto, um root coberto por qualquer um dos seus datasets.
- [x] `docs/ingestion/portal_completeness.md` — seção nova sobre a deriva medida e o piso agora
      testado, incluindo o que o gate **não** pega.
- [x] Gate re-rodado: **10 pendentes de 54** (era 33).

## Controle negativo — verificado

Mutação: remover as **9** linhas `cia_aberta-*` de `_IMPLEMENTED_PACKAGES`.

| passo | resultado |
|---|---|
| baseline | 11 passed |
| mutante (9 linhas removidas, contagem assertada no script) | **1 failed**, 10 passed |
| teste que falhou | `test_every_portal_root_is_registered_in_the_implemented_set` |
| restore por cópia de snapshot | `diff` byte-idêntico, 11 passed |

⚠️ O **`1`** é achado, não acaso: existe **exatamente uma** defesa para esse fato. E o restore foi
por **cópia de snapshot** com `diff` conferido, não `git checkout` — a lição
`a-negative-control-needs-a-verified-restore` (#191) aplicada de primeira.

## Escopo deliberadamente NÃO feito

- [ ] **Cobertura por dataset.** O gate é de nível **root**: `fi` está coberto por `fi-doc-cda`, então
      esquecer um segundo dataset do `fi` (foi o caso do `fi-doc-eventual`) **continua invisível**.
      Fechar isso exigiria derivar "implementado?" de nomes de reader — exatamente a derivação que o
      docstring do script rejeita e que o job de deriva de contrato evita (`cad_fi` × `cad_fi_hist`).
      Preferido um piso grosso e honesto a um mapeamento frágil.
- [ ] **Sincronizar a issue #122 agora.** O job semanal a reescreve sozinho no próximo run; forçar à
      mão mascararia se o fix pegou.

## Backlog real depois deste PR — 10 datasets

`fi-doc-perfil_mensal` (próximo alvo, decidido com o user) · `fi-doc-extrato` · `fi-doc-balancete` ·
`fi-doc-compl` · `fi-doc-entrega` · `emissores` · `distrpubl` · `ato_declr-intermed` ·
`processo-sancionador` · `arrecadacao-receita-publica`.

Completed — kept as a record.
