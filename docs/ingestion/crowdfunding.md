# **Cadastro de Plataformas de Crowdfunding (CROWDFUNDING) — leitura**

Leitura (← CVM) do cadastro das **plataformas eletrônicas de investimento participativo**
(*crowdfunding*) registradas na CVM, publicado no
[portal de dados abertos da CVM](https://dados.cvm.gov.br/dados/). Estes readers **inauguram** o
*portal root* `crowdfunding/` (irmão de `coord_oferta/`, `intermed/`, …).

> Quarta fatia da **Wave 4 do #41**. ZIP multi-membro, no molde do
> [COORD_OFERTA](coord_oferta.md) / [INTERMED](intermed.md), com os satélites sem data do
> [ADM_CART](adm_cart.md).

> **Veja também:** [Referência da API](../api.md) · [Uso](../usage.md).

---

## Descrição

| Reader | Membro do `cad_crowdfunding.zip` | Colunas | Colunas de data | Chave CNPJ |
|--------|----------------------------------|---------|-----------------|------------|
| `CrowdfundingReader` | `cad_crowdfunding.csv` (registro) | 17 | 2 | `CNPJ` |
| `CrowdfundingAdmRespReader` | `cad_crowdfunding_adm_resp.csv` | 2 | **0** | `CNPJ` (da plataforma) |
| `CrowdfundingSociosReader` | `cad_crowdfunding_socios.csv` | 2 | **0** | `CNPJ` (da plataforma) |

`CROWDFUNDING/CAD` publica um **ZIP de três membros**: o registro da plataforma (CNPJ, denominação
social/comercial, data de registro, situação, site, e-mail, endereço e telefone) e duas tabelas
satélite — **administradores responsáveis** e **sócios**. Como o `cad_fi.csv`, é um **retrato do
estado atual** numa **URL fixa** que a CVM sobrescreve no lugar — por isso **não há `date_ref`**, e
um `path_raw` persistido é o único registro do que o cadastro dizia no dia da coleta. Nenhum grão é
assumido.

⚠️ **Os 3 membros não são um split `pf`/`pj`** — são um registro mais dois satélites, **todos
chaveados pelo `CNPJ` da plataforma** (100% válidos nos três).

⚠️ **Os 2 satélites não têm NENHUMA coluna de data** (`_DATE_COLS = ()`, a forma do
[ADM_CART](adm_cart.md)) — todas as suas colunas voltam como texto exato. Eles carregam **dado
pessoal** (`ADM_RESP`; `SOCIO` mistura pessoa física e jurídica) mas **nenhuma coluna de CPF**: o
único identificador validado é o `CNPJ` da plataforma.

⚠️ **O registro é mais enxuto que os irmãos** — **não tem** `DT_CANCEL`, `MOTIVO_CANCEL` nem
`CD_CVM`, e grafa o site como `WEBSITE` (não `SITE_WEB`, do COORD_OFERTA) e o DDD como `DDD` (não
`DDD_TEL`). Copiar o contract de um irmão embarcaria colunas erradas **com todos os testes verdes**
— por isso o contract é **gerado do header publicado** e **pinado** a
`tests/fixtures/cad_crowdfunding/*_header.csv`, e a diferença tem teste próprio.

### Tipagem

As colunas `DT_REG` / `DT_INI_SIT` do registro viram `date` puro (brancos viram `NaT`); nos dois
satélites nada é convertido. Todo o restante mantém o **texto exato da CVM** — inclusive `CEP`,
`TEL` e `DDD`, que o META declara `numeric` mas são **identificadores, não quantidades** (um `CEP`
com zero à esquerda sobrevive). O mapa de tipos é derivado do contrato, então os dois não podem
divergir.

### META

⚠️ **A META deste dataset é um `.zip` de três membros** (`meta_cad_crowdfunding.zip`), **não um
`.txt`** — o palpite `meta_cad_crowdfunding.txt` devolve 404. A URL do META é uma **constante por
dataset**, nunca derivada da forma de um irmão. Como no INTERMED / COORD_OFERTA, as `section`
voltam **assimétricas** (`cad_crowdfunding`, `adm_resp`, `socios`), porque um membro tem o nome do
stem puro e não tem sufixo `<stem>_` a remover — comportamento documentado da base, honrado e
pinado por teste.

---

## Política de retry

Todo reader aceita `retry_policy: RetryPolicy | None = None` e declara o seu padrão em
`_RETRY_POLICY` (padrão paciente: 5 tentativas, *backoff* ~2, 4, 8, 10 s). Veja a
[visão geral da leitura](index.md#politica-de-retry-retry_policy-e-_retry_policy).

---

## Exemplos

### Plataformas registradas

```python
from filings_cvm import CrowdfundingReader

df_ = CrowdfundingReader().read()
# df_[["CNPJ", "DENOM_SOCIAL", "SIT", "WEBSITE", "MUN", "UF"]]
```

### Sócios + persistir a camada *bronze*

```python
from pathlib import Path
from filings_cvm import CrowdfundingSociosReader

df_ = CrowdfundingSociosReader(
    path_raw=Path("/data/bronze/cvm/cad_crowdfunding"),
).read()
# df_[["CNPJ", "SOCIO"]] — sem coluna de data: tudo é texto exato.
# o ZIP inteiro e os três membros ficam em disco: um path_raw de qualquer
# reader serve os outros (todos baixam o mesmo arquivo).
```

Cada `read` levanta `OSError` (falha de download), `ContractError` (CSV viola o contrato) ou
`ValueError` (membro ausente no arquivo) — falha cedo, sem devolver dados corrompidos.
