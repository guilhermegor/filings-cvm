# **Informe de Portabilidade**

Envio (→ CVM) do padrão **Informe de Portabilidade**
([`PadraoXMLInfoPortabilidade.asp`](https://cvmweb.cvm.gov.br/SWB/Sistemas/SCW/PadroesXML/PadraoXMLInfoPortabilidade.asp)).

> **Veja também:** [Referência da API](../api.md) para cada símbolo público · [Uso](../usage.md)
> para instalação e o conceito geral.

---

## Descrição

Monte um `InformePortabilidadeDocument` (um `PortabilidadeHeader` + uma lista de
`PortabilidadeInform`, uma por regulado e mês) e serialize com `InformePortabilidade().export(...)`.
O XML usa o namespace `urn:portab`, `COD_DOC=478` e `VERSAO=1.0`, em `windows-1252`.

| Modelo | Tag XML | Papel |
|--------|---------|-------|
| `InformePortabilidadeDocument` | `DOC_ARQ` | Documento completo: `header` + `informs` (ao menos um). |
| `PortabilidadeHeader` | `CAB_INFORM` | `dt_compt` (`MM/AAAA`) e `dt_gerac_arq` (`DD/MM/AAAA`). |
| `PortabilidadeInform` | `INFORM` | Solicitações de portabilidade de um regulado em um mês. |

Campos de `PortabilidadeInform` (ordem do XML): `cnpj_partic`, `dt_event`, `qtde_solicit_orig`,
`qtde_solicit_dest`, `qtde_canc`, `atend_prazo_regul`, `atend_prazo_estend`, `qtde_recus`.

## Regras aplicadas

- `cnpj_partic`: forma (14 caracteres, nu ou mascarado) e dígitos verificadores; gravado nu.
- As seis quantidades são **inteiros não negativos estritos**: `float`, `bool` e texto numérico
  levantam `ValidationError`. Não há campo decimal neste padrão.
- Datas são interpretadas (mês 13 ou `31/02` são recusados; ano mínimo 1900).
- `export` codifica o texto em `windows-1252` e confere a boa formação **antes** de abrir o
  arquivo de saída: um caractere não codificável levanta `ValueError` e não apaga o arquivo.

## O que a página deixa em aberto

- `DT_EVENT` ("mês das solicitações") não tem formato declarado: adotado `MM/AAAA`.
- A cardinalidade de `INFORM` não é declarada: ao menos um, sem teto superior.
- Nenhuma relação entre as quantidades é declarada, então nenhuma é imposta.
- Nenhum validador da CVM foi executado contra a saída.
