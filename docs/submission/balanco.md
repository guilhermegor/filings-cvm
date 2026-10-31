# **Balanço — COFI 4016**

Envio (→ CVM) do **Balanço** ([`PadraoXMLBalanco.asp`](https://cvmweb.cvm.gov.br/SWB/Sistemas/SCW/PadroesXML/PadraoXMLBalanco.asp)).

> **Veja também:** [Referência da API](../api.md) · [Uso](../usage.md).

---

## Descrição

⚠️ A página da CVM **não define XML** para o Balanço: ele só pode ser enviado por upload no padrão
**COS 4016** (layout do Banco Central) ou **COFI 4016**, este último obrigatório para os FMP-FGTS e
FMP-FGTS Carteira Livre. Esta biblioteca implementa o **COFI 4016**: arquivo texto de largura fixa,
**71 colunas**, extensão `.cvm`, layout em
[`PadraoCOFI.aspx`](https://cvmweb.cvm.gov.br/SWB/Sistemas/SCW/PadroesXML/PadraoCOFI.aspx).
O COS 4016 não está implementado.

| Registro | Conteúdo |
|----------|----------|
| Cabeçalho (1 por fundo) | `#C1`, código do documento `4016`, CNPJ (14), filler (8), competência `MMAAAA`, filler (36). |
| Conta (1 por conta) | Conta (10: código de 8 caracteres com dígito verificador, zero à esquerda), filler (4), três colunas de 18 dígitos (total, até 90 dias, após 90 dias), cada uma seguida de sinal `+`/`-`. |
| Rodapé (1 por arquivo) | `@1`, número de registros gravados **incluindo os de controle** (6), filler (63). |

Modelos: `BalancoDocument` (`competencia` + 1 ou mais `BalancoFund`), `BalancoFund` (`cnpj` + `contas`),
`BalancoAccount` (`conta`, `total`, `ate_90`, `apos_90`). Um arquivo pode ter vários fundos, desde que
da mesma competência (e, regra da CVM não verificável aqui, do mesmo administrador).

### Críticas da CVM aplicadas ao construir o documento

| Código | Verificação |
|--------|-------------|
| D1 | Conta fora do plano COFI ou não vigente no último dia da competência. |
| D4 | Conta sem a conta superior no arquivo. |
| D5 | Conta repetida. |
| D7 | Coluna em branco: as três colunas são obrigatórias. |
| E1 | Sinal contrário à natureza (normal não negativa; retificadora não positiva). |
| E4 | Conta diferente da soma das subcontas presentes (nas três colunas). |
| E5 | Contas de compensação `3.0.x` ≠ `9.0.x` (coluna total). |
| EX | CC 3.023 §44: `3.0.3.30 + 3.0.3.40 + 3.0.3.50` ≠ `1.3.0 − 1.3.3` (coluna total). |
| G1 / G2 / G3 | Total do ativo ≠ passivo; total ausente; total ≠ soma dos grupos. |
| KD | Ordem dos registros: garantida na construção (contas em ordem de código). |

**D2** (desdobramentos obrigatórios) não é implementada: o plano publicado não indica quais são
obrigatórios. Nenhum validador da CVM foi executado.

### Premissas (a página não define)

- **Escala:** colunas de 18 dígitos com **2 casas decimais implícitas**, truncadas (nunca arredondadas); `float` é recusado.
- **Dígito verificador da conta:** `(−Σ pesos·dígitos) mod 10`, pesos `3,1,7` repetidos nos 7 dígitos; medido contra as 479 contas do plano COFI (todas conferem).
- **Fim de linha** CRLF; **codificação** ASCII por padrão (`encoding="ebcdic"` usa a página de código 037).
- **Sinal zero** é escrito `+`; a página permite `+` ou branco.
- **Verificação E5/EX/G1** na coluna total.

## Exemplos

```python
from filings_cvm.submission import Balanco, BalancoDocument

doc = BalancoDocument(
    competencia="062026",
    fundos=[{
        "cnpj": "11222333000181",
        "contas": [
            {"conta": "39999993", "total": "10.00", "ate_90": "10.00", "apos_90": "0"},
            {"conta": "99999995", "total": "10.00", "ate_90": "10.00", "apos_90": "0"},
        ],
    }],
)
texto = Balanco().export(doc)                           # retorna str
Balanco().export(doc, output_path="balanco.cvm")        # grava bytes, retorna None
```

A escrita codifica tudo antes de abrir o arquivo: uma falha nunca trunca um arquivo existente.
