# **Cadastro de Companhias Abertas (CIA_ABERTA/CAD) — leitura**

Leitura (← CVM) do cadastro das **companhias abertas** registradas na CVM, publicado no
[portal de dados abertos da CVM](https://dados.cvm.gov.br/dados/). Este reader **inaugura** o
*portal root* `cia_aberta/` — a **última e maior raiz** da Wave 4 do #41.

> ⚠️ **CIA_ABERTA é grande — esta página cobre SÓ o `CAD`.** O root tem 9 datasets: `CAD` (este
> cadastro) + 7 sob `DOC/` (CGVN, DFP, FCA, FRE, IPE, ITR, VLMO — demonstrações financeiras, ZIPs
> multi-membro) + `EVENTOS/RECOMPRA_ACOES`. Cada um ganha o seu próprio reader.

> **Veja também:** [Referência da API](../api.md) · [Uso](../usage.md).

---

## Descrição

| Reader | Artefato | Colunas | Colunas de data | Chaves CNPJ |
|--------|----------|---------|-----------------|-------------|
| `CadastroCiaAbertaReader` | `cad_cia_aberta.csv` (CSV solto) | 47 | 7 | `CNPJ_CIA`, `CNPJ_AUDITOR` |

`CIA_ABERTA/CAD` publica um **CSV solto** — não um ZIP — com uma linha por companhia aberta
registrada (~2.677 linhas): `CNPJ_CIA` mascarado, denominação social/comercial, situação, tipo de
mercado, categoria de registro, controle acionário, endereço e contato (da companhia e do
representante), e os dados do auditor (`CNPJ_AUDITOR` + `AUDITOR`). Como os demais cadastros, é um
**retrato do estado atual** numa **URL fixa** que a CVM sobrescreve no lugar — por isso **não há
`date_ref`**, e um `path_raw` persistido é o único registro do que o cadastro dizia no dia da coleta.

⚠️ **Não é cópia do CIA_ESTRANG / CIA_INCENT** — a chave da companhia é `CNPJ_CIA` (não `CNPJ`), e
acrescenta `TP_MERC` (tipo de mercado). Por isso o contract é próprio, **gerado do header e pinado**
a `tests/fixtures/cad_cia_aberta/cad_cia_aberta_header.csv` (47 colunas = risco real de
transcrição — o header verbatim é o oráculo).

⚠️ **Duas colunas de CNPJ** — o da companhia (`CNPJ_CIA`, mascarado) e o do seu auditor
(`CNPJ_AUDITOR`) —, ambas exigidas com ao menos um CNPJ válido. `RESP` traz o **nome** do
representante (dado pessoal) mas **não há coluna de CPF**. `MOTIVO_CANCEL` é texto livre, não data.

### Tipagem

As **sete** colunas `DT_*` (`DT_REG`, `DT_CONST`, `DT_CANCEL`, `DT_INI_SIT`, `DT_INI_CATEG`,
`DT_INI_SIT_EMISSOR`, `DT_INI_RESP`) viram `date` puro (brancos viram `NaT`). Todo o restante
mantém o **texto exato da CVM** — inclusive `CD_CVM`, `CEP`, `TEL`, `FAX` e `DDD_*`, que o META
declara `numeric`/`char` mas são **identificadores, não quantidades**. O mapa de tipos é derivado do
contrato, então os dois não podem divergir.

---

## Política de retry

O reader aceita `retry_policy: RetryPolicy | None = None` e declara o seu padrão em `_RETRY_POLICY`
(padrão paciente: 5 tentativas, *backoff* ~2, 4, 8, 10 s). Veja a
[visão geral da leitura](index.md#politica-de-retry-retry_policy-e-_retry_policy).

---

## Exemplos

### Companhias abertas

```python
from filings_cvm import CadastroCiaAbertaReader

df_ = CadastroCiaAbertaReader().read()
# df_[["CNPJ_CIA", "DENOM_SOCIAL", "TP_MERC", "SIT", "CNPJ_AUDITOR", "AUDITOR"]]
```

### Persistir a camada *bronze*

```python
from pathlib import Path
from filings_cvm import CadastroCiaAbertaReader

df_ = CadastroCiaAbertaReader(
    path_raw=Path("/data/bronze/cvm/cad_cia_aberta"),
).read()
# o CSV bruto fica em disco — o único registro do snapshot, que a CVM sobrescreve no lugar.
```

Cada `read` levanta `OSError` (falha de download) ou `ContractError` (CSV viola o contrato) — falha
cedo, sem devolver dados corrompidos.
