# **Recompra de Ações — leitura**

Leitura (← CVM) dos **programas de recompra de ações** das companhias abertas
(`cia_aberta_recompra_acoes.zip`), publicados no
[portal de dados abertos](https://dados.cvm.gov.br).

> **Ver também:** [Referência da API](../api.md) · [Uso](../usage.md) · os datasets `DOC` do mesmo
> root: [IPE](ipe_cia_aberta.md), [VLMO](vlmo_cia_aberta.md), [FCA](fca_cia_aberta.md),
> [CGVN](cgvn_cia_aberta.md), [FRE](fre_cia_aberta.md), [DFP](dfp_cia_aberta.md),
> [ITR](itr_cia_aberta.md).

**Com este dataset o portal root `cia_aberta/` fica COMPLETO.**

---

## Os 3 membros

**ZIP snapshot**, 0,09 MB, **nenhum ragged**. Os três se juntam por **`ID_Programa`**.

| reader | membro | cols | linhas | o que é |
|---|---|---|---|---|
| `RecompraAcoesReader` | `cia_aberta_recompra_acoes` | 11 | 1.916 | o **programa** |
| `RecompraAcoesIntermediariosReader` | `..._intermediarios` | 3 | 4.269 | corretoras do programa |
| `RecompraAcoesQuantidadesReader` | `..._quantidades` | 5 | 2.381 | quantidades por tipo/classe |

`ID_Programa` é **único no registro** (1.916 distintos em 1.916 linhas) e **repete** nos satélites —
um programa pode listar várias corretoras e vários tipos de ação.

---

## ⚠️⚠️ Este dataset NÃO segue os vizinhos do `DOC` — quatro divergências medidas

1. **É SNAPSHOT ⇒ sem `date_ref`.** Os 7 datasets do `DOC` são `<ds>_cia_aberta_AAAA.zip`; este tem
   **URL fixa**, no molde dos `CAD`. **Um único arquivo cobre de 1997 até hoje** (~28 anos), e a
   CVM **sobrescreve no lugar** — só um `path_raw` persistido guarda o retrato de um dia.
2. ⚠️ **O nome é INVERTIDO:** `cia_aberta_recompra_acoes.zip` põe o **root primeiro**, ao contrário
   de `dfp_cia_aberta_AAAA.zip` (dataset primeiro). Derivar do padrão do `DOC` erraria.
3. ⚠️ **Colunas em CamelCase** (`CNPJ_Companhia`, `Data_Deliberacao`) — como o
   [CGVN](cgvn_cia_aberta.md), e **não** como DFP/ITR/FCA, que usam `CNPJ_CIA`/`DT_REFER`. **Não há
   convenção do root**, só medição por dataset; o teste usa o DFP como contra-exemplo vivo.
4. ⚠️ **Dois dos três membros não têm NENHUMA coluna de data** — só o registro tem, e tem **duas**.

## ⚠️⚠️ `quantidades` não declara coluna de CNPJ — porque não tem nenhuma

O membro identifica apenas o programa a que pertence. Seu `tuple_cnpj_cols` é **vazio**, e isso é
**decisão medida, não esquecimento**: declarar uma coluna inventaria algo que a fonte não tem (e um
contrato que nomeia coluna inexistente falha toda leitura).

Como "vazio" e "esquecido" são indistinguíveis num diff, o teste afirma os **três** de uma vez — o
vazio **e** os dois irmãos que declaram (`CNPJ_Companhia` e `CNPJ_Intermediario`, ambos **100%
válidos**: 355 e 116 valores distintos).

## Tipagem

Colunas de data: **só no registro** — `Data_Deliberacao` e `Data_Final_Prazo`, ambas 100% ISO e
**sem branco**. Todo o restante é **texto exato**, incluindo `ID_Programa` (identificador) e
`Quantidade_*` (contagens).

⚠️ **Várias colunas chegam parcialmente vazias**, e vazio volta vazio — sem placeholder, sem zero:

| coluna | vazias |
|---|---|
| `Classe_Acao` | **2.322 / 2.381 (97,5%)** — ação ordinária não tem classe |
| `Quantidade_Acoes_Preferenciais` | 1.064 / 1.916 |
| `Quantidade_Acoes_Ordinarias` | 405 / 1.916 |
| `Finalidade_Compra` | 306 / 1.916 |
| `Motivo` | 304 / 1.916 |
| `Tipo_Operacao` | 302 / 1.916 |

## ⚠️ META

`meta_cia_aberta_recompra_acoes.zip` — medida de **duas formas independentes**: `HEAD` **200**, e a
listagem do diretório `META/`, onde é o **único** arquivo. As outras 5 grafias candidatas dão
**404**, inclusive o infixo `_txt` que é o correto do DFP e do ITR **neste mesmo root**.

---

## Uso

```python
from pathlib import Path

from filings_cvm.ingestion.cia_aberta import (
    RecompraAcoesIntermediariosReader,
    RecompraAcoesQuantidadesReader,
    RecompraAcoesReader,
)

# O registro dos programas (sem date_ref — é um snapshot):
df_programas = RecompraAcoesReader().read()

# Guardando o .zip cru na bronze (a CVM sobrescreve o arquivo no lugar):
df_programas = RecompraAcoesReader(path_raw=Path("/data/bronze/cvm/recompra")).read()

# Os satélites, para juntar por ID_Programa a jusante:
df_corretoras = RecompraAcoesIntermediariosReader().read()
df_quantidades = RecompraAcoesQuantidadesReader().read()

# Só os programas em andamento:
df_ativos = df_programas[df_programas["Situacao"] == "Em Andamento"]
```
