# **Cadastro de Companhias Incentivadas (CIA_INCENT) — leitura**

Leitura (← CVM) do cadastro das **companhias incentivadas** registradas na CVM, publicado no
[portal de dados abertos da CVM](https://dados.cvm.gov.br/dados/). Este reader **inaugura** o
*portal root* `cia_incent/` (irmão de `cia_estrang/`, `fi/`, `adm_fii/`, …).

> Segunda fatia da **Wave 4 do #41** (companhias/ofertas). Um **CSV solto** de 1 reader — molde do
> [CIA_ESTRANG](cia_estrang.md) / [ADM_FII](adm_fii.md), não o multi-membro dos ZIPs.

> **Veja também:** [Referência da API](../api.md) · [Uso](../usage.md).

---

## Descrição

| Reader | Artefato | Colunas | Colunas de data | Chaves CNPJ |
|--------|----------|---------|-----------------|-------------|
| `CadastroCiaIncentReader` | `cad_cia_incent.csv` (CSV solto) | 47 | 7 | `CNPJ`, `CNPJ_AUDITOR` |

`CIA_INCENT/CAD` publica um **CSV solto** — não um ZIP — com uma linha por companhia incentivada
registrada (~3.570 linhas): `CNPJ` mascarado, denominação social/comercial, situação, categoria de
registro, controle acionário, endereço e contato (da companhia e do representante legal) e os dados
do auditor (`CNPJ_AUDITOR` + `AUDITOR`). Como o `cad_fi.csv` / `cad_cia_estrang.csv`, é um **retrato
do estado atual** numa **URL fixa** que a CVM sobrescreve no lugar — por isso **não há `date_ref`**,
e um `path_raw` persistido é o único registro do que o cadastro dizia no dia da coleta.

⚠️ **Não é cópia do CIA_ESTRANG.** Acrescenta `ST_CIA_INCENT_REG`, **não tem** `PAIS_ORIGEM` /
`CD_PAIS_*`, e usa `MUN` / `UF` (domésticos) no lugar de `CIDADE` / `ESTADO`. Por isso o contract é
próprio, **gerado do header e pinado** a `tests/fixtures/cad_cia_incent/cad_cia_incent_header.csv`
(47 colunas = risco real de transcrição — o header verbatim é o oráculo).

⚠️ **Duas colunas de CNPJ** — o da companhia (`CNPJ`, mascarado) e o do seu auditor
(`CNPJ_AUDITOR`) —, ambas exigidas com ao menos um CNPJ válido. `RESP` traz o **nome** do
representante legal (dado pessoal) mas **não há coluna de CPF**. `MOTIVO_CANCEL` é texto livre, não
uma data.

### Tipagem

As **sete** colunas `DT_*` (`DT_REG`, `DT_CONST`, `DT_CANCEL`, `DT_INI_SIT`, `DT_INI_CATEG`,
`DT_INI_SIT_EMISSOR`, `DT_INI_RESP`) viram `date` puro (brancos viram `NaT`). ⚠️ `DT_INI_CATEG`
está **100% vazia** no snapshot atual — ainda assim é coluna de data por contrato (o META a declara
e o irmão CIA_ESTRANG a preenche), então volta como tudo `NaT`. Todo o restante mantém o **texto
exato da CVM** — inclusive `CD_CVM`, `CEP`, `TEL` e `DDD_*`, que o META declara `numeric`/`char`
mas são **identificadores, não quantidades**. O mapa de tipos é derivado do contrato, então os dois
não podem divergir.

---

## Política de retry

O reader aceita `retry_policy: RetryPolicy | None = None` e declara o seu padrão em `_RETRY_POLICY`
(padrão paciente: 5 tentativas, *backoff* ~2, 4, 8, 10 s). Veja a
[visão geral da leitura](index.md#politica-de-retry-retry_policy-e-_retry_policy).

---

## Exemplos

### Companhias incentivadas

```python
from filings_cvm import CadastroCiaIncentReader

df_ = CadastroCiaIncentReader().read()
# df_[["CNPJ", "DENOM_SOCIAL", "SIT", "MUN", "UF", "CNPJ_AUDITOR", "AUDITOR"]]
```

### Persistir a camada *bronze*

```python
from pathlib import Path
from filings_cvm import CadastroCiaIncentReader

df_ = CadastroCiaIncentReader(
    path_raw=Path("/data/bronze/cvm/cad_cia_incent"),
).read()
# o CSV bruto fica em disco — o único registro do snapshot, que a CVM sobrescreve no lugar.
```

Cada `read` levanta `OSError` (falha de download) ou `ContractError` (CSV viola o contrato) — falha
cedo, sem devolver dados corrompidos.
