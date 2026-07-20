# **Cadastro de Intermediários (INTERMED) — leitura**

Leitura (← CVM) do cadastro dos **intermediários** supervisionados pela CVM, publicado no
[portal de dados abertos da CVM](https://dados.cvm.gov.br/dados/). Estes readers **inauguram** o
*portal root* `intermed/` (irmão de `fi/`, `auditor/`, `invnr/`, …).

> Quinta fatia da **Wave 3** do #41 (snapshots CAD de prestadores de serviço). Copia o molde
> multi-membro do [AUDITOR](auditor.md) / [AGENTE_AUTON](agente_auton.md) / [INVNR](invnr.md).

> **Veja também:** [Referência da API](../api.md) · [Uso](../usage.md).

---

## Descrição

| Reader | Membro do `cad_intermed.zip` | Colunas | Chave CNPJ |
|--------|------------------------------|---------|------------|
| `IntermedReader` | `cad_intermed.csv` (registro do intermediário) | 28 | `CNPJ` (mascarado) |
| `IntermedRespReader` | `cad_intermed_resp.csv` (responsáveis) | 8 | `CNPJ` (do intermediário, mascarado) |

`INTERMED/CAD` publica um **ZIP de dois membros**. ⚠️ **Ao contrário dos irmãos anteriores, os dois
membros NÃO são um split `pf`/`pj`** — são o **registro do intermediário** (`CNPJ` mascarado,
denominação social/comercial, datas e motivo de cancelamento, situação, código CVM, setor de
atividade, controle acionário, patrimônio líquido, endereço, telefone, fax, e-mail, site) e a tabela
de **responsáveis** (o `TP_PARTIC`/`CNPJ`/`DENOM_SOCIAL` do intermediário mais o cargo, nome, data de
início e e-mail de cada responsável), **ambos chaveados pelo `CNPJ` do intermediário**. Como o
`cad_fi.csv`, é um **retrato do estado atual** numa **URL fixa** que a CVM sobrescreve no lugar — por
isso **não há `date_ref`**, e um `path_raw` persistido é o único registro do que o cadastro dizia no
dia da coleta. Nenhum grão é assumido.

⚠️ O membro **responsáveis carrega dado pessoal** — `RESP` (nome do responsável) e `EMAIL_RESP` — mas
**não há coluna de CPF**: identifica o responsável pelo nome dentro do `CNPJ` do intermediário. Logo
`tuple_cnpj_cols` é `("CNPJ",)` nos dois membros (o CNPJ do intermediário, mascarado —
`03.532.415/0001-02`), nunca um identificador pessoal; a rotina `br_identifiers` aceita a forma
mascarada.

### Tipagem

As colunas `DT_*` viram `date` puro (brancos viram `NaT`): `DT_REG`/`DT_CANCEL`/`DT_INI_SIT`/
`DT_PATRIM_LIQ` no registro, `DT_REG`/`DT_INI_RESP` nos responsáveis. Todo o restante mantém o
**texto exato da CVM** — inclusive `CEP`, `TEL`, `FAX`, `DDD_TEL`, `DDD_FAX` e `CD_CVM`, que o META
declara `numeric`/`char` mas são **identificadores, não quantidades** (o `DDD_TEL` já chega `051`,
com zero à esquerda). O mapa de tipos é derivado do contrato, então os dois não podem divergir.

---

## Política de retry

Todo reader aceita `retry_policy: RetryPolicy | None = None` e declara o seu padrão em
`_RETRY_POLICY` (padrão paciente: 5 tentativas, *backoff* ~2, 4, 8, 10 s). Veja a
[visão geral da leitura](index.md#politica-de-retry-retry_policy-e-_retry_policy).

---

## Exemplos

### Registro dos intermediários

```python
from filings_cvm import IntermedReader

df_ = IntermedReader().read()
# df_[["CNPJ", "DENOM_SOCIAL", "TP_PARTIC", "SIT", "MUN", "UF"]]
```

### Responsáveis + persistir a camada *bronze*

```python
from pathlib import Path
from filings_cvm import IntermedRespReader

df_ = IntermedRespReader(
    path_raw=Path("/data/bronze/cvm/cad_intermed"),
).read()
# o ZIP inteiro e ambos os membros ficam em disco: um path_raw de qualquer
# reader serve o outro (os dois baixam o mesmo arquivo).
```

Cada `read` levanta `OSError` (falha de download), `ContractError` (CSV viola o contrato) ou
`ValueError` (membro ausente no arquivo) — falha cedo, sem devolver dados corrompidos.
