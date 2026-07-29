# **FRE Companhias Abertas — leitura**

Leitura (← CVM) do **Formulário de Referência** das companhias abertas (`fre_cia_aberta_AAAA.zip`),
publicado no
[portal de dados abertos da CVM](https://dados.cvm.gov.br/dados/CIA_ABERTA/DOC/FRE/DADOS/).

> **Veja também:** [Referência da API](../api.md) · [Uso](../usage.md) ·
> o [IPE](ipe_cia_aberta.md), o [VLMO](vlmo_cia_aberta.md), o [FCA](fca_cia_aberta.md) e o
> [CGVN](cgvn_cia_aberta.md).

---

## ⚠️ O maior dataset do portal — entregue em 4 fatias

O FRE tem **36 membros e ~131 mil linhas** (o FCA, o segundo maior, tem 10 membros). Está sendo
implementado em **4 PRs temáticos**, cada um revisável e releasável sozinho:

| fatia | tema | membros | estado |
|---|---|---|---|
| **1** | **índice + estrutura de capital** | **8** | ✅ **esta** |
| 2 | administração / pessoas (**todos os membros com CPF**) | 7 | ⬜ |
| 3 | diversidade (contagens agregadas) | 11 | ⬜ |
| 4 | remuneração + valores mobiliários + transações | 10 | ⬜ |

---

## Os 8 membros desta fatia

| reader | membro | cols | linhas (2025) | colunas de data |
|---|---|---|---|---|
| `FreCiaAbertaReader` | índice | 9 | 4.931 | `DT_REFER`, `DT_RECEB` |
| `FreCiaAbertaCapitalSocialReader` | `capital_social` | 13 | 2.402 | `Data_Referencia`, `Data_Autorizacao_Aprovacao` |
| `FreCiaAbertaCapitalSocialClasseAcaoReader` | `capital_social_classe_acao` | 8 | 292 | `Data_Referencia` |
| `FreCiaAbertaCapitalSocialTituloConversivelReader` | `capital_social_titulo_conversivel` | 8 | 26 | `Data_Referencia` |
| `FreCiaAbertaDistribuicaoCapitalReader` | `distribuicao_capital` | 15 | 700 | `Data_Referencia`, `Data_Ultima_Assembleia` |
| `FreCiaAbertaDistribuicaoCapitalClasseAcaoReader` | `distribuicao_capital_classe_acao` | 9 | 170 | `Data_Referencia` |
| `FreCiaAbertaResponsavelReader` | `responsavel` | 7 | 1.413 | `Data_Referencia` |
| `FreCiaAbertaMercadoEstrangeiroReader` | `mercado_estrangeiro` | 17 | 11 | `Data_Referencia`, `Data_Emissao`, `Data_Inicio_Listagem` |

**Particionado por ano** — o `date_ref` seleciona o **ano**, e **todos** os readers do FRE baixam o
**mesmo** arquivo (um `path_raw` escrito por um serve os outros).

---

## ⚠️ O índice não segue a convenção dos próprios satélites

| | índice | os 35 satélites |
|---|---|---|
| CNPJ | `CNPJ_CIA` | `CNPJ_Companhia` |
| data de referência | `DT_REFER` | `Data_Referencia` |
| denominação | `DENOM_CIA` | `Nome_Empresarial` |

O [FCA](fca_cia_aberta.md) faz **igual**; o [CGVN](cgvn_cia_aberta.md) **não** — o índice dele é
CamelCase. **Não há regra entre datasets do `DOC`, só medição por dataset.** A divergência é pinada
por teste **nas duas direções**, com o CGVN como contra-exemplo explícito.

⚠️ Ao longo dos 36 membros o FRE usa **seis** nomes de coluna de CNPJ — `CNPJ`, `CNPJ_Auditor`,
`CNPJ_CIA`, `CNPJ_Companhia`, `CNPJ_Emissor`, `CNPJ_Emissor_Pessoa_Relacionada`. Cada contrato
declara o seu; nada é herdado.

---

## Tipagem

Todas as colunas de data chegam **100% ISO** (só `Data_Ultima_Assembleia` tem algumas em branco, que
viram **`NaT`**). Todo o restante é **texto exato da fonte**, incluindo:

- `Valor_Capital` (monetário),
- `Quantidade_*` (contagens de ações e de acionistas),
- `Percentual_*` (percentuais de circulação).

Nunca um float binário: um `float64` perde a escala publicada de forma irreversível e silenciosa, e
`bin/check_dtypes.py` barra o atalho. Converta para `Decimal` a jusante se precisar de aritmética.

`responsavel.Nome_Responsavel` é nome de pessoa, mas **este membro não tem CPF** — os membros com
CPF do FRE ficam todos na **fatia 2**.

---

## Uso

```python
from datetime import date
from pathlib import Path

from filings_cvm import FreCiaAbertaCapitalSocialReader, FreCiaAbertaReader

# O índice dos formulários entregues no ano:
df_indice = FreCiaAbertaReader(date_ref=date(2025, 6, 15)).read()

# O capital social, guardando o .zip cru (serve às outras fatias também):
df_capital = FreCiaAbertaCapitalSocialReader(
    date_ref=date(2025, 6, 15),
    path_raw=Path("/data/bronze/cvm/fre"),
).read()

# Aritmética a jusante — Decimal, nunca float:
from decimal import Decimal

total = sum(Decimal(v) for v in df_capital["Valor_Capital"] if v)
```

O frame devolvido carrega, além das colunas da fonte, as seis colunas de
[proveniência](../api.md).

---

## META

A especificação da CVM sai em `MetaFreCiaAbertaReader` (o **42º** Meta reader) — veja
[META](meta.md).

⚠️ A URL é a forma **padrão** `meta_fre_cia_aberta.zip`; as outras 3 candidatas dão **404** —
inclusive `fre_cia_aberta.zip` **sem prefixo**, que é justamente a forma correta do
[FCA](fca_cia_aberta.md).

⚠️ O arquivo traz **50 membros para 36 membros de dados**, e a nomenclatura interna é **mista**: a
maioria tem o prefixo `meta_fre_cia_aberta*`, mas ao menos um
(`fre_cia_aberta_empregado_local_faixa_etaria.txt`) **não tem**. As seções a mais e o prefixo
inconsistente voltam **como publicados** — o parser rotula cada seção pelo nome do membro que
encontra, sem normalizar.
