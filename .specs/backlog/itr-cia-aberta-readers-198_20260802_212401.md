# ITR CIA_ABERTA — 19 membros, 3,64M linhas — **FECHA O `DOC` (7/7)** — #198

Branch: `feat/198-itr-cia-aberta-readers` · Issue: #198 · Sub-root `CIA_ABERTA/DOC` **completo**;
resta só `EVENTOS/RECOMPRA_ACOES` no root `cia_aberta/`.

## Feito

- [x] Grounding contra os bytes reais (2025) — membros, cols **e** linhas, ragged, valores, e a
      **grafia da META medida** entre 4 candidatas.
- [x] **Comparação header a header contra as fixtures pinadas do DFP** — o achado da fatia.
- [x] 19 fixtures header-only verbatim + 19 contracts **gerados dos headers do ITR** (nunca
      copiados do DFP).
- [x] 19 readers sobre `_base_itr_reader.py` + `MetaItrCiaAbertaReader` (45º).
- [x] Registro nos **3** `__init__` + os 2 contracts em `contracts/__init__.py`; `_META_MEMBERS`.
- [x] **Contagens RE-MEDIDAS:** **279 readers** (era 259), **45 Meta = 17 `.txt` + 28 `.zip`**.
- [x] 107 testes no arquivo do ITR; suíte **2784** unit + 4 integration.
- [x] Docs: página nova + `nav`, seção em `api.md`, roster/contagens em `meta.md`, catálogo +
      layout + contagens no `CLAUDE.md`.

## Medições (2025)

**19 membros, 31,63 MB, 3.640.994 linhas** — 3× o DFP, o maior artefato da biblioteca. Nenhum
ragged. 19 → **6** listas distintas (16 demonstrações em 3), a mesma forma do DFP.

CNPJ_CIA **100% válido** em todos (medido sobre **valores distintos** — ver nota de método), todo
`DT_*` **100% ISO** sem branco. Parcialmente vazias: `COLUNA_DF` (1.767/623.847) e **`TP_RELAT_ESP`
(4.844/7.051)**.

## ⚠️⚠️ O achado — 18/19 idênticos ao DFP, e exatamente 1 não

| | DFP (anual) | ITR (trimestral) |
|---|---|---|
| `parecer`, coluna 5 | `TP_RELAT_AUD` | **`TP_RELAT_ESP`** |

**Mesma largura (8), mesma posição (5ª), 7 de 8 nomes.** O DFP é *auditado*; o ITR passa por
*revisão especial*. Copiar o contract do `parecer` do DFP erraria **uma** coluna e passaria em tudo
menos no header pinado.

⚠️ **É o contraponto exato da lição que o DFP acabou de ensinar.** Lá o achado foi "aqui, ao
contrário de CRA/CRI/FCA/FRE, membros irmãos **são** idênticos". Levar *essa* generalização para o
dataset vizinho é o mesmo erro num casaco novo — **18/19 idênticos é precisamente o que faz alguém
copiar o 19º.** A comparação é pinada **membro a membro, contra as fixtures dos DOIS datasets**.

## Nota de método — medir sobre valores DISTINTOS

O probe original (herdado do DFP) validava CNPJ/ISO **linha a linha**: 3,6M linhas × 15 colunas ≈
**50 milhões** de validações. Ficou inviável (nem chegou a imprimir uma linha em >10 min).

Trocado por varredura sobre **valores distintos** por coluna — `CNPJ_CIA` tem ~700 empresas
distintas, não 3,6M. **Mesma evidência, ordens de grandeza mais barato**, e terminou em segundos.
⚠️ Isso vale porque as perguntas são sobre o **conjunto** de valores ("todo `DT_*` é ISO?", "todo
CNPJ é válido?"); uma pergunta sobre **taxa** (quantas linhas em branco) continua precisando da
contagem por linha, e foi feita assim.

## Controles negativos (todos vermelhos)

Baseline **107 passed**.

- [x] **Copiar o contract do `parecer` do DFP** (a mutação que esta fatia existe para pegar) →
      **3 falhas**, incluindo a cruzada nomeada.
- [x] `DRE_con` lendo o membro do irmão → **1 falha** — a defesa de **identidade do membro**, nascida
      no DFP, funciona aqui de imediato.

## Aberto / próximo

- [ ] **Release PATCH** ao mergear (`feat`, `src/` muda).
- [ ] **`EVENTOS/RECOMPRA_ACOES`** — o **único** pendente do root `cia_aberta/`.
- [ ] #192 (testes dos 3 `bin/check_*` sem cobertura) segue em Ready.
