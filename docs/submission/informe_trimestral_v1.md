# **Informe Trimestral — V1**

Envio (→ CVM) do padrão **Informe Trimestral V1**, válido até 2017-06 (FMIEE, FIP, FIC-FIP e
FUNCINE) ([`PadraoXMLInfoTrim.asp`](https://cvmweb.cvm.gov.br/SWB/Sistemas/SCW/PadroesXML/PadraoXMLInfoTrim.asp)).
Substituto: [Informe Quadrimestral V2](informe_quadrimestral.md).

> **Veja também:** [Referência da API](../api.md) · [Uso](../usage.md)

---

## Descrição

Monte um `InformeTrimestralV1Document` (um `InformeTrimestralV1Header` + de 1 a 100
`InformeTrimestralV1Inform`, um por fundo) e serialize com `InformeTrimestralV1().export(...)`.
O XML usa o namespace `urn:inftrim`, `COD_DOC=51` e `VERSAO=1.0`, em `windows-1252`. Todos os
informes de um arquivo têm a mesma competência.

| Modelo | Tag XML | Papel |
|--------|---------|-------|
| `InformeTrimestralV1Document` | `DOC_ARQ` | `header` + `informs` (1 a 100 fundos, sem CNPJ repetido). |
| `InformeTrimestralV1Header` | `CAB_INFORM` | `dt_compt` (`MM/AAAA`) e `dt_gerac_arq` (`DD/MM/AAAA`). |
| `InformeTrimestralV1Inform` | `INFORM` | O informe de um fundo: `cnpj_fdo`, `patrim_liq`, `qt_cotistas`, `qt_quota`, `vl_patrim_quota`. |

Cada campo do schema é a tag da página em minúsculas, declarado na ordem do XML. Diferente da V2,
não há listas nem blocos aninhados: são cinco campos por fundo. Só o
serializador de elementos é compartilhado com o writer da V2.

## Tipagem

- `patrim_liq`: `Decimal` com **2 casas**; `vl_patrim_quota`: `Decimal` com **12 casas**. Nunca
  `float` (recusado); casas excedentes são **truncadas**, nunca arredondadas; vírgula decimal e
  a escala cheia na saída (`1,000000000000`). Ambos aceitam valor negativo.
- `qt_cotistas` e `qt_quota`: inteiros ≥ 0 (a página diz apenas "inteiro").
- `cnpj_fdo`: CNPJ (formato verificado, depois dígitos verificadores), gravado sem máscara.
- `dt_compt`: `MM/AAAA` real; o mês fecha um trimestre civil (`03`, `06`, `09` ou `12`).
- `dt_gerac_arq`: data de calendário real.

## O que foi medido na página

- Exemplo: `DOC_ARQ xmlns="urn:inftrim"` > `CAB_INFORM` (`COD_DOC`, `DT_COMPT`, `DT_GERAC_ARQ`,
  `VERSAO`) + `LISTA_INFORM` > `INFORM` (`CNPJ_FDO`, `PATRIM_LIQ`, `QT_COTISTAS`, `QT_QUOTA`,
  `VL_PATRIM_QUOTA`), codificação `windows-1252`, `COD_DOC` = `51`, `VERSAO` = `1.0`.
- Notas dos campos: `PATRIM_LIQ` decimal com 2 casas; `VL_PATRIM_QUOTA` decimal com 12 casas;
  `QT_COTISTAS` e `QT_QUOTA` inteiros; vírgula como separador decimal; sem "fillers" de zeros;
  no máximo 100 fundos por arquivo.
- Diferença da V2: a V2 usa `NR_PF_PJ_FDO` onde a V1 usa `CNPJ_FDO`, tem 8 casas decimais em
  vez de 2/12, e acrescenta listas de categorias e classes de cotas. `COD_DOC` (`51`), namespace
  e encoding são os mesmos.

## Limites e pontos em aberto

- **Conflito na página:** o exemplo traz `<VERSAO>1.0</VERSAO>`, mas a nota do campo diz "Deve
  conter o número 2.0 que indica que o arquivo está na nova versão" (texto herdado da V2). Adotado
  `1.0`: o exemplo, e o verificador de sintaxe da página é chamado com `VERSAO=1`. `"2.0"` é
  recusado.
- A página não fixa largura máxima dos números: aceitos até 18 dígitos inteiros nos decimais e
  até 999.999.999.999 nos inteiros.
- A página não diz se o patrimônio líquido pode ser negativo; aceito (fundo descoberto).
- A página não diz quais meses de competência valem além de "mês final do trimestre civil":
  `03`, `06`, `09` e `12`.
- Nenhum validador da CVM foi executado (a página oferece um verificador de sintaxe).
- A gravação em disco usa arquivo temporário no mesmo diretório + `os.replace`; a #330
  (`atomic_write_bytes`) passa a fornecê-la.

## Exemplos

```python
from filings_cvm.submission import InformeTrimestralV1, InformeTrimestralV1Document

doc = InformeTrimestralV1Document(
    header={"dt_compt": "06/2017", "dt_gerac_arq": "15/07/2017"},
    informs=[
        {
            "cnpj_fdo": "11222333000181",
            "patrim_liq": "1000.50",
            "qt_cotistas": 12,
            "qt_quota": 3400,
            "vl_patrim_quota": "12.123456789012",
        }
    ],
)

print(InformeTrimestralV1().export(doc))
InformeTrimestralV1().export(doc, output_path="informe_trimestral_v1.xml")
```
