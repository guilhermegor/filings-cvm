# DFP CIA_ABERTA — 19 membros, ~1,17M linhas — #196

Branch: `feat/196-dfp-cia-aberta-readers` · Issue: #196 · Leva o sub-root `CIA_ABERTA/DOC` a
**6 de 7** datasets (só falta o ITR).

## Feito

- [x] Grounding contra os bytes reais (2025) — membros, cols **e** linhas, ragged, classificação de
      **toda** coluna por valor, e a **grafia da META medida** (4 candidatas).
- [x] 19 fixtures header-only verbatim + 19 contracts **gerados dos headers**.
- [x] 19 readers sobre a base privada `_base_dfp_reader.py` (molde do `_base_fre_reader.py`) +
      `MetaDfpCiaAbertaReader` (44º).
- [x] Registro nos **3** `__init__` da cadeia + os **2** contracts em `contracts/__init__.py`;
      `_META_MEMBERS` do drift estendido.
- [x] **Contagens RE-MEDIDAS, não incrementadas:** **259 readers** (era 239), **44 Meta readers =
      17 `.txt` + 27 `.zip`**, 22 roots.
- [x] 106 testes novos no arquivo do DFP; suíte **2597** unit + 4 integration.
- [x] Docs: página nova `docs/ingestion/dfp_cia_aberta.md` + `nav`, seção em `docs/api.md`,
      linha e contagens em `docs/ingestion/meta.md`, catálogo + layout + contagens no `CLAUDE.md`.

## Medições (2025)

19 membros, 12,73 MB, **~1,17 milhão de linhas**, **nenhum ragged**. `_con` = consolidado,
`_ind` = individual.

| grupo | membros | cols |
|---|---|---|
| índice | 1 | 9 |
| balanço (`BPA`/`BPP` × `con`/`ind`) | 4 | 14 |
| fluxo (`DFC_MD`/`DFC_MI`/`DRA`/`DRE`/`DVA` × `con`/`ind`) | 10 | 15 |
| mutações do PL (`DMPL` × `con`/`ind`) | 2 | 16 |
| composição do capital | 1 | 10 |
| parecer | 1 | 8 |

## ⚠️⚠️ O achado 1 — este dataset INVERTE a armadilha de todos os anteriores

Em CRA, CRI, FCA e FRE a lição era *"membros de mesma largura têm colunas diferentes — nunca copie o
irmão"*. **Aqui é o oposto:** os 16 membros de demonstração colapsam em **3** listas, e membros
diferentes são **genuinamente idênticos**. 19 membros → **6** listas distintas.

A diferença 14 × 15 é **exatamente `DT_INI_EXERC`**: balanço é retrato num instante, fluxo cobre
período. `DMPL` soma `COLUNA_DF`.

**Medido contra as fixtures**, não presumido — e o teste afirma o agrupamento, não só a contagem.
**Presumir "são iguais" e presumir "são diferentes" é o mesmo erro: não medir.** Precedente: no CRI,
2 das 7 seções eram de fato idênticas ao CRA, e a coincidência era da fonte.

## ⚠️⚠️ O achado 2 — o BURACO que as listas idênticas abrem (e a defesa que faltava)

Com 10 membros de lista **idêntica**, um reader apontado ao membro **errado** — o swap `con`↔`ind`
que a nomenclatura convida — devolve um frame **perfeitamente válido**: colunas conferem, tipos
conferem, contrato passa. **Nada fica vermelho.**

**Provado por mutação:** trocar o `_MEMBER_STEM` de `DRE_con` pelo de `DRE_ind` passava na suíte
**INTEIRA**. E o swap `BPA_con`→`BPA_ind` quebrava **1** teste — mas **incidentalmente**: aquele
teste constrói um `BPA_con` deliberadamente quebrado esperando `ContractError`, e o reader passou a
ler o irmão intacto. Não era defesa, era acidente.

**Defesa acrescentada:** cada membro sintético dos testes **se identifica** numa coluna que todos
têm (`DENOM_CIA`), e um teste parametrizado exige que cada reader leia **o seu**. Re-rodadas as duas
mutações: `BPA_con`→`BPA_ind` passa a falhar **2**, e `DRE_con`→`DRE_ind` — que antes passava por
completo — falha **1**, o teste novo.

⚠️ **Foi a contagem baixa do mutante que revelou isso**, exatamente como a lição
`a-negative-control-needs-a-verified-restore` prevê: uma falha só não é "defesa suficiente", é um
número a investigar.

## ⚠️⚠️ O achado 3 — a escala do valor está em OUTRA coluna

`VL_CONTA` chega com **10 casas decimais** (`2398719197.0000000000`) → **texto exato** (um `float64`
apaga os dígitos, como já medido no VLMO). Mas o número **sozinho não significa nada**:
`ESCALA_MOEDA` vale `MIL` ou `UNIDADE`, então **somar `VL_CONTA` sem ler `ESCALA_MOEDA` erra por
1000×**. Os readers **não reescalam** (ficam thin; reescalar destruiria o valor publicado) — está
documentado no docstring, na página e no `api.md`, com o exemplo de conversão a jusante.

## Outras armadilhas honradas

- `CD_CVM` vem `001023`, **zero à esquerda** — texto load-bearing (precedente CGVN).
- `ORDEM_EXERC` (`ÚLTIMO`/`PENÚLTIMO`) **duplica cada conta** → **nenhuma chave única**.
- **Todos os 19 membros usam `CNPJ_CIA`/`DT_REFER`**, inclusive os satélites — **diferente** do FCA
  e do FRE. O teste usa o FRE como **contra-exemplo vivo**.
- `COLUNA_DF` (DMPL) e `TP_RELAT_AUD` (parecer) parcialmente vazias.
- META = `meta_dfp_cia_aberta_txt.zip` (**infixo `_txt`**); as outras 3 dão **404**, inclusive a
  sem-prefixo que é a **correta do FCA**. A previsão do survey acertou pela 1ª vez — o que **não**
  torna o nome derivável.

## Controles negativos (todos vermelhos, restore por cópia de snapshot)

Baseline **87 → 106** passed, re-medido entre as mutações.

- [x] Dar `DT_INI_EXERC` ao balanço (a diferença de 1 coluna entre as 2 listas grandes) → **3**.
- [x] Declarar `CD_CVM` como coluna de CNPJ (classificar pelo nome) → **7**.
- [x] `BPA_con` lendo o membro do irmão → **1 antes** (incidental) / **2 depois** da defesa nova.
- [x] `DRE_con` lendo o membro do irmão → **0 antes** (!) / **1 depois**.

## Aberto / próximo

- [ ] **Release PATCH** ao mergear (`feat`, `src/` muda).
- [ ] **ITR** (`itr_cia_aberta_AAAA.zip`, 30,14 MiB) — **fecha o `DOC` (7/7)**; contagem de membros
      **a medir**, jamais presumida do DFP.
- [ ] Depois: `EVENTOS/RECOMPRA_ACOES`.
- [ ] #192 (testes dos 3 `bin/check_*` sem cobertura) segue em Ready.
