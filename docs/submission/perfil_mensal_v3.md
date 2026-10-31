# **Perfil Mensal — V3**

Envio (→ CVM) do padrão **Perfil Mensal V3** (vigente a partir de 01/10/2015,
[`PadraoXMLPerfilV3.asp`](https://cvmweb.cvm.gov.br/SWB/Sistemas/SCW/PadroesXML/PadraoXMLPerfilV3.asp)).

> **Veja também:** [Perfil Mensal V4](perfil_mensal.md) · [Referência da API](../api.md)

---

## Descrição

Medido contra as páginas V3 e V4 da CVM: a sequência de tags do exemplo XML (91 tags), as escalas
decimais, as cardinalidades, o namespace `urn:perf`, o `COD_DOC=40` e a codificação
`windows-1252` são **idênticos**. O `PerfilMensalV3` reaproveita, portanto, o serializador do V4 e
fixa `VERSAO` em `3.0`.

A única diferença estrutural é o bloco `DISTR_PATRIM`: no V3 ele e cada uma de suas 16 tags
`PR_*` são **obrigatórios** (no V4 o bloco é opcional para classes com subclasses). Por isso o V3
tem modelos próprios para a linha e o bloco; cabeçalho e demais blocos são os do V4.

| Modelo | Tag XML | Diferença para o V4 |
|--------|---------|---------------------|
| `PerfilMensalV3Document` | `DOC_ARQ` | `rows` é uma lista de `PerfilMensalV3Row`. |
| `PerfilMensalV3Row` | `ROW_PERFIL` | `distr_patrim` obrigatório. |
| `PatrimonyDistributionV3` | `DISTR_PATRIM` | As 16 tags `PR_*` obrigatórias (1 casa, máx. 100). |

> A página V3 descreve a tag do CNPJ como `CNPJ_FUNDO` na tabela de tags, mas o exemplo XML (e o
> V4) usam `CNPJ_FDO`; o writer segue o exemplo.

## Exemplo

```python
from filings_cvm.submission import (
    ClientCount, DocumentHeader, PatrimonyDistributionV3,
    PerfilMensalV3, PerfilMensalV3Document, PerfilMensalV3Row,
)

clientes = ClientCount(**{campo: 0 for campo in ClientCount.model_fields})
distribuicao = PatrimonyDistributionV3(
    **{campo: "0" for campo in PatrimonyDistributionV3.model_fields}
)
doc = PerfilMensalV3Document(
    header=DocumentHeader(dt_compt="01/2015", dt_gerac_arq="15/01/2015"),
    rows=[
        PerfilMensalV3Row(
            cnpj_fdo="11222333000181",
            nr_client=clientes,
            distr_patrim=distribuicao,
            total_recurs_exter="0", total_recurs_br="0",
            tot_ativos_p_relac="0", tot_ativos_cred_priv="0",
        )
    ],
)

xml = PerfilMensalV3().export(doc)                       # str, com <VERSAO>3.0</VERSAO>
PerfilMensalV3().export(doc, output_path="perfil.xml")   # grava em windows-1252
```
