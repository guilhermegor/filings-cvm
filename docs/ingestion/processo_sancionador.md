# **Processo Sancionador (PROCESSO/SANCIONADOR) — leitura**

Leitura (← CVM) dos **processos administrativos sancionadores** da CVM e de seus acusados,
publicados no [portal de dados abertos](https://dados.cvm.gov.br/dados/). Estes readers
**inauguram** o *portal root* `processo/` (irmão de `oferta/`, `intermed/`, `fi/`, …).

> **Veja também:** [Referência da API](../api.md) · [Uso](../usage.md).

---

## Descrição

| Reader | Membro do `processo_sancionador.zip` | Colunas | Colunas de data | Grão |
|--------|--------------------------------------|---------|-----------------|------|
| `ProcessoSancionadorReader` | `processo_sancionador.csv` (processos) | 9 | 2 | um processo por `NUP` (chave única) |
| `ProcessoSancionadorAcusadoReader` | `processo_sancionador_acusado.csv` (acusados) | 4 | 1 | um acusado por processo (`NUP` se repete) |

O dataset publica um **ZIP de dois membros**: o processo (objeto, ementa, data de abertura,
componente organizacional da instrução, fase, subfase e local atuais, data da última movimentação)
e a tabela de **acusados** com a situação de cada um. É um **retrato do estado atual** numa **URL
fixa** que a CVM sobrescreve no lugar — por isso **não há `date_ref`**, e um `path_raw` persistido é
o único registro do que o dataset dizia no dia da coleta.

Medido nos bytes reais (snapshot de 2026-10-31): **581 processos** (`NUP` único, 17 dígitos) e
**2.070 acusados** em 1.614 nomes distintos; todo `NUP` de acusado existe em processos e todo
processo tem ao menos um acusado. ISO-8859-1, separador `;`, CRLF, nenhuma linha irregular.

⚠️ **Os 2 membros NÃO são um split `pf`/`pj`** — são duas tabelas relacionadas, ligadas pelo `NUP`
(a única coluna em comum, pinado por teste). ⚠️ **Nenhuma coluna de nenhum membro guarda CNPJ ou
CPF**, então `tuple_cnpj_cols` é **vazio nos dois** — decisão medida, não esquecimento.
`Nome_Acusado` é **dado pessoal** (pessoas físicas e jurídicas são nomeadas), mas sem número de
documento; por isso as fixtures são **só o header** (sem linhas de dados).

## Tipagem

As colunas `Data_*` viram `date` puro (brancos viram `NaT`): `Data_Abertura` e
`Data_Ultima_Movimentacao` nos processos, `Data_Situacao` nos acusados (ISO em 100% das linhas
preenchidas). Todo o restante mantém o **texto exato da CVM** — em especial o `NUP`, um
**identificador** de 17 dígitos que um dtype numérico transformaria em inteiro. `Ementa` chega vazia
em ~35% dos processos e `Situacao`/`Data_Situacao` têm uma linha vazia cada: vazio volta vazio.
⚠️ As **aspas são dados literais** (`QUOTE_NONE`): aparecem dentro da `Ementa` (`letra "b"`) e nunca
como delimitador. Os contracts são **gerados dos headers publicados** e **pinados** a
`tests/fixtures/processo_sancionador/*_header.csv`.

## META

⚠️ **A META é um `.zip` de dois membros** (`meta_processo_sancionador.zip`). A URL é uma **constante
por dataset**, nunca derivada. As duas `section` voltam **assimétricas** (`processo_sancionador` e
`acusado`): um membro tem o nome do stem puro, sem sufixo `<stem>_` a remover — comportamento
documentado da base, como no INTERMED e no COORD_OFERTA, honrado e pinado por teste. A META declara
13 campos (9 + 4) e não descreve a maioria deles (`Descrição` vazia).

---

## Política de retry

Todo reader aceita `retry_policy: RetryPolicy | None = None` e declara o seu padrão em
`_RETRY_POLICY` (padrão paciente: 5 tentativas, *backoff* ~2, 4, 8, 10 s). Veja a
[visão geral da leitura](index.md#politica-de-retry-retry_policy-e-_retry_policy).

---

## Exemplos

### Processos

```python
from filings_cvm.ingestion.processo import ProcessoSancionadorReader

df_ = ProcessoSancionadorReader().read()
# df_[["NUP", "Data_Abertura", "Fase_Atual", "Local_Atual", "Data_Ultima_Movimentacao"]]
```

### Acusados + persistir a camada *bronze*

```python
from pathlib import Path
from filings_cvm.ingestion.processo import ProcessoSancionadorAcusadoReader

df_ = ProcessoSancionadorAcusadoReader(
    path_raw=Path("/data/bronze/cvm/processo_sancionador"),
).read()
# df_[["NUP", "Nome_Acusado", "Situacao", "Data_Situacao"]]
# o ZIP inteiro e os dois membros ficam em disco: um path_raw de qualquer
# reader serve o outro (ambos baixam o mesmo arquivo).
```

Cada `read` levanta `OSError` (falha de download), `ContractError` (CSV viola o contrato) ou
`ValueError` (membro ausente no arquivo) — falha cedo, sem devolver dados corrompidos.
