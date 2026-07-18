# **Deriva de contrato — detecção semanal, não-bloqueante**

Job agendado que pega a **CVM mudando o contrato de um dataset _depois_ que a gente embarcou** — o
que **nenhum check de PR consegue pegar**. Roda `bin/check_contract_drift.py` via
`.github/workflows/contract-drift.yaml`; ao encontrar divergência, **abre (ou atualiza) uma única
issue**, nunca reprova o build.

> **Veja também:** [META (metadados da CVM)](meta.md) · [Proveniência](index.md).

---

## As duas camadas, e por que precisa das duas

| camada | quando | pega | bloqueia? |
|---|---|---|---|
| fixture de header pinado (issue #96) | PR-time, offline | **nós** escrevendo o contract errado | ✅ sim |
| **este job** | semanal, online | **a CVM** mudando o contract depois do ship | ❌ **nunca** |

O fixture pinado prova que o contract batia com o que a CVM publicava **no dia em que foi escrito**.
Nada no PR-time consegue saber que a CVM mudou desde então — só um job que vai olhar de novo.

---

## Dois oráculos, complementares

- **Header real do artefato** — as colunas que um `read()` bem-sucedido devolve, em **ordem da
  fonte**, antes das colunas de proveniência. Autoritativo para o **conjunto** e a **ordem** das
  colunas, mas só existe para um período que a CVM já publicou.
- **META** — os nomes de campo declarados. Fica numa **URL fixa, sempre acessível** (mesmo quando o
  artefato do período corrente ainda não saiu), mas a CVM **trunca o nome em exatamente 50
  caracteres** e não preserva ordem — então é um oráculo de **conjunto de nomes**, comparado no
  prefixo de 50 (veja [META](meta.md)).

Cada oráculo é comparado com o `tuple_required` do contract. Header real: nome **e** ordem. META:
conjunto de nomes, *truncation-aware*.

---

## ⚠️ Não-bloqueante, de propósito

- `tests/conftest.py` **bloqueia rede** — este job jamais roda em teste.
- "A CVM caiu" e "nosso contract está errado" seriam **indistinguíveis** num check vermelho, e um
  check vermelho não pode gatilhar release nem travar PR (issue #86 já nos queimou: um flake externo
  pulou um publish).

Logo: divergência ou falha → **issue aberta**, nunca CI vermelha. O script sai `0` na deriva; uma
issue já aberta é **atualizada** (encontrada por label `contract-drift` + marcador oculto no corpo),
nunca duplicada. Um outage da CVM vira ruído tolerável.

---

## Fiação explícita, nunca derivada

Quais readers um META descreve mora em `_META_MEMBERS`; o contract de um reader que não expõe
`_CONTRACT` mora em `_UNEXPOSED_CONTRACTS`. Derivar por nome estaria **errado**: `cad_fi` e
`cad_fi_hist` compartilham radical mas são datasets diferentes (os 19 readers `cad_fi_hist_*`
casam com **os dois** por prefixo), e os membros de `registro_fundo_classe` são `registro_fundo` /
`registro_classe` / `registro_subclasse` — sem relação de prefixo. Um teste estrutural
(`tests/unit/test_check_contract_drift.py`) garante que a fiação continua completa: um reader novo
não pode ser esquecido em silêncio.

## Cobertura parcial — `tuple_required` é "pelo menos estas", não "exatamente estas"

Um `FileContract` declara as colunas que o arquivo **precisa ter**, não necessariamente **todas** as
que ele tem. Dois casos de cobertura deliberadamente parcial:

- **Contract subset** — o `CdaReader` exige só as 4 colunas-chave (`TP_FUNDO_CLASSE`,
  `CNPJ_FUNDO_CLASSE`, `DENOM_SOCIAL`, `DT_COMPTC`) de um arquivo de ~60; o resto passa como texto.
- **Membros não implementados** — o META da Lâmina descreve o dataset inteiro, incluindo os membros
  `rentab_ano`/`rentab_mes` ainda não implementados.

Para esses datasets, "a fonte tem uma coluna/campo que o contract não lista" é **esperado, não
deriva** — então a **direção de coluna-extra** de ambos os oráculos é **suprimida**. A direção que
sustenta o job — **"uma coluna exigida sumiu da fonte"** — continua ativa para **todos**. Os
datasets parciais moram em `_PARTIAL_DATASETS` (chaveado pelo Meta reader, com o porquê de cada um),
e um teste estrutural garante que cada chave é um dataset real. Sem isso, o primeiro run real
(issue #115) abriu **123 achados, ~120 falso-positivo** — a maioria por tratar contracts subset como
se listassem o header inteiro (issue #117).

## Escopo

Reporta deriva; **não conserta**. O conserto (agente propondo PR sobre contracts pinados ao header
real) é o loop da bedrock-fm e fica fora daqui.
