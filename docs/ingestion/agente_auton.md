# **Cadastro de Agentes Autônomos (AGENTE_AUTON) — leitura**

Leitura (← CVM) do cadastro dos **agentes autônomos de investimento** (AAI) supervisionados pela
CVM, publicado no [portal de dados abertos da CVM](https://dados.cvm.gov.br/dados/). Estes readers
**inauguram** o *portal root* `agente_auton/` (irmão de `fi/`, `auditor/`, `agente_fiduc/`, …).

> Terceira fatia da **Wave 3** do #41 (snapshots CAD de prestadores de serviço). Copia o molde
> multi-membro do [AUDITOR](auditor.md) / [AGENTE_FIDUC](agente_fiduc.md).

> **Veja também:** [Referência da API](../api.md) · [Uso](../usage.md).

---

## Descrição

| Reader | Membro do `cad_agente_auton.zip` | Colunas | Chave CNPJ |
|--------|----------------------------------|---------|------------|
| `AgenteAutonPfReader` | `cad_agente_auton_pf.csv` (pessoa física) | 6 | — (não há coluna de CNPJ) |
| `AgenteAutonPjReader` | `cad_agente_auton_pj.csv` (pessoa jurídica) | 19 | `CNPJ` (mascarado) |

`AGENTE_AUTON/CAD` publica um **ZIP de dois membros**: os agentes **pessoa física** (nome, datas e
motivo de cancelamento, situação) e as **firmas** (o mesmo mais o `CNPJ` mascarado, denominação
social/comercial, endereço, telefone, e-mail e site do administrador). Como o `cad_fi.csv`, é um
**retrato do estado atual** numa **URL fixa** que a CVM sobrescreve no lugar — por isso **não há
`date_ref`**, e um `path_raw` persistido é o único registro do que o cadastro dizia no dia da coleta.
Nenhum grão é assumido.

⚠️ O membro **pessoa física não tem CPF** — o cadastro identifica o agente pessoa física pelo `NOME`
(que pode inclusive vir **em branco**), então `tuple_cnpj_cols` é vazio (explícito) e não há chave
única. O `CNPJ` do membro pessoa jurídica chega **mascarado** (`49.270.551/0001-64`) e é a única
coluna de CNPJ; a rotina `br_identifiers` aceita a forma mascarada.

⚠️ **Não é cópia dos irmãos** (a lição do #96): acrescenta `MOTIVO_CANCEL`, `DENOM_COMERC`, `EMAIL`,
`SITE_ADMIN` e usa `DDD` (não `DDD_TEL`). São **3 colunas de data** (`DT_REG`, `DT_CANCEL`,
`DT_INI_SIT`); `MOTIVO_CANCEL` é texto livre, **não** data. Cada contract é **gerado do header
publicado** e **pinado** a um fixture verbatim.

### Tipagem

As três colunas `DT_*` viram `date` puro (brancos viram `NaT`). Todo o restante — inclusive o
`CEP`/`DDD`/`TEL` numéricos, que preservam zeros à esquerda — mantém o **texto exato da CVM**. O mapa
de tipos é derivado do contrato, então os dois não podem divergir.

---

## Política de retry

Todo reader aceita `retry_policy: RetryPolicy | None = None` e declara o seu padrão em
`_RETRY_POLICY` (padrão paciente: 5 tentativas, *backoff* ~2, 4, 8, 10 s). Veja a
[visão geral da leitura](index.md#politica-de-retry-retry_policy-e-_retry_policy).

---

## Exemplos

### Firmas de agente autônomo (pessoa jurídica)

```python
from filings_cvm import AgenteAutonPjReader

df_ = AgenteAutonPjReader().read()
# df_[["CNPJ", "DENOM_SOCIAL", "SIT", "MUN", "UF", "EMAIL"]]
```

### Agentes pessoa física + persistir a camada *bronze*

```python
from pathlib import Path
from filings_cvm import AgenteAutonPfReader

df_ = AgenteAutonPfReader(
    path_raw=Path("/data/bronze/cvm/cad_agente_auton"),
).read()
# o ZIP inteiro e ambos os membros ficam em disco: um path_raw de qualquer
# reader serve o outro (os dois baixam o mesmo arquivo).
```

Cada `read` levanta `OSError` (falha de download), `ContractError` (CSV viola o contrato) ou
`ValueError` (membro ausente no arquivo) — falha cedo, sem devolver dados corrompidos.
