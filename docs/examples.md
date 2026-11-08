# **Exemplos**

Receitas autocontidas para tarefas comuns com a biblioteca. Cada receita é independente — copie e
ajuste.

> **Veja também:** [Uso](usage.md) para o básico · [Referência da API](api/index.md) para cada
> símbolo público.

---

## Receita: ler o Informe Diário de um mês

Baixa o dump aberto da CVM para o mês e devolve um `DataFrame` tipado. Qualquer dia do mês
seleciona o dump; prefira um mês passado, pois o corrente pode ainda não estar publicado.

```python
from datetime import date

from filings_cvm.ingestion.fi import InformeDiarioReader

df_ = InformeDiarioReader(date_ref=date(2025, 1, 15)).read()

print(df_.dtypes)
print(df_.head())
```

## Receita: guardar o arquivo bruto baixado

Com `path_raw`, o artefato original (`.zip`, `.csv`, …) é gravado e **mantido** antes de qualquer
parse — assim, se a CVM mudar o contrato, os bytes que quebraram a transformação continuam em
disco para reprocessamento. Sem `path_raw`, nada persiste.

```python
from datetime import date
from pathlib import Path

from filings_cvm.ingestion.fi import InformeDiarioReader

df_ = InformeDiarioReader(date_ref=date(2025, 1, 15), path_raw=Path("raw")).read()
```

## Receita: gerar um XML para envio à CVM

O fluxo de envio valida o modelo na construção e só então serializa. Exemplo mínimo (Perfil
Mensal, apenas os campos obrigatórios):

```python
from filings_cvm.submission import (
    ClientCount,
    DocumentHeader,
    PerfilMensal,
    PerfilMensalDocument,
    PerfilMensalRow,
)

header = DocumentHeader(dt_compt="01/2025", dt_gerac_arq="15/01/2025")
clientes = ClientCount(
    nr_pf_priv_bank=0, nr_pf_varj=0,
    nr_pj_n_financ_priv_bank=0, nr_pj_n_financ_varj=0,
    nr_bnc_comerc=0, nr_pj_corr_dist=0, nr_pj_outr_financ=0,
    nr_inv_n_res=0, nr_ent_ab_prev_compl=0, nr_ent_fc_prev_compl=0,
    nr_reg_prev_serv_pub=0, nr_soc_seg_reseg=0,
    nr_soc_captlz_arrendm_merc=0, nr_fdos_club_inv=0,
    nr_cotst_distr_fdo=0, nr_outros_n_relac=0,
)
linha = PerfilMensalRow(
    cnpj_fdo="11222333000181",
    nr_client=clientes,
    total_recurs_exter="0",
    total_recurs_br="0",
    tot_ativos_p_relac="0",
    tot_ativos_cred_priv="0",
)
doc = PerfilMensalDocument(header=header, rows=[linha])

xml = PerfilMensal().export(doc)                              # string, sem tocar o disco
PerfilMensal().export(doc, output_path="perfil_202501.xml")   # ou grava o arquivo
```

Valores decimais vão como **strings** (`"10.5"`), nunca `float`. Todos os campos e os demais
padrões estão em [Uso](usage.md#uso-basico).
