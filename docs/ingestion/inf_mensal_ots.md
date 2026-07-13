# **Informe Mensal OTS (Securitização) — leitura**

Leitura (← CVM) do **Informe Mensal das Operações de Securitização** não-CRA/CRI
(`inf_mensal_ots_AAAA.zip`, dataset `SECURIT/DOC/INF_MENSAL_OTS`), publicado no
[portal de dados abertos da CVM](https://dados.cvm.gov.br/dados/SECURIT/DOC/INF_MENSAL_OTS/DADOS/).
Segunda fatia da **Wave 2** do #41 (Securitização).

> **Veja também:** [Referência da API](../api.md) · [Uso](../usage.md).

---

## Descrição

`inf_mensal_ots_AAAA.zip` traz **8 membros** — as seções do informe mensal. Cada membro compartilha
o mesmo prefixo-chave de quatro colunas — `CNPJ_Securitizadora`, `Codigo_Identificacao_Certificado`,
`Data_Referencia`, `Versao` — e então carrega as colunas específicas da sua seção. Cada seção tem o
seu reader:

| Reader | Membro | Conteúdo |
|--------|--------|----------|
| `InfMensalOtsGeralReader` | `geral` | Cadastro da operação (securitizadora, agente fiduciário, custodiante, emissão, lastro, totais, risco, contingências) |
| `InfMensalOtsAtivoPassivoReader` | `ativo_passivo` | Ativo (direitos creditórios, caixa, derivativos) e passivo |
| `InfMensalOtsClasseReader` | `classe` | Séries/classes emitidas (longo — uma linha por classe/série) |
| `InfMensalOtsDireitosCreditoriosReader` | `direitos_creditorios` | Carteira de direitos creditórios (a vencer/não pagos por faixa, garantias, concentração) |
| `InfMensalOtsDesembolsoReader` | `desembolso` | Desembolsos programados por faixa de prazo |
| `InfMensalOtsFluxoCaixaReader` | `fluxo_caixa` | Fluxo de caixa (recebimentos, pagamentos por classe) |
| `InfMensalOtsDerivativosReader` | `derivativos` | Exposição a derivativos (mercado × fator de risco) |
| `InfMensalOtsCedenteDevedorReader` | `cedente_devedor` | Concentração de cedentes/devedores (longo) |

Os 8 baixam o **mesmo** ZIP anual, então um `path_raw` gravado por qualquer um serve aos outros.

> ⚠️ **Particionado por ANO, apesar de mensal.** O dump é `inf_mensal_ots_AAAA.zip` (membros
> `inf_mensal_ots_<seção>_AAAA.csv`), então o `date_ref` seleciona o **ano** — o padrão dos FII, não
> o dos FIDC. O arquivo de um ano contém as linhas de todos os meses, chaveadas por `Data_Referencia`.

### Três armadilhas confirmadas nos bytes reais (honradas pelos readers)

1. **`CNPJ_Securitizadora` é a única coluna de CNPJ.** A coluna `CNPJ` de `cedente_devedor` guarda um
   **CPF em 257 de 1650 linhas** (o cedente/devedor pode ser pessoa física) — declará-la como CNPJ
   faria um arquivo válido falhar o contrato (a armadilha do `CPF_CNPJ_GESTOR` do `cad_fi`). É lida
   como texto exato e nunca validada — e, sendo CPF, é **dado pessoal** (verbatim no *bronze*, LGPD a
   jusante).
2. **`Indice_Subordinacao_Data_Base` (em `classe`) NÃO é data**, apesar do nome — os valores reais
   são numéricos. Fica texto exato; convertê-la pelo nome corromperia a coluna.
3. **Grafia da CVM preservada verbatim:** `Outras_Contigencias_Relevantes` em `geral` (falta o *n* de
   *Contingências*) — enquanto `Contingencias_Principais_Fatos`, no **mesmo** arquivo, está correta.

### Tipagem

Colunas de data viram `date` puro — **por membro**: todos têm `Data_Referencia`, `geral` acrescenta
`Data_Entrega`/`Data_Emissao`/`Data_Classificacao_Risco` e `classe` acrescenta `Data_Vencimento`.
Todo o restante (valores monetários, quantidades, percentuais, códigos) mantém o **texto exato da
CVM** — nunca `float`. O mapa de tipos é derivado do contrato.

---

## Política de retry

Todo reader aceita `retry_policy: RetryPolicy | None = None` e declara o seu padrão em
`_RETRY_POLICY` (padrão paciente: 5 tentativas, *backoff* ~2, 4, 8, 10 s). Veja a
[visão geral da leitura](index.md#politica-de-retry-retry_policy-e-_retry_policy).

---

## Exemplos

### Cadastro das operações de um ano

```python
from datetime import date
from filings_cvm import InfMensalOtsGeralReader

df_ = InfMensalOtsGeralReader(date_ref=date(2025, 6, 1)).read()   # o ANO de 2025
# uma linha por certificado por mês de referência.
```

### Persistir o ZIP bruto (camada *bronze*) uma vez para os 8

```python
from datetime import date
from pathlib import Path
from filings_cvm import InfMensalOtsClasseReader

InfMensalOtsClasseReader(
    date_ref=date(2025, 6, 1),
    path_raw=Path("/data/bronze/cvm/inf_mensal_ots/2025"),
).read()   # baixa o ZIP e mantém os 8 CSVs em disco para os outros readers.
```

Cada `read` levanta `OSError` (falha de download), `ContractError` (CSV viola o contrato) ou
`ValueError` (o ZIP não contém o membro esperado do ano) — falha cedo, sem devolver dados
corrompidos.
