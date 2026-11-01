# **Informe Diário — V3**

Envio (→ CVM) do padrão **Informe Diário V3**, vigente a partir de 01/10/2015
([`PadraoXMLInfoDiarioNetV3.asp`](https://cvmweb.cvm.gov.br/SWB/Sistemas/SCW/PadroesXML/PadraoXMLInfoDiarioNetV3.asp)).

> **Veja também:** [Informe Diário (V4)](informe_diario.md) · [Referência da API](../api.md)

## Descrição

Monte um `InformeDiarioV3Document` (`InformeDiarioV3Header` + até 100 `InformeDiarioV3Inform`)
e serialize com `InformeDiarioV3().export(doc, output_path=None)`. Namespace `urn:infdiario`,
`COD_DOC=1`, `VERSAO=3.0`, `windows-1252`.

## Diferenças medidas contra o V4

A página foi comparada ao schema V4. Só há duas diferenças:

- `VERSAO` é `3.0`.
- O fundo é identificado **somente** por `CNPJ_FDO`; `COD_SUBCLASSE` não existe (rejeitado).

Ordem das tags, escalas (2 casas; `VL_QUOTA` até 12; `PR_COTST` até 4) e o bloco
`COTST_SIGNIF` são idênticos ao V4, por isso os modelos estendem os do V4. O writer usa o writer V4 por composição, não por herança.

## Decisões

- `NOME_FUNDO`, `RESG_NAO_PROCES` e `LIQ_DIA_DISPON` aparecem na descrição das tags, mas
  cercados por `-->` e ausentes do modelo XML: não são emitidos.
- Excesso de casas decimais é truncado, nunca arredondado.
