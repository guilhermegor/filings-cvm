# **Atualização do Cadastro de Ativos**

Envio (→ CVM) do padrão **Atualização do Cadastro de Ativos**
([`PadraoXMLAtivos.asp`](https://cvmweb.cvm.gov.br/SWB/Sistemas/SCW/PadroesXML/PadraoXMLAtivos.asp)).

> **Veja também:** [Referência da API](../api.md) · [Uso](../usage.md)

---

## Descrição

Monte um `CadastroAtivosDocument` (um `CadastroAtivosHeader` + de 1 a 1000 `CadastroAtivosRow`,
todos do mesmo mercado de negociação) e serialize com `CadastroAtivos().export(...)`. O XML não
usa namespace, tem `COD_DOC=2` e é gravado em `windows-1252`.

| Modelo | Tag XML | Papel |
|--------|---------|-------|
| `CadastroAtivosDocument` | `DOC_ARQ` | `header` + `rows` (até 1000). |
| `CadastroAtivosHeader` | `DESC_MERC` | `cnpj_merc` e `dt_gerac_arq` (`DD/MM/AAAA`). |
| `CadastroAtivosRow` | `ROW_ATIVO` | Uma inclusão (`I`), alteração (`A`) ou remoção (`R`). |

**Validações vindas da página da CVM:**

- `ACAO` é `I`, `A` ou `R`; `TP_ATIV` é um código da Tabela 1; `TP_EMP_EMISSORA`, da Tabela 2
  (informe `1`, não `01`: a página proíbe zeros à esquerda fora de CNPJ).
- O ativo é identificado por `CD_ATIV`, `TP_ATIV` e `DT_INICIO_VIGEN`: sempre obrigatórios.
- `DS_ATIV`, `CNPJ_EMP_EMISSORA`, `TP_EMP_EMISSORA`, `NM_EMP_EMISSORA` e `DS_ISIN` são
  obrigatórios em `I`/`A` e opcionais em `R`. Fim de vigência e datas de suspensão são sempre
  opcionais.
- `TP_ATIV`/`TP_EMP_EMISSORA` são `int` estritos: `True`, `2.0` e `"2"` são recusados.
- CNPJs: o formato é checado antes de qualquer normalização (`NN.NNN.NNN/NNNN-NN`, 14
  caracteres sem máscara, ou só dígitos sem os zeros à esquerda, como a página permite);
  depois, dígito verificador, e a gravação é sem máscara. Datas `DD/MM/AAAA` reais, ano ≥ 1900.
- Textos não vazios, de uma linha e compatíveis com `windows-1252`.
- A página não informa tamanhos máximos; nenhum é imposto. Os códigos 16 e 25 a 46 da Tabela 1
  não constam da página e são recusados.

---

## Exemplos

```python
from filings_cvm.submission import (
    CadastroAtivos, CadastroAtivosDocument, CadastroAtivosHeader, CadastroAtivosRow,
)

doc = CadastroAtivosDocument(
    header=CadastroAtivosHeader(cnpj_merc="11.222.333/0001-81", dt_gerac_arq="05/04/2024"),
    rows=[
        CadastroAtivosRow(
            acao="I", cd_ativ="PETR4", ds_ativ="Petrobras PN", tp_ativ=2,
            cnpj_emp_emissora="11.222.333/0001-81", tp_emp_emissora=1,
            nm_emp_emissora="Petrobras", ds_isin="BRPETRACNPR6",
            dt_inicio_vigen="02/01/2024",
        ),
        CadastroAtivosRow(acao="R", cd_ativ="OLD3", tp_ativ=1, dt_inicio_vigen="01/01/2010"),
    ],
)
xml = CadastroAtivos().export(doc)                  # devolve a string
CadastroAtivos().export(doc, "ativos.xml")          # ou grava o arquivo (windows-1252)
```
