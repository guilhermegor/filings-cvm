# Work ledger — #97 public META download module

Branch `feat/ingestion-meta-download-97`. Expõe um **módulo público** que baixa os **META**
(a spec que a própria CVM publica) de cada dataset do open data, para o datalake do bedrock-fm e
para o loop do sniffer. `feat` em `src/` → **release PATCH** depois do merge.

Este arquivo é o **spec + ledger** desta branch (design validado com o usuário em 2026-07-15).

## Por que — o META é o único oráculo NÃO-tautológico

Contract, reader, fixture e teste codificam **a nossa crença**, então só podem concordar entre si:
um contract errado passa em 100% dos testes. O #96 (CRA) provou na prática — copiar os contracts do
OTS teria embarcado 8 errados com tudo verde. O META é a versão **declarada pela CVM** desse oráculo.

## Achados na fonte real (2026-07-15) — mudaram o design

Levantados contra os bytes reais do portal, não por suposição:

- [x] **A CVM TRUNCA o nome do campo em exatamente 50 caracteres no META — provado, 8/8.**
  Maior nome no META = 50; maior no header real = 60. Todo nome real > 50 aparece no META cortado em
  `[:50]` (`Pagamentos_Classe_Subordinada_Mezanino_Amortizacao_Principal` (60) →
  `…_Amortizacao` (50)). **Consequência: o META NÃO pode ser gate duro de nomes** — 8 campos do CRA
  dariam falso-positivo de drift.
- [x] **A ordem do META NUNCA bate com o header real — 0/8 seções** (não é só o `FIE/MEDIDAS`).
  `meta_cad_fi.txt` começa `ADMIN, AUDITOR, CD_CVM` = **alfabético**. O **header do artefato real
  continua sendo a fonte da ordem** (e dos nomes longos).
- [x] **O nome do arquivo META não é derivável por regra**: `meta_inf_mensal_cri.zip`, mas
  `meta_cda_fi_txt.zip` / `meta_lamina_fi_txt.zip` / `meta_inf_mensal_fidc_txt.zip` (infixo `_txt`);
  `FIE/MEDIDAS` publica `.csv` **e** `.txt`.
- [x] **ARMADILHA — `meta_cad_fi.txt` e `meta_cad_fi.zip` são datasets DIFERENTES** com o mesmo
  radical: o `.txt` (41 campos) é o `cad_fi.csv`; o `.zip` (19 membros) é o `cad_fi_**hist**`. Uma
  regra "prefira .zip" entregaria silenciosamente o metadado do *hist* para quem pediu `cad_fi`.
  **É exatamente o modo de falha do #96.** → mata a ideia de URL derivada/descoberta automática.
- [x] **21/21 datasets publicam META** (nenhum degrada hoje). `meta_inf_mensal_cri.zip` tem
  **11 membros**, confirmando a contagem do CRI.
- [x] **Formato**: texto em blocos (`Campo:` / `Descrição` / `Domínio` / `Tipo Dados` /
  `Tamanho`|`Precisão`+`Scale`), **ISO-8859-1**, CRLF — **não é CSV**. 12 são `.txt` soltos, 9 são
  `.zip` multi-membro.

**Reenquadramento:** o META não é uma "segunda fonte de nomes de coluna" — é a **semântica declarada
pela CVM** (descrição, tipo, tamanho, domínio), com um canal de nome **lossy**. É isso que o header
real *não* carrega.

## Decisões de design (validadas com o usuário)

- [x] **Job do módulo**: baixar **raw + parsear** (os dois). Raw sempre persistível via `path_raw`
  (bronze, fiel); DataFrame parseado como conveniência para comparar contra os contracts.
- [x] **Uma classe por dataset** (não um seam genérico), com **base privada** para o que repete —
  o padrão que o repo já usa (`_base_inf_mensal_cra_reader.py` + subclasses finas). Consequência
  boa: a classe por dataset **dissolve o problema da descoberta** — o nome irregular vira uma
  constante `_META_URL`, como o `_BASE_URL` de todo reader hoje. Sem scraping de autoindex, sem
  registry.
- [x] **Layout — dataset é SEMPRE uma pasta, com um `meta.py` dentro** (escolha do usuário):
  espelha o portal (a CVM tem um dir por dataset: `SECURIT/DOC/DFIN_CRA/META/`) e põe o META ao lado
  dos readers que ele explica. Exige **promover os 12 datasets que hoje são módulo soltos** a
  pacotes (`dfin_cra.py` → `dfin_cra/{dfin_cra.py,meta.py}`). Precedente: `lamina/lamina.py`; e o #44
  já fez esse tipo de move mecânico (28 `git mv`), com a API pública **plana via re-export**.
- [x] **Saída**: **UM DataFrame longo com coluna `secao`** — mesma forma para `.txt` solto e `.zip`
  multi-membro (`secao | campo | descricao | dominio | tipo_dados | tamanho | precisao | scale` +
  as 6 colunas de proveniência). Um `.txt` solto é só `secao=<dataset>`. Respeita o port
  (`read() -> DataFrame`) e cai direto num load de warehouse.
