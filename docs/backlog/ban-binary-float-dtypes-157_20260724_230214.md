# Work ledger — #157 banir float binário em valores ingeridos + gate `check_dtypes`

Branch `fix/157-banir-float-binario-gate-check-dtypes`. Fecha **#157**. **Com release** (`fix`, há
diff em `src/`) → PATCH.

## O que a issue pedia, e o que o grounding mudou

A issue afirmava que o boundary JSON era **inexistente** ("blindagem para a primeira fonte JSON").
**Não é.** `_read_raw` já tinha um ramo `.json` vivo:

```python
df_json = pd.read_json(path_file)
return df_json.astype(str_dtype) if str_dtype is not None else df_json
```

Como `read_table` sempre passa `str_dtype="str"`, CSV e Excel são de fato **text-first** e estavam
seguros. O ramo JSON **não estava**: o parser do pandas infere um tipo por coluna **antes** de
qualquer dtype declarado, e o `astype("str")` seguinte apenas **preserva fielmente o estrago**.

Ou seja: era um caminho **lossy de verdade**, não uma hipótese. Corrigido de raiz, não blindado.

## O bug era maior que float

O controle negativo (reverter o fix e exigir que os testes novos falhem) revelou que o
`pd.read_json` corrompia **duas** coisas, não uma:

| entrada JSON | `pd.read_json` (antes) | `json.loads(parse_float=Decimal)` (agora) |
|---|---|---|
| `"code": "007"` | `7` → `"7"` | `"007"` |
| `"amount": 1984223115.42` | float → `"1984223115.4200001"` | `"1984223115.42"` |

O zero-padding é **exatamente** o exemplo que o docstring do próprio módulo usa para explicar por que
o seam nunca confia na inferência do pandas (`"007" vira 7, irrecuperável por um astype posterior`).
O ramo JSON violava o contrato declarado do próprio arquivo.

## O gate se pagou na primeira execução (2ª vez na família `filings-*`)

Rodado contra o `main`, o `bin/check_dtypes.py` acusou **1 violação** — o docstring do próprio
`apply_dtypes`:

```
src/filings_cvm/_internal/utils/dtypes.py:59: ``"int64"``, ``"float64"``). A ``"str"`` declaration…
```

É o **pior lugar possível**, e o mesmo achado do `filings-b3` (lá foi o exemplo de docstring de uma
classe base): todo reader novo nasce copiando um existente, então um exemplo errado no seam
compartilhado ensina o padrão errado para o portal inteiro. Removido.

## Feito

- [x] **`_to_decimal`** (`_internal/utils/dtypes.py`) — texto/`int`/`Decimal` entram; **`float` é
  RECUSADO, não convertido** (converter lavaria um valor já perdido num tipo que anuncia exatidão).
  `NaN` é reconhecido como **ausente antes** da recusa (NaN é float e é o marcador de ausente do
  pandas) — senão toda célula vazia levantaria.
- [x] **`list_decimal_cols`** em `apply_dtypes`, entrando na validação de disjunção (agora **4**
  conjuntos, não 3) e na checagem de colunas ausentes.
- [x] **Propagado** por `read_table`, `read_query` e `_finalize` — arquivo e DB não podem divergir.
- [x] **Boundary JSON corrigido de raiz**: `json.loads(..., parse_float=Decimal)` + `pd.DataFrame`,
  no lugar de `pd.read_json`. Encoding passa a honrar `str_encoding` (BOM), documentado.
- [x] **`bin/check_dtypes.py`** — gate textual no padrão de `check_typing.py`/`check_provenance.py`.
  Ruff **não** dá conta: `banned-api` casa import e acesso a atributo, não um literal `"float64"`
  dentro de um dict. Escape hatch `# dtype-ok: <razão>` com motivo obrigatório.
- [x] **Gate parity**: registrado em `.pre-commit-config.yaml` (`check-dtypes`) **E** em
  `.github/workflows/tests.yaml` (step `Run Binary-Float Dtype Ban`) — hook sozinho é burlado por
  `--no-verify`, e a branch protection roda o *workflow*.
- [x] Docstrings do módulo/`apply_dtypes`/`read_table`/`read_query` apontam `list_decimal_cols` e o
  gate; o exemplo `"float64"` saiu.

## Verificação

- [x] **Gate por MUTAÇÃO, não só caminho feliz** (critério de aceite explícito da issue):
  - contra o `main` → **1 violação** (o docstring), provando que não é gate vazio;
  - float deliberado em `src/` → **EXIT=1**;
  - a mesma linha com `# dtype-ok: <razão>` → **EXIT=0**;
  - `src/` como entregue → **EXIT=0**.
- [x] **Controle negativo dos testes de JSON**: revertido o ramo para `pd.read_json`, **os 2 testes
  novos falham**; restaurado, passam. Não são tautologia.
- [x] ⚠️ **Um teste meu passou no código quebrado e foi corrigido**: `Decimal("10.5") ==
  Decimal("10.50")` é **`True`** — a igualdade de `Decimal` compara valor numérico e **ignora a
  escala**. Asserção de escala trocada para `str(...)`. É a mesma armadilha do `pytest.approx`, um
  nível abaixo: a igualdade exata não bastava, precisava ser exata **na representação**.
- [x] Igualdade **exata** nos testes de decimal (`==` contra `Decimal("…")`, nunca `pytest.approx`),
  incluindo a asserção de que `value != Decimal(1984223115.42)` — o round-trip binário que o seam
  existe para excluir.
- [x] `ruff check` + `ruff format --check` limpos; `mypy` **347** arquivos OK; `check_typing`,
  `check_provenance`, `check_dtypes` OK; **1850 unit** (era 1828, +22).
- [x] ⚠️ **`ruff format bin/` reformatou 4 scripts pré-existentes** (`check_docstrings`,
  `check_backlog_ledger`, `check_typing`, `check_provenance` — ~1560 linhas de churn). É a **dívida
  conhecida de `bin/`** registrada no checkpoint, **não** desta issue → revertidos, commit atômico.
  Segue valendo um PR de chore separado.
- [x] 2 falsos-positivos de lint resolvidos **sem suprimir**: `S105` (o nome `_ALLOW_TOKEN` lido como
  credencial → renomeado `_ALLOW_MARKER`) e `ERA001` (`"reader: it infers…"` lido como anotação de
  variável → comentário reescrito).

## Aberto / próximo

- [ ] PR (`Closes #157`) → aprovação → merge → **release PATCH**.
- [ ] Nenhum reader usa `list_decimal_cols` hoje — a convenção do repo é devolver monetários como
  **texto decimal exato** (`str`), e isso continua correto e lossless. O novo seam é para quando um
  reader precisar do `Decimal` tipado, e o gate é o que impede o atalho `float64` nesse dia.
- [ ] Retomar a sweep do #41 (Wave 4): os 7 datasets `CIA_ABERTA/DOC` + `EVENTOS`, um PR por dataset
  — agora protegidos pelo gate.
