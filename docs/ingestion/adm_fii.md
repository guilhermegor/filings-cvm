# **Cadastro de Administradores de FII (ADM_FII) — leitura**

Leitura (← CVM) do cadastro das entidades registradas para **administrar Fundos de Investimento
Imobiliário (FII)**, publicado no
[portal de dados abertos da CVM](https://dados.cvm.gov.br/dados/). Este reader **inaugura** o
*portal root* `adm_fii/` (irmão de `fi/`, `adm_cart/`, `auditor/`, …).

> Oitava e **última** fatia da **Wave 3** do #41 — **encerra a Wave 3** (8/8 registros de prestadores
> de serviço). É o **único** membro da Wave 3 num **CSV solto** (não ZIP), no molde do
> [Cadastro FI](cadastro_fi.md) / Emissor CEPAC, não o multi-membro dos irmãos.

> **Veja também:** [Referência da API](../api.md) · [Uso](../usage.md).

---

## Descrição

| Reader | Artefato | Colunas | Colunas de data | Chave CNPJ |
|--------|----------|---------|-----------------|------------|
| `CadastroAdmFiiReader` | `cad_adm_fii.csv` (CSV solto) | 18 | 3 | `CNPJ` (mascarado) |

`ADM_FII/CAD` publica um **CSV solto** — não um ZIP — com uma linha por entidade registrada para
administrar FII: `CNPJ` mascarado, denominação social/comercial, datas de registro/cancelamento e
motivo, situação, endereço, telefone e e-mail. Como o `cad_fi.csv` / `cad_emissor_cepac.csv`, é um
**retrato do estado atual** numa **URL fixa** que a CVM sobrescreve no lugar — por isso **não há
`date_ref`**, e um `path_raw` persistido é o único registro do que o cadastro dizia no dia da coleta
(não pode ser re-obtido).

⚠️ O cadastro é **chaveado pelo `CNPJ` do administrador** (uma instituição) e **não tem coluna de
CPF** — nenhum dado pessoal de pessoa física. `MOTIVO_CANCEL` é **texto livre**, não uma data.

### Tipagem

As colunas `DT_REG` / `DT_CANCEL` / `DT_INI_SIT` viram `date` puro (brancos viram `NaT`). Todo o
restante mantém o **texto exato da CVM** — inclusive `CEP`, `DDD` e `TEL`, que o META declara
`numeric` mas são **identificadores, não quantidades**. O `pj` usa **`DDD`** (como o ADM_CART /
AGENTE_AUTON), não o `DDD_TEL` do INVNR/INTERMED. O mapa de tipos é derivado do contrato, então os
dois não podem divergir.

---

## Política de retry

O reader aceita `retry_policy: RetryPolicy | None = None` e declara o seu padrão em `_RETRY_POLICY`
(padrão paciente: 5 tentativas, *backoff* ~2, 4, 8, 10 s). Veja a
[visão geral da leitura](index.md#politica-de-retry-retry_policy-e-_retry_policy).

---

## Exemplos

### Administradores de FII

```python
from filings_cvm import CadastroAdmFiiReader

df_ = CadastroAdmFiiReader().read()
# df_[["CNPJ", "DENOM_SOCIAL", "DENOM_COMERC", "SIT", "MUN", "UF"]]
```

### Persistir a camada *bronze*

```python
from pathlib import Path
from filings_cvm import CadastroAdmFiiReader

df_ = CadastroAdmFiiReader(
    path_raw=Path("/data/bronze/cvm/cad_adm_fii"),
).read()
# o CSV bruto fica em disco — o único registro do snapshot, que a CVM sobrescreve no lugar.
```

Cada `read` levanta `OSError` (falha de download) ou `ContractError` (CSV viola o contrato) — falha
cedo, sem devolver dados corrompidos.
