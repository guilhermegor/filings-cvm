# FRE CIA_ABERTA — fatia 3 de 4 (diversidade, 11 membros agregados) — #183

Branch: `feat/183-fre-readers-3-4-diversidade` · Issue: #183 · Fatias anteriores: #172/#179

**Primeira fatia depois do #91** — a superfície pública agora é o portal root.

## Feito

- [x] Grounding contra os bytes reais de 2025 — cols **e** linhas por membro, ragged, header-only,
      e classificação de **toda** coluna por valor.
- [x] 11 fixtures header-only verbatim + 11 contracts **gerados dos headers**.
- [x] 11 readers gerados por template sobre `_base_fre_reader.py` (zero infraestrutura nova).
- [x] Registro e **contagem conferida**: 227 readers (era 216), 26 FRE readers = 26 FRE contracts.
- [x] Testes: 126 no arquivo do FRE (era 73); suíte **2296** (+53).
- [x] Docs: `docs/ingestion/fre_cia_aberta.md`, `docs/api.md`, `CLAUDE.md`.

## Medições

Nenhum header-only, nenhum ragged, **11 headers distintos**. Todos com 1 col de data
(`Data_Referencia`, 100% ISO) e 1 de CNPJ (`CNPJ_Companhia`, 100% válido).

⚠️ **5 pares de mesma largura e listas diferentes** — o risco central desta fatia:
9 (`local` × `posicao` faixa etária) · 10 (`administrador_PCD` × `empregado_PCD`) ·
11 (`local` × `posicao` gênero) · 12 (`administrador_declaracao_genero` × `empregado_posicao_local`) ·
13 (`local` × `posicao` raça). `administrador_PCD` e `empregado_PCD` compartilham **8** das 10 (divergem em 2 cada).

⚠️ `administrador_PCD.Quantidade_*` chega ~1/5 **vazia** — declaração ausente, **não** zero.

## ⚠️ Duas armadilhas de MÉTODO nesta fatia

**1. O scan por valor produz falso-positivo de CNPJ/CPF em coluna numérica.** A lição emendada no
#179 manda classificar **toda** coluna por valor, e foi o que fiz — mas o resultado acusou
`Quantidade_Branco: CNPJ=8/3117` e `ID_Documento: CNPJ=50/3495`. **Não é achado, é ruído:**
`unmask_cnpj` faz **zero-pad à esquerda** (a CVM publica CNPJ sem zeros), então `'157767'` vira
`'00000000157767'` e passa nos dígitos verificadores por coincidência (~1/70). É comportamento
**deliberado e documentado**, não bug — não abri issue.
→ **A regra correta é ler a TAXA, não a presença:** `CNPJ_Companhia` dá **100%**, as colunas de
contagem dão ~0,1–1,4%. Só a primeira é coluna de CNPJ.

**2. `cia_aberta` precisa de TRÊS `__init__`, não dois.** O `CLAUDE.md` que **eu** escrevi no #91
dizia "exatamente DOIS" — errado para um root aninhado: aqui a cadeia é `doc/fre/` → `doc/` →
`cia_aberta/`. O `ImportError` apareceu na hora; **a guidance estava errada, não o código**, e foi
corrigida no mesmo commit. Também acrescentei que o contract precisa entrar em
`contracts/__init__.py` — eu tinha esquecido, e **nada falhou**: o reader importa o contract do
módulo direto, então só a **contagem exportada** (15 em vez de 26) denunciou.

## Controles negativos (2 mutações, ambas vermelhas)

- [x] **Dar ao `empregado_posicao_faixa_etaria` a coluna de agrupamento do irmão `local`** → 3
      testes falham (header pinado + os 2 anti-cópia). É exatamente o erro que os 5 pares convidam.
- [x] **Declarar uma `Quantidade_*` como coluna de CNPJ** (o erro de classificar pelo nome) → 7
      testes falham, incluindo `ContractError` em runtime.

## Aberto / próximo

- [ ] **Release PATCH 0.26.1** (`feat`, pós-0.26.0 — `src/` muda).
- [ ] **Fatia 4 de 4** — remuneração + valores mobiliários + transações (10 membros) → fecha o FRE.
- [ ] Depois: **DFP** (12,12 MiB) e **ITR** (30,14) e `EVENTOS/RECOMPRA_ACOES`.
