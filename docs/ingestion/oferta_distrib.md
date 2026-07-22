# **Ofertas de Distribuição de Valores Mobiliários (OFERTA/DISTRIB) — leitura**

Leitura (← CVM) do registro das **ofertas de distribuição de valores mobiliários**, publicado no
[portal de dados abertos da CVM](https://dados.cvm.gov.br/dados/). Estes readers **inauguram** o
*portal root* `oferta/` (irmão de `coord_oferta/`, `securit/`, …) e fecham a issue #14.

> Quinta fatia da **Wave 4 do #41**. ZIP de **2 membros por regime regulatório** — a maior tabela de
> ofertas do portal, no molde do [COORD_OFERTA](coord_oferta.md) (base privada + membros), mas
> **não** um par registro+satélite.

> **Veja também:** [Referência da API](../api.md) · [Uso](../usage.md).

---

## Descrição

| Reader | Membro do `oferta_distribuicao.zip` | Colunas | Colunas de data | Chaves CNPJ |
|--------|-------------------------------------|---------|-----------------|-------------|
| `OfertaDistribuicaoReader` | `oferta_distribuicao.csv` (histórico, pré-RCVM 160) | 76 | 9 | `CNPJ_Emissor`, `CNPJ_Lider`, `CNPJ_Ofertante` |
| `OfertaResolucao160Reader` | `oferta_resolucao_160.csv` (RCVM 160) | 71 | 3 | `CNPJ_Emissor`, `CNPJ_Lider` |

`OFERTA/DISTRIB` publica um **ZIP de dois membros**, um por regime regulatório: o registro histórico
das ofertas (pré-RCVM 160, ~48,9 mil linhas) e os requerimentos de oferta sob a Resolução CVM 160
(~13,9 mil linhas). Cada linha traz os números de processo/registro, emissor/líder/ofertante (nomes
e CNPJs), datas, atributos do ativo e da oferta, e a quebra de investidores por tipo. Como os
cadastros, é um **retrato do estado atual** numa **URL fixa** que a CVM sobrescreve no lugar — por
isso **não há `date_ref`**, e um `path_raw` persistido é o único registro do que o arquivo dizia no
dia da coleta. Nenhum grão é assumido.

⚠️ **Os 2 membros NÃO são um par registro+satélite** (ao contrário do
[COORD_OFERTA](coord_oferta.md)) — são duas tabelas de ofertas de **regimes diferentes**, com
colunas disjuntas. Copiar uma na outra embarcaria o contract errado com todos os testes verdes; por
isso cada contract é **gerado do header publicado** e **pinado** a
`tests/fixtures/oferta_distribuicao/*_header.csv` (76/71 cols = risco real de transcrição), e a
diferença tem teste próprio.

### Tipagem

As colunas `Data_*` **em ISO** viram `date` puro (9 no histórico, 3 na RCVM 160). Todo o restante
mantém o **texto exato da CVM** — inclusive as dezenas de colunas de contagem (`Nr_*`, `Num_*`,
`Qtd_*`, `Qtde_*`) e os campos monetários (`Valor_*`, `Preco_*`), que preservam o texto decimal
exato para um cast a `Decimal` a jusante (o reader é fino; a camada gold computa). O mapa de tipos é
derivado do contrato, então os dois não podem divergir.

⚠️ **`Data_deliberacao_aprovou_oferta` (RCVM 160) chega em `DD/MM/YYYY`** (ex. `02/01/2023`), não no
ISO que todas as outras colunas de data usam. A coerção compartilhada é ISO-only (`pd.to_datetime`
sem `dayfirst`), então tratá-la como data **trocaria dia e mês silenciosamente**. Ela é exigida pelo
contrato mas fica deliberadamente **fora de `_DATE_COLS`** — volta como **`str`** exato, e um
consumidor parseia com `dayfirst=True`. Honrado, não "consertado".

### META

⚠️ **A META deste dataset é um `.zip` de dois membros** (`meta_oferta_distribuicao.zip`), **não um
`.txt`** — o palpite `meta_oferta_distribuicao.txt` devolve 404. A URL do META é uma **constante por
dataset**, nunca derivada da forma de um irmão. Os dois membros compartilham o prefixo `oferta_`,
então com `_MEMBER_STEM = "oferta"` as `section` voltam **simétricas** (`distribuicao`,
`resolucao_160`) — diferente do INTERMED/COORD_OFERTA, cujo membro de stem puro força o *fallback*
assimétrico.

---

## Política de retry

Todo reader aceita `retry_policy: RetryPolicy | None = None` e declara o seu padrão em
`_RETRY_POLICY` (padrão paciente: 5 tentativas, *backoff* ~2, 4, 8, 10 s). Veja a
[visão geral da leitura](index.md#politica-de-retry-retry_policy-e-_retry_policy).

---

## Exemplos

### Ofertas históricas (pré-RCVM 160)

```python
from filings_cvm import OfertaDistribuicaoReader

df_ = OfertaDistribuicaoReader().read()
# df_[["Numero_Registro_Oferta", "Tipo_Oferta", "Nome_Emissor", "Valor_Total"]]
```

### Requerimentos RCVM 160 + persistir a camada *bronze*

```python
from pathlib import Path
from filings_cvm import OfertaResolucao160Reader

df_ = OfertaResolucao160Reader(
    path_raw=Path("/data/bronze/cvm/oferta_distribuicao"),
).read()
# df_[["Numero_Requerimento", "Status_Requerimento", "Nome_Emissor", "Valor_Total_Registrado"]]
# o ZIP inteiro e os dois membros ficam em disco: um path_raw de qualquer
# reader serve o outro (ambos baixam o mesmo arquivo).
```

Cada `read` levanta `OSError` (falha de download), `ContractError` (CSV viola o contrato) ou
`ValueError` (membro ausente no arquivo) — falha cedo, sem devolver dados corrompidos.
