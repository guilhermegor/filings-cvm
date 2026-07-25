# Work ledger — #164 CIA_ABERTA/DOC/VLMO readers (índice + conteúdo)

Branch `feat/164-vlmo-cia-aberta-readers`. Fecha **#164**. **Com release** (`feat`, diff em `src/`)
→ PATCH. **2ª das 7 fatias `DOC`** (`DOC` agora 2/7).

## Forma da fonte (medida, nada presumido)

⚠️ **Os 2 membros NÃO são registro+satélite** — são **índice + conteúdo**:

| membro | cols | linhas | o que é |
|---|---|---|---|
| `vlmo_cia_aberta_2025.csv` | 12 | 5.812 | índice de documentos (molde IPE + `Motivo_Reapresentacao`) |
| `vlmo_cia_aberta_con_2025.csv` | 17 | 63.056 | movimentações de valores mobiliários |

Base privada `_base_vlmo_reader.py` (molde: `_base_inf_mensal_fii_reader` — ZIP anual multi-membro
com `_MEMBER_STEM`). Contracts **gerados dos headers** e pinados a fixtures verbatim.

## ⚠️ O achado principal: as primeiras colunas monetárias do root `cia_aberta/`

`Preco_Unitario` e `Volume` chegam com **10 casas decimais**; `Quantidade` é inteiro. O META
declara `decimal`/`decimal`/`bigint`. **Ficam texto exato.**

**Provado por mutação, não afirmado:** tipando `Volume` como `float64`,
`61961072.9999543100` → `np.float64(61961072.99995431)` — **os 2 últimos dígitos somem em
silêncio**. E **duas defesas independentes dispararam na mesma mutação**:

1. o teste de valor falhou;
2. **`bin/check_dtypes.py` (o gate do #157) acusou o literal `"float64"` → EXIT=1**.

Ou seja: o trabalho do #157, feito duas fatias atrás, **pegou seu primeiro caso real aqui**. Os
dígitos `…99995` são resíduo de aritmética float **na própria CVM** — devolvê-los como publicados é
fidelidade; re-arredondar seria inventar dado.

## Outros achados

- ⚠️ **`Data_Movimentacao` chega ~58% VAZIA** (26.328 de 63.056). É data por contrato; **verificado
  no seam real antes de escrever** que branco vira `NaT` e o `errors="raise"` **não** levanta. O
  índice tem datas 100% preenchidas, então só o membro `con` exercita esse caminho — sem o teste,
  uma leitura real de qualquer ano quebraria.
- ⚠️ **SEM dado pessoal, contra a intuição.** "Informe de insider" sugere CPF; medindo, `Empresa` é a
  **companhia** (`Tipo_Empresa` ∈ Companhia/Controlada/Controladora) e `Tipo_Cargo` é **categoria de
  cargo**. **Zero** CPF/CNPJ dentro de `Empresa`. O indivíduo nunca é nomeado.
- `CNPJ_Companhia` **100% válido nos dois** — sem o placeholder `00.000.000/0000-00` do IPE.
- ⚠️ **META é `.zip` e o `.txt` dá 404 — o INVERSO do IPE** (cujo `.txt` é a única forma). 2 membros,
  `section` **assimétricas** (`meta_vlmo_cia_aberta` + `con`) porque o 1º membro é o stem puro →
  fallback documentado do `_section_of` (molde INTERMED/COORD_OFERTA). **Previsto do checkpoint
  ANTES de escrever**, confirmado no live-verify, pinado por teste.

## Feito

- [x] 2 readers + base privada + `MetaVlmoCiaAbertaReader` (**39º**).
- [x] Contracts gerados dos headers + 2 fixtures verbatim.
- [x] Registrado nas 5 camadas de `__init__` + `contracts/__init__` + `_META_MEMBERS` do drift
  (registry fecha: **186 readers, 39 Meta**). `_UNEXPOSED_CONTRACTS` **não** foi tocado — estes
  readers expõem `_CONTRACT` na classe (ao contrário do IPE, inline).
- [x] Docs: página nova + nav + `api.md` (seção + Meta 39) + `meta.md` (3 contagens + linha) +
  **`CLAUDE.md` raiz (catálogo + árvore + contagem META 38→39)** e `test_meta_readers.py` 38→39.
- [x] 16 testes novos.

## Verificação

- [x] **Oráculo anti-tautologia por mutação**: renomear `Preco_Unitario` no contract → falha;
  restaurado → passa.
- [x] **Teste monetário por mutação**: tipar `Volume` como `float64` → o teste falha **e** o
  `check_dtypes` acusa. Sem essa mutação o teste seria só mais uma tautologia verde.
- [x] Asserção monetária feita sobre a **string**, não sobre número: `float()` compara igual a várias
  strings decimais diferentes, então só o texto prova que nada se perdeu. `Decimal(str)` round-trip
  também pinado.
- [x] Anti-cópia índice×conteúdo pinada (conjuntos de colunas disjuntos nos pontos que importam).
- [x] ⚠️ **Um erro meu pego por olhar os números**: as âncoras de `str.replace` casaram só os blocos
  de **import**, não os `__all__` (que são strings com aspas) — os 3 readers ficaram **importáveis
  mas NÃO exportados**, e as contagens não subiram (189/183/4/2 iguais). Corrigido; agora **192
  nomes públicos, 39 Meta**. *Conferir a contagem depois de registrar, não só rodar os testes* — os
  testes do reader passariam mesmo sem export.
- [x] `check_dtypes` limpo; ruff/format; mypy; suíte completa; mkdocs --strict; codespell.

## Aberto / próximo

- [ ] PR (`Closes #164`) → aprovação → merge → **release PATCH**.
- [ ] `DOC` restante (5): **FCA** (10 membros, o próximo salto de forma) → CGVN → FRE → DFP → ITR,
  depois `EVENTOS/RECOMPRA_ACOES`. **Conferir a URL da META de cada um no portal** — já vimos 4
  grafias, e IPE×VLMO provam que datasets vizinhos se contradizem.
