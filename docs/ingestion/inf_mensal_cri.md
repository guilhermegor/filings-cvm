# **Informe Mensal CRI (Securitização) — leitura**

Leitura (← CVM) do **Informe Mensal das operações de CRI** — *Certificado de Recebíveis
Imobiliários* (`inf_mensal_cri_AAAA.zip`, dataset `SECURIT/DOC/INF_MENSAL_CRI`), publicado no
[portal de dados abertos da CVM](https://dados.cvm.gov.br/dados/SECURIT/DOC/INF_MENSAL_CRI/DADOS/).
**Quarta e última fatia da Wave 2** do #41 (Securitização) — **com este, o portal root `securit/`
está completo (4/4)**.

> **Veja também:** [Referência da API](../api.md) · [Uso](../usage.md) ·
> [Informe Mensal CRA](inf_mensal_cra.md) (o irmão agro) ·
> [Informe Mensal OTS](inf_mensal_ots.md) (o residual não-CRA/CRI).

---

## Descrição

`inf_mensal_cri_AAAA.zip` traz **11 membros** — as seções do informe mensal. Cada membro compartilha
o mesmo prefixo-chave de quatro colunas — `CNPJ_Emissora`, `Codigo_Identificacao_Certificado`,
`Data_Referencia`, `Versao` — e então carrega as colunas específicas da sua seção. Cada seção tem o
seu reader:

| Reader | Membro | Colunas | Conteúdo |
|--------|--------|---------|----------|
| `InfMensalCriGeralReader` | `geral` | 44 | Cadastro da operação (emissora, agente fiduciário, custodiante, emissão, lastro, LTV, risco) |
| `InfMensalCriAtivoPassivoReader` | `ativo_passivo` | 65 | Balanço (ativo, passivo, derivativos) + a cascata de pagamentos |
| `InfMensalCriClasseReader` | `classe` | 28 | Séries/classes emitidas (longo — uma linha por classe/série) |
| `InfMensalCriCreditosReader` | `creditos` | 51 | Carteira de recebíveis imobiliários (incorporação, aluguéis, aquisição, loteamento, multipropriedade, home equity), aging e concentração |
| `InfMensalCriCarteiraReader` | `carteira` | 29 | Carteira de créditos vinculados por faixa de prazo/inadimplência (**exclusivo do CRI**) |
| `InfMensalCriCarteiraModificacaoReader` | `carteira_modificacao` | 7 | Eventos de modificação de carteira (**exclusivo do CRI**; esparso) |
| `InfMensalCriDesembolsoReader` | `desembolso` | 22 | Desembolsos (despesas/investidores) por faixa de prazo |
| `InfMensalCriFluxoCaixaReader` | `fluxo_caixa` | 21 | Fluxo de caixa (recebimentos, despesas, tranches sênior/mezanino/júnior) |
| `InfMensalCriDerivativosReader` | `derivativos` | 20 | Exposição a derivativos por mercado e subjacente |
| `InfMensalCriCedenteDevedorReader` | `cedente_devedor` | 7 | Concentração de cedentes/devedores (longo) |
| `InfMensalCriResponsavelReader` | `responsavel` | 6 | Responsável pelo informe (**exclusivo do CRI**; esparso) |

Os 11 baixam o **mesmo** ZIP anual, então um `path_raw` gravado por qualquer um serve aos outros.

> ⚠️ **Particionado por ANO, apesar de mensal.** O dump é `inf_mensal_cri_AAAA.zip` (membros
> `inf_mensal_cri_<seção>_AAAA.csv`), então o `date_ref` seleciona o **ano** — o padrão do OTS/CRA,
> não o dos FIDC. O arquivo de um ano contém as linhas de todos os meses, chaveadas por
> `Data_Referencia`.

## ⚠️ Compartilha nomes de seção com CRA/OTS — mas o CRI é imobiliário, não uma cópia

O `INF_MENSAL_CRI` compartilha **sete nomes de seção** com o [`INF_MENSAL_CRA`](inf_mensal_cra.md) e
o [`INF_MENSAL_OTS`](inf_mensal_ots.md), mas **não tem `direitos_creditorios`** — a sua seção de
recebíveis é `creditos` (51 colunas, crédito imobiliário) — e **acrescenta quatro membros** que não
existem no CRA/OTS: `carteira`, `carteira_modificacao`, `creditos` e `responsavel`.

Das sete seções compartilhadas, cinco diferem do CRA (`geral`, `ativo_passivo`, `classe`,
`fluxo_caixa`, `derivativos`) e **duas são de fato idênticas** — `desembolso` (22) e
`cedente_devedor` (7) — por serem estruturas genéricas (baldes de prazo de pagamento; a tupla
cedente/devedor) sem conteúdo específico de classe de ativo. Essa coincidência é **da fonte**,
provada pelo oráculo de header pinado, e **não** um erro de cópia.

Por isso cada contract deste dataset é **gerado do header publicado** e fica **pinado** a
`tests/fixtures/inf_mensal_cri/*_header.csv` (os bytes verbatim do header da CVM). Um contract
copiado do irmão falha o teste **offline, em menos de um segundo** — enquanto todo o resto da suíte
passaria, porque os testes afirmam o contract que foi escrito.

## Armadilhas honradas (verificadas nos bytes reais de 2025)

- **`cedente_devedor.CNPJ` NÃO é uma coluna de CNPJ** — é um identificador de texto livre que pode
  guardar um **CPF** quando o cedente/devedor é pessoa física. Fica fora de `tuple_cnpj_cols` (é
  lido como texto exato; sendo CPF, é dado pessoal — verbatim no bronze, LGPD tratada a jusante).
- **`classe.Indice_Subordinacao_Data_Base` NÃO é data**, apesar do nome — os valores reais são
  numéricos (`0.00`). Fica `str`.
- **`geral.Data_LTV` NÃO é data** — o META da CVM declara **`varchar`** (e a coluna é 100% vazia em
  2025). Segue `str`, na palavra do META, não do nome.
- **`geral` tem três colunas `CNPJ_*` 100% vazias** (`CNPJ_Agente_Fiduciario`, `CNPJ_Custodiante`,
  `CNPJ_Agencia_Classificadora`) — publicadas (logo no contract), mas fora de `tuple_cnpj_cols`.
- **`carteira_modificacao` e `responsavel` são header-only em 2025** (zero linhas — uma modificação
  e o responsável são registrados só em circunstâncias específicas). Um membro sem linhas não tem
  CNPJ a validar, então esses dois declaram `tuple_cnpj_cols` vazio — do contrário um arquivo
  legitimamente vazio falharia o contract.
- **`geral.Outras_Contigencias_Relevantes`** preserva a grafia da CVM **verbatim** (o CRI mantém o
  bloco de contingências que o CRA derruba).

## Uso

```python
from datetime import date

from filings_cvm import InfMensalCriGeralReader

# O ano de 2025 (o dump é particionado por ano, apesar de mensal).
df = InfMensalCriGeralReader(date_ref=date(2025, 6, 15)).read()

# Persistindo o ZIP bruto (camada bronze de um datalake):
df = InfMensalCriGeralReader(date_ref=date(2025, 6, 15), path_raw="./bronze").read()
```

Cada frame vem tipado e carimbado com as seis colunas de proveniência
(`url`, `updated_at`, `source_key`, `package_version`, `ingestion_run_id`, `content_hash`).
