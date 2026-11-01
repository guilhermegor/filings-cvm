# **Lâmina de Fundos — V1**

Envio (→ CVM) do padrão **Lâmina de Fundos V1**
([`PadraoXMLLamina.asp`](https://cvmweb.cvm.gov.br/SWB/Sistemas/SCW/PadroesXML/PadraoXMLLamina.asp)),
a versão original (`COD_DOC` 24, `VERSAO` 1.0, Instrução CVM 522).

> **Veja também:** [Referência da API](../api.md) · [Uso](../usage.md) · versão vigente:
> [Lâmina V3](lamina.md).

---

## Descrição

Monte um `LaminaV1Document` (um `LaminaV1Header` + de 1 a 70 `LaminaV1Inform`, um por fundo, todos
da **mesma competência**) e serialize com `LaminaV1().export(...)`.

| Modelo | Tag XML | Papel |
|--------|---------|-------|
| `LaminaV1Document` | `DOC_ARQ` / `LISTA_INFORM` | Documento: `header` + `informs` (1 a 70). |
| `LaminaV1Header` | `CAB_INFORM` | `COD_DOC` = 24 e `VERSAO` = 1.0 (fixos), `DT_COMPT` `MM/AAAA`, `DT_GERAC_ARQ` `DD/MM/AAAA`. |
| `LaminaV1Inform` | `INFORM` | A lâmina de um fundo (37 campos). |

Todos os blocos internos (`CARENCIA`, `CONVERSAO`, `INFOR_TX_ADM`, `INFOR_TX_ENTR`,
`INFOR_TX_SAIDA`, `INFOR_DESPESAS`, `LISTA_COMP_CARTEIRA`, `INFOR_TAB_RENT_ANUAL`,
`LISTA_TAB_RENT_ANUAL`, `LISTA_TAB_RENT_MENSAL`, `TAB_VAR_DESEMP`, `INFORM_EXEMPLO_COMP`,
`TAB_SIMUL_DESPESAS`) são **os mesmos da V3** (`Lamina*`, ver [Lâmina V3](lamina.md)): a página da
V1 os define com as mesmas tags, ordem, tamanhos e cardinalidades, então o esquema os importa em
vez de copiá-los. Tipagem, escalas decimais e regras entre campos são as da V3.

## O que a V1 muda em relação à V3 (medido na página)

| | V1 | V3 |
|---|---|---|
| Identificação | `CNPJ_FUNDO` obrigatório | `CNPJ_FUNDO` **ou** `COD_SUBCLASSE` |
| `ALAV` | obrigatório | opcional |
| `CONC_EMISSOR` | existe (0 a 100) | não existe |
| `UTILIZ_DERIV_APENAS_PROTECAO_CART`, `PERC_MAX`, `OBS_HOR_APL_RESG`, `TP_PRAZO_DIAS` | **não existem** (`PRAZO_PAGAM` é sempre em dias úteis) | existem |
| `DS_FORMA_REMUN_DISTR`, `PRINC_DISTR_OFERTA`, `PRINC_CONFLITO_INTERES`, `INFO_ADIC` | **não existem** | existem |
| `VERSAO` | `1.0` | `3.0` |

Campos da V3 passados à V1 são **recusados** (o modelo é fechado), não descartados em silêncio. A
ordem dos campos é a do arquivo de exemplo da página, e os testes a fixam com a lista de tags
digitada a partir dela.

## Limites e pontos em aberto

1. **Nenhum validador da CVM foi executado**; o XML foi verificado apenas contra os testes.
2. **Namespace:** o exemplo usa `xmlns="urn:lamina"`; a lista de tags diz `urn:infdiario` (cópia
   do Informe Diário). Foi usado `urn:lamina`, como na V3.
3. **Tag do mês:** o exemplo escreve `<MES>` e a lista de tags `<MES_RENT>`; foi usado `MES`
   (herdado de `LaminaTabRentMensal`).
4. **Escalas decimais** não constam da página (tudo é "float"); valem as do repositório (dinheiro 2
   casas, percentual 4, truncando), como na V3. `CONC_EMISSOR` é limitado a 0 a 100 por
   inferência do significado.
5. Blocos que a página marca como "não obrigatório para fundos com menos de um ano" são opcionais
   para todos; a idade do fundo não consta do arquivo e a obrigatoriedade não é verificada.
6. Autorização e envio ficam fora do escopo; a biblioteca só gera o arquivo.
7. A escrita em disco é atômica (arquivo temporário no mesmo diretório e `os.replace`); um erro de
   codificação ou de XML levanta `ValueError` antes de tocar o destino.

---

## Exemplos

### Arquivo XML mínimo

```python
from filings_cvm.submission import LaminaV1, LaminaV1Document

doc = LaminaV1Document.model_validate({
    "header": {"dt_compt": "12/2024", "dt_gerac_arq": "15/01/2025"},
    "informs": [{
        "cnpj_fundo": "11222333000181",
        "nome_fantasia": "Fundo Alfa",
        "end_eletr": "www.alfa.com.br",
        "desc_pub_alvo": "Investidores em geral",
        "restr_inv": "Nenhuma",
        "desc_objet": "Superar o CDI",
        "desc_pol_inv": "Títulos públicos",
        "ativo_ext": "10", "cred_priv": "20", "alav": "1", "conc_emissor": "30",
        "perdas_sign": "N", "pl_negat": "N",
        "inv_inicial": "100", "inv_adic": "50", "resg_min": "10", "valor_perm": "0",
        "hor_apl_resg": "14:30",
        "conversao": {"abert_fech": "A", "dia_aplic": 1, "abert_fech_c": "F", "dia_resg": 2},
        "prazo_pagam": 3,
        "infor_tx_adm": {"tipo_tx_adm": "F", "tx_adm": "1.5"},
        "tx_desempenho": "20% do que exceder o CDI",
        "classif_risco": 3,
        "tel_sac": "1140041234", "reclamacoes": "sac@alfa.com.br",
    }],
})

print(LaminaV1().export(doc))
```

### Escrever em disco (windows-1252)

```python
LaminaV1().export(doc, output_path="lamina_v1_202412.xml")
```
