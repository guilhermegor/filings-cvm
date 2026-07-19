# **Completude do portal — detecção semanal, não-bloqueante**

Job agendado que enumera **todos os datasets publicados** em `dados.cvm.gov.br`, subtrai os que o
pacote já implementa, e **abre (ou atualiza) uma única issue de rastreio** com o que falta. Automatiza
o survey manual (#41) e espelha o [job de deriva de contrato](contract_drift.md): a divergência vira
**issue**, nunca um check vermelho. Roda `bin/check_portal_completeness.py` via
`.github/workflows/portal-completeness.yaml`.

> **Veja também:** [Deriva de contrato](contract_drift.md) (o job-irmão) · [Proveniência](index.md).

---

## Como funciona

1. **Enumera via CKAN, nunca raspando HTML.** O portal da CVM é um CKAN, então
   `/api/3/action/package_list` devolve o slug de **todo** dataset (54 hoje) — estável e legível por
   máquina.
2. **Calcula o gap:** `set(publicados) − set(implementados)`, ordenado.
3. **Abre/atualiza uma issue** (label `portal-completeness` + marcador oculto no corpo), listando os
   slugs que faltam. Só detecção — **sem geração de código**.

## Cobertura é declarada, nunca derivada

Os slugs que o pacote cobre moram em `_IMPLEMENTED_PACKAGES` (lista explícita), **não** inferidos dos
readers. Um slug CKAN não mapeia limpo para os nossos readers: `fi-cad` é **um** pacote mas **três**
famílias de reader (cadastro, registro, cad_fi_hist), e a granularidade do CKAN difere entre `*-cad`
(dois níveis) e `*-doc-*` (três). Derivar "implementado?" de nomes/URLs é a mesma armadilha que o job
de deriva evita (`cad_fi` vs `cad_fi_hist`). Ao implementar um dataset do portal, **adicione o seu
slug a `_IMPLEMENTED_PACKAGES`** — ele sai do gap. Um teste estrutural verifica que os slugs são
bem-formados.

## Só detecção — geração de reader fica de fora

Reportar um gap é barato e seguro pré-1.0; gerar um reader **não** é — um reader gerado mexe num
`FileContract` pinado ao header real, a superfície onde "testes verdes" não provam nada
([pin-contracts-to-a-source-published-oracle]), e o `pr_gate` **nunca** faz auto-merge de `src/`.
Geração por LLM + auto-PR é uma fase posterior, **revisada por humano, pós-≥1.0.0**, fora deste job.

## Não-bloqueante, de propósito

O script sempre sai `0`; um outage do portal é tolerado (logado, sem issue), então a CVM fora do ar
**nunca** abre uma issue espúria de "tudo faltando". Um crash inesperado avermelha o run, mas um run
agendado avermelhado não trava nada.
