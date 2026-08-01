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
| **1** | **índice + estrutura de capital** | **8** | ✅ |
| **2** | **administração / pessoas (todos os membros com CPF)** | **7** | ✅ **esta** |
| 3 | diversidade (contagens agregadas) | 11 | ⬜ |
| 4 | remuneração + valores mobiliários + transações | 10 | ⬜ |

---

## Os 8 membros da fatia 1 — índice + capital

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

## Os 7 membros da fatia 2 — administração / pessoas

| reader | membro | cols | linhas (2025) | colunas de data |
|---|---|---|---|---|
| `FreCiaAbertaAuditorReader` | `auditor` | 18 | 1.097 | `Data_Referencia`, `Data_Inicio_Contratacao`, `Data_Fim_Contratacao`, `Data_Inicio_Prestacao_Servico` |
| `FreCiaAbertaAdministradorMembroConselhoFiscalReader` | `administrador_membro_conselho_fiscal` | 21 | 8.988 | `Data_Referencia`, `Data_Eleicao`, `Data_Posse`, `Data_Inicio_Primeiro_Mandato`, `Data_Nascimento` |
| `FreCiaAbertaMembroComiteReader` | `membro_comite` | 21 | 4.538 | as mesmas 5 do anterior |
| `FreCiaAbertaRelacaoFamiliarReader` | `relacao_familiar` | 17 | 1.698 | `Data_Referencia` |
| `FreCiaAbertaRelacaoSubordinacaoReader` | `relacao_subordinacao` | 17 | 9.102 | `Data_Referencia`, `Data_Inicio_Exercicio_Social`, `Data_Fim_Exercicio_Social` |
| `FreCiaAbertaPosicaoAcionariaReader` | `posicao_acionaria` | 29 | 31.508 | `Data_Referencia`, `Data_Composicao_Capital_Social`, `Data_Ultima_Alteracao` |
| `FreCiaAbertaPosicaoAcionariaClasseAcaoReader` | `posicao_acionaria_classe_acao` | 9 | 2.092 | `Data_Referencia` |

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

## ⚠️ Coluna de CNPJ é a que **só** guarda CNPJ — o nome não é o teste

Quase todo membro declara só o `CNPJ_Companhia`, mas **dois declaram mais**, e **três colunas que
parecem identificador ficam de fora**. Cada caso foi decidido contando os valores reais de 2025:

| membro | declara | fica de fora | por quê |
|---|---|---|---|
| `auditor` | `CNPJ_Companhia`, `CNPJ_Auditor` | `CPF_Auditor` | CPF é dado pessoal |
| `relacao_familiar` | `CNPJ_Companhia`, `CNPJ_Emissor`, `CNPJ_Emissor_Pessoa_Relacionada` | 2 colunas de CPF | idem |
| `relacao_subordinacao` | `CNPJ_Companhia` | **`Documento_Pessoa_Relacionada`** | guarda **CNPJ e CPF** (8.462 × 34) |
| `posicao_acionaria` | `CNPJ_Companhia` | as 3 `CPF_CNPJ_*` | mistas por definição |

`Documento_Pessoa_Relacionada` é o caso que uma regra pelo nome erra: **não diz nem CPF nem CNPJ, e
guarda os dois** (tipados pela coluna irmã `Tipo_Pessoa_Relacionada`, `PJ`/`PF`). Uma coluna mista
declarada passaria no ano em que os valores fossem todos CNPJ e quebraria no primeiro CPF.

⚠️ **O estilo de máscara não é uniforme nem dentro de um membro:** em `auditor`, `CNPJ_Companhia`
vem pontuado (`00.000.000/0001-91`) e `CNPJ_Auditor`, na mesma linha, vem em dígitos crus
(`49928567000111`). Os dois são declarados — o validador normaliza a pontuação — e voltam **como
publicados**.

---

## Tipagem

Todas as colunas de data chegam **100% ISO**; branco vira **`NaT`**. Duas chegam **inteiramente
vazias** em 2025 — `auditor.Data_Fim_Contratacao` (contrato em aberto não tem fim) e
`posicao_acionaria.Data_Composicao_Capital_Social` — e **seguem sendo data por contrato**: um ano
vazio não rebaixa a coluna para texto.

Todo o restante é **texto exato da fonte**, incluindo `Valor_Capital` (monetário), `Quantidade_*` e
`Numero_*` (contagens) e `Percentual_*`.

Nunca um float binário: um `float64` perde a escala publicada de forma irreversível e silenciosa, e
`bin/check_dtypes.py` barra o atalho. Converta para `Decimal` a jusante se precisar de aritmética.

---

## ⚠️ Dado pessoal (LGPD) — a fatia 2 concentra todo o CPF do FRE

Seis dos sete membros desta fatia carregam CPF, e vários carregam nome, profissão e **data de
nascimento** de pessoa física. Tudo volta **como publicado**, sem mascarar e sem reformatar, mas:

- **nenhuma coluna de CPF entra em `tuple_cnpj_cols`** — CPF não é identificador de empresa;
- as **fixtures de teste são só cabeçalho**, sem uma linha de dado, para que nenhum CPF real entre
  no repositório.

`posicao_acionaria_classe_acao` é o **único membro da fatia sem dado pessoal** — identifica o
acionista só pelo `ID_Acionista`.

⚠️ `posicao_acionaria` grafa `CPF_CNPJ_Representante_legal` com **`legal` minúsculo**, ao contrário
das duas colunas irmãs. A grafia é preservada **verbatim**: "corrigir" faria a coluna não ser
encontrada no arquivo real.

⚠️ Os membros de **diversidade** (`*_declaracao_raca`, `*_declaracao_genero`, `*_PCD`,
`*_faixa_etaria`, na fatia 3) **não** são dado pessoal sensível — são **contagens agregadas** por
companhia (`Quantidade_Preto`, `Quantidade_Feminino`). O nome do membro sugere o contrário; medir as
colunas desmentiu.

---

## Uso

```python
from datetime import date
from pathlib import Path

from filings_cvm import (
    FreCiaAbertaCapitalSocialReader,
    FreCiaAbertaPosicaoAcionariaReader,
    FreCiaAbertaReader,
)

# O índice dos formulários entregues no ano:
df_indice = FreCiaAbertaReader(date_ref=date(2025, 6, 15)).read()

# O capital social, guardando o .zip cru (serve às outras fatias também):
df_capital = FreCiaAbertaCapitalSocialReader(
    date_ref=date(2025, 6, 15),
    path_raw=Path("/data/bronze/cvm/fre"),
).read()

# A base acionária — o maior membro da fatia 2 (31.508 linhas em 2025):
df_acionistas = FreCiaAbertaPosicaoAcionariaReader(date_ref=date(2025, 6, 15)).read()

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
