# **Informe Quadrimestral — V2**

Envio (→ CVM) do padrão **Informe Quadrimestral V2** (antigo Informe Trimestral, FIP)
([`PadraoXMLInfoTrimV2.asp`](https://cvmweb.cvm.gov.br/SWB/Sistemas/SCW/PadroesXML/PadraoXMLInfoTrimV2.asp)).

> **Veja também:** [Referência da API](../api.md) · [Uso](../usage.md)

---

## Descrição

Monte um `InformeQuadrimestralDocument` (um `InformeQuadrimestralHeader` + de 1 a 100
`InformeQuadrimestralInform`, um por fundo) e serialize com `InformeQuadrimestral().export(...)`.
O XML usa o namespace `urn:inftrim`, `COD_DOC=51` e `VERSAO=2.0`, em `windows-1252`.

| Modelo | Tag XML | Papel |
|--------|---------|-------|
| `InformeQuadrimestralDocument` | `DOC_ARQ` | `header` + `informs` (1 a 100 fundos, sem CNPJ repetido). |
| `InformeQuadrimestralHeader` | `CAB_INFORM` | `dt_compt` (`MM/AAAA`) e `dt_gerac_arq` (`DD/MM/AAAA`). |
| `InformeQuadrimestralInform` | `INFORM` | O informe de um fundo. |
| `ListaCotstCateg` | `LISTA_COTST_CATEG` | Cotistas por categoria + totais. |
| `CotistCategory` | `COTST_CATEG` | Uma categoria da Tabela I. |
| `ListaClasseCotas` | `LISTA_CLASSE_COTAS` | Classes de cotas do fundo. |
| `ClasseCotas` | `CLASSE_COTAS` | Uma classe de cotas. |

Cada campo do schema é a tag da página em minúsculas, declarado na ordem do XML.

## Tipagem

### Decimais

A página declara todo número como "decimal com até 12 algarismos na parte inteira e até 8 na
parte decimal". Os decimais são `Decimal` (nunca `float`, que é recusado), saem com **8 casas** e
vírgula decimal, e casas excedentes são **truncadas** (nunca arredondadas). Quantidades, capital
e percentuais não podem ser negativos; percentuais ficam entre 0 e 100. `vl_pl_fdo` e
`vl_atual_cota` aceitam valor negativo.

### Inteiros, textos e formatos

- Contagens (`qtd_cotst_subscr`, `tot_cotst_subscr`, `num_cotst_subs`) são inteiros ≥ 0;
  `num_classe` é inteiro ≥ 1.
- `entid_invest`, `direito_polit_especial` e `direito_dist_econ_finan`: `S` ou `N`.
- `publico_alvo`: `2` (qualificados) ou `3` (somente profissionais).
- `nr_pf_pj_fdo`: CNPJ (formato verificado, depois dígitos verificadores), gravado sem máscara.
- `dt_compt`: `MM/AAAA` real; o mês deve fechar um quadrimestre civil (`04`, `08` ou `12`).
- `dt_gerac_arq`: data de calendário real.

### Regras entre campos

- Um fundo não repete categoria nem número de classe; um arquivo não repete fundo.
- Os dois blocos de lista são obrigatórios e têm ao menos um item.

## Limites e pontos em aberto

- **Conflito na página:** o texto proíbe "fillers" de zeros à esquerda, mas a Tabela I imprime os
  códigos de categoria como `001`…`015`. Adotado: o código sai com **3 dígitos**, como na
  tabela; `"1"` é recusado.
- A página não diz se `LISTA_COTST_CATEG` e `LISTA_CLASSE_COTAS` são obrigatórias; tratadas como
  obrigatórias (todo fundo tem cotistas e ao menos uma classe).
- Os totais (`tot_cotst_subscr`, `tx_num_tot_cot`) não são recalculados nem conferidos contra os
  itens: a página não define a relação.
- Nenhum validador da CVM foi executado (a página oferece um verificador de sintaxe).

## Exemplos

### Arquivo XML mínimo

```python
from filings_cvm.submission import InformeQuadrimestral, InformeQuadrimestralDocument

doc = InformeQuadrimestralDocument(
    header={"dt_compt": "04/2026", "dt_gerac_arq": "15/05/2026"},
    informs=[
        {
            "nr_pf_pj_fdo": "11222333000181",
            "entid_invest": "S",
            "publico_alvo": 2,
            "vl_pl_fdo": "1000.50",
            "vl_capital_comprom": "5000",
            "qtd_cotas_subscr": "100",
            "vl_tot_capital_subscr": "4000",
            "qtd_cotas_integr": "50",
            "vl_tot_capital_integr": "2000",
            "vl_tot_cotas_outros_fip": "0",
            "lista_cotst_categ": {
                "cotst_categ": [
                    {"cod_categ": "001", "qtd_cotst_subscr": 5, "pr_cotas_subscr": "100"}
                ],
                "tot_cotst_subscr": 5,
                "tx_num_tot_cot": "100",
            },
            "lista_classe_cotas": {
                "classe_cotas": [
                    {
                        "num_classe": 1,
                        "num_cotst_subs": 5,
                        "qtd_atual_cotas_subs": "100",
                        "qtd_atual_cotas_integ": "50",
                        "vl_atual_cota": "12.5",
                        "direito_polit_especial": "N",
                        "direito_dist_econ_finan": "N",
                    }
                ]
            },
        }
    ],
)

print(InformeQuadrimestral().export(doc))
```

### Escrever em disco (windows-1252)

O texto é codificado antes de abrir o destino; uma falha não apaga um arquivo existente.

```python
InformeQuadrimestral().export(doc, output_path="informe_quadrimestral.xml")
```

### Valor recusado cedo

```python
from pydantic import ValidationError

try:
    InformeQuadrimestralDocument(
        header={"dt_compt": "01/2026", "dt_gerac_arq": "15/05/2026"}, informs=[]
    )
except ValidationError as exc:
    print(exc)
```
