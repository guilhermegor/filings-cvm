# **Extrato das Informações sobre o Fundo — V2**

Envio (→ CVM) do padrão **Extrato das Informações sobre o Fundo V2**
([`PadraoXMLInfExtratoV2.asp`](https://cvmweb.cvm.gov.br/SWB/Sistemas/SCW/PadroesXML/PadraoXMLInfExtratoV2.asp)).

> **Veja também:** [Extrato V3](extrato.md) (a versão corrente; descreve todos os campos, regras e
> escalas decimais, que valem aqui) · [Referência da API](../api.md) · [Uso](../usage.md).

---

## Descrição

Monte um `ExtratoV2Document` (um `ExtratoV2Header` + de 1 a 1000 `ExtratoRow`) e serialize com
`ExtratoV2().export(...)`. O arquivo não pode passar de **1 MB**.

## O que mudou em relação ao V3 (medido na página)

O arquivo de exemplo do V2 e o do V3 têm **as mesmas tags, na mesma ordem**. As diferenças medidas:

| Item | V2 | V3 |
|------|----|----|
| `VERSAO` | `2.0` | `3.0` |
| `CNPJ_FDO` | CNPJ **do fundo** | CNPJ **da classe de cotas** do fundo |
| Tabela de tags | sem marcação de opcional | `Tag opcional` em `ABERTA_NEG_MER_ORGAN`, `LISTA_MERC_BLOQUEIO`, `PUBLICO_ALVO` e outras |
| Descrição de 7 tags | ausente (`PUBLICO_ALVO`, `APLICACAO_MINIMA_FUNDO`, `TIPO_VALOR_COTA`, `VALOR_COTA_BASE_PL`, `PRAZO_PAGAM_RESG`, `TAXA_ADM`, `TAXA_MAXIMA_CUSTODIA`) | presente |

`COD_DOC` (41), o namespace (`urn:extr`), a codificação (`windows-1252`) e a vírgula decimal são
iguais. Por isso `ExtratoRow` e os blocos são os do V3, **importados e não copiados**; só o
cabeçalho (`ExtratoV2Header`, que fixa `VERSAO=2.0`) e o documento que o carrega são próprios, e o
`ExtratoV2` reusa o serializador do `Extrato` (`_build_payload`).

## Escolhas documentadas

- As 7 tags do exemplo V2 sem descrição na tabela seguem **opcionais** (como no V3): o exemplo as
  traz, a tabela não as exige.
- A página V2 não marca tags opcionais; vale a opcionalidade do V3 (mais permissiva), então um
  documento V2 válido aqui nunca é mais rígido do que a página.
- Demais divergências internas da página (duas gerações do formulário, `urn:perf`, `CNPJ_FUNDO`):
  as mesmas do V3, ver [Extrato V3](extrato.md).

## Exemplo

```python
from filings_cvm.submission import ExtratoV2, ExtratoV2Document, ExtratoV2Header

doc = ExtratoV2Document(
    header=ExtratoV2Header(dt_gerac_arq="31/10/2026"),
    rows=[...],  # ExtratoRow
)
xml = ExtratoV2().export(doc)
```

Nenhum validador da CVM foi executado contra a saída.
