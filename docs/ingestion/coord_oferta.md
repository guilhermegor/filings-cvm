# **Cadastro de Coordenadores de Oferta (COORD_OFERTA) — leitura**

Leitura (← CVM) do cadastro das instituições registradas para **coordenar ofertas de valores
mobiliários**, publicado no [portal de dados abertos da CVM](https://dados.cvm.gov.br/dados/).
Estes readers **inauguram** o *portal root* `coord_oferta/` (irmão de `intermed/`, `fi/`, …).

> Terceira fatia da **Wave 4 do #41** e o **primeiro ZIP multi-membro da Wave 4** — volta ao molde
> do [INTERMED](intermed.md), não ao CSV solto de [CIA_ESTRANG](cia_estrang.md) /
> [CIA_INCENT](cia_incent.md).

> **Veja também:** [Referência da API](../api.md) · [Uso](../usage.md).

---

## Descrição

| Reader | Membro do `cad_coord_oferta.zip` | Colunas | Colunas de data | Chave CNPJ |
|--------|----------------------------------|---------|-----------------|------------|
| `CoordOfertaReader` | `cad_coord_oferta.csv` (registro) | 25 | 4 | `CNPJ` |
| `CoordOfertaRespReader` | `cad_coord_oferta_resp.csv` (responsáveis) | 6 | 2 | `CNPJ` (do coordenador) |

`COORD_OFERTA/CAD` publica um **ZIP de dois membros**: o registro do coordenador (CNPJ, denominação
social/comercial, datas e motivo de cancelamento, situação, código CVM, setor de atividade,
patrimônio líquido, endereço, telefone, fax, e-mail e site) e a tabela de **responsáveis**. Como o
`cad_fi.csv`, é um **retrato do estado atual** numa **URL fixa** que a CVM sobrescreve no lugar —
por isso **não há `date_ref`**, e um `path_raw` persistido é o único registro do que o cadastro
dizia no dia da coleta. Nenhum grão é assumido.

⚠️ **Os 2 membros NÃO são um split `pf`/`pj`** (ao contrário do
[AUDITOR](auditor.md) / [AGENTE_FIDUC](agente_fiduc.md) / [INVNR](invnr.md)) — são duas tabelas
relacionadas do mesmo cadastro, **ambas chaveadas pelo `CNPJ` do coordenador** (100% válidos nos
dois membros). É a mesma forma do [INTERMED](intermed.md).

⚠️ O membro `resp` carrega **dado pessoal** (`RESP`, o nome do responsável) mas **nenhuma coluna de
CPF** — o único identificador validado é o `CNPJ` do coordenador. `MOTIVO_CANCEL` é texto livre,
não uma data.

### Tipagem

As colunas `DT_*` viram `date` puro (brancos viram `NaT`) — 4 no registro (`DT_REG`, `DT_CANCEL`,
`DT_INI_SIT`, `DT_PATRIM_LIQ`) e 2 no `resp` (`DT_REG`, `DT_INI_RESP`). Todo o restante mantém o
**texto exato da CVM** — inclusive `CD_CVM`, `CEP`, `TEL`, `FAX` e `DDD_*`, que o META declara
`numeric`/`char` mas são **identificadores, não quantidades** (um `CEP` com zero à esquerda
sobrevive). O mapa de tipos é derivado do contrato, então os dois não podem divergir. Os contracts
são **gerados dos headers publicados** e **pinados** a `tests/fixtures/cad_coord_oferta/*_header.csv`.

### META

⚠️ **A META deste dataset é um `.zip` de dois membros** (`meta_cad_coord_oferta.zip`), **não um
`.txt`** — o palpite `meta_cad_coord_oferta.txt` devolve 404. A URL do META é uma **constante por
dataset**, nunca derivada da forma de um irmão. Como no INTERMED, as duas `section` voltam
**assimétricas** (`cad_coord_oferta` e `resp`), porque um membro tem o nome do stem puro e não tem
sufixo `<stem>_` a remover — comportamento documentado da base, honrado e pinado por teste.

---

## Política de retry

Todo reader aceita `retry_policy: RetryPolicy | None = None` e declara o seu padrão em
`_RETRY_POLICY` (padrão paciente: 5 tentativas, *backoff* ~2, 4, 8, 10 s). Veja a
[visão geral da leitura](index.md#politica-de-retry-retry_policy-e-_retry_policy).

---

## Exemplos

### Coordenadores de oferta

```python
from filings_cvm import CoordOfertaReader

df_ = CoordOfertaReader().read()
# df_[["CNPJ", "DENOM_SOCIAL", "SIT", "MUN", "UF", "VL_PATRIM_LIQ"]]
```

### Responsáveis + persistir a camada *bronze*

```python
from pathlib import Path
from filings_cvm import CoordOfertaRespReader

df_ = CoordOfertaRespReader(
    path_raw=Path("/data/bronze/cvm/cad_coord_oferta"),
).read()
# df_[["CNPJ", "TP_RESP", "RESP", "DT_INI_RESP"]]
# o ZIP inteiro e os dois membros ficam em disco: um path_raw de qualquer
# reader serve o outro (ambos baixam o mesmo arquivo).
```

Cada `read` levanta `OSError` (falha de download), `ContractError` (CSV viola o contrato) ou
`ValueError` (membro ausente no arquivo) — falha cedo, sem devolver dados corrompidos.
