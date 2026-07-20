# **Cadastro de Administradores de Carteira (ADM_CART) — leitura**

Leitura (← CVM) do cadastro dos **administradores de carteira** supervisionados pela CVM, publicado
no [portal de dados abertos da CVM](https://dados.cvm.gov.br/dados/). Estes readers **inauguram** o
*portal root* `adm_cart/` (irmão de `fi/`, `auditor/`, `intermed/`, …).

> Sexta fatia da **Wave 3** do #41 e o **primeiro root de 5 membros** — degrau acima do padrão de 2
> membros do [AUDITOR](auditor.md) / [INVNR](invnr.md) / [INTERMED](intermed.md).

> **Veja também:** [Referência da API](../api.md) · [Uso](../usage.md).

---

## Descrição

| Reader | Membro do `cad_adm_cart.zip` | Colunas | Colunas de data | Chave CNPJ |
|--------|------------------------------|---------|-----------------|------------|
| `AdmCartPfReader` | `cad_adm_cart_pf.csv` (pessoa física) | 7 | 3 | — (não há coluna) |
| `AdmCartPjReader` | `cad_adm_cart_pj.csv` (pessoa jurídica) | 24 | 4 | `CNPJ` (mascarado) |
| `AdmCartDiretorReader` | `cad_adm_cart_diretor.csv` (diretores) | 3 | **0** | `CNPJ` (do administrador) |
| `AdmCartRespReader` | `cad_adm_cart_resp.csv` (responsáveis) | 3 | **0** | `CNPJ` (do administrador) |
| `AdmCartSociosReader` | `cad_adm_cart_socios.csv` (sócios) | 2 | **0** | `CNPJ` (do administrador) |

`ADM_CART/CAD` publica um **ZIP de cinco membros**: os administradores **pessoa física** (nome,
datas e motivo de cancelamento, situação, categoria de registro) e as **firmas** (o mesmo mais
`CNPJ` mascarado, denominação social/comercial, sub-categoria, controle acionário, endereço,
telefone, patrimônio líquido, e-mail e site), acompanhados de três tabelas satélite — **diretores**,
**responsáveis** e **sócios** — todas chaveadas pelo `CNPJ` do administrador. Como o `cad_fi.csv`, é
um **retrato do estado atual** numa **URL fixa** que a CVM sobrescreve no lugar — por isso **não há
`date_ref`**, e um `path_raw` persistido é o único registro do que o cadastro dizia no dia da
coleta. Nenhum grão é assumido.

⚠️ **Três dos cinco membros não têm NENHUMA coluna de data** (`diretor`, `resp`, `socios`) — a
primeira ocorrência dessa forma na biblioteca. Os readers correspondentes declaram `_DATE_COLS = ()`
e **todas** as suas colunas voltam como texto exato. O META confirma: esses três não declaram
nenhum campo `date`.

⚠️ O membro **pessoa física não tem CNPJ nem CPF** — o cadastro identifica o administrador pessoa
física pelo `ADMIN` (o nome), então `tuple_cnpj_cols` é vazio (explícito) e não há chave única. Os
membros `diretor`/`resp`/`socios` carregam **dado pessoal** (`DIRETOR`, `RESP`, `SOCIOS` — nomes de
pessoas; `SOCIOS` mistura pessoa física e jurídica) mas **nenhuma coluna de CPF**: o único `CNPJ` é
o do administrador, mascarado.

⚠️ **Um CNPJ genuinamente malformado existe na fonte** — `00.010.354/1901-72`, presente em `pj` e
`resp`, reprova no dígito verificador. Como o contrato exige **ao menos um** CNPJ válido na coluna
(não todos), a leitura passa e o valor é **devolvido como publicado**, nunca filtrado ou
"corrigido".

### Tipagem

As colunas `DT_*` viram `date` puro (brancos viram `NaT`); nos três membros sem data, nada é
convertido. Todo o restante mantém o **texto exato da CVM** — inclusive `CEP` e `TEL`, que o META
declara `numeric` mas são **identificadores, não quantidades** (o `CEP` já chega sem o zero à
esquerda, ex. `1451010`). Note que o `pj` usa **`DDD`** (como o AGENTE_AUTON), não o `DDD_TEL` do
INVNR/INTERMED. O mapa de tipos é derivado do contrato, então os dois não podem divergir.

---

## Política de retry

Todo reader aceita `retry_policy: RetryPolicy | None = None` e declara o seu padrão em
`_RETRY_POLICY` (padrão paciente: 5 tentativas, *backoff* ~2, 4, 8, 10 s). Veja a
[visão geral da leitura](index.md#politica-de-retry-retry_policy-e-_retry_policy).

---

## Exemplos

### Firmas administradoras (pessoa jurídica)

```python
from filings_cvm import AdmCartPjReader

df_ = AdmCartPjReader().read()
# df_[["CNPJ", "DENOM_SOCIAL", "CATEG_REG", "SIT", "MUN", "UF"]]
```

### Sócios + persistir a camada *bronze*

```python
from pathlib import Path
from filings_cvm import AdmCartSociosReader

df_ = AdmCartSociosReader(
    path_raw=Path("/data/bronze/cvm/cad_adm_cart"),
).read()
# df_[["CNPJ", "SOCIOS"]] — sem coluna de data: tudo é texto exato.
# o ZIP inteiro e os cinco membros ficam em disco: um path_raw de qualquer
# reader serve os outros (todos baixam o mesmo arquivo).
```

Cada `read` levanta `OSError` (falha de download), `ContractError` (CSV viola o contrato) ou
`ValueError` (membro ausente no arquivo) — falha cedo, sem devolver dados corrompidos.
