# **Lâmina de Fundos — V3**

Envio (→ CVM) do padrão **Lâmina de Fundos V3**
([`PadraoXMLLaminaV3.asp`](https://cvmweb.cvm.gov.br/SWB/Sistemas/SCW/PadroesXML/PadraoXMLLaminaV3.asp)).

> **Veja também:** [Referência da API](../api.md) para cada símbolo público · [Uso](../usage.md)
> para instalação e o conceito geral · leitura do dump aberto:
> [Lâmina FIF](../ingestion/lamina.md).

---

## Descrição

Monte um `LaminaDocument` (um `LaminaHeader` + de 1 a 70 `LaminaInform`, uma por classe ou
subclasse de cotas, todas da **mesma competência**) e serialize com `Lamina().export(...)`.

| Modelo | Tag XML | Papel |
|--------|---------|-------|
| `LaminaDocument` | `DOC_ARQ` / `LISTA_INFORM` | Documento: `header` + `informs` (1 a 70). |
| `LaminaHeader` | `CAB_INFORM` | `COD_DOC` = 24 e `VERSAO` = 3.0 (fixos), `DT_COMPT` `MM/AAAA`, `DT_GERAC_ARQ` `DD/MM/AAAA`. |
| `LaminaInform` | `INFORM` | A lâmina de um fundo. |
| `LaminaCarencia` | `CARENCIA` | Carência (bloco opcional). |
| `LaminaConversao` | `CONVERSAO` | Conversão de cotas na aplicação e no resgate. |
| `LaminaTaxaAdministracao` | `INFOR_TX_ADM` | Taxa fixa (`F`) ou variável (`V`). |
| `LaminaTaxaEntrada` | `INFOR_TX_ENTR` | Taxa de entrada (opcional). |
| `LaminaTaxaSaida` | `INFOR_TX_SAIDA` | Taxa de saída (opcional). |
| `LaminaDespesas` | `INFOR_DESPESAS` | Despesas do período (opcional). |
| `LaminaListaCompCarteira` · `LaminaCompCarteira` | `LISTA_COMP_CARTEIRA` · `COMP_CARTEIRA` | PL e de 1 a 5 espécies de ativo (opcional). |
| `LaminaInforTabRentAnual` · `LaminaAntesInic2` | `INFOR_TAB_RENT_ANUAL` · `ANTES_INIC2` | Rentabilidade em 5 anos, índice de referência e anos sem dados (opcional). |
| `LaminaListaTabRentAnual` · `LaminaTabRentAnual` | `LISTA_TAB_RENT_ANUAL` · `TAB_RENT_ANUAL` | Até 5 anos de rentabilidade (opcional). |
| `LaminaListaTabRentMensal` · `LaminaTabRentMensal` | `LISTA_TAB_RENT_MENSAL` · `TAB_RENT_MENSAL` | Até 12 meses de rentabilidade (opcional). |
| `LaminaTabVarDesemp` | `TAB_VAR_DESEMP` | Variação do desempenho e fórmula (opcional). |
| `LaminaInformExemploComp` | `INFORM_EXEMPLO_COMP` | Exemplo de custos no ano de emissão (opcional). |
| `LaminaTabSimulDespesas` | `TAB_SIMUL_DESPESAS` | Simulação de despesas a 3 e 5 anos (opcional). |

Os campos de cada modelo são o nome da tag em minúsculas (`nome_fantasia` → `NOME_FANTASIA`) e
estão declarados **na ordem do arquivo de exemplo da CVM**; o serializador percorre os campos nessa
ordem, omite o que é `None` e repete o elemento de cada lista. Os modelos são imutáveis e recusam
campos desconhecidos.

**Identificação:** cada `INFORM` informa **exatamente um** de `cnpj_fundo` (classe, validado por
dígito verificador, gravado sem máscara) ou `cod_subclasse`. O mesmo CNPJ ou código não pode
aparecer duas vezes no arquivo.

## Tipagem

### Decimais — escala é política do repositório, não número da CVM

A página tipa todo valor numérico como "float" e **não informa nenhuma escala**. Foram aplicadas as
escalas padrão do repositório (truncamento em direção a zero, `ROUND_DOWN`, nunca arredondamento):

| Tipo | Escala | Faixa | Campos |
|------|--------|-------|--------|
| dinheiro | 2 | ≥ 0 | `inv_inicial`, `inv_adic`, `resg_min`, `valor_perm`, `valor_resg`, `impostos`, `valor_ing`, `valor_saida`, `valor_despesas`, `desp_prev3`, `desp_prev5` |
| dinheiro com sinal | 2 | qualquer | `pl_fundo` (existe `PL_NEGAT`), `ajuste_perfor`, `retor_brut3`, `retor_brut5` |
| percentual | 4 | 0 a 100 | `ativo_ext`, `cred_priv`, `perc_max` (a página fixa o máximo em 100,00), `perc_pl`, `tx_adm`, `tx_min`, `tx_max`, `tx_entr`, `tx_saida`, `despesas` |
| razão | 4 | ≥ 0 | `alav` |
| percentual com sinal | 4 | qualquer | `rent_5anos`, `rent_ind_ref`, `rent_liq`, `var_ind_ref`, `rent_perc_ind_ref`, `rent_mens`, `var_mens_ind_ref`, `rent_mens_perc_ind_ref`, `var_desemp` |

Todos têm no máximo 18 dígitos. Entram `Decimal`, `int` e `str`; **`float`, `bool`, NaN e infinito
são recusados** (o erro binário do `float` já veio embutido). `-0,00` sai como `0,00`. Na
serialização a vírgula é o separador decimal e a escala é fixa (`10,5000`).

### Inteiros, textos e formatos

- **`short`** (`dias_car`, `dia_aplic`, `dia_resg`, `prazo_pagam`, `dias_saida`): inteiro estrito de
  0 a 32767. Anos: 1900 a 9999. `mes`: 1 a 12. `classif_risco`: 1 a 5. `anos_abaixo`: 0 a 5.
  Sem zeros à esquerda na saída.
- **Datas** (`DD/MM/AAAA`, `MM/AAAA`): precisam existir no calendário (31/02 é recusado), com
  dígitos ASCII, e ano ≥ 1900. `HOR_APL_RESG` é `HH:MM` de 00:00 a 23:59. Os formatos mantêm o
  preenchimento com zeros que a própria página define para eles.
- **Textos**: nunca vazios nem só espaços, até o tamanho máximo "até N casas" da página (500, 100, 1000,
  900, 300, 600, 50 e 20 conforme o campo; `reclamacoes` tem só 50). Caracteres de controle
  (exceto `\n` e `\t`) e qualquer caractere que o `windows-1252` não codifica são recusados na
  construção do modelo.
- **`tel_sac`** (long): só dígitos, sem zero à esquerda, até 19 dígitos e cabendo em 64 bits. Por
  isso um número iniciado em zero (como 0800) não pode ser enviado como a página o define.
- **S/N, A/F, F/V, 1/2**: valores literais exatos; `tp_prazo_dias` é a *string* `"1"` ou `"2"`.

### Regras entre campos

- `INFOR_TX_ADM`: taxa **fixa** (`F`) exige `tx_adm` e proíbe `tx_min`/`tx_max`; **variável** (`V`)
  exige `tx_min` e `tx_max` (com `tx_min ≤ tx_max`) e proíbe `tx_adm`.
- `inic_periodo ≤ fim_periodo`; `ano_ant = ano_emiss − 1`.
- `COMP_CARTEIRA`: 1 a 5; `TAB_RENT_ANUAL`: 1 a 5 linhas sem ano repetido; `TAB_RENT_MENSAL`: 1 a
  12 linhas sem mês repetido; um ano não pode estar ao mesmo tempo em `ANTES_INIC2` e numa linha
  anual.
- `rent_ind_ref`, `var_ind_ref`, `rent_perc_ind_ref`, `var_mens_ind_ref` e
  `rent_mens_perc_ind_ref` só são aceitos com `ind_refer` ("quando houver").

## Limites e pontos em aberto

O que a biblioteca **não** garante, e o que a página deixa sem resposta:

1. **Nenhum validador da CVM foi executado.** A página oferece um teste de sintaxe do arquivo; o XML
   gerado foi verificado apenas contra os testes deste repositório.
2. **Namespace:** o exemplo da página usa `xmlns="urn:lamina"` e a lista de tags diz
   `urn:infdiario` (cópia do Informe Diário). Foi usado `urn:lamina`.
3. **Tag do mês:** o exemplo escreve `<MES>` e a lista de tags escreve `<MES_RENT>`. Foi usado
   `MES`. Trocar é uma linha (o nome do campo em `LaminaTabRentMensal`).
4. **Escalas decimais** não constam da página (acima). A faixa de cada campo é inferida do
   significado, não declarada pela CVM.
5. **`cod_subclasse`:** a página não dá formato nem tamanho; assumido 1 a 50 caracteres.
6. **Fundos com menos de um ano:** a página marca vários blocos como "não obrigatório" para eles,
   mas a idade do fundo não consta do arquivo. Esses blocos são opcionais para todos e **a
   obrigatoriedade para os fundos mais antigos não é verificada**. Dentro de um bloco presente,
   todo campo que a página não marca como opcional é obrigatório.
7. **Subclasses:** a página rejeita o envio se as subclasses de uma classe não vierem todas no
   mesmo arquivo; o arquivo não traz a relação classe → subclasse, então isso **não é verificado**.
   A competência única por arquivo é garantida por haver um só `DT_COMPT`.
8. **Autorização e envio** (administrador de carteira, delegação no CVMWeb) estão fora do escopo; a
   biblioteca só gera o arquivo.
9. Não há leitura do XML de volta (`ingestion` lê o dump aberto, que é outro artefato).
10. Um erro de codificação ou de XML (só possível com validação contornada, p. ex.
    `model_construct`) levanta `ValueError` **antes** de abrir o destino.

---

## Exemplos

### Arquivo XML mínimo

```python
from filings_cvm.submission import Lamina, LaminaDocument

doc = LaminaDocument.model_validate({
    "header": {"dt_compt": "01/2025", "dt_gerac_arq": "15/01/2025"},
    "informs": [{
        "cnpj_fundo": "11222333000181",
        "nome_fantasia": "Fundo Alfa",
        "end_eletr": "www.alfa.com.br",
        "desc_pub_alvo": "Investidores em geral",
        "restr_inv": "Nenhuma",
        "desc_objet": "Superar o CDI",
        "desc_pol_inv": "Títulos públicos",
        "ativo_ext": "10", "cred_priv": "20", "perc_max": "100",
        "utiliz_deriv_apenas_protecao_cart": "S", "perdas_sign": "N", "pl_negat": "N",
        "inv_inicial": "100", "inv_adic": "50", "resg_min": "10", "valor_perm": "0",
        "hor_apl_resg": "14:30", "obs_hor_apl_resg": "Até as 14h30",
        "conversao": {"abert_fech": "A", "dia_aplic": 1, "abert_fech_c": "F", "dia_resg": 2},
        "tp_prazo_dias": "1", "prazo_pagam": 3,
        "infor_tx_adm": {"tipo_tx_adm": "F", "tx_adm": "1.5"},
        "tx_desempenho": "20% do que exceder o CDI",
        "classif_risco": 3,
        "ds_forma_remun_distr": "Parte da taxa de administração",
        "princ_distr_oferta": "Não", "princ_conflito_interes": "Nenhum",
        "tel_sac": "1140041234", "reclamacoes": "sac@alfa.com.br", "info_adic": "Nada a declarar",
    }],
})

print(Lamina().export(doc))
```

### Escrever em disco (windows-1252)

```python
Lamina().export(doc, output_path="lamina_202501.xml")
```

O arquivo só é aberto depois que o texto foi codificado e checado; uma falha nunca deixa o
destino truncado.

### Taxa de administração variável

```python
"infor_tx_adm": {"tipo_tx_adm": "V", "tx_min": "0.5", "tx_max": "2"}
```

### Subclasse em vez de classe

```python
{"cod_subclasse": "SUB-001", ...}   # sem cnpj_fundo
```

### Tabelas de rentabilidade com índice de referência

```python
"infor_tab_rent_anual": {"ind_refer": "CDI", "rent_ind_ref": "40"},
"lista_tab_rent_anual": {"tab_rent_anual": [
    {"ano_rent": 2024, "rent_liq": "10", "var_ind_ref": "11"},
]},
"lista_tab_rent_mensal": {"tab_rent_mensal": [
    {"mes": 1, "rent_mens": "0.8"},
]},
```

### Valor recusado cedo

```python
from pydantic import ValidationError

try:
    LaminaDocument.model_validate({"header": {"dt_compt": "01/2025", "dt_gerac_arq": "31/02/2025"},
                                   "informs": []})
except ValidationError as exc:
    print(exc)   # 31/02 não existe; informs precisa de ao menos 1
```
