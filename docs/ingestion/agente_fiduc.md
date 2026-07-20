# **Cadastro de Agentes Fiduciários (AGENTE_FIDUC) — leitura**

Leitura (← CVM) do cadastro dos **agentes fiduciários** supervisionados pela CVM, publicado no
[portal de dados abertos da CVM](https://dados.cvm.gov.br/dados/). Estes readers **inauguram** o
*portal root* `agente_fiduc/` (irmão de `fi/`, `auditor/`, `securit/`, …).

> Segunda fatia da **Wave 3** do #41 (snapshots CAD de prestadores de serviço). Copia o molde
> multi-membro estabelecido pelo [AUDITOR](auditor.md) — base privada + `pf`/`pj` + Meta reader,
> contratos pinados aos headers publicados.

> **Veja também:** [Referência da API](../api.md) · [Uso](../usage.md).

---

## Descrição

| Reader | Membro do `cad_agente_fiduc.zip` | Colunas | Chave CNPJ |
|--------|----------------------------------|---------|------------|
| `AgenteFiducPfReader` | `cad_agente_fiduc_pf.csv` (pessoa física) | 5 | — (não há coluna de CNPJ) |
| `AgenteFiducPjReader` | `cad_agente_fiduc_pj.csv` (pessoa jurídica) | 15 | `CNPJ` (mascarado) |

`AGENTE_FIDUC/CAD` publica um **ZIP de dois membros**: os agentes **pessoa física** (nome, datas de
registro/cancelamento/situação) e as **firmas** (o mesmo mais o `CNPJ` mascarado, a denominação
social, o endereço completo — inclusive `PAIS` — e o telefone). Como o `cad_fi.csv`, é um **retrato
do estado atual** numa **URL fixa** que a CVM sobrescreve no lugar — por isso **não há `date_ref`**, e
um `path_raw` persistido é o único registro do que o cadastro dizia no dia da coleta. Nenhum grão é
assumido.

⚠️ O membro **pessoa física não tem CPF nem `CD_CVM`** — o cadastro identifica o agente pessoa física
**só pelo nome** (`tuple_cnpj_cols` vazio, explícito). O `CNPJ` do membro pessoa jurídica chega
**mascarado** (`00.271.457/0001-30`) e é a única coluna de CNPJ; a rotina `br_identifiers` aceita a
forma mascarada.

⚠️ **Não é cópia do [AUDITOR](auditor.md)** (a lição do #96/#127): são **3 colunas de data**
(`DT_REG`, `DT_CANCEL`, `DT_INI_SIT`) em vez de 1, não há `CD_CVM`, e o `pj` acrescenta
`PAIS`/`DDD_TEL`/`TEL`. Cada contract é **gerado do header publicado** e **pinado** a um fixture
verbatim — copiar o irmão embarcaria colunas erradas com todos os testes verdes.

### Tipagem

As três colunas `DT_*` viram `date` puro (brancos, p.ex. `DT_CANCEL` de um registro ativo, viram
`NaT`). Todo o restante — inclusive o `CEP`/`DDD_TEL`/`TEL` numéricos, que preservam zeros à esquerda
— mantém o **texto exato da CVM**. O mapa de tipos é derivado do contrato, então os dois não podem
divergir.

---

## Política de retry

Todo reader aceita `retry_policy: RetryPolicy | None = None` e declara o seu padrão em
`_RETRY_POLICY` (padrão paciente: 5 tentativas, *backoff* ~2, 4, 8, 10 s). Veja a
[visão geral da leitura](index.md#politica-de-retry-retry_policy-e-_retry_policy).

---

## Exemplos

### Firmas de agente fiduciário (pessoa jurídica)

```python
from filings_cvm import AgenteFiducPjReader

df_ = AgenteFiducPjReader().read()
# df_[["CNPJ", "DENOM_SOCIAL", "SIT", "MUN", "UF"]]
```

### Agentes pessoa física + persistir a camada *bronze*

```python
from pathlib import Path
from filings_cvm import AgenteFiducPfReader

df_ = AgenteFiducPfReader(
    path_raw=Path("/data/bronze/cvm/cad_agente_fiduc"),
).read()
# o ZIP inteiro e ambos os membros ficam em disco: um path_raw de qualquer
# reader serve o outro (os dois baixam o mesmo arquivo).
```

Cada `read` levanta `OSError` (falha de download), `ContractError` (CSV viola o contrato) ou
`ValueError` (membro ausente no arquivo) — falha cedo, sem devolver dados corrompidos.
