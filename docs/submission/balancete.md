# **Balancete — COFI 4010**

Envio (→ CVM) do **Balancete** de fundos. A página
[`PadraoXMLBalancete.asp`](https://cvmweb.cvm.gov.br/SWB/Sistemas/SCW/PadroesXML/PadraoXMLBalancete.asp)
**não define XML**: o informe só é enviado por upload no padrão COS 4010 (BACEN) ou COFI 4010
(CVM). Este writer implementa o **COFI 4010**, layout de largura fixa descrito em
[`PadraoCOFI.aspx`](https://cvmweb.cvm.gov.br/SWB/Sistemas/SCW/PadroesXML/PadraoCOFI.aspx)
(extensão `.cvm`). O COS 4010 não é implementado.

> **Veja também:** [Referência da API](../api.md) · [Uso](../usage.md).

---

## Descrição

Monte um `BalanceteDocument` (competência `MMAAAA` + uma lista de `BalanceteFundo`, cada um
com seu CNPJ e uma lista de `BalanceteConta`) e serialize com `Balancete().export(...)`.

| Registro | Posições (71) |
|----------|---------------|
| Cabeçalho (um por fundo) | `#C1`, código do documento `4010` (4-7), CNPJ (8-21), filler (22-29), competência `MMAAAA` (30-35), filler (36-71) |
| Conta | código com DV (1-10), filler (11-14), total (15-32) + sinal (33), até 90 dias (34-51) + sinal (52), após 90 dias (53-70) + sinal (71) |
| Rodapé (um por arquivo) | `@1`, nº de registros gravados incluindo os de controle (3-8), filler (9-71) |

Sinal: `+` para zero/positivo, `-` para negativo; o valor vai em módulo, 18 dígitos.

**Validações:** CNPJ com dígito verificador; competência com mês 01-12; código de conta com
exatamente 10 dígitos; conta repetida no mesmo fundo é recusada (crítica D5); CNPJ repetido no
arquivo é recusado; contagem de registros limitada a 6 dígitos. Valores `float` são recusados.

## Premissas

- A página não declara escala decimal: os valores têm **2 casas decimais implícitas**, truncadas
  (`ROUND_DOWN`), p.ex. `12.34` → `000000000000001234`.
- O código do documento é fixo em `4010`.
- Um cabeçalho por fundo e um único rodapé por arquivo (a página diz que o arquivo pode conter
  balancetes de vários fundos da mesma competência).
- Registros separados por CRLF; o arquivo é gravado em ASCII, codificado antes de abrir o destino.
- As críticas de consistência da CVM (soma de subcontas, ativo = passivo, plano de contas,
  sinal pela natureza) **não** são reproduzidas aqui; o writer não conhece o plano COFI. Nenhum
  validador da CVM foi executado.

## Exemplo

```python
from filings_cvm.submission import (
    Balancete, BalanceteConta, BalanceteDocument, BalanceteFundo,
)

doc = BalanceteDocument(
    competence="012025",
    fundos=[BalanceteFundo(
        cnpj_fdo="11222333000181",
        contas=[BalanceteConta(cod_conta="1110000009", vl_total="12.34")],
    )],
)
Balancete().export(doc, "balancete.cvm")
```
