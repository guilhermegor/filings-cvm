# Work ledger — #170 CIA_ABERTA/DOC/CGVN readers (índice + práticas)

Branch `feat/170-cgvn-cia-aberta-readers`. Fecha **#170**. **Com release** (`feat`) → PATCH.
**4ª das 7 fatias `DOC`** (agora 4/7).

## Forma (medida) — molde do VLMO

| membro | reader | cols | linhas |
|---|---|---|---|
| `cgvn_cia_aberta.csv` | `CgvnCiaAbertaReader` | 12 | 382 |
| `cgvn_cia_aberta_praticas.csv` | `CgvnCiaAbertaPraticasReader` | 11 | **19.980** |

⚠️ **Os 4,01 MiB do ZIP são UM membro de conteúdo grande, não muitos membros** — a expectativa que eu
tinha pelo tamanho estava errada; a `Explicacao` chega a ~6.000 chars. **Nenhum membro header-only**
(o row-count por membro foi impresso no grounding, conforme a lição emendada no #166).

## ⚠️ Achado principal: o FCA era a EXCEÇÃO, não a regra

O índice do FCA usa `CNPJ_CIA`/`DT_REFER`/`DENOM_CIA`. **O do CGVN usa CamelCase**
(`CNPJ_Companhia`/`Data_Referencia`/`Nome_Empresarial`). Se eu tivesse generalizado a "regra do
índice" a partir do FCA — a fatia imediatamente anterior — este dataset sairia errado. **Anti-
generalização pinada** por um teste que compara os **dois** contracts diretamente, não só afirma o
deste.

## ⚠️ `Codigo_CVM` com zero à esquerda — o texto é load-bearing aqui

Valor real: **`001023`**. No IPE não havia zeros à esquerda, então tipar `Codigo_CVM` como texto era
**apenas convenção**; aqui é correção. **Provado por mutação:** com `int64`, a asserção falha com
`np.int64(1023) == '001023'`. `ID_Item` é hierárquico (`1.1.1`) e também fica texto.

## Outros achados

- `CNPJ_Companhia` **100% válido** nos dois membros (382 e 19.980), sem placeholder.
- **Date cols:** índice **4** (inclui `Data_Inicio_Exercicio_Social`/`Data_Fim_Exercicio_Social`),
  `praticas` **1**. Todas 100% ISO.
- `Explicacao` (11.935/19.980) e `Pratica_Recomendada` (até 1.262 chars) são texto livre longo;
  `QUOTE_NONE` dá **larguras uniformes** (medido) → nenhum `;` embutido.
- ⚠️ `Link_Download` é **`http://…/ENETCONSULTA/…`**, não o `https://…/ENET/…` do IPE/VLMO. Devolvido
  **como publicado** — o reader não normaliza esquema nem segue o link. Pinado por teste.
- ⚠️ **META = `meta_cgvn_cia_aberta.zip`** (forma padrão). As outras 3 dão **404** — inclusive
  `cgvn_cia_aberta.zip` **sem prefixo**, que é a forma **correta do FCA**. 5 datasets, 5 medições.

## Feito

- [x] 2 readers + base privada + `MetaCgvnCiaAbertaReader` (**41º**). **206 nomes públicos, 200
  readers, 41 Meta** (medido: 41 = 16 `.txt` + 25 `.zip`).
- [x] Contracts gerados dos headers + 2 fixtures verbatim; drift `_META_MEMBERS` atualizado.
- [x] Docs: página nova + nav + `api.md` (seção + Meta 41) + `meta.md` (3 contagens + linha) +
  **`CLAUDE.md` (catálogo, árvore e contagem META 40→41, mesmo commit — #161)** +
  `test_meta_readers.py` 40→41.
- [x] 17 testes novos.

## Verificação

- [x] **Oráculo anti-tautologia** dos 2 contracts contra os headers verbatim.
- [x] **Controle negativo do zero à esquerda:** `int64` → falha com `1023`; texto → passa.
- [x] **Controle negativo do anti-generalização:** renomear `Nome_Empresarial`→`DENOM_CIA` falha
  **2** testes (o oráculo e o comparativo CGVN×FCA).
- [x] ruff + format, mypy **378**, 4 check_*, suíte completa, mkdocs --strict, codespell.
- [x] ⚠️ Reincidência: rewrap de docstring por `str.replace` **empurra o overflow para a linha
  seguinte** — 3 rodadas de E501 nesta fatia. Reembrulhar o **parágrafo inteiro** de uma vez.

## Aberto / próximo

- [ ] PR (`Closes #170`) → aprovação → merge → **release PATCH**.
- [ ] `DOC` restante (3): **FRE** (8,10 MiB) → **DFP** (12,12) → **ITR** (30,14), depois
  `EVENTOS/RECOMPRA_ACOES`. **Nenhum tem contagem de membros medida** — imprimir **cols E linhas**
  por membro, e **medir a URL da META** (já vimos 5 resultados diferentes em 5 datasets).
