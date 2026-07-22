# **Cadastro de Companhias Estrangeiras (CIA_ESTRANG) — leitura**

Leitura (← CVM) do cadastro das **companhias estrangeiras** registradas na CVM, publicado no
[portal de dados abertos da CVM](https://dados.cvm.gov.br/dados/). Este reader **inaugura** o
*portal root* `cia_estrang/` (irmão de `fi/`, `adm_fii/`, `auditor/`, …).

> **Abre a Wave 4 do #41** (companhias/ofertas). Um **CSV solto** de 1 reader — molde do
> [Cadastro FI](cadastro_fi.md) / [ADM_FII](adm_fii.md), não o multi-membro dos ZIPs.

> **Veja também:** [Referência da API](../api.md) · [Uso](../usage.md).

---

## Descrição

| Reader | Artefato | Colunas | Colunas de data | Chaves CNPJ |
|--------|----------|---------|-----------------|-------------|
| `CadastroCiaEstrangReader` | `cad_cia_estrang.csv` (CSV solto) | 49 | 7 | `CNPJ`, `CNPJ_AUDITOR` |

`CIA_ESTRANG/CAD` publica um **CSV solto** — não um ZIP — com uma linha por companhia estrangeira
registrada: `CNPJ` mascarado, país de origem, denominação social/comercial, situação, categoria de
registro, controle acionário, endereço e contato (da companhia e do representante legal) e os dados
do auditor (`CNPJ_AUDITOR` + `AUDITOR`). Como o `cad_fi.csv` / `cad_adm_fii.csv`, é um **retrato do
estado atual** numa **URL fixa** que a CVM sobrescreve no lugar — por isso **não há `date_ref`**, e
um `path_raw` persistido é o único registro do que o cadastro dizia no dia da coleta.

⚠️ **Duas colunas de CNPJ** — o da companhia (`CNPJ`, mascarado) e o do seu auditor
(`CNPJ_AUDITOR`) —, ambas exigidas com ao menos um CNPJ válido. `RESP` traz o **nome** do
representante legal (dado pessoal) mas **não há coluna de CPF**.

⚠️ **`MOTIVO_CANCEL` é texto livre**, não uma data. A companhia é estrangeira, então `PAIS_ORIGEM`
/ `PAIS` são preenchidos e o endereço pode ser no exterior.

### Tipagem

As **sete** colunas `DT_*` (`DT_REG`, `DT_CONST`, `DT_CANCEL`, `DT_INI_SIT`, `DT_INI_CATEG`,
`DT_INI_SIT_EMISSOR`, `DT_INI_RESP`) viram `date` puro (brancos viram `NaT`). Todo o restante
mantém o **texto exato da CVM** — inclusive `CD_CVM`, `CEP`, `TEL`, `FAX`, `DDD_*` e `CD_PAIS_*`,
que o META declara `numeric`/`char` mas são **identificadores, não quantidades**. O mapa de tipos é
derivado do contrato, então os dois não podem divergir. O contract é **gerado do header publicado**
e **pinado** a `tests/fixtures/cad_cia_estrang/cad_cia_estrang_header.csv` (49 colunas = risco real
de transcrição — o header verbatim é o oráculo).

---

## Política de retry

O reader aceita `retry_policy: RetryPolicy | None = None` e declara o seu padrão em `_RETRY_POLICY`
(padrão paciente: 5 tentativas, *backoff* ~2, 4, 8, 10 s). Veja a
[visão geral da leitura](index.md#politica-de-retry-retry_policy-e-_retry_policy).

---

## Exemplos

### Companhias estrangeiras

```python
from filings_cvm import CadastroCiaEstrangReader

df_ = CadastroCiaEstrangReader().read()
# df_[["CNPJ", "DENOM_SOCIAL", "PAIS_ORIGEM", "SIT", "CNPJ_AUDITOR", "AUDITOR"]]
```

### Persistir a camada *bronze*

```python
from pathlib import Path
from filings_cvm import CadastroCiaEstrangReader

df_ = CadastroCiaEstrangReader(
    path_raw=Path("/data/bronze/cvm/cad_cia_estrang"),
).read()
# o CSV bruto fica em disco — o único registro do snapshot, que a CVM sobrescreve no lugar.
```

Cada `read` levanta `OSError` (falha de download) ou `ContractError` (CSV viola o contrato) — falha
cedo, sem devolver dados corrompidos.
