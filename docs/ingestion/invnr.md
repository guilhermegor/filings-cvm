# **Cadastro de Representantes de Investidores Não Residentes (INVNR) — leitura**

Leitura (← CVM) do cadastro dos **representantes de investidores não residentes** supervisionados
pela CVM, publicado no [portal de dados abertos da CVM](https://dados.cvm.gov.br/dados/). Estes
readers **inauguram** o *portal root* `invnr/` (irmão de `fi/`, `auditor/`, `agente_fiduc/`,
`agente_auton/`, …).

> Quarta fatia da **Wave 3** do #41 (snapshots CAD de prestadores de serviço). Copia o molde
> multi-membro do [AUDITOR](auditor.md) / [AGENTE_FIDUC](agente_fiduc.md) / [AGENTE_AUTON](agente_auton.md).

> **Veja também:** [Referência da API](../api.md) · [Uso](../usage.md).

---

## Descrição

| Reader | Membro do `cad_invnr_repres.zip` | Colunas | Chave CNPJ |
|--------|----------------------------------|---------|------------|
| `InvnrRepresPfReader` | `cad_invnr_repres_pf.csv` (pessoa física) | 6 | — (não há coluna de CNPJ) |
| `InvnrRepresPjReader` | `cad_invnr_repres_pj.csv` (pessoa jurídica) | 23 | `CNPJ` (mascarado) |

`INVNR/CAD` publica um **ZIP de dois membros**: os representantes **pessoa física** (nome, datas e
motivo de cancelamento, situação) e as **firmas** (o mesmo mais o `CNPJ` mascarado, denominação
social/comercial, controle acionário, endereço completo, telefone, fax, patrimônio líquido e sua
data-base, e e-mail). Como o `cad_fi.csv`, é um **retrato do estado atual** numa **URL fixa** que a
CVM sobrescreve no lugar — por isso **não há `date_ref`**, e um `path_raw` persistido é o único
registro do que o cadastro dizia no dia da coleta. Nenhum grão é assumido.

⚠️ O membro **pessoa física não tem CPF** — o cadastro identifica o representante pessoa física pelo
`NOME`, então `tuple_cnpj_cols` é vazio (explícito) e não há chave única. O `CNPJ` do membro pessoa
jurídica chega **mascarado** (`76.621.457/0001-85`) e é a única coluna de CNPJ; a rotina
`br_identifiers` aceita a forma mascarada.

⚠️ **Não é cópia dos irmãos** (a lição do #96): acrescenta `CONTROLE_ACIONARIO`, `DDD_FAX`, `FAX`,
`VL_PATRIM_LIQ` e `DT_PATRIM_LIQ`, e usa `DDD_TEL` (não o `DDD` do AGENTE_AUTON). O membro pessoa
jurídica tem por isso **quatro** colunas de data (`DT_REG`, `DT_CANCEL`, `DT_INI_SIT`,
`DT_PATRIM_LIQ`) contra as três do pessoa física; `MOTIVO_CANCEL` é texto livre, **não** data. Cada
contract é **gerado do header publicado** e **pinado** a um fixture verbatim.

### Tipagem

As colunas `DT_*` viram `date` puro (brancos viram `NaT`). Todo o restante mantém o **texto exato da
CVM** — inclusive `CEP`, `TEL` e `FAX`, que o META declara `numeric` mas são **identificadores, não
quantidades**: o `CEP` já chega com o zero à esquerda perdido (`1311920`), e tipá-lo como número
consolidaria a perda. O mapa de tipos é derivado do contrato, então os dois não podem divergir.

---

## Política de retry

Todo reader aceita `retry_policy: RetryPolicy | None = None` e declara o seu padrão em
`_RETRY_POLICY` (padrão paciente: 5 tentativas, *backoff* ~2, 4, 8, 10 s). Veja a
[visão geral da leitura](index.md#politica-de-retry-retry_policy-e-_retry_policy).

---

## Exemplos

### Firmas representantes (pessoa jurídica)

```python
from filings_cvm import InvnrRepresPjReader

df_ = InvnrRepresPjReader().read()
# df_[["CNPJ", "DENOM_SOCIAL", "SIT", "MUN", "UF", "VL_PATRIM_LIQ"]]
```

### Representantes pessoa física + persistir a camada *bronze*

```python
from pathlib import Path
from filings_cvm import InvnrRepresPfReader

df_ = InvnrRepresPfReader(
    path_raw=Path("/data/bronze/cvm/cad_invnr_repres"),
).read()
# o ZIP inteiro e ambos os membros ficam em disco: um path_raw de qualquer
# reader serve o outro (os dois baixam o mesmo arquivo).
```

Cada `read` levanta `OSError` (falha de download), `ContractError` (CSV viola o contrato) ou
`ValueError` (membro ausente no arquivo) — falha cedo, sem devolver dados corrompidos.
