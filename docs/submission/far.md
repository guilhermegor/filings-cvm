# **FAR — Demonstrativo de Fontes e Aplicações de Recursos**

Envio (→ CVM) do padrão **FAR**
([`PadraoXMLFAR.asp`](https://cvmweb.cvm.gov.br/SWB/Sistemas/SCW/PadroesXML/PadraoXMLFAR.asp)).

> **Veja também:** [Referência da API](../api.md) para cada símbolo público · [Uso](../usage.md)
> para instalação e o conceito geral.

---

## Descrição

O FAR expressa o fluxo de caixa do fundo em regime de caixa, com periodicidade mensal. Monte um
`FarDocument` (um `FarHeader` + de 1 a N `FarFund`, todos da **mesma competência e do mesmo
administrador**) e serialize com `Far().export(...)`.

| Modelo | Tag XML | Papel |
|--------|---------|-------|
| `FarDocument` | `DOC_ARQ` / `FAR` | Documento: `header` + `funds` (pelo menos 1; `CNPJ_FUNDO` sem repetição). |
| `FarHeader` | `DESC_ADM` | `COD_DOC` = 4 (fixo), `CNPJ_ADM`, `DT_COMPT` `MM/AAAA`, `DT_GERAC_ARQ` `DD/MM/AAAA`. |
| `FarFund` | `ROW_REGISTRO_MOVIMENTO` | O informe de um fundo, com `DOC_MOV_MES` a partir de `movements`. |
| `FarMovement` | `ROW_MOV_POR_FUNDO` | Uma movimentação da Tabela A (`CD_MOV`, `VL_ENTR`, `VL_SAIDA`). |

Os campos são o nome da tag em minúsculas e seguem a ordem da página. Os modelos são imutáveis e
recusam campos desconhecidos. A codificação do arquivo é `windows-1252`; a página não informa
número de versão.

## Tipagem

- **Decimais com 10 casas** (`NR_QUOTA_CIRCUL_ULT_DIA_MES`, `VL_QUOTA_ULT_DIA_MES`,
  `VL_ULT_DISTR_QUOTA`, `VL_QUOTA_DT_ULT_DISTR`): escala **dita pela página**, truncada em direção
  a zero (`ROUND_DOWN`), nunca negativa. Entram `Decimal`, `int` e `str`; **`float`, `bool`, NaN e
  infinito são recusados**. Na saída a vírgula é o separador e a escala é fixa
  (`1000,5000000000`).
- **Inteiros** (`NR_TOTAL_QUOTST_ULT_DIA_MES`, `VL_ENTR`, `VL_SAIDA`, em R$ mil): inteiros
  estritos, não negativos, até 64 bits. A página diz "inteiro, salvo onde indicado" e não indica
  exceção.
- **CNPJ** (`CNPJ_ADM`, `CNPJ_FUNDO`): o formato (14 caracteres, nu ou com máscara) é checado
  antes do dígito verificador; a página pede **somente dígitos**, então CNPJ alfanumérico é
  recusado. Na saída vai **sem máscara e sem zeros à esquerda**, como a página manda.
- **Datas**: `DD/MM/AAAA` e `MM/AAAA` precisam existir no calendário (31/02 é recusado), com dígitos
  ASCII e ano ≥ 1900.

### Regras entre campos

- `VL_ULT_DISTR_QUOTA`, `DT_DISTR` e `VL_QUOTA_DT_ULT_DISTR` são condicionais: **os três juntos ou
  nenhum** (sem distribuição no mês, as três tags não aparecem).
- **Tabela A:** todo código (37, 48, 53, …, 150) aparece **exatamente uma vez** por fundo. Cada
  código só aceita as colunas que a tabela marca como preenchíveis: onde a tabela diz "N" a coluna
  deve ficar vazia e **a tag é omitida**; onde diz "S" o valor é obrigatório.

## Limites e pontos em aberto

- **A página se contradiz:** diz que cada movimentação tem `VL_ENTR` e `VL_SAIDA` (1 por
  movimentação) e, ao mesmo tempo, que na Tabela A "N" significa "não pode ser preenchido".
  Escolha: a tag da coluna "N" **é omitida** (não é emitida vazia nem com zero).
- A página não diz se a ordem dos `ROW_MOV_POR_FUNDO` importa; são emitidos na ordem de `movements`.
- Competência e administrador iguais para todos os fundos: o arquivo tem um único cabeçalho, então
  isso é garantido por construção.
- Não é verificado que `DT_DISTR` caia no mês da competência nem que `DT_GERAC_ARQ` seja posterior
  a ela (a página não afirma).
- O XML não declara namespace (a página não cita um).
- Nenhum validador da CVM foi executado.

## Exemplos

### Arquivo mínimo

```python
from filings_cvm.submission import Far, FarDocument

# Tabela A completa: (código, Entrada preenchível, Saída preenchível)
CODES = {37: "ES", 48: "ES", 53: "E", 54: "S", 55: "ES", 56: "E", 57: "E", 58: "E", 60: "E",
         61: "S", 62: "S", 63: "S", 64: "S", 65: "S", 66: "S", 67: "E", 68: "S", 69: "S",
         70: "ES", 71: "E", 72: "S", 73: "S", 74: "ES", 75: "ES", 77: "ES", 78: "ES",
         144: "E", 145: "ES", 150: "S"}
movements = [
    {"cd_mov": code, "vl_entr": 0 if "E" in cols else None, "vl_saida": 0 if "S" in cols else None}
    for code, cols in CODES.items()
]
doc = FarDocument(
    header={"cnpj_adm": "11.444.777/0001-61", "dt_compt": "09/2026", "dt_gerac_arq": "10/10/2026"},
    funds=[{
        "cnpj_fundo": "11222333000181",
        "nr_quota_circul_ult_dia_mes": "1000.5",
        "vl_quota_ult_dia_mes": "12.1234567890",
        "nr_total_quotst_ult_dia_mes": 42,
        "movements": movements,
    }],
)
xml = Far().export(doc)
```

### Com distribuição no mês

Acrescente os três campos juntos: `vl_ult_distr_quota="0.5"`, `dt_distr="05/09/2026"`,
`vl_quota_dt_ult_distr="12.1"`.

### Escrever em disco (windows-1252)

```python
Far().export(doc, output_path="far.xml")  # retorna None
```

O texto é codificado e checado como XML bem formado **antes** de abrir o destino: uma falha não
trunca um arquivo existente.

### Valor recusado cedo

```python
FarDocument(header=..., funds=[{..., "vl_quota_ult_dia_mes": 1.5}])  # ValidationError: float
```