- [x] **Sem `date_ref`**: o META fica numa **URL fixa** e a CVM sobrescreve no lugar — precedente
  `CadastroFiReader` / `CadastroEmissorCepacReader`. Logo `__init__(path_raw, retry_policy,
  cls_logger)`, e um `path_raw` persistido é o **único** registro do que a spec dizia naquele dia.
- [x] **Base privada em `ingestion/_base_meta_reader.py`** (raiz de `ingestion/`): as bases
  existentes são escopadas ao seu pacote, mas esta é compartilhada pelas 23 subclasses de todos os
  portal roots.
- [x] **Contracts**: **um módulo** `_internal/config/contracts/meta.py` com as 23 instâncias vindas
  de um factory sobre a tupla compartilhada. A forma do frame parseado é **nossa** e idêntica nos 23;
  o que difere é o `str_source_key` (que o `stamp_provenance` exige para desambiguar no bronze).
  Precedente: `cad_fi_hist.py` (19 contracts num módulo só).
- [x] **PR shape**: **um PR, dois commits** (1º os moves puros, 2º o META). A promoção só existe
  para servir o layout do #97 — separada, seria um refactor sem motivação, e deixaria a árvore
  meio-aninhada entre ciclos.

## Regra de ouro deste módulo

**Devolver o que a CVM publicou, verbatim — inclusive o nome truncado em 50.** "Consertar" o nome
fabricaria um dado que a CVM nunca escreveu e destruiria o valor de oráculo. Reconciliar META↔header
é trabalho do **consumidor** (#98), e tem de ser **truncation-aware** (`real[:50] == meta`).

## Escopo

- [ ] Promover os 12 datasets módulo-soltos a pacotes (`git mv`), API pública plana via re-export
- [ ] `ingestion/_base_meta_reader.py` — base privada com toda a máquina: `raw_workspace` →
      `download_file` → `hash_artifact` → parser de blocos (`.txt` ou `.zip` pelo sufixo da URL) →
      `stamp_provenance`
- [ ] 23 `meta.py` finos (só `_META_URL` + `_SOURCE_KEY` + docstring), um por dataset
- [ ] `_internal/config/contracts/meta.py` — 23 contracts via factory
- [ ] Re-export na API pública (`ingestion/__init__` + `filings_cvm/__init__`, `__all__`)
- [ ] Testes: parser contra **fixtures de bytes reais** da CVM; `download_file` mockado; um teste
      trava a **truncagem em 50 preservada verbatim** (o único oráculo não-tautológico)
- [ ] Gates: ruff/format/check_typing/check_provenance/mypy/codespell + pytest nas **duas majors do
      pandas** + mkdocs --strict
- [ ] Docs: página + nav do mkdocs + api.md + índice de ingestion + catálogo do CLAUDE.md raiz
- [ ] PR (`Closes #97`) → **esperar aprovação+merge do usuário** → release **PATCH** (Test PyPI →
      verificar por install → PyPI → verificar)

## Decidido no self-review do spec (eram ambiguidades — resolvidas, sujeitas à revisão do usuário)

- [x] **Colunas do frame parseado em INGLÊS**: `section | field | description | domain | data_type |
      size | precision | scale`. Motivo: a fronteira de língua aqui é **de quem é o dado**, não de
      quem lê. Os readers preservam o nome de coluna **da CVM** verbatim (`Provisoes_Contigencias`)
      porque a coluna é *dela*; este frame é uma **construção nossa** (a CVM não publica tabela
      nenhuma), como as 6 colunas de proveniência — que já são inglês (`url`, `updated_at`,
      `source_key`). Os **valores** seguem verbatim da CVM (`field="Provisoes_Contigencias"`,
      `description` em pt-BR como ela escreveu).
- [x] **`FIE/MEDIDAS` → usar o `.txt`**, o formato que os 23 têm em comum (o `.csv` é exceção de 1
      dataset; uma segunda regra de formato para um caso só é a troca ruim). O `.csv` fica
      registrado aqui como conscientemente não usado.
- [x] **`_SOURCE_KEY` com prefixo `meta_`** (`meta_inf_mensal_cri`): sem prefixo colidiria com o
      `source_key` do reader do mesmo dataset, e o `source_key` existe justamente para desambiguar
      linhas de datasets diferentes que caem na mesma tabela do bronze.

## Release

`feat` em `src/` → **PATCH**. Próxima versão = acima do **máximo das DUAS índices** (PyPI 0.25.4,
Test PyPI 0.25.4) → provável **0.25.5**. ⚠️ Este release é a **primeira prova real do fix do #102**:
o job `Create GitHub Release` tem de ficar verde e a tag `v0.25.5` tem de aparecer **sozinha**, sem
`gh release edit --draft=false` na mão.

Relacionado: #45 (META como artefato trackeado), #46 (contracts META-first), #98 (job de drift),
#41 (sweep), #108 (gate do ledger).
