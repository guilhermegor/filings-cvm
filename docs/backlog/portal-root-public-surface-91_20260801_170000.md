# Portal-root packages são a superfície pública (slim top-level `__all__`) — #91

Branch: `refactor/91-portal-root-packages-public-surface` · Issue: #91 · **BREAKING → 0.26.0**

## Decisão reconfirmada com o user (2026-08-01)

A issue registrava a versão **dura** e pedia para reconfirmar no início do PR. Perguntei; o user
escolheu a **dura**: os leitores saem de vez do topo, `from filings_cvm import XReader` levanta
`ImportError`.

⚠️ **O user acrescentou uma regra que a issue NÃO tinha:** *"submission should be imported from the
submission folder, not from filings_cvm"*. A issue previa manter os 4 nomes de submission no topo.
Com isso a regra ficou **simétrica** e muito mais fácil de enunciar: **cada seção é dona dos seus
nomes**, e o topo guarda só o que não pertence a nenhuma (`RetryPolicy`, `__version__`).

| o que | importa de |
|---|---|
| leitor | `filings_cvm.ingestion.<portal_root>` (22 roots) |
| serializador | `filings_cvm.submission` |
| `RetryPolicy` | `filings_cvm` |

## Feito

- [x] **Provei a precondição ANTES de apagar:** os 216 leitores do `__all__` plano são exatamente
      os 216 alcançáveis pelos 22 roots — bijeção, zero órfão, zero nome em 2 roots.
- [x] `filings_cvm/__init__.py` → só `RetryPolicy` + `__version__` (de 222 nomes para 2).
- [x] `filings_cvm/ingestion/__init__.py` → exporta os **22 root packages**, não os leitores.
- [x] Migração mecânica dos imports por script (ast para `.py`, linha a linha para `.md`):
      **23 arquivos de teste + 43 de docs/README**.
- [x] `_internal/utils/introspection.py` — `iter_public_readers()` / `iter_root_packages()`.
- [x] 4 seams de descoberta religados a ele (3 testes + `bin/check_contract_drift.py`).
- [x] `tests/unit/test_public_surface.py` — 17 testes, pinando nas **2 direções**.
- [x] Docs: `api.md`, `ingestion/index.md`, `CLAUDE.md` (Layout + Public vs private), README.
- [x] Gates: ruff, mypy **398**, 4 check_*, **2199 unit** (+17), 4 integration, codespell,
      mkdocs --strict.

## ⚠️ O erro que quase passou: a cobertura caiu 40% e a suíte continuou verde

Depois de remover o `__all__` plano, a suíte passou de **2182** para **1311** testes — **sem uma
única falha nova de coleção**. Causa: 4 gates descobriam os leitores varrendo o `__all__` plano
(`test_reader_retry_policy`, `test_meta_readers` ×3 sites, `test_check_contract_drift`,
`bin/check_contract_drift.py`). Com o namespace vazio, a varredura devolvia **zero** e os testes
parametrizados **colapsaram para nenhum caso** — verde, inerte e silencioso.

**Só foi visto porque conferi a CONTAGEM, não o resultado.** É exatamente a lição
`docs-that-enumerate-code-need-a-gate` ("um gate que pode casar zero em silêncio é pior que gate
nenhum") aparecendo do lado do *código*. Por isso `iter_public_readers()` **levanta** em vez de
devolver vazio, e `test_reader_retry_policy` agora afirma `len(roots) == 22` e `len(readers) > 200`.

## Controles negativos (2 mutações, ambas vermelhas antes do fix)

- [x] **Deixar 1 leitor reexportado no topo** (refactor pela metade) → falham 2 testes, nas 2
      direções. Sem isso, um leitor esquecido no topo não quebraria nada.
- [x] **Tirar 1 root do `ingestion.__all__`** → falham 3 testes, incluindo o guard de contagem do
      retry-policy. É a mutação que reproduz o colapso silencioso acima.

## Aberto / próximo

- [ ] **Release 0.26.0** (MINOR em 0.x = breaking) com a nota de migração — o `BREAKING CHANGE:`
      no corpo do commit é o que o `cz changelog` publica.
- [ ] Fatias **3/4** (diversidade, 11 membros) e **4/4** (remuneração, 10) do FRE.
- [ ] Bônus já valendo: um leitor novo passa a tocar **2** `__init__` (o do dataset e o do root),
      não 4 — menos colisão entre PRs de leitor.

## Fora de escopo (dívida pré-existente, deliberadamente não tocada)

4 scripts em `bin/` (`check_backlog_ledger`, `check_docstrings`, `check_provenance`,
`check_typing`) seguem fora do formato do ruff. É dívida conhecida e **não é deste PR** — formatar
a pasta inteira inflaria o diff com ~1560 linhas alheias. Só o arquivo tocado foi formatado.
