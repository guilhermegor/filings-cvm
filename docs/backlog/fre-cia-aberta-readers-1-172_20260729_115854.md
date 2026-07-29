# Work ledger — #172 CIA_ABERTA/DOC/FRE readers, fatia 1/4 (índice + capital)

Branch `feat/172-fre-cia-aberta-readers-1`. Fecha **#172**. **Com release** (`feat`) → PATCH.
**5ª das 7 fatias `DOC`** (`DOC` em 5/7, FRE parcial).

## Por que 4 PRs (decisão do user)

⚠️ **O FRE é o maior dataset do portal: 36 membros, 131.105 linhas, 8,5 MB** — 3,6× o FCA, que já
tinha sido um PR de 40 arquivos. Levei a decisão ao user com os números medidos; ele escolheu
**dividir em 4 PRs temáticos** em vez de um único. Racional: cada um revisável e releasável sozinho,
e **os 6 membros com CPF ficam concentrados na fatia 2**, num diff que dá para escrutinar.

| fatia | tema | membros |
|---|---|---|
| **1 (esta)** | índice + estrutura de capital | **8** |
| 2 | administração/pessoas (**todos com CPF**) | 7 |
| 3 | diversidade (agregados) | 11 |
| 4 | remuneração + val. mobiliários + transações | 10 |

## Feito nesta fatia

- [x] 8 readers + base privada `_base_fre_reader.py` (molde VLMO/FCA) + `MetaFreCiaAbertaReader`
  (**42º**). **215 nomes públicos, 209 readers, 42 Meta** (medido: 42 = 16 `.txt` + 26 `.zip`).
- [x] 8 contracts **gerados dos headers** + 8 fixtures verbatim; `_META_MEMBERS` do drift com os 8
  (as fatias 2–4 estendem essa tupla).
- [x] Docs: página nova (com a tabela das 4 fatias) + nav + `api.md` + `meta.md` +
  **`CLAUDE.md` (catálogo, árvore, contagem META 41→42, mesmo commit — #161)** +
  `test_meta_readers.py` 41→42.
- [x] 40 testes novos.

## ⚠️ Achados

- **O índice usa `CNPJ_CIA`/`DT_REFER`/`DT_RECEB`** (maiúsculas), os satélites `CNPJ_Companhia`/
  `Data_Referencia`. **O FCA faz igual; o CGVN NÃO.** Convenção do índice por dataset: FCA ✓, CGVN ✗,
  FRE ✓ — **não há regra a inferir**. Pinado nas 2 direções **com o CGVN como contra-exemplo
  explícito** no teste.
- **SEIS nomes de coluna de CNPJ** nos 36 membros → cada contrato declara o seu.
- Todas as datas 100% ISO; `Data_Ultima_Assembleia` tem linhas vazias → `NaT` (pinado).
- `Valor_Capital`/`Quantidade_*`/`Percentual_*` = **texto exato** (#157).
- **Nenhum membro header-only e nenhum ragged** nos 36 (row-count por membro impresso no grounding).
- ⚠️ **META = `meta_fre_cia_aberta.zip`** (padrão; as outras 3 dão 404, inclusive a sem-prefixo que é
  a correta do FCA). **50 membros para 36 de dados**, com prefixo interno **misto** (ao menos um
  membro sem `meta_`). Honrado como publicado.

## ⚠️ Dois erros MEUS, ambos pegos por medição/gate

1. **Marquei os membros `*_declaracao_raca`/`*_declaracao_genero`/`*_PCD`/`*_faixa_etaria` como
   DADO PESSOAL SENSÍVEL — pelo NOME.** Ler as **colunas** desmentiu: são `Quantidade_Preto`,
   `Quantidade_Feminino`, `Quantidade_PCD` — **contagens agregadas** por companhia/órgão, sem
   indivíduo algum. O PII real está em **6 outros membros** com `CPF`/`Nome`, vários dos quais o
   nome não anunciava. **Lição `ground-invariants-not-just-schema-in-artifact` emendada:** um NOME é
   hipótese de semântica, nunca o achado — classificar por VALORES.
2. **Escrevi uma asserção FALSA:** `str(float("1984223115.42")) != "1984223115.42"`. O `repr` do
   Python faz round-trip **exato** desse valor — o teste falhou e estava certo. O float destrói a
   **escala** (zeros à direita) e precisão além de ~15 dígitos significativos, **não toda string
   decimal** (o caso do VLMO, `61961072.9999543100`, perde mesmo). Asserção removida; o docstring
   agora explica **por que** o texto garante fidelidade para *todo* valor, não só onde o estrago é
   visível.

## Verificação

- [x] **Oráculo anti-tautologia** dos 8 contracts + as 8 larguras pinadas
  (`[9,13,8,8,15,9,7,17]`).
- [x] ⚠️ **O gate de contagem de docs (#155/#161) PEGOU a deriva** — a suíte reprovou porque eu tinha
  adicionado o 42º Meta reader sem atualizar `meta.md`/`api.md`/`CLAUDE.md`. **O gate funcionou
  exatamente como projetado**, antes do commit.
- [x] ruff + format, mypy **390**, 4 check_*, **2100 unit**, 4 integration, mkdocs --strict,
  codespell.

## Aberto / próximo

- [ ] PR (`Closes #172`) → aprovação → merge → **release PATCH**.
- [ ] **Fatia 2 do FRE** (7 membros, **todos os com CPF**): `auditor`, `administrador_membro_conselho_fiscal`,
  `membro_comite`, `relacao_familiar`, `relacao_subordinacao`, `posicao_acionaria` (**3** cols
  `CPF_CNPJ_*` mistas, 31.508 linhas), `posicao_acionaria_classe_acao`. **Fixtures header-only
  obrigatórias**; CPF **fora** de `tuple_cnpj_cols`.
- [ ] Depois fatias 3 e 4, então **DFP** (12,12 MiB) e **ITR** (30,14) e `EVENTOS/RECOMPRA_ACOES`.
