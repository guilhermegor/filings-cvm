# **Registro de Fundos, Classes e Subclasses (RCVM 175) — leitura**

Leitura (← CVM) do cadastro pós-**Resolução CVM 175** (`registro_fundo_classe.zip`), publicado no
[portal de dados abertos da CVM](https://dados.cvm.gov.br/dados/FI/CAD/DADOS/).

> **Veja também:** [Referência da API](../api.md) para cada símbolo público · [Uso](../usage.md)
> para instalação e o conceito geral.

---

## Descrição

O arquivo `registro_fundo_classe.zip` traz **três membros** em **três granularidades**, numa
hierarquia `fundo → classe → subclasse`. Cada nível tem o seu leitor:

| Leitor | Membro | Grão | Chave |
|--------|--------|------|-------|
| `RegistroFundoReader` | `registro_fundo.csv` (21 col.) | fundo | `ID_Registro_Fundo` |
| `RegistroClasseReader` | `registro_classe.csv` (30 col.) | classe | `ID_Registro_Classe` (FK `ID_Registro_Fundo`) |
| `RegistroSubclasseReader` | `registro_subclasse.csv` (14 col.) | subclasse | `ID_Subclasse` (FK `ID_Registro_Classe`) |

As chaves substitutas ligam os níveis e resolvem **100%** no arquivo real. Os três leitores
baixam o **mesmo** ZIP, então um `path_raw` gravado por qualquer um serve aos outros.

### Por que este, e não `cad_fi.csv`

É aqui que estão os fundos **vivos**. No mesmo dia, `registro_fundo.csv` tinha **34 mil** fundos
`Em Funcionamento Normal`, contra 22 no `cad_fi.csv` legado (~99,5% cancelado). Use o
[`CadastroFiReader`](cadastro_fi.md) só para o cadastro histórico pré-175; use estes para o atual.

### Três leitores, **não** um `join`

A hierarquia é **um-para-muitos** (um fundo tem várias classes, uma classe várias subclasses),
então juntar tudo num único frame **multiplicaria** as linhas do fundo — a mesma armadilha de
mistura de grãos que o [CDA](cda.md) documenta. Faça o `join` você mesmo, nas chaves substitutas,
no grão que precisar:

```python
from filings_cvm.ingestion import RegistroFundoReader, RegistroClasseReader

fundos = RegistroFundoReader().read()
classes = RegistroClasseReader().read()

# fundo × classe, explicitamente, no grão que você escolhe:
fc = classes.merge(fundos, on="ID_Registro_Fundo", suffixes=("_classe", "_fundo"))
```

### Sem mês de referência, chave quase única

Como o CAD/FI, é um **retrato do estado atual** (URL fixa, sem partição `AAAAMM`), então os
leitores **não** aceitam `date_ref`, e a CVM sobrescreve o arquivo no lugar — grave `path_raw` para
guardar o retrato do dia. `ID_Registro_Fundo` é *quase* único (1.121 de ~89 mil linhas o repetem,
por re-registro entre regimes), então o leitor **não declara grão** e **não deduplica**; trate uma
colisão de chave como sendo da fonte, não do leitor.

### Tipagem

Toda coluna é texto (`str`) exceto as colunas `Data_*`, convertidas para `date` puro (vazios viram
`NaT`). `Patrimonio_Liquido` mantém o texto decimal exato da CVM — **nunca `float`**.
`CPF_CNPJ_Gestor` contém um **CPF** quando `Tipo_Pessoa_Gestor == "PF"`, por isso **não** é validado
como CNPJ. A subclasse **não tem coluna de CNPJ**. O mapa de tipos é derivado do contrato, então os
dois não podem divergir.

---

## Exemplos

### Listar os fundos em funcionamento

```python
from filings_cvm.ingestion import RegistroFundoReader

fundos = RegistroFundoReader().read()
ativos = fundos[fundos["Situacao"] == "Em Funcionamento Normal"]
```

### Persistir o retrato (camada *bronze*) uma vez para os três

```python
from datetime import date
from pathlib import Path

# Um download; o ZIP e os três CSVs ficam em disco para os outros leitores.
RegistroFundoReader(path_raw=Path(f"/data/bronze/cvm/registro/{date.today():%Y%m%d}")).read()
```

### Timeout

O padrão é `60 s` (o ZIP tem ~6,6 MB):

```python
RegistroClasseReader().read(int_timeout_s=120)
```

Cada `read` levanta `OSError` (falha de download), `ContractError` (CSV viola o contrato) ou
`ValueError` (o ZIP não contém o membro esperado) — falha cedo, sem devolver dados corrompidos.
