# **Exemplos**

Receitas curtas e autocontidas para tarefas comuns. Cada uma se sustenta sozinha — copie e ajuste.

> **Veja também:** [Uso](usage.md) para o básico · [Referência da API](api.md) para cada símbolo
> público.

---

## Receita: gerar o arquivo XML mínimo do Perfil Mensal

O menor documento válido: um cabeçalho e uma linha com apenas os campos obrigatórios.

```python
from filings_cvm.submission import (
    ClientCount,
    DocumentHeader,
    PerfilMensal,
    PerfilMensalDocument,
    PerfilMensalRow,
)

clientes = ClientCount(
    nr_pf_priv_bank=0, nr_pf_varj=0,
    nr_pj_n_financ_priv_bank=0, nr_pj_n_financ_varj=0,
    nr_bnc_comerc=0, nr_pj_corr_dist=0, nr_pj_outr_financ=0,
    nr_inv_n_res=0, nr_ent_ab_prev_compl=0, nr_ent_fc_prev_compl=0,
    nr_reg_prev_serv_pub=0, nr_soc_seg_reseg=0,
    nr_soc_captlz_arrendm_merc=0, nr_fdos_club_inv=0,
    nr_cotst_distr_fdo=0, nr_outros_n_relac=0,
)

doc = PerfilMensalDocument(
    header=DocumentHeader(dt_compt="01/2025", dt_gerac_arq="15/01/2025"),
    rows=[
        PerfilMensalRow(
            cnpj_fdo="11222333000181",
            nr_client=clientes,
            total_recurs_exter="0",
            total_recurs_br="0",
            tot_ativos_p_relac="0",
            tot_ativos_cred_priv="0",
        )
    ],
)

xml = PerfilMensal().to_xml(doc)
print(xml)
```

---

## Receita: escrever direto em disco (codificação da CVM)

Quando `output_path` é informado, o arquivo é gravado em **`windows-1252`** — a codificação que a
CVM espera — e o método retorna `None`.

```python
# doc: PerfilMensalDocument já montado (veja a receita anterior)
PerfilMensal().to_xml(doc, output_path="perfil_202501.xml")
# o arquivo perfil_202501.xml está pronto para envio à CVM
```

---

## Receita: truncamento de casas decimais (nunca arredonda para cima)

Valores com precisão excedente são cortados em direção a zero (`ROUND_DOWN`), garantindo que um
valor reportado nunca ultrapasse o que o padrão permite. `TOTAL_RECURS_BR` usa duas casas:

```python
# ... total_recurs_br="10.999" na linha ...
xml = PerfilMensal().to_xml(doc)
assert "<TOTAL_RECURS_BR>10,99</TOTAL_RECURS_BR>" in xml   # 10,99 — não 11,00
```

Repare também no **separador decimal por vírgula** (`10,99`), exigido pelo padrão CVM.

---

## Receita: várias classes de fundo em um só documento

`rows` aceita uma lista — cada item vira um bloco `<ROW_PERFIL>`.

```python
doc = PerfilMensalDocument(
    header=DocumentHeader(dt_compt="01/2025", dt_gerac_arq="15/01/2025"),
    rows=[
        PerfilMensalRow(cnpj_fdo="11222333000181", nr_client=clientes,
                        total_recurs_exter="0", total_recurs_br="0",
                        tot_ativos_p_relac="0", tot_ativos_cred_priv="0"),
        PerfilMensalRow(cnpj_fdo="11444777000161", nr_client=clientes,
                        total_recurs_exter="0", total_recurs_br="0",
                        tot_ativos_p_relac="0", tot_ativos_cred_priv="0"),
    ],
)
```

---

## Receita: tratar a rejeição de CNPJ inválido

Um CNPJ com dígitos verificadores incorretos levanta `ValidationError` já na construção do modelo
— falhe cedo, antes de gerar qualquer XML.

```python
from pydantic import ValidationError
from filings_cvm.submission import PerfilMensalRow

try:
    PerfilMensalRow(
        cnpj_fdo="12345678000100",   # dígitos verificadores inválidos
        nr_client=clientes,
        total_recurs_exter="0", total_recurs_br="0",
        tot_ativos_p_relac="0", tot_ativos_cred_priv="0",
    )
except ValidationError as exc:
    print("CNPJ recusado:", exc)
```
