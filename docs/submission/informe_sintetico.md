# **Informe Sintético — FCCE, FITVM, FIC-FITVM e Outros**

Envio (→ CVM) da família **Informe Sintético**: quatro padrões, um por tipo de fundo.

| Tipo | Página da CVM | `COD_DOC` | Tipos de fundo | Writer |
|----------|---------------|-----------|----------------|--------|
| FCCE | [`PadraoXMLSintFCCE.asp`](https://cvmweb.cvm.gov.br/SWB/Sistemas/SCW/PadroesXML/PadraoXMLSintFCCE.asp) | 5 | FCCE, FCCE-AI | `InformeSinteticoFcce` |
| FITVM | [`PadraoXMLSintFITVM.asp`](https://cvmweb.cvm.gov.br/SWB/Sistemas/SCW/PadroesXML/PadraoXMLSintFITVM.asp) | 7 | FITVM, FMP-FGTS CL, FIIM | `InformeSinteticoFitvm` |
| FIC-FITVM | [`PadraoXMLSintFIC.asp`](https://cvmweb.cvm.gov.br/SWB/Sistemas/SCW/PadroesXML/PadraoXMLSintFIC.asp) | 8 | FIC-FITVM | `InformeSinteticoFic` |
| Outros | [`PadraoXMLSintOutros.asp`](https://cvmweb.cvm.gov.br/SWB/Sistemas/SCW/PadroesXML/PadraoXMLSintOutros.asp) | 9 | FICE, FMP-FGTS, FMAI | `InformeSinteticoOutros` |

> **Veja também:** [Referência da API](../api.md) para cada símbolo público · [Uso](../usage.md)
> para instalação e o conceito geral.

---

## Descrição

As quatro **não são versões** de um mesmo layout: os blocos da carteira, os nomes das tags e o
`COD_DOC` mudam, então cada tipo tem o seu cabeçalho, os seus blocos, a sua linha e o seu
documento (um writer por tipo). Um bloco de uma tipo é recusado em outra.

Monte um `InformeSintetico<Tipo>Document` (um `header` + de 1 a N `informs`, um por fundo,
todos da **mesma competência** e do **mesmo administrador**) e serialize com
`InformeSintetico<Tipo>().export(...)`. Cada arquivo é mensal; a CVM exige o envio até o
quinto dia útil do mês seguinte.

Os campos de cada modelo são o nome da tag em minúsculas e estão declarados **na ordem do
arquivo de exemplo da CVM**. Os modelos são imutáveis, recusam campos desconhecidos e **todos os
campos são obrigatórios** (a página manda preencher todos).

| Modelo | Tag XML |
|--------|---------|
| `...Document` | `DOC_ARQ` (+ `INFORME_SINTETICO`) |
| `FcceHeader` · `FitvmHeader` · `FicHeader` · `OutrosHeader` | `DESC_ADM` (`COD_DOC` fixo: 5, 7, 8, 9) |
| `...Inform` | `ROW_INFORME` (`cnpj_fundo` + `aplicacoes_pos_final`) |
| `...AplicacoesPosFinal` | `APLICACOES_POS_FINAL` |
| `...Aplicacoes` · `...Outras` | `APLICACOES` · `OUTRAS` |
| `SinteticoMercATermo` · `SinteticoMercOpcao` | `MERC_A_TERMO` · `MERC_OPCAO` (FITVM e Outros) |
| `SinteticoContrFuturo` · `SinteticoDebt` | `CONTR_FUTURO` · `DEBT` (só FITVM) |

### Diferenças entre as tipos

- **FCCE:** `ACOES`, `QUOTA_FDO_RENDA_FIXA`, `TIT_DIVIDA_PUBLIC_FED`,
  `OUTRO_VL_MOBILI_EMISS_CIA_ABER`, `OUTRA_APLIC`; em `OUTRAS` abre com
  `VL_CONTR_FUTURO_MANTIDO_ABER`.
- **FITVM:** `ACAO`, `MERC_A_TERMO`, `CONTR_FUTURO`, `MERC_OPCAO`, `DEBT` (`SIMPLES`,
  `CONVERSIVEIS`), certificados/recibos, títulos públicos, renda fixa de instituição financeira,
  quotas de fundo financeiro, outras.
- **FIC-FITVM:** só `COTAS`, `TIT_PUBLIC`, `TIT_RENDA_FIXA_EMISS_INSTIT_FINANC`,
  `COTA_FDO_INVEST_FINANC`, `OUTRA_APLIC`.
- **Outros:** `ACAO`, `MERC_OPCAO` antes de `MERC_A_TERMO`, `CONVERSIVEIS` e `SIMPLES` direto em
  `APLICACOES` (sem `DEBT`, nesta ordem), `TIT_PUBLIC`, `MOEDA_PRIVAT`, `OUTRA_APLIC`; `OUTRAS`
  abre com `VL_CONTR_FUTURO_MANTIDO_ABERTO` (o FCCE grafa `..._ABER`).

## Tipagem

- **Valores em R$ mil** ("INTEIROS" na página): inteiro estrito (`float`, `bool` e texto são
  recusados), de 0 a 2^63-1. `PATRIM_LIQ` é o único que aceita negativo (fundo com patrimônio
  negativo). `NR_TOT_QUOTST_ULT_DIA_MES` é contagem, ≥ 0.
- **`VL_QUOTA_ULT_DIA_MES`** é o único decimal. A página só diz "(decimal)" e **não informa
  escala**: aplicada a escala de dinheiro do repositório, **2 casas, truncando em direção a zero**
  (nunca arredondando), até 18 dígitos, ≥ 0. Entram `Decimal`, `int` e `str`; `float`, `bool`, NaN
  e infinito são recusados. Saída com vírgula decimal (`1,23`).
- **Datas:** `DT_COMPT` `MM/AAAA` e `DT_GERAC_ARQ` `DD/MM/AAAA` precisam existir no calendário
  (31/02 é recusado), com dígitos ASCII e ano ≥ 1900.
- **CNPJ** (`CNPJ_ADM`, `CNPJ_FUNDO`): forma validada primeiro (14 caracteres ou máscara
  `NN.NNN.NNN/NNNN-NN`) e depois por dígito verificador. Na saída sai sem máscara **e sem zeros à
  esquerda**, como a página manda ("pontos, traços, barras e zeros a esquerda devem ser omitidos").
- **Regras entre campos:** ao menos um `ROW_INFORME`; o mesmo `CNPJ_FUNDO` não pode repetir no
  arquivo.
- Arquivo em `windows-1252`, sem comentários, sem namespace; o destino só é aberto depois que o
  texto foi codificado e checado.

## Limites e pontos em aberto

1. **Nenhum validador da CVM foi executado.** A página sugere checar a sintaxe num leitor de XML;
   o XML foi conferido apenas pelos testes do repositório, contra as listas de tags digitadas
   da página.
2. **Escala de `VL_QUOTA_ULT_DIA_MES`** é política do repositório, não número da CVM. Uma cota
   costuma ter mais casas; a constante está em um só lugar do schema (`_QUOTA_SCALE`).
3. **FIC-FITVM:** a lista de tags descreve `OUTRAS` sem `VL_QUOTA_ULT_DIA_MES`, mas o exemplo da
   página o traz. Seguido o **exemplo** (campo obrigatório).
4. **Outros:** a lista de tags omite os contêineres `APLICACOES`/`OUTRAS`, que o exemplo traz.
   Seguido o **exemplo**. O título da página diz FICE, FMP-FGTS e FMAI (a issue do repositório
   resume como FMP-FGTS/FMAI).
5. **Zeros à esquerda do CNPJ** são removidos na saída, conforme o texto da página; CNPJ
   alfanumérico recebe o mesmo tratamento.
6. **Sinais:** a página não diz quais campos podem ser negativos; só `PATRIM_LIQ` aceita.
7. **Arquivo único por competência/administrador** é garantido por haver um só cabeçalho; que os
   fundos pertençam mesmo àquele administrador não é verificável.
8. Não há leitura do XML de volta, e o envio ao CVMWeb está fora do escopo.

---

## Exemplos

### FIC-FITVM

```python
from filings_cvm.submission import InformeSinteticoFic, InformeSinteticoFicDocument

doc = InformeSinteticoFicDocument.model_validate({
    "header": {"cnpj_adm": "00360305000104", "dt_compt": "09/2026", "dt_gerac_arq": "05/10/2026"},
    "informs": [{
        "cnpj_fundo": "11222333000181",
        "aplicacoes_pos_final": {
            "aplicacoes": {
                "cotas": 100, "tit_public": 0, "tit_renda_fixa_emiss_instit_financ": 0,
                "cota_fdo_invest_financ": 0, "outra_aplic": 0,
            },
            "outras": {
                "nr_tot_quotst_ult_dia_mes": 12, "vl_quota_ult_dia_mes": "1.2345",
                "patrim_liq": 100, "quota_emitida_mes": 10, "quota_resg_mes": 5,
            },
        },
    }],
})

xml = InformeSinteticoFic().export(doc)                       # retorna str
InformeSinteticoFic().export(doc, output_path="sint_fic.xml")  # grava windows-1252, retorna None
```

### Outro tipo de fundo

Troque o par `Document`/writer e o formato dos blocos (`InformeSinteticoFcceDocument`,
`InformeSinteticoFitvmDocument`, `InformeSinteticoOutrosDocument`); a tabela acima lista os campos.

### Valor recusado cedo

```python
from pydantic import ValidationError

try:
    InformeSinteticoFicDocument.model_validate(
        {"header": {"cnpj_adm": "00360305000104", "dt_compt": "13/2026",
                    "dt_gerac_arq": "05/10/2026"}, "informs": []})
except ValidationError as exc:
    print(exc)   # mês 13 não existe; informs precisa de ao menos 1
```
