# **META (metadados da CVM) — leitura**

Leitura (← CVM) dos **META** — a *especificação que a própria CVM publica* para cada dataset do
[portal de dados abertos](https://dados.cvm.gov.br/dados/). Um reader por dataset, **37 no total**,
todos sob `.../<DATASET>/META/`.

> **Veja também:** [Referência da API](../api.md) · [Uso](../usage.md) · [Proveniência](index.md).

---

## Por que o META importa

Contract, reader, fixture e teste codificam **a nossa crença** sobre um arquivo — então só podem
concordar entre si. **Um contract errado passa em 100% dos testes**, porque os testes afirmam o
contract que foi escrito. É por isso que `src/` nunca tem auto-merge aqui.

O META é o **único oráculo não-tautológico** disponível: ele vem da CVM, não de nós. É a descrição
declarada de cada campo — descrição, tipo, tamanho, domínio — que o *header* do artefato real não
carrega.

Evidência concreta: os 8 membros do [`INF_MENSAL_CRA`](inf_mensal_cra.md) têm os **mesmos nomes de
seção** do [`INF_MENSAL_OTS`](inf_mensal_ots.md), mas **nenhuma** lista de colunas igual. Copiar os
contracts do irmão teria embarcado 8 errados com tudo verde.

---

## ⚠️ Duas propriedades da fonte que este módulo **honra**, em vez de disfarçar

### 1. A CVM **trunca o nome do campo em exatamente 50 caracteres**

Medido, 8/8 no CRA: o header real traz nomes de até **60** caracteres; o META traz o prefixo de 50.

| onde | valor |
|---|---|
| header real (`fluxo_caixa`) | `Pagamentos_Classe_Subordinada_Mezanino_Amortizacao_Principal` (60) |
| META | `Pagamentos_Classe_Subordinada_Mezanino_Amortizacao` (50) |

O reader devolve o nome **truncado, verbatim**. "Consertar" fabricaria uma string que a CVM nunca
publicou e destruiria o valor de oráculo. **Reconciliar META ↔ header é trabalho do consumidor, e
tem de ser *truncation-aware*:** compare `header[:50] == meta`.

Consequência prática: **o META não serve como gate duro de nomes** — 8 campos do CRA dariam
falso-positivo de drift.

### 2. A ordem do META **nunca** é a ordem do arquivo real

Verificado: 0/8 seções do CRA batem. O `meta_cad_fi.txt` começa em `ADMIN, AUDITOR, CD_CVM` —
**alfabético**. O `meta_dfin_cra.txt` abre em `Data_Entrega`, enquanto o arquivo real abre em
`CNPJ_Emissora`.

> **O header do artefato real continua sendo a fonte da ordem — e dos nomes longos.** Os dois
> oráculos são **complementares**, não substitutos: o META vale por *nomes/tipos/semântica*, o
> header por *ordem*.

---

## ⚠️ A armadilha do `cad_fi`: mesmo radical, datasets diferentes

`FI/CAD/META/` publica três arquivos, e dois compartilham o radical:

| arquivo | dataset | conteúdo | reader |
|---|---|---|---|
| `meta_cad_fi.**txt**` | `cad_fi` | **41 campos** (o `cad_fi.csv`) | `MetaCadastroFiReader` |
| `meta_cad_fi.**zip**` | `cad_fi_**hist**` | **19 membros** (o log de alterações) | `MetaCadFiHistReader` |
| `meta_registro_fundo_classe.zip` | registro | 3 membros | `MetaRegistroReader` |

Qualquer regra do tipo *"derive o nome"* ou *"prefira o .zip"* entregaria silenciosamente o metadado
do **hist** para quem pediu `cad_fi`. Por isso **cada classe carrega a sua URL como constante** —
nunca derivada. Os nomes são irregulares de fato: `meta_inf_mensal_cri.zip`, mas
`meta_cda_fi_txt.zip` / `meta_lamina_fi_txt.zip` / `meta_inf_mensal_fidc_txt.zip` (infixo `_txt`).

---

## Os 37 readers

Todos devolvem **o mesmo formato**: uma linha por campo declarado.

| Coluna | Conteúdo |
|---|---|
| `section` | a seção — o membro do ZIP, ou o próprio dataset num META `.txt` solto |
| `field` | o nome do campo, **verbatim da CVM** (truncado em 50 quando for o caso) |
| `description` · `domain` · `data_type` · `size` · `precision` · `scale` | o que a CVM declara (texto exato, em pt-BR) |

Os nomes de coluna são **em inglês** porque o frame é uma **construção nossa** (a CVM não publica
tabela alguma) — como as seis colunas de proveniência. Os **valores** seguem verbatim da fonte.

| Portal root | Reader | META |
|---|---|---|
| `FI/DOC/INF_DIARIO` | `MetaInformeDiarioReader` | `.txt` |
| `FI/DOC/CDA` | `MetaCdaReader` | `.zip` |
| `FI/DOC/LAMINA` | `MetaLaminaReader` | `.zip` |
| `FI/CAD` | `MetaCadastroFiReader` | `.txt` (41 campos) |
| `FI/CAD` | `MetaCadFiHistReader` | `.zip` (19 membros) |
| `FI/CAD` | `MetaRegistroReader` | `.zip` (3 membros) |
| `FIDC/DOC/INF_MENSAL` | `MetaInfMensalFidcReader` | `.zip` |
| `FII/DOC/INF_MENSAL` | `MetaInfMensalFiiReader` | `.zip` |
| `FII/DOC/DFIN` | `MetaDfinFiiReader` | `.txt` |
| `FII/DOC/INF_TRIMESTRAL` | `MetaInfTrimestralFiiReader` | `.zip` |
| `FII/DOC/INF_ANUAL` | `MetaInfAnualFiiReader` | `.zip` |
| `FIP/DOC/INF_TRIMESTRAL` | `MetaInfTrimestralFipReader` | `.txt` |
| `FIP/DOC/INF_QUADRIMESTRAL` | `MetaInfQuadrimestralFipReader` | `.txt` |
| `FIAGRO/DOC/INF_MENSAL` | `MetaInfMensalFiagroReader` | `.zip` |
| `FIE/DOC/BALANCETE` | `MetaBalanceteFieReader` | `.txt` |
| `FIE/DOC/BALANCO` | `MetaBalancoFieReader` | `.txt` |
| `FIE/MEDIDAS` | `MetaMedidasMesFieReader` | `.txt` |
| `SECURIT/DOC/DFIN_CRA` | `MetaDfinCraReader` | `.txt` |
| `SECURIT/DOC/DFIN_CRI` | `MetaDfinCriReader` | `.txt` |
| `SECURIT/DOC/INF_MENSAL_OTS` | `MetaInfMensalOtsReader` | `.zip` |
| `SECURIT/DOC/INF_MENSAL_CRA` | `MetaInfMensalCraReader` | `.zip` |
| `SECURIT/DOC/INF_MENSAL_CRI` | `MetaInfMensalCriReader` | `.zip` (11 membros) |
| `EMISSOR_CEPAC/CAD` | `MetaCadEmissorCepacReader` | `.txt` |
| `AUDITOR/CAD` | `MetaAuditorReader` | `.zip` (2 membros) |
| `AGENTE_FIDUC/CAD` | `MetaAgenteFiducReader` | `.zip` (2 membros) |
| `AGENTE_AUTON/CAD` | `MetaAgenteAutonReader` | `.zip` (2 membros) |
| `INVNR/CAD` | `MetaInvnrRepresReader` | `.zip` (2 membros) |
| `INTERMED/CAD` | `MetaIntermedReader` | `.zip` (2 membros) |
| `ADM_CART/CAD` | `MetaAdmCartReader` | `.zip` (5 membros) |
| `CONSULTOR_VLMOB/CAD` | `MetaConsultorVlmobReader` | `.zip` (5 membros) |
| `ADM_FII/CAD` | `MetaCadAdmFiiReader` | `.txt` |
| `CIA_ESTRANG/CAD` | `MetaCadCiaEstrangReader` | `.txt` |
| `CIA_INCENT/CAD` | `MetaCadCiaIncentReader` | `.txt` |
| `COORD_OFERTA/CAD` | `MetaCoordOfertaReader` | `.zip` (2 membros) |
| `CROWDFUNDING/CAD` | `MetaCrowdfundingReader` | `.zip` (3 membros) |
| `OFERTA/DISTRIB` | `MetaOfertaReader` | `.zip` (2 membros) |
| `CIA_ABERTA/CAD` | `MetaCadCiaAbertaReader` | `.txt` |

> ℹ️ **`FIE/MEDIDAS`** publica `.csv` **e** `.txt`; usamos o **`.txt`**, o formato que os 37
> compartilham.

---

## **Sem `date_ref`** — e por que o `path_raw` importa mais aqui

O META fica numa **URL fixa**, e a CVM **sobrescreve no lugar** (o precedente do
[`CadastroFiReader`](cadastro_fi.md)). Não há partição por data para selecionar — então o construtor
não tem `date_ref`.

Consequência: **um `path_raw` gravado é o único registro do que a spec dizia naquele dia.** Sem ele,
a versão anterior é irrecuperável no dia em que a CVM mudar o contrato.

## Uso

```python
from pathlib import Path
from filings_cvm import MetaInfMensalCraReader

# A spec declarada dos 8 membros do INF_MENSAL_CRA.
df_meta = MetaInfMensalCraReader().read()

# Preservando os bytes crus para o bronze de um datalake (a CVM sobrescreve no lugar).
df_meta = MetaInfMensalCraReader(path_raw=Path("/data/bronze/cvm/meta")).read()
```

Um META `.zip` multi-membro volta como **um único frame longo**, com o nome do membro em `section`:

```python
df_meta["section"].unique()
# ['ativo_passivo', 'cedente_devedor', 'classe', 'derivativos',
#  'desembolso', 'direitos_creditorios', 'fluxo_caixa', 'geral']
```

Cada frame carrega, além das colunas da fonte, as seis colunas de [proveniência](index.md) (`url`,
`updated_at`, `source_key`, `package_version`, `ingestion_run_id`, `content_hash`). O `source_key` é
**prefixado com `meta_`** (`meta_inf_mensal_cra`) — sem isso, o META e o reader do mesmo dataset
ficariam indistinguíveis na mesma tabela do *bronze*, que é exatamente a ambiguidade que o
`source_key` existe para evitar.
