# **Informe Mensal CRA (Securitização) — leitura**

Leitura (← CVM) do **Informe Mensal das operações de CRA** — *Certificado de Recebíveis do
Agronegócio* (`inf_mensal_cra_AAAA.zip`, dataset `SECURIT/DOC/INF_MENSAL_CRA`), publicado no
[portal de dados abertos da CVM](https://dados.cvm.gov.br/dados/SECURIT/DOC/INF_MENSAL_CRA/DADOS/).
Terceira fatia da **Wave 2** do #41 (Securitização).

> **Veja também:** [Referência da API](../api.md) · [Uso](../usage.md) ·
> [Informe Mensal OTS](inf_mensal_ots.md) (o irmão não-CRA/CRI).

---

## Descrição

`inf_mensal_cra_AAAA.zip` traz **8 membros** — as seções do informe mensal. Cada membro compartilha
o mesmo prefixo-chave de quatro colunas — `CNPJ_Emissora`, `Codigo_Identificacao_Certificado`,
`Data_Referencia`, `Versao` — e então carrega as colunas específicas da sua seção. Cada seção tem o
seu reader:

| Reader | Membro | Colunas | Conteúdo |
|--------|--------|---------|----------|
| `InfMensalCraGeralReader` | `geral` | 31 | Cadastro da operação (emissora, agente fiduciário, custodiante, emissão, lastro, cadeia produtiva, segmento, risco) |
| `InfMensalCraAtivoPassivoReader` | `ativo_passivo` | 31 | Ativo (direitos creditórios, caixa, derivativos) e passivo |
| `InfMensalCraClasseReader` | `classe` | 23 | Séries/classes emitidas (longo — uma linha por classe/série) |
| `InfMensalCraDireitosCreditoriosReader` | `direitos_creditorios` | **56** | Carteira de direitos creditórios + os *baldes agro* (produção, comercialização, beneficiamento, industrialização) |
| `InfMensalCraDesembolsoReader` | `desembolso` | 22 | Desembolsos programados por faixa de prazo |
| `InfMensalCraFluxoCaixaReader` | `fluxo_caixa` | 21 | Fluxo de caixa (recebimentos, aquisições, pagamentos por classe) |
| `InfMensalCraDerivativosReader` | `derivativos` | 20 | Exposição a derivativos (inclui *commodities agrícolas*) |
| `InfMensalCraCedenteDevedorReader` | `cedente_devedor` | 7 | Concentração de cedentes/devedores (longo) |

Os 8 baixam o **mesmo** ZIP anual, então um `path_raw` gravado por qualquer um serve aos outros.

> ⚠️ **Particionado por ANO, apesar de mensal.** O dump é `inf_mensal_cra_AAAA.zip` (membros
> `inf_mensal_cra_<seção>_AAAA.csv`), então o `date_ref` seleciona o **ano** — o padrão do OTS/FII,
> não o dos FIDC. O arquivo de um ano contém as linhas de todos os meses, chaveadas por
> `Data_Referencia`.

## ⚠️ Mesmos nomes de seção do OTS — e **nenhuma** lista de colunas igual

O `INF_MENSAL_CRA` e o [`INF_MENSAL_OTS`](inf_mensal_ots.md) têm as **mesmas 8 seções** e o mesmo
formato de reader. Parecem intercambiáveis — **não são**. O CRA é *agro*; o OTS é o residual
genérico. **Os 8 contracts diferem:**

| membro | OTS | CRA |
|---|---|---|
| todos os 8 | `CNPJ_Securitizadora` | **`CNPJ_Emissora`** |
| `direitos_creditorios` | 43 colunas | **56** — 13 baldes agro a mais (`_Producao`, `_Comercializacao`, `_Beneficiamento`, `_Industrializacao`, cada um também `_Insumos` / `_Maquinas`) |
| `geral` | 36 | 31 — acrescenta `Cadeia_Producao`, `Tipo_Segmento`, `Data_Ultima_Classificacao`; **derruba o bloco de contingências** |
| `derivativos` | `*_Commodities` | `*_Commodities_Agricolas` |
| `classe` | `Codigo_Negociacao_Mercado_Secundario`, `Total_Integralizado` | `Codigo_CETIP`, `Valor_Total_Integralizado` |
| `fluxo_caixa` | `Recebimentos_Creditos` | `Recebimentos_Direitos_Creditorios` |

Consequência: a grafia `Outras_Contigencias_Relevantes` (a *typo* preservada no OTS) **não existe
aqui** — quirk é fato de artefato, não de família.

Por isso cada contract deste dataset é **gerado do header publicado** e fica **pinado** a
`tests/fixtures/inf_mensal_cra/*_header.csv` (os bytes verbatim do header da CVM). Um contract
copiado do irmão falha o teste **offline, em menos de um segundo** — enquanto todo o resto da suíte
passaria, porque os testes afirmam o contract que foi escrito.

### Três armadilhas confirmadas nos bytes reais (honradas pelos readers)

1. **`CNPJ_Emissora` é a única coluna de CNPJ declarada.** A coluna `CNPJ` de `cedente_devedor`
   **não é coluna de CNPJ**: é campo de identificador livre e sujo. No arquivo de 2025 inteiro ela
   guarda CNPJs de 14 dígitos (7.090 linhas), **CPFs de 11 dígitos (327 — o cedente/devedor pode ser
   pessoa física)**, o placeholder `'0'` (2.352), uma vírgula solta `','` (103), um valor malformado
   de 15 dígitos (72) e até **dois identificadores na mesma célula** (12). Declará-la como CNPJ faria
   um arquivo válido falhar o contrato (a armadilha do `CPF_CNPJ_GESTOR` do `cad_fi`). É lida como
   texto exato e nunca validada — e, sendo CPF, é **dado pessoal** (verbatim no *bronze*, LGPD a
   jusante).
2. **`Indice_Subordinacao_Data_Base` (em `classe`) NÃO é data**, apesar do nome — os valores reais
   são numéricos (`0.00`). Fica texto exato; convertê-la pelo nome corromperia a coluna.
3. **`geral` tem 3 colunas 100% em branco** em 2025 — `CNPJ_Agente_Fiduciario`, `CNPJ_Custodiante` e
   `CNPJ_Agencia_Classificadora`. São publicadas, então entram no contract; mas ficam **fora** de
   `tuple_cnpj_cols`: não há o que validar hoje, e declará-las faria um arquivo válido falhar no dia
   em que a CVM começar a preenchê-las com o mesmo texto livre do `cedente_devedor.CNPJ`.

### Colunas de data por membro

| Membro | `_DATE_COLS` |
|---|---|
| `geral` | `Data_Referencia`, `Data_Entrega`, `Data_Emissao`, `Data_Ultima_Classificacao` |
| `classe` | `Data_Referencia`, `Data_Vencimento` — e **não** `Indice_Subordinacao_Data_Base` |
| os outros 6 | só `Data_Referencia` |

Todo o resto é **texto exato** (`str`): valores monetários, quantidades e percentuais mantêm a
precisão da fonte para um `Decimal` a jusante.

---

## Uso

```python
from datetime import date
from filings_cvm import InfMensalCraGeralReader, InfMensalCraCedenteDevedorReader

# O ano inteiro de 2025 (todos os meses), seção geral.
df_geral = InfMensalCraGeralReader(date_ref=date(2025, 6, 1)).read()

# Preservando o ZIP cru para o bronze de um datalake.
from pathlib import Path
df_cedentes = InfMensalCraCedenteDevedorReader(
	date_ref=date(2025, 6, 1),
	path_raw=Path("/data/bronze/cvm/inf_mensal_cra"),
).read()
```

Cada frame devolvido carrega, além das colunas da fonte, as seis colunas de
[proveniência](index.md) (`url`, `updated_at`, `source_key`, `package_version`, `ingestion_run_id`,
`content_hash`).

> ℹ️ O arquivo do **ano corrente é parcial** — cresce conforme os informes são entregues. Para um ano
> completo, passe um `date_ref` de um ano passado.
