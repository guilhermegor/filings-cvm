# **Cadastro de Consultores de Valores Mobiliários (CONSULTOR_VLMOB) — leitura**

Leitura (← CVM) do cadastro dos **consultores de valores mobiliários** supervisionados pela CVM,
publicado no [portal de dados abertos da CVM](https://dados.cvm.gov.br/dados/). Estes readers
**inauguram** o *portal root* `consultor_vlmob/` (irmão de `fi/`, `adm_cart/`, `intermed/`, …).

> Sétima fatia da **Wave 3** do #41 — mesmo formato de 5 membros do [ADM_CART](adm_cart.md), mais
> simples. Fecha os roots de 5 membros; resta só o ADM_FII (CSV solto) para encerrar a Wave 3.

> **Veja também:** [Referência da API](../api.md) · [Uso](../usage.md).

---

## Descrição

| Reader | Membro do `cad_consultor_vlmob.zip` | Colunas | Colunas de data | Chave CNPJ |
|--------|-------------------------------------|---------|-----------------|------------|
| `ConsultorVlmobPfReader` | `cad_consultor_vlmob_pf.csv` (pessoa física) | 7 | 3 | — (não há coluna) |
| `ConsultorVlmobPjReader` | `cad_consultor_vlmob_pj.csv` (pessoa jurídica) | 20 | 3 | `CNPJ` (mascarado) |
| `ConsultorVlmobDiretorReader` | `cad_consultor_vlmob_diretor.csv` (diretores) | 3 | **0** | `CNPJ` (do consultor) |
| `ConsultorVlmobRespReader` | `cad_consultor_vlmob_resp.csv` (responsáveis) | 3 | **0** | `CNPJ` (do consultor) |
| `ConsultorVlmobSociosReader` | `cad_consultor_vlmob_socios.csv` (sócios) | 2 | **0** | `CNPJ` (do consultor) |

`CONSULTOR_VLMOB/CAD` publica um **ZIP de cinco membros**: os consultores **pessoa física** (nome,
datas e motivo de cancelamento, situação, site) e as **firmas** (o mesmo mais `CNPJ` mascarado,
denominação social/comercial, controle acionário, endereço, telefone, e-mail e site), acompanhados
de três tabelas satélite — **diretores**, **responsáveis** e **sócios** — todas chaveadas pelo
`CNPJ` do consultor. Como o `cad_fi.csv`, é um **retrato do estado atual** numa **URL fixa** que a
CVM sobrescreve no lugar — por isso **não há `date_ref`**, e um `path_raw` persistido é o único
registro do que o cadastro dizia no dia da coleta. Nenhum grão é assumido.

⚠️ **Três dos cinco membros não têm NENHUMA coluna de data** (`diretor`, `resp`, `socios`), como no
ADM_CART. Os readers correspondentes declaram `_DATE_COLS = ()` e **todas** as suas colunas voltam
como texto exato. O META confirma: esses três não declaram nenhum campo `date`.

⚠️ O membro **pessoa física não tem CNPJ nem CPF** — o cadastro identifica o consultor pessoa física
pelo `NOME`, então `tuple_cnpj_cols` é vazio (explícito) e não há chave única. Os membros
`diretor`/`resp`/`socios` carregam **dado pessoal** (`DIRETOR`, `RESP`, `SOCIOS` — nomes de pessoas)
mas **nenhuma coluna de CPF**: o único `CNPJ` é o do consultor, mascarado. Todos os `CNPJ` da fonte
são 100% válidos.

⚠️ **Não é cópia do ADM_CART.** O `pf` é chaveado por `NOME` (não `ADMIN`) e a 7ª coluna é
`SITE_ADMIN` (não `CATEG_REG`); o `pj` tem **20 colunas** (o do ADM_CART tem 24), sem
`CATEG_REG`/`SUBCATEG_REG`/`VL_PATRIM_LIQ`/`DT_PATRIM_LIQ` — logo o `pj` tem **só 3 colunas de
data**, não 4.

### Tipagem

As colunas `DT_*` viram `date` puro (brancos viram `NaT`); nos três membros sem data, nada é
convertido. Todo o restante mantém o **texto exato da CVM** — inclusive `CEP` e `TEL`, que o META
declara `numeric` mas são **identificadores, não quantidades** (o `CEP` já chega sem o zero à
esquerda). O `pj` usa `DDD` (como o ADM_CART), não `DDD_TEL`. O mapa de tipos é derivado do
contrato, então os dois não podem divergir.

---

## Política de retry

Todo reader aceita `retry_policy: RetryPolicy | None = None` e declara o seu padrão em
`_RETRY_POLICY` (padrão paciente: 5 tentativas, *backoff* ~2, 4, 8, 10 s). Veja a
[visão geral da leitura](index.md#politica-de-retry-retry_policy-e-_retry_policy).

---

## Exemplos

### Firmas consultoras (pessoa jurídica)

```python
from filings_cvm import ConsultorVlmobPjReader

df_ = ConsultorVlmobPjReader().read()
# df_[["CNPJ", "DENOM_SOCIAL", "SIT", "MUN", "UF", "EMAIL"]]
```

### Sócios + persistir a camada *bronze*

```python
from pathlib import Path
from filings_cvm import ConsultorVlmobSociosReader

df_ = ConsultorVlmobSociosReader(
    path_raw=Path("/data/bronze/cvm/cad_consultor_vlmob"),
).read()
# df_[["CNPJ", "SOCIOS"]] — sem coluna de data: tudo é texto exato.
# o ZIP inteiro e os cinco membros ficam em disco: um path_raw de qualquer
# reader serve os outros (todos baixam o mesmo arquivo).
```

Cada `read` levanta `OSError` (falha de download), `ContractError` (CSV viola o contrato) ou
`ValueError` (membro ausente no arquivo) — falha cedo, sem devolver dados corrompidos.
