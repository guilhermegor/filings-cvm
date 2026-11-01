# Work ledger — #159 CIA_ABERTA/DOC/IPE reader (índice de documentos)

Branch `feat/159-ipe-cia-aberta-reader`. Fecha **#159**. **Com release** (`feat`, há diff em
`src/`) → PATCH. **Sétima fatia da Wave 4 do #41; abre o sub-root `CIA_ABERTA/DOC`.**

## Por que o IPE primeiro

Survey do `CIA_ABERTA/DOC` (medido, não presumido): os 7 datasets são **todos ZIP anual**
(`<ds>_cia_aberta_AAAA.zip`), mas o número de membros varia muito. Ordenado pelo custo:

| dataset | zip 2025 | membros |
|---|---|---|
| **IPE** | 2,16 MiB | **1** ← esta fatia |
| VLMO | 0,78 MiB | 2 |
| FCA | 0,37 MiB | 10 |
| CGVN | 4,01 MiB | ? |
| FRE | 8,10 MiB | ? |
| DFP | 12,12 MiB | ? |
| ITR | 30,14 MiB | ? |

IPE é o mais barato (1 membro) e o de semântica mais simples — índice de documentos, molde já
existente no repo.

## Molde

Dois readers existentes combinados, nenhum código novo de infraestrutura:

- **`DfinFiiReader`** — semântica de **índice de documentos** (`Link_Download` devolvido como texto
  e não seguido) e, por coincidência confirmada, **exatamente o mesmo par de date cols**
  (`Data_Referencia` + `Data_Entrega`).
- **`BalanceteFieReader`** — extração de **ZIP de 1 membro** (`extract_all` + `find_member` por
  nome exato).

## Grounding (medido contra os bytes reais de 2025 — nada presumido)

- **13 colunas**, ~49,3k linhas. Contract **gerado do header** e **pinado** a
  `tests/fixtures/ipe_cia_aberta/ipe_cia_aberta_header.csv` (bytes verbatim, ISO-8859-1).
- **2 date cols**, ambas **100% ISO** `AAAA-MM-DD` — e o META as declara `date` (dois oráculos
  concordando).
- ⚠️ **`CNPJ_Companhia` tem 44 placeholders `00.000.000/0000-00`** (emissores estrangeiros sem CNPJ
  brasileiro, ex. JBS Foods International DAC) + **49.233 válidos**, **zero malformados**.
  Devolvidos **como publicados**. `tuple_cnpj_cols=("CNPJ_Companhia",)` é seguro — **provado** com
  `find_file_problems`: só-placeholders → `ContractError`, misto → válido. A aresta está **pinada
  por teste** (mesma classe da lição `value-presence-contract-tolerates-empty-artifact` do CRI).
- `Codigo_CVM` (`Domínio: Numérico`) e `Versao` (`smallint`) no META ficam **`str`** —
  identificadores, não quantidades (precedente `DfinFiiReader`).
- `Tipo` (41.190), `Especie` (17.334), `Assunto` (32.777), `Protocolo_Entrega` (48.370) chegam
  **parcialmente preenchidos** — colunas obrigatórias, valores não.
- **META** = `.txt` solto, 13 campos, seção única, ISO-8859-1 + CRLF, **ordem alfabética** (≠ ordem
  do arquivo → o header real segue sendo a fonte da ordem).

## ⚠️ Achado que vale para as 6 fatias seguintes: 4 grafias de META em 7 datasets

| dataset | META |
|---|---|
| CGVN / FRE / VLMO | `meta_<ds>_cia_aberta.zip` |
| DFP / ITR | `meta_<ds>_cia_aberta_txt.zip` (**infixo `_txt`**) |
| **FCA** | **`fca_cia_aberta.zip`** (**sem o prefixo `meta_`**) |
| **IPE** | **`meta_ipe_cia_aberta.txt`** (**`.txt` solto**) |

Uma regra "derive o nome da META a partir do dataset" erraria em **3 dos 7** — 404 ou a
especificação do dataset errado, **com os testes verdes**. Confirma a regra padrão do repo: a URL é
constante por dataset, **jamais derivada**. Pinado por teste (`test_meta_url_is_the_loose_txt...`).

## Feito

