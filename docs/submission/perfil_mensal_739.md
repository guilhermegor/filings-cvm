# **Perfil Mensal — ICVM 739**

Envio (→ CVM) do padrão **Perfil Mensal** da Instrução CVM 409 (vigente a partir de 01/07/2012,
[`PadraoXMLPerfil739.asp`](https://cvmweb.cvm.gov.br/SWB/Sistemas/SCW/PadroesXML/PadraoXMLPerfil739.asp)).

> **Veja também:** [Perfil Mensal V4](perfil_mensal.md) · [Referência da API](../api.md)

---

## Descrição

Medido contra as páginas 739, V3 e V4 da CVM: a sequência de tags do exemplo XML, o namespace
`urn:perf`, o `COD_DOC=40` e a codificação `windows-1252` são **idênticos**. O `PerfilMensal739`
reaproveita, portanto, o serializador do V4. As diferenças medidas são:

| Ponto | 739 | V3 / V4 |
|-------|-----|---------|
| `VERSAO` | `1.0` | `3.0` / `4.0` |
| `DISTR_PATRIM` (16 tags `PR_*`) | obrigatório | obrigatório (V3) / opcional (V4) |
| `VAR_DIAR_PERC_PATRIM_FDO_VAR_N_TAXA_ANUAL`, `..._TAXA_CAMBIO`, `VAR_PATRIM_FDO_N_PRECO_ACOES`, `VAL_PERCENT_OUTROS` | **2** casas decimais | 4 casas |
| `MONTANTE_DISTRIB`, `INF_COMPL_PERFIL` | **não existem** | existem no V4 |

Decimais além da escala são **truncados em direção a zero**, nunca arredondados, e saem com vírgula.
Os modelos reaproveitam os do V4 (cabeçalho, contagem de clientes, listas de fatores, etc.); só
mudam os abaixo.

| Modelo | Tag XML | Diferença para o V4 |
|--------|---------|---------------------|
| `PerfilMensal739Document` | `DOC_ARQ` | `rows` é uma lista de `PerfilMensal739Row`. |
| `PerfilMensal739Row` | `ROW_PERFIL` | `distr_patrim` obrigatório; sensibilidades com 2 casas; `montante_distrib` e `inf_compl_perfil` rejeitados. |
| `PatrimonyDistribution739` | `DISTR_PATRIM` | As 16 tags `PR_*` obrigatórias (1 casa, máx. 100). |
| `VarOutros739` | `VARIACAO_DIAR_PERC_PATRIM_FDO_VAR_N_OUTROS` | `val_percent_outros` com 2 casas. |

> A página 739 descreve a tag do CNPJ como `CNPJ_FUNDO` na tabela de tags, mas o exemplo XML (e o
> V4) usam `CNPJ_FDO`; o writer segue o exemplo.

## Exemplo

```python
from filings_cvm.submission import (
    ClientCount, DocumentHeader, PatrimonyDistribution739,
    PerfilMensal739, PerfilMensal739Document, PerfilMensal739Row,
)

clientes = ClientCount(**{campo: 0 for campo in ClientCount.model_fields})
distribuicao = PatrimonyDistribution739(
    **{campo: "0" for campo in PatrimonyDistribution739.model_fields}
)
doc = PerfilMensal739Document(
    header=DocumentHeader(dt_compt="07/2012", dt_gerac_arq="15/08/2012"),
    rows=[
        PerfilMensal739Row(
            cnpj_fdo="11222333000181",
            nr_client=clientes,
            distr_patrim=distribuicao,
            total_recurs_exter="0", total_recurs_br="0",
            tot_ativos_p_relac="0", tot_ativos_cred_priv="0",
        )
    ],
)

xml = PerfilMensal739().export(doc)                       # str, com <VERSAO>1.0</VERSAO>
PerfilMensal739().export(doc, output_path="perfil.xml")   # grava em windows-1252
```
