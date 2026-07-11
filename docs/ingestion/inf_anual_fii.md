# **Informe Anual FII — leitura**

Leitura (← CVM) do **Informe Anual dos FII** (`inf_anual_fii_AAAA.zip`), publicado no
[portal de dados abertos da CVM](https://dados.cvm.gov.br/dados/FII/DOC/INF_ANUAL/DADOS/).
**Com este dataset o portal root `fii/` fica completo (4/4).**

> **Veja também:** [Referência da API](../api.md) · [Uso](../usage.md) ·
> [Informe Mensal FII](inf_mensal_fii.md) · [DFIN FII](dfin_fii.md) ·
> [Informe Trimestral FII](inf_trimestral_fii.md).

---

## Descrição

`inf_anual_fii_AAAA.zip` traz **12 membros**, cada um com o seu reader. Todos são chaveados por
`CNPJ_Fundo_Classe` + `Data_Referencia` + `Versao`:

| Reader | Membro | Conteúdo |
|--------|--------|----------|
| `InfAnualFiiGeralReader` | `geral` | Cadastro do fundo e administrador. |
| `InfAnualFiiComplementoReader` | `complemento` | Prestadores (gestor, custodiante, auditor, …), seções narrativas do exercício e o `Link_Download_Anexo`. |
| `InfAnualFiiAtivoAdquiridoReader` | `ativo_adquirido` | Ativos adquiridos no ano (objetivos, montante, origem dos recursos). |
| `InfAnualFiiAtivoTransacaoReader` | `ativo_transacao` | Transações de ativos (o maior membro). |
| `InfAnualFiiAtivoValorContabilReader` | `ativo_valor_contabil` | Valor contábil × valor justo de cada ativo. |
| `InfAnualFiiDistribuicaoCotistasReader` | `distribuicao_cotistas` | Cotistas por faixa de participação (até 5%, …, acima de 50%), PF × PJ. |
| `InfAnualFiiDiretorResponsavelReader` | `diretor_responsavel` | Diretor responsável (⚠️ contém **CPF**). |
| `InfAnualFiiExperienciaProfissionalReader` | `experiencia_profissional` | Histórico profissional dos diretores/representantes. |
| `InfAnualFiiPrestadorServicoReader` | `prestador_servico` | Prestadores de serviço (com `CNPJ_Prestador`). |
| `InfAnualFiiProcessoReader` | `processo` | Processos judiciais do fundo. |
| `InfAnualFiiProcessoSemelhanteReader` | `processo_semelhante` | Processos repetitivos agrupados por causa. |
| `InfAnualFiiRepresentanteCotistaReader` | `representante_cotista` | Representante dos cotistas (⚠️ contém **CPF**). |

Os 12 baixam o **mesmo** ZIP anual, então um `path_raw` gravado por qualquer um serve aos outros.
Aqui a partição anual é **natural** (é o informe *anual*) — ao contrário dos informes mensal e
trimestral do FII, onde o arquivo anual é a pegadinha.

**Sem chave única.** A maioria dos membros é **longa** — uma linha por ativo / transação / processo
/ prestador / diretor —, então um fundo aparece muitas vezes.

### Tipagem

Toda coluna é texto (`str`) exceto as `Data_*`, convertidas para `date` puro (vazios viram `NaT`).
Valores, quantidades e percentuais mantêm o **texto exato da CVM** — **nunca `float`**.

### ⚠️ Dois pontos de atenção

- **`Link_Download_Anexo`** (em `complemento`) é uma URL externa para o anexo protocolado. O reader
  a **devolve como texto e não a segue** — baixar o anexo é trabalho de camada superior, exatamente
  como o [`DfinFiiReader`](dfin_fii.md) trata o seu `Link_Download`.
- **`CPF`** (em `diretor_responsavel` e `representante_cotista`) é o identificador de uma **pessoa
  física**. É lido como texto exato e **nunca** validado como CNPJ — trate-o como **dado pessoal**
  na camada de destino.

`CNPJ_Fundo_Classe` é a única coluna validada como CNPJ; os CNPJs de contraparte
(`CNPJ_Prestador`, `CNPJ_Administrador`, e os do `complemento`) são lidos como texto.

---

## Política de retry

Como todo leitor da biblioteca, os 12 seguem o padrão de **`_RETRY_POLICY` por módulo**. Veja
[a visão geral da leitura](index.md#política-de-retry-retry_policy-e-_retry_policy).

---

## Exemplos

### Distribuição de cotistas de um ano

```python
from datetime import date
from filings_cvm import InfAnualFiiDistribuicaoCotistasReader

df_ = InfAnualFiiDistribuicaoCotistasReader(date_ref=date(2025, 6, 15)).read()
# faixas: Numero_Cotistas_Faixa_Ate_5, …, Percentual_Detido_PJ_Faixa_Acima_50
```

### Processos judiciais do fundo

```python
from datetime import date
from filings_cvm import InfAnualFiiProcessoReader

df_ = InfAnualFiiProcessoReader(date_ref=date(2025, 6, 15)).read()
# uma linha por processo: Juizo, Instancia, Data_Instauracao, Valor_Causa, Chance_Perda…
```

### Persistir o dump bruto (camada *bronze*) uma vez para os 12

```python
from datetime import date
from pathlib import Path
from filings_cvm import InfAnualFiiGeralReader

InfAnualFiiGeralReader(
    date_ref=date(2025, 6, 15),
    path_raw=Path("/data/bronze/cvm/inf_anual_fii/2025"),
).read()
```

Cada `read` levanta `OSError` (falha de download), `ContractError` (CSV viola o contrato) ou
`ValueError` (o ZIP não contém o membro daquele ano) — falha cedo, sem devolver dados corrompidos.