- [x] `IpeCiaAbertaReader` (`ingestion/cia_aberta/doc/ipe/ipe.py`) + `MetaIpeCiaAbertaReader`
  (**38º**), pasta por dataset (`ipe/{ipe.py,meta.py,__init__.py}`) conforme a convenção.
- [x] Contract `ipe_cia_aberta.py` **gerado do header** (script, não transcrição) + fixture verbatim.
- [x] `META_IPE_CIA_ABERTA` em `contracts/meta.py` (factory compartilhado).
- [x] Registrado nas 4 camadas de `__init__` + `contracts/__init__`; **`__all__` reordenado**
  (a inserção ingênua quebrou a ordem alfabética — corrigido e verificado, `sorted == True`).
- [x] Drift registry (`bin/check_contract_drift.py`): import + `_UNEXPOSED_CONTRACTS` (o reader
  guarda o contract inline, como o `DfinFiiReader`) + `_META_MEMBERS`. Fecha: 183 readers, 38 Meta.
- [x] Docs: página nova `docs/ingestion/ipe_cia_aberta.md`, nav, `docs/api.md` (seção nova + o aviso
  do CAD corrigido), `docs/ingestion/meta.md` (**as 3 contagens 37→38 + linha na tabela**),
  `CLAUDE.md` raiz (catálogo + árvore de layout).
- [x] `tests/unit/test_meta_readers.py`: total 37 → 38.
- [x] 12 testes novos em `test_ipe_cia_aberta_ingestion.py`.

## Verificação

- [x] **Oráculo anti-tautologia provado por MUTAÇÃO** (não só caminho feliz): com uma coluna
  **removida** do contract → falha; com `Especie` → `Espécie` (erro de transcrição realista, com
  acento) → falha; restaurado → passa. É a única asserção do arquivo cujo valor esperado não fomos
  nós que escrevemos.
- [x] **Semântica "ao menos um CNPJ válido" provada** com `find_file_problems` antes de escrever o
  docstring que a afirma — só-placeholders levanta, misto passa.
- [x] `Link_Download` **não seguido**: a lista de URLs capturadas contém **apenas** o ZIP, e a
  asserção verifica explicitamente que nada de `rad.cvm.gov.br` foi requisitado.
- [x] URL **anual**: dois `date_ref` diferentes do mesmo ano resolvem para o mesmo artefato.
- [x] `QUOTE_NONE` conferido contra os bytes reais: **639 campos contêm `"` literal**, mas todos
  **no meio** do campo, então `QUOTE_NONE` e `QUOTE_MINIMAL` dão **valores idênticos** em 2025 (0
  linhas divergentes) e ambos 13 campos. Mantido `QUOTE_NONE` (convenção do repo + robusto a um
  `"` inicial futuro) — **sem alegar que 2025 o provou necessário**.
- [x] ruff check + format limpos, `mypy` **352** arquivos OK, `check_typing`/`check_provenance`/
  `check_dtypes`/`check_docstrings` OK, **1870 unit** (era 1850, +20), 4 integration, codespell
  limpo, `mkdocs build --strict` limpo, `check_backlog_ledger` OK.
- [x] ⚠️ **`ruff check --fix` foi necessário para 4 blocos de import** — a inserção por âncora
  (`str.replace`) coloca o import no lugar do texto ancorado, não na posição alfabética, então o
  `I001` disparou nos 4 arquivos de registro. Corrigido com `--fix` **escopado aos 4 arquivos** e
  conferido por `--numstat`: **só inserções, zero deleções** → nenhum churn em código alheio.
- [x] ⚠️ **2 quebras minhas pegas pelos gates, não pelo olho:** (a) linkei
  `../architecture.md`, **que não existe** neste repo (presumi o nome) → `mkdocs --strict` abortou;
  apontado para `../api.md`, que documenta as colunas de proveniência. (b) codespell pegou o pt-BR
  `longe` → reescrito (mais claro assim), sem crescer a lista de ignore.

## Aberto / próximo

- [ ] PR (`Closes #159`) → aprovação → merge → **release PATCH**.
- [ ] As 6 fatias restantes do `DOC` (VLMO 2 membros → FCA 10 → CGVN → FRE → DFP → ITR) e o
  `EVENTOS/RECOMPRA_ACOES`. **Grounding próprio para cada** — a tabela de membros acima já mostra
  que a forma não se repete; e a META de cada um tem de ser **verificada, nunca derivada**.
