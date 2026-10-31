# **Lâmina de Fundos — V2**

Envio (→ CVM) do padrão **Lâmina de Fundos V2** (a partir de 2015-10-01, ICVM 555)
([`PadraoXMLLaminaV2.asp`](https://cvmweb.cvm.gov.br/SWB/Sistemas/SCW/PadroesXML/PadraoXMLLaminaV2.asp)).

> **Veja também:** [Lâmina V3](lamina.md), a versão atual, cujos blocos, tipos e regras esta versão
> reaproveita · [Referência da API](../api.md) · [Uso](../usage.md).

---

## Descrição

Monte um `LaminaV2Document` (um `LaminaV2Header` + de 1 a 70 `LaminaV2Inform`, todas da **mesma
competência**) e serialize com `LaminaV2().export(...)`.

| Modelo | Tag XML | Papel |
|--------|---------|-------|
| `LaminaV2Document` | `DOC_ARQ` / `LISTA_INFORM` | Documento: `header` + `informs` (1 a 70). |
| `LaminaV2Header` | `CAB_INFORM` | `COD_DOC` = 24 e `VERSAO` = **2.0** (fixos). |
| `LaminaV2Inform` | `INFORM` | A lâmina de um fundo, identificado por `CNPJ_FUNDO` (obrigatório). |

Todos os demais blocos (`LaminaCarencia`, `LaminaConversao`, `LaminaTaxaAdministracao`, ...) são
**os mesmos de V3** e vêm de [Lâmina V3](lamina.md), inclusive tipagem, escalas decimais e regras
entre campos.

## Diferenças medidas contra V3

Comparação das duas páginas da CVM (2026-10-31): o exemplo e a lista de tags têm a **mesma ordem**,
e toda descrição de campo é idêntica, exceto:

| Ponto | V2 | V3 |
|-------|----|----|
| `VERSAO` | `2.0` | `3.0` |
| `COD_SUBCLASSE` | não existe | opcional, após `CNPJ_FUNDO` |
| `CNPJ_FUNDO` | sempre obrigatório | omitido quando o informe é de subclasse |

## Limites e pontos em aberto

Os mesmos de V3: a página não diz a escala de nenhum decimal (política do repositório: dinheiro 2,
percentuais 4, truncado), o namespace do exemplo (`urn:lamina`) contradiz o da lista de tags
(`urn:infdiario`, usado `urn:lamina`) e a tag da linha mensal diverge (`MES` no exemplo, `MES_RENT`
na lista; usada `MES`). Nenhum validador da CVM foi executado.

## Exemplos

```python
from filings_cvm.submission import LaminaV2, LaminaV2Document

doc = LaminaV2Document.model_validate(
    {"header": {"dt_compt": "01/2025", "dt_gerac_arq": "15/01/2025"}, "informs": [inform]}
)
xml = LaminaV2().export(doc)                          # retorna str
LaminaV2().export(doc, output_path="lamina_v2.xml")   # grava windows-1252, retorna None
```

`inform` é o dicionário de campos de um `INFORM`, os mesmos de [V3](lamina.md) sem `cod_subclasse`.
