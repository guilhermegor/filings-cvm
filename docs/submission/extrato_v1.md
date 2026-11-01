# **Extrato das Informações sobre o Fundo — V1 (ICVM 450)**

Envio (→ CVM) do padrão **Extrato das Informações sobre o Fundo V1**
([`PadraoXMLInfExtrato450.asp`](https://cvmweb.cvm.gov.br/SWB/Sistemas/SCW/PadroesXML/PadraoXMLInfExtrato450.asp)).
Para a versão atual veja [Extrato V3](extrato.md).

> **Veja também:** [Referência da API](../api.md) · [Uso](../usage.md) · leitura do dump aberto
> (**outro artefato**): [Extrato FI](../ingestion/extrato_fi.md).

---

## Descrição

Monte um `ExtratoV1Document` (um `ExtratoV1Header` + de 1 a 1000 `ExtratoV1Row`, uma por fundo) e
serialize com `ExtratoV1().export(...)`. O arquivo não pode passar de **1 MB**.

| Modelo | Tag XML | Papel |
|--------|---------|-------|
| `ExtratoV1Document` | `DOC_ARQ` / `EXTRATO_FUNDO` | `header` + `rows`. |
| `ExtratoV1Header` | `CAB_INFORM` | `COD_DOC` = 41, `VERSAO` = 1.0 (fixos), `DT_GERAC_ARQ`. |
| `ExtratoV1Row` | `ROW_EXTRATO` | O extrato de um fundo. |

Os campos de cada bloco são o nome da tag em minúsculas, **na ordem do arquivo de exemplo da CVM**;
`None` é omitido. Namespace `urn:extr`, codificação `windows-1252`. **Não é o V3**: o V3 é outro
questionário (classe de cotas, ANBIMA, tabelas de emissor); só os tipos genéricos e o serializador
são compartilhados.

## Tipagem

### Decimais

"Valor real" com vírgula decimal. Escalas: **2 casas** nos valores em R$ (`VL_APLIC_MIN`,
`VL_MOVIM_MIN`, `VL_SALDO_MIN`, taxas fixas) e em `QT_OPER_PATRIM_LIQ` ("inteiro com duas casas"; ou
o literal `SL` sem teto); **4 casas** nos percentuais (a página não diz a escala: política do
repositório, truncado). `float`, `bool`, NaN e infinito são recusados.

### Regras por resposta

`COD_MERC_SECUND`, `DIAS_RESG_COTAS` e `DS_RISCO_MERC` só com a resposta `S` que os motiva;
`CALC_TX_PERFM`, `PRAZO_APROP` e `PRAZO_PAGAM` exatamente quando se cobra performance;
`QT_OPER_PATRIM_LIQ` exatamente quando se pode operar acima do PL; taxa de ingresso/saída cobrada
leva **um** valor (fixo ou percentual), não cobrada leva nenhum. Mínimo não ultrapassa máximo.
`LIM_TIT_ADM` e `LIM_FDO_ADM` são obrigatórios; os demais `LIM_*` são opcionais.

### Tabelas e tamanhos

Tabelas A (mercado 1 a 3), B (distribuição 1 a 3), C (política 1 a 4), D (índice 1 a 35 ou 99),
E (1 a 2) e F (1, 2, 3, 6). Textos: `DS_ENDER`/`DS_EMAIL`/`DS_WEB` 50, `DS_NOME_RESP` 100,
`DS_RESUMO_POLIT` 4000, `DS_RISCO_MERC` 200, `HORAR_FECH_MERC` 100, `TX_ADM` (texto) e
`INFO_ADICIONAL` 400. DDD até 4 e telefone até 11 dígitos, sem zeros à esquerda.

## Política de retry

Não se aplica: sem rede. O texto é codificado e validado como XML bem formado, e o tamanho
checado, **antes** de tocar o destino; a gravação é atômica (arquivo temporário + `os.replace`),
então uma falha não trunca um arquivo existente.

## Divergências da página (escolhas documentadas)

- Tag do CNPJ: exemplo `CNPJ_FDO`, lista `CNPJ_FUNDO`. Usado `CNPJ_FDO`, **sem zeros à esquerda**
  (a página manda omiti-los de todos os campos).
- `LIM_TIT_ADM` aparece no exemplo sem a tag de fechamento; tratado como bloco com `PR_MAX_TIT_ADM`.
- A lista de tags repete `LIM_CIA_ABERTA` para o teto por emissor; o exemplo usa
  `LIM_APLIC_CIA_ABERTA`, que foi seguido.
- `CALC_TX_PERFM`: a página torna taxa, índice e % do índice obrigatórios só para investidores não
  qualificados, mas o documento não informa o público. Exige-se o trio completo **ou**
  `INFO_ADICIONAL`.
- `TX_ADM`: percentual (0 a 100) ou texto até 400 caracteres; texto só numérico é recusado.
- Blocos `LIM_*` sem campo obrigatório são opcionais inteiros; dias sem teto na página: 0 a 9999.
- Nenhum validador da CVM foi executado contra a saída.

## Exemplos

```python
from filings_cvm.submission import ExtratoV1, ExtratoV1Document, ExtratoV1Header, ExtratoV1Row

doc = ExtratoV1Document(
    header=ExtratoV1Header(dt_gerac_arq="01/11/2026"),
    rows=[ExtratoV1Row(...)],
)
xml = ExtratoV1().export(doc)
ExtratoV1().export(doc, output_path="extrato_v1.xml")
```
