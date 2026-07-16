# Public META Download Module — Implementation Plan (#97)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development
> (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use
> checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship a public, per-dataset module that downloads the CVM-published **META** (the declared
spec) for every implemented open-data dataset and returns it as a typed, provenance-stamped
DataFrame — the only non-tautological oracle the contracts have.

**Architecture:** Every dataset becomes a **folder** holding its readers plus a `meta.py`. Each
`meta.py` is a ~10-line `IngestionReader` subclass declaring only `_META_URL` + `_SOURCE_KEY`; all
machinery lives in the private base `ingestion/_base_meta_reader.py`, and the pure text→records
transform lives in `_internal/utils/meta_parser.py` (I/O at the edges, logic in the core).

**Tech Stack:** Python 3.10+ · pandas (2.x **and** 3.x) · stdlib `re`/`zipfile` · pytest ·
ruff/mypy · Poetry.

**Spec:** `docs/backlog/ingestion-meta-download-97_20260715_204524.md` (approved 2026-07-15).
**Branch:** `feat/ingestion-meta-download-97` (@ `3ac29bf`). **Issue:** #97.

## Global Constraints

- **Return what CVM published, verbatim.** META truncates field names at **exactly 50 chars**
  (proven 8/8). Never "repair" a truncated name — it would fabricate data CVM never wrote.
  Reconciling META↔header is the consumer's job (#98), truncation-aware (`real[:50] == meta`).
- **META is ISO-8859-1 with CRLF.** Normalise `\r\n` → `\n` **once**, at the parser entry, or every
  parsed value keeps a trailing `\r` (verified: without it the field is `"Data_Referencia\r"` and
  the 50-char truncation lock silently fails because names measure 51).
- **No `date_ref`** on any META class — META lives at a fixed URL and CVM overwrites it in place
  (precedent: `CadastroFiReader`, `CadastroEmissorCepacReader`).
- **Runtime type checking is mandatory**: every class under `src/` declares a checker metaclass
  (inherited — only the hierarchy root declares it); every standalone function gets `@type_checker`.
  Pydantic models and the typing engine are the only exclusions.
- **Ruff**: line-length 99, **tab** indent, double quotes, NumPy docstrings. `from __future__ import
  annotations` at the top of each module (matches every existing reader).
- **Every reader declares `_RETRY_POLICY`** — `tests/unit/test_reader_retry_policy.py` discovers
  readers from `ingestion.__all__` and fails CI if one forgets.
- **Naming**: `str_`/`int_`/`list_`/`dict_`/`df_`/`cls_`/`path_`/`bool_` prefixes, per the codebase.
- **Language**: code/CI/commits in **English**; published docs in **pt-BR** (the boundary is the
  audience). Parsed-frame **column names are English** (our construct); **values stay verbatim**
  pt-BR as CVM wrote them.
- **Tests never touch the network** (autouse socket guard in `tests/conftest.py`); mock
  `download_file` at the **reader module's own dotted path**.
- **No release for a `ci`/`docs` diff.** This PR is a `feat` in `src/` → **PATCH** → **0.25.5**.

## File Structure

**Created**
| Path | Responsibility |
|---|---|
| `src/filings_cvm/_internal/utils/meta_parser.py` | Pure `parse_meta_blocks(text, section)` — CVM block text → records. No I/O. |
| `src/filings_cvm/ingestion/_base_meta_reader.py` | Private base: download → hash → parse (`.txt` flat / `.zip` multi-member) → stamp. |
| `src/filings_cvm/_internal/config/contracts/meta.py` | `_meta_contract()` factory + the 22 `META_*` instances. |
| `src/filings_cvm/ingestion/**/<dataset>/meta.py` × 22 | Thin subclass: `_META_URL` + `_SOURCE_KEY` only. |
| `src/filings_cvm/ingestion/**/<dataset>/__init__.py` × 12 | Re-export for each promoted package. |
| `tests/unit/test_meta_parser.py` | Parser unit tests, pinned to real CVM fixtures. |
| `tests/unit/test_meta_readers.py` | Base + subclass tests (mocked download); introspective coverage test. |
| `tests/fixtures/meta/*.txt` | **Real CVM META bytes** (the oracle). No PII — META describes fields, carries no data rows. |
| `docs/ingestion/meta.md` | Published page (pt-BR). |

**Modified**: 8 test files (patch targets), `ingestion/__init__.py`, `filings_cvm/__init__.py`,
`_internal/config/contracts/__init__.py`, `mkdocs.yml`, `docs/api.md`, `docs/ingestion/index.md`,
root `CLAUDE.md`, the branch ledger.

---

### Task 1: Promote the 12 single-module datasets to packages

Pure move — **no behaviour change**. Precedent: `fi/doc/lamina/lamina.py` and #44's 28 `git mv`.
The public API stays flat because each new package's `__init__` re-exports the class, so **parent
`__init__` imports keep working unchanged**.

**Files — the 12 moves (exact):**

| From | To |
|---|---|
| `ingestion/fi/doc/informe_diario.py` | `ingestion/fi/doc/informe_diario/informe_diario.py` |
| `ingestion/fi/doc/cda.py` | `ingestion/fi/doc/cda/cda.py` |
| `ingestion/fi/cad/cadastro_fi.py` | `ingestion/fi/cad/cadastro_fi/cadastro_fi.py` |
| `ingestion/fii/doc/dfin.py` | `ingestion/fii/doc/dfin/dfin.py` |
| `ingestion/fip/doc/inf_trimestral.py` | `ingestion/fip/doc/inf_trimestral/inf_trimestral.py` |
| `ingestion/fip/doc/inf_quadrimestral.py` | `ingestion/fip/doc/inf_quadrimestral/inf_quadrimestral.py` |
| `ingestion/fie/doc/balancete.py` | `ingestion/fie/doc/balancete/balancete.py` |
| `ingestion/fie/doc/balanco.py` | `ingestion/fie/doc/balanco/balanco.py` |
| `ingestion/fie/medidas.py` | `ingestion/fie/medidas/medidas.py` |
| `ingestion/securit/doc/dfin_cra.py` | `ingestion/securit/doc/dfin_cra/dfin_cra.py` |
| `ingestion/securit/doc/dfin_cri.py` | `ingestion/securit/doc/dfin_cri/dfin_cri.py` |
| `ingestion/emissor_cepac/cad/cadastro.py` | `ingestion/emissor_cepac/cad/cadastro/cadastro.py` |

**Interfaces:**
- Consumes: nothing.
- Produces: 12 packages, each exporting its existing reader class unchanged
  (`InformeDiarioReader`, `CdaReader`, `CadastroFiReader`, `DfinFiiReader`,
  `InfTrimestralFipReader`, `InfQuadrimestralFipReader`, `BalanceteFieReader`,
  `BalancoFieReader`, `MedidasMesFieReader`, `DfinCraReader`, `DfinCriReader`,
  `CadastroEmissorCepacReader`) — each now importable at `…<dataset>.<dataset>`.

- [ ] **Step 1: Run the suite first to record the green baseline**

Run: `poetry run pytest tests/unit -q`
Expected: PASS (record the count — it must be identical at the end of this task; a pure move changes
no test outcome).

- [ ] **Step 2: Move all 12 modules into their own package directory**

```bash
cd src/filings_cvm/ingestion
for p in fi/doc/informe_diario fi/doc/cda fi/cad/cadastro_fi fii/doc/dfin \
         fip/doc/inf_trimestral fip/doc/inf_quadrimestral \
         fie/doc/balancete fie/doc/balanco fie/medidas \
         securit/doc/dfin_cra securit/doc/dfin_cri emissor_cepac/cad/cadastro; do
  n=$(basename "$p")
  mkdir -p "$p"
  git mv "$p.py" "$p/$n.py"
done
git status --short
```
Expected: 12 renames staged (`R  …/cda.py -> …/cda/cda.py`, …).

- [ ] **Step 3: Write each package's `__init__.py` re-export**

Mirror `fi/doc/lamina/__init__.py` exactly. One file per package; example for `cda` —
**repeat the same shape for the other 11**, substituting module + class + a one-line pt-BR summary:

```python
"""CVM open-data **CDA** reader (`FI/DOC/CDA`).

Demonstrativo de Composição e Diversificação das Aplicações. Re-exported from
`filings_cvm.ingestion`.
"""

from filings_cvm.ingestion.fi.doc.cda.cda import CdaReader


__all__ = ["CdaReader"]
```

Module→class map for the other 11: `informe_diario`→`InformeDiarioReader` ·
`cadastro_fi`→`CadastroFiReader` · `dfin`→`DfinFiiReader` ·
`inf_trimestral`→`InfTrimestralFipReader` · `inf_quadrimestral`→`InfQuadrimestralFipReader` ·
`balancete`→`BalanceteFieReader` · `balanco`→`BalancoFieReader` · `medidas`→`MedidasMesFieReader` ·
`dfin_cra`→`DfinCraReader` · `dfin_cri`→`DfinCriReader` · `cadastro`→`CadastroEmissorCepacReader`.

- [ ] **Step 4: Run the suite — expect FAILURES, and understand why**

Run: `poetry run pytest tests/unit -q`
Expected: **FAIL** in the 8 test files below. This failure is the point of the next step: a test
patches `"filings_cvm.ingestion.fi.doc.cda.download_file"`, but `…fi.doc.cda` is now a **package**
whose `__init__` re-exports `CdaReader` and **not** `download_file`. The patch binds an unused
attribute on the package, the reader module keeps its real `download_file`, the read attempts a real
fetch, and the autouse socket guard in `tests/conftest.py` fails it. **A green run here would mean
the mock silently stopped working — treat green as a red flag.**

- [ ] **Step 5: Repoint the patch targets to the module inside the package**

The fix is the `lamina` precedent (`…fi.doc.lamina.lamina.download_file`): insert the module name
once more. Files and their current dotted prefixes:

| Test file | Rewrite prefix |
|---|---|
| `tests/unit/test_informe_diario_ingestion.py` | `…fi.doc.informe_diario` → `…fi.doc.informe_diario.informe_diario` |
| `tests/unit/test_cda_ingestion.py` | `…fi.doc.cda` → `…fi.doc.cda.cda` |
| `tests/unit/test_cadastro_fi_ingestion.py` | `…fi.cad.cadastro_fi` → `…fi.cad.cadastro_fi.cadastro_fi` |
| `tests/unit/test_dfin_fii_ingestion.py` | `…fii.doc.dfin` → `…fii.doc.dfin.dfin` |
| `tests/unit/test_inf_trimestral_fip_ingestion.py` | `…fip.doc.inf_trimestral` → `…fip.doc.inf_trimestral.inf_trimestral` |
| `tests/unit/test_inf_quadrimestral_fip_ingestion.py` | `…fip.doc.inf_quadrimestral` → `…fip.doc.inf_quadrimestral.inf_quadrimestral` |
| `tests/unit/test_fie_ingestion.py` | `…fie.doc.balancete` → `…fie.doc.balancete.balancete`; `…fie.doc.balanco` → `…fie.doc.balanco.balanco`; `…fie.medidas` → `…fie.medidas.medidas` |
| `tests/unit/test_securit_cepac_flat_ingestion.py` | `…securit.doc.dfin_cra` → `…securit.doc.dfin_cra.dfin_cra`; `…securit.doc.dfin_cri` → `…securit.doc.dfin_cri.dfin_cri`; `…emissor_cepac.cad.cadastro` → `…emissor_cepac.cad.cadastro.cadastro` |

Rewrite **only** the `monkeypatch.setattr(...)` / module-path strings and any
`from …<dataset> import _DATE_COLS, _DTYPES`-style private imports (the `lamina` test does this at
its line 203). **Do not** touch imports of the public reader classes — those still resolve via the
package `__init__`.

- [ ] **Step 6: Run the suite — back to the exact baseline**

Run: `poetry run pytest tests/unit -q`
Expected: PASS, with the **same test count as Step 1**. A pure move must not change any outcome.

- [ ] **Step 7: Prove the public API is byte-identical**

Run:
```bash
poetry run python -c "import filings_cvm as f; print(len(f.__all__)); print(f.__all__ == sorted(f.__all__, key=str.lower))"
```
Expected: the same count as before the move (108 at `0.25.4`), and the ordering check unchanged.
This is the real assertion that the promotion was transparent to consumers.

- [ ] **Step 8: Run the full gate set**

Run:
```bash
poetry run ruff check src tests && poetry run ruff format --check src tests \
  && poetry run mypy src && poetry run python bin/check_typing.py \
  && poetry run python bin/check_provenance.py && poetry run codespell
```
Expected: all clean.

- [ ] **Step 9: Commit (commit 1 of 2)**

```bash
git add -A
git commit -F - <<'MSG'
refactor(ingestion): every dataset is a package, ready for its meta.py

Promotes the 12 single-module datasets to packages (dfin_cra.py ->
dfin_cra/dfin_cra.py), mirroring the CVM portal, which has a directory per
dataset. Pure move: the public API stays flat because each package __init__
re-exports its reader, so parent imports are unchanged. Precedent:
fi/doc/lamina/lamina.py and #44.

Test patch targets follow the module into the package (the lamina precedent):
patching "...cda.download_file" would now bind an unused attribute on the
package __init__ and let the reader attempt a real fetch.

Refs #97
MSG
git log --oneline -1
```
Expected: exit 0 and HEAD advanced. **Do not pipe this commit through `tail`** — a failing hook
scrolls off and the commit silently does not land (bit this repo twice).

---

### Task 2: The META block parser (pure, no I/O)

**Files:**
- Create: `src/filings_cvm/_internal/utils/meta_parser.py`
- Create: `tests/unit/test_meta_parser.py`
- Create: `tests/fixtures/meta/meta_inf_mensal_cra_fluxo_caixa.txt`,
  `tests/fixtures/meta/meta_dfin_cra.txt`

**Interfaces:**
- Consumes: nothing (stdlib only).
- Produces: `parse_meta_blocks(str_text: str, str_section: str) -> list[dict[str, str]]` — one dict
  per field with exactly the keys `section, field, description, domain, data_type, size, precision,
  scale` (all `str`; absent attributes are `""`).

- [ ] **Step 1: Save the real CVM fixtures (the oracle)**

```bash
mkdir -p tests/fixtures/meta
curl -sS --max-time 60 -o /tmp/meta_cra.zip \
  https://dados.cvm.gov.br/dados/SECURIT/DOC/INF_MENSAL_CRA/META/meta_inf_mensal_cra.zip
python3 -c "
import zipfile
z = zipfile.ZipFile('/tmp/meta_cra.zip')
open('tests/fixtures/meta/meta_inf_mensal_cra_fluxo_caixa.txt','wb').write(
    z.read('meta_inf_mensal_cra_fluxo_caixa.txt'))
"
curl -sS --max-time 60 -o tests/fixtures/meta/meta_dfin_cra.txt \
  https://dados.cvm.gov.br/dados/SECURIT/DOC/DFIN_CRA/META/meta_dfin_cra.txt
ls -l tests/fixtures/meta/
```
Expected: two files, non-zero size. These are **verbatim CVM bytes** (ISO-8859-1, CRLF) — the only
non-tautological oracle. Never hand-edit them. `fluxo_caixa` is chosen deliberately: it carries the
50-char truncation.

- [ ] **Step 2: Write the failing tests**

```python
"""Unit tests for the CVM META block parser.

Pinned to **real CVM bytes** (`tests/fixtures/meta/`): a fixture written by hand would only assert
our own belief. The truncation test is the one that matters — CVM cuts field names at exactly 50
chars, and this parser must hand that back verbatim rather than "repair" it.
"""

from pathlib import Path

from filings_cvm._internal.utils.meta_parser import parse_meta_blocks


_FIXTURES = Path(__file__).resolve().parents[1] / "fixtures" / "meta"


def _read(str_name: str) -> str:
	return (_FIXTURES / str_name).read_bytes().decode("ISO-8859-1")


def test_parse_meta_blocks_returns_one_record_per_field() -> None:
	"""Every `Campo:` block becomes exactly one record, in document order."""
	list_rows = parse_meta_blocks(_read("meta_dfin_cra.txt"), "dfin_cra")
	assert len(list_rows) == 9
	assert list_rows[0]["field"] == "CNPJ_Emissora"
	assert {r["section"] for r in list_rows} == {"dfin_cra"}


def test_parse_meta_blocks_strips_the_crlf_carriage_return() -> None:
	"""CVM ships CRLF; no parsed value may keep a trailing `\\r`."""
	list_rows = parse_meta_blocks(_read("meta_dfin_cra.txt"), "dfin_cra")
	assert not any("\r" in str_value for dict_row in list_rows for str_value in dict_row.values())


def test_parse_meta_blocks_preserves_cvm_50_char_truncation_verbatim() -> None:
	"""CVM truncates field names at exactly 50 chars — hand it back UNREPAIRED.

	The real header says `Pagamentos_Classe_Subordinada_Mezanino_Amortizacao_Principal` (60 chars);
	the META says the 50-char prefix. "Fixing" it here would fabricate a name CVM never published
	and destroy the oracle. Reconciliation is the consumer's job (#98), truncation-aware.
	"""
	list_rows = parse_meta_blocks(_read("meta_inf_mensal_cra_fluxo_caixa.txt"), "fluxo_caixa")
	set_fields = {dict_row["field"] for dict_row in list_rows}
	assert "Pagamentos_Classe_Subordinada_Mezanino_Amortizacao" in set_fields
	assert "Pagamentos_Classe_Subordinada_Mezanino_Amortizacao_Principal" not in set_fields
	assert max(len(str_f) for str_f in set_fields) == 50


def test_parse_meta_blocks_maps_every_attribute_and_defaults_the_absent_to_empty() -> None:
	"""A varchar block has `size` and no `precision`/`scale`; a numeric block is the reverse."""
	list_rows = parse_meta_blocks(_read("meta_dfin_cra.txt"), "dfin_cra")
	dict_by_field = {dict_row["field"]: dict_row for dict_row in list_rows}
	dict_versao = dict_by_field["Versao"]
	assert dict_versao["data_type"] == "tinyint"
	assert dict_versao["precision"] == "3"
	assert dict_versao["scale"] == "0"
	assert dict_versao["size"] == ""


def test_parse_meta_blocks_returns_empty_for_text_without_blocks() -> None:
	"""Degrade quietly on unexpected content — no exception, no fabricated rows."""
	assert parse_meta_blocks("nothing to see here", "x") == []
```

- [ ] **Step 3: Run to verify they fail**

Run: `poetry run pytest tests/unit/test_meta_parser.py -q`
Expected: FAIL — `ModuleNotFoundError: No module named 'filings_cvm._internal.utils.meta_parser'`.

- [ ] **Step 4: Write the parser**

This code is **verified against the real CRI + CRA META** (300 rows / 11 sections parsed clean).

```python
"""CVM META parser — the block-structured spec text CVM publishes → flat records.

Every open-data dataset ships a **META** artifact (`.../<DATASET>/META/meta_*.txt|zip`) describing
its fields. It is **not** CSV: it is a block of the form

    -----------------------
    Campo: Data_Referencia
    -----------------------
       Descrição : Data de referência do documento
       Domínio   : AAAA-MM-DD
       Tipo Dados: date
       Tamanho   : 10

encoded **ISO-8859-1** with **CRLF** line endings.

Two properties of the source are load-bearing, and both are honoured here rather than smoothed over:

- **CVM truncates the field name at exactly 50 characters.** The real artifact header carries names
  up to 60. This parser returns the truncated name **verbatim** — "repairing" it would fabricate a
  string CVM never published and destroy the only non-tautological oracle the contracts have.
  Reconciling META against the real header belongs to the consumer, and must compare
  ``real[:50] == meta``.
- **CRLF.** The line endings are normalised **once**, on entry. Skip it and every value silently
  keeps a trailing ``\\r`` — a field parses as ``"Data_Referencia\\r"`` and even a 50-char
  truncation check misses, because the name measures 51.

Pure text→records transform: no I/O, no pandas. The reader owns the download and the frame.
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING


if TYPE_CHECKING:
	from filings_cvm._internal.utils.typing import type_checker
else:
	try:
		from filings_cvm._internal.utils.typing import type_checker
	except ModuleNotFoundError:  # DDD ships the engine as chassis.typing
		from filings_cvm._internal.utils.typing import type_checker


# CVM's pt-BR attribute labels → this package's English column names. The labels are *hers* (they
# are the source's text); the column names are *ours* (CVM publishes no table), which is why they
# are English like the provenance columns. Values stay verbatim pt-BR.
_ATTRIBUTE_COLUMNS: dict[str, str] = {
	"Descrição": "description",
	"Domínio": "domain",
	"Tipo Dados": "data_type",
	"Tamanho": "size",
	"Precisão": "precision",
	"Scale": "scale",
}

# The output record's keys, in column order. `section` and `field` are positional; the rest come
# from _ATTRIBUTE_COLUMNS, so the two cannot drift.
_RECORD_COLUMNS: tuple[str, ...] = ("section", "field", *_ATTRIBUTE_COLUMNS.values())

_RE_FIELD = re.compile(r"^Campo:[ \t]*(?P<field>.+?)[ \t]*$", re.MULTILINE)
_RE_ATTRIBUTE = re.compile(
	r"^[ \t]*(?P<key>" + "|".join(_ATTRIBUTE_COLUMNS) + r")[ \t]*:[ \t]*(?P<value>.*?)[ \t]*$",
	re.MULTILINE,
)


@type_checker
def parse_meta_blocks(str_text: str, str_section: str) -> list[dict[str, str]]:
	"""Parse one META document into one record per declared field.

	Parameters
	----------
	str_text : str
		The decoded META text (ISO-8859-1 → str). CRLF is normalised here.
	str_section : str
		The section this document describes — a ZIP member's name for a multi-member META, or the
		dataset itself for a flat one. Copied onto every record.

	Returns
	-------
	list of dict of (str, str)
		One record per ``Campo:`` block, in document order, each carrying exactly
		:data:`_RECORD_COLUMNS`. An attribute the block omits is ``""`` (never ``None``) — a varchar
		block has no ``Precisão``/``Scale``, a numeric one has no ``Tamanho``. Text with no block at
		all yields ``[]`` rather than raising: a META that changes shape must not crash a datalake
		run.
	"""
	# CVM ships CRLF. Normalise ONCE, here — otherwise every value keeps a trailing "\r".
	str_normalised = str_text.replace("\r\n", "\n")
	list_matches = list(_RE_FIELD.finditer(str_normalised))
	list_records: list[dict[str, str]] = []
	for int_index, cls_match in enumerate(list_matches):
		int_block_end = (
			list_matches[int_index + 1].start()
			if int_index + 1 < len(list_matches)
			else len(str_normalised)
		)
		dict_record = dict.fromkeys(_RECORD_COLUMNS, "")
		dict_record["section"] = str_section
		dict_record["field"] = cls_match.group("field")
		for cls_attribute in _RE_ATTRIBUTE.finditer(str_normalised[cls_match.end() : int_block_end]):
			dict_record[_ATTRIBUTE_COLUMNS[cls_attribute.group("key")]] = cls_attribute.group("value")
		list_records.append(dict_record)
	return list_records
```

- [ ] **Step 5: Run the tests**

Run: `poetry run pytest tests/unit/test_meta_parser.py -q`
Expected: 5 passed. If `test_parse_meta_blocks_returns_one_record_per_field` fails on the count,
**do not edit the fixture** — read the real file and fix the expectation (the fixture is the oracle).

- [ ] **Step 6: Commit**

```bash
git add src/filings_cvm/_internal/utils/meta_parser.py tests/unit/test_meta_parser.py tests/fixtures/meta
git commit -m "feat(ingestion): CVM META block parser pinned to real bytes"
git log --oneline -1
```

---

### Task 3: The META contracts

**Files:**
- Create: `src/filings_cvm/_internal/config/contracts/meta.py`
- Modify: `src/filings_cvm/_internal/config/contracts/__init__.py`
- Modify: `tests/unit/test_meta_readers.py` (created in Task 4 — write this test there if running
  out of order; otherwise add it now and let Task 4 extend the file)

**Interfaces:**
- Consumes: `FileContract` — `@dataclass(frozen=True)` with fields `str_name: str`,
  `str_source_key: str`, `tuple_required: tuple[str, ...]`, `tuple_cnpj_cols: tuple[str, ...]`.
- Produces: `META_COLUMNS: tuple[str, ...]`, `_meta_contract(str_dataset, str_label) -> FileContract`,
  and 22 module-level instances named `META_<DATASET>` (e.g. `META_INF_MENSAL_CRA`, `META_CAD_FI`).

- [ ] **Step 1: Write the failing test**

Add to `tests/unit/test_meta_readers.py` (create the file if absent):

```python
"""Unit tests for the META contracts and readers."""

from filings_cvm._internal.config.contracts.meta import META_CAD_FI, META_COLUMNS, META_DFIN_CRA


def test_meta_contracts_share_one_column_tuple() -> None:
	"""The parsed shape is OURS and identical for every dataset — only the source key differs."""
	assert META_DFIN_CRA.tuple_required == META_COLUMNS
	assert META_CAD_FI.tuple_required == META_COLUMNS


def test_meta_source_keys_are_prefixed_and_unique() -> None:
	"""`meta_` prefix keeps a META frame distinguishable from its own dataset's reader in bronze."""
	assert META_DFIN_CRA.str_source_key == "meta_dfin_cra"
	assert META_CAD_FI.str_source_key == "meta_cad_fi"
	assert META_DFIN_CRA.str_source_key != META_CAD_FI.str_source_key


def test_meta_contracts_declare_no_cnpj_columns() -> None:
	"""META describes fields; it holds no CNPJ values to validate."""
	assert META_DFIN_CRA.tuple_cnpj_cols == ()
```

- [ ] **Step 2: Run to verify it fails**

Run: `poetry run pytest tests/unit/test_meta_readers.py -q`
Expected: FAIL — `ModuleNotFoundError: … contracts.meta`.

- [ ] **Step 3: Write the contracts module**

```python
"""Contracts for the CVM **META** artifacts — one per dataset.

Unlike every other contract here, ``tuple_required`` does **not** describe a CVM artifact's columns:
the META is block text, not a table, so the parsed frame's shape is **ours** and is identical for
all 22 datasets. What genuinely differs is ``str_source_key`` — which is exactly what
``stamp_provenance`` writes onto every row so a datalake can tell two datasets apart when they land
in one bronze table. Hence a factory over a shared tuple rather than 22 hand-copied literals.

Consolidating many contracts in one module follows the ``cad_fi_hist.py`` precedent (19 members of
one archive in one file).

The ``meta_`` prefix on every source key is load-bearing: without it, ``META_DFIN_CRA`` and the
``DfinCraReader``'s own contract would both stamp ``dfin_cra`` and become indistinguishable
downstream — the precise ambiguity ``source_key`` exists to prevent.
"""

from __future__ import annotations

from filings_cvm._internal.utils.tabular_reader import FileContract


# The parsed META frame's source columns, in order — see `utils.meta_parser._RECORD_COLUMNS`.
# The six provenance columns are appended later by `stamp_provenance` and are deliberately NOT here
# (tuple_required validates the parsed source; provenance is added after).
META_COLUMNS: tuple[str, ...] = (
	"section",
	"field",
	"description",
	"domain",
	"data_type",
	"size",
	"precision",
	"scale",
)


def _meta_contract(str_dataset: str, str_label: str) -> FileContract:
	"""Build the contract for one dataset's META.

	Parameters
	----------
	str_dataset : str
		The dataset slug (e.g. ``"inf_mensal_cra"``); ``meta_``-prefixed to form the source key.
	str_label : str
		Human-readable label for logs and notifications.

	Returns
	-------
	FileContract
		Contract carrying the shared :data:`META_COLUMNS` and this dataset's unique source key.
	"""
	return FileContract(
		str_name=str_label,
		str_source_key=f"meta_{str_dataset}",
		tuple_required=META_COLUMNS,
		tuple_cnpj_cols=(),
	)


META_INF_DIARIO_FI = _meta_contract("inf_diario_fi", "META — Informe Diário FI")
META_CDA_FI = _meta_contract("cda_fi", "META — CDA FI")
META_LAMINA_FI = _meta_contract("lamina_fi", "META — Lâmina FI")
META_CAD_FI = _meta_contract("cad_fi", "META — Cadastro FI")
META_CAD_FI_HIST = _meta_contract("cad_fi_hist", "META — Cadastro FI histórico")
META_REGISTRO_FUNDO_CLASSE = _meta_contract(
	"registro_fundo_classe", "META — Registro fundo/classe/subclasse"
)
META_INF_MENSAL_FIDC = _meta_contract("inf_mensal_fidc", "META — Informe Mensal FIDC")
META_INF_MENSAL_FII = _meta_contract("inf_mensal_fii", "META — Informe Mensal FII")
META_DFIN_FII = _meta_contract("dfin_fii", "META — DFIN FII")
META_INF_TRIMESTRAL_FII = _meta_contract("inf_trimestral_fii", "META — Informe Trimestral FII")
META_INF_ANUAL_FII = _meta_contract("inf_anual_fii", "META — Informe Anual FII")
META_INF_TRIMESTRAL_FIP = _meta_contract("inf_trimestral_fip", "META — Informe Trimestral FIP")
META_INF_QUADRIMESTRAL_FIP = _meta_contract(
	"inf_quadrimestral_fip", "META — Informe Quadrimestral FIP"
)
META_INF_MENSAL_FIAGRO = _meta_contract("inf_mensal_fiagro", "META — Informe Mensal FIAGRO")
META_BALANCETE_FIE = _meta_contract("balancete_fie", "META — Balancete FIE")
META_BALANCO_FIE = _meta_contract("balanco_fie", "META — Balanço FIE")
META_MEDIDAS_MES_FIE = _meta_contract("medidas_mes_fie", "META — Medidas Mensais FIE")
META_DFIN_CRA = _meta_contract("dfin_cra", "META — DFIN CRA")
META_DFIN_CRI = _meta_contract("dfin_cri", "META — DFIN CRI")
META_INF_MENSAL_OTS = _meta_contract("inf_mensal_ots", "META — Informe Mensal OTS")
META_INF_MENSAL_CRA = _meta_contract("inf_mensal_cra", "META — Informe Mensal CRA")
META_CAD_EMISSOR_CEPAC = _meta_contract("cad_emissor_cepac", "META — Cadastro Emissor CEPAC")
```

- [ ] **Step 4: Re-export from the contracts aggregator**

In `src/filings_cvm/_internal/config/contracts/__init__.py`, add the import block in alphabetical
position (after the `lamina_*` imports, before `medidas_mes_fie`) and add every name to `__all__`
in its **isort-natural** sorted position:

```python
from filings_cvm._internal.config.contracts.meta import (
	META_BALANCETE_FIE,
	META_BALANCO_FIE,
	META_CAD_EMISSOR_CEPAC,
	META_CAD_FI,
	META_CAD_FI_HIST,
	META_CDA_FI,
	META_COLUMNS,
	META_DFIN_CRA,
	META_DFIN_CRI,
	META_DFIN_FII,
	META_INF_ANUAL_FII,
	META_INF_DIARIO_FI,
	META_INF_MENSAL_CRA,
	META_INF_MENSAL_FIAGRO,
	META_INF_MENSAL_FIDC,
	META_INF_MENSAL_FII,
	META_INF_MENSAL_OTS,
	META_INF_QUADRIMESTRAL_FIP,
	META_INF_TRIMESTRAL_FII,
	META_INF_TRIMESTRAL_FIP,
	META_LAMINA_FI,
	META_MEDIDAS_MES_FIE,
	META_REGISTRO_FUNDO_CLASSE,
)
```

- [ ] **Step 5: Run the tests**

Run: `poetry run pytest tests/unit/test_meta_readers.py -q`
Expected: 3 passed.

- [ ] **Step 6: Commit**

```bash
git add src/filings_cvm/_internal/config/contracts tests/unit/test_meta_readers.py
git commit -m "feat(ingestion): META contracts, one source key per dataset"
git log --oneline -1
```

---

### Task 4: The private base META reader

**Files:**
- Create: `src/filings_cvm/ingestion/_base_meta_reader.py`
- Modify: `tests/unit/test_meta_readers.py`

**Interfaces:**
- Consumes: `parse_meta_blocks` (Task 2); `META_*` contracts (Task 3); `IngestionReader` (ABC with
  abstract `read(self) -> pd.DataFrame`, metaclass `ABCTypeCheckerMeta`);
  `raw_workspace(path_raw: Path | None) -> Iterator[Path]` (context manager);
  `download_file(str_url, path_dest, int_timeout_s=60, retry_policy=None) -> Path`;
  `hash_artifact(path_artifact: Path) -> str`;
  `stamp_provenance(df_input, str_url, cls_contract, str_content_hash) -> pd.DataFrame`;
  `RetryPolicy`, `LogEmitter`.
- Produces: `BaseMetaReader` with class attributes `_META_URL: ClassVar[str]`,
  `_CONTRACT: ClassVar[FileContract]`, `_RETRY_POLICY: ClassVar[RetryPolicy | None]`, constructor
  `(path_raw=None, retry_policy=None, cls_logger=None)`, and `read(int_timeout_s: int = 60)`.

- [ ] **Step 1: Write the failing tests**

Append to `tests/unit/test_meta_readers.py`:

```python
from pathlib import Path
import shutil
import zipfile

import pandas as pd
import pytest

from filings_cvm._internal.utils.tabular_reader import FileContract
from filings_cvm.ingestion.securit.doc.dfin_cra.meta import MetaDfinCraReader
from filings_cvm.ingestion.securit.doc.inf_mensal_cra.meta import MetaInfMensalCraReader


_FIXTURES = Path(__file__).resolve().parents[1] / "fixtures" / "meta"


def _fake_download_flat(str_url: str, path_dest: Path, *args: object, **kwargs: object) -> Path:
	shutil.copyfile(_FIXTURES / "meta_dfin_cra.txt", path_dest)
	return path_dest


def _fake_download_zip(str_url: str, path_dest: Path, *args: object, **kwargs: object) -> Path:
	# Build the ZIP from the REAL member bytes: the container is trivial, the member is the oracle.
	with zipfile.ZipFile(path_dest, "w") as cls_zip:
		cls_zip.writestr(
			"meta_inf_mensal_cra_fluxo_caixa.txt",
			(_FIXTURES / "meta_inf_mensal_cra_fluxo_caixa.txt").read_bytes(),
		)
	return path_dest


def test_flat_meta_reader_returns_the_parsed_frame(monkeypatch: pytest.MonkeyPatch) -> None:
	"""A `.txt` META parses to one row per field, section = the dataset."""
	monkeypatch.setattr(
		"filings_cvm.ingestion._base_meta_reader.download_file", _fake_download_flat
	)
	df_ = MetaDfinCraReader().read()
	assert len(df_) == 9
	assert set(df_["section"].unique()) == {"dfin_cra"}


def test_meta_reader_stamps_provenance(monkeypatch: pytest.MonkeyPatch) -> None:
	"""Every ingested frame carries the six provenance columns, source_key from the contract."""
	monkeypatch.setattr(
		"filings_cvm.ingestion._base_meta_reader.download_file", _fake_download_flat
	)
	df_ = MetaDfinCraReader().read()
	for str_column in FileContract.PROVENANCE_COLUMNS:
		assert str_column in df_.columns
	assert set(df_["source_key"].unique()) == {"meta_dfin_cra"}


def test_zip_meta_reader_labels_each_member_as_a_section(monkeypatch: pytest.MonkeyPatch) -> None:
	"""A multi-member META zip yields ONE long frame; the member name becomes `section`."""
	monkeypatch.setattr("filings_cvm.ingestion._base_meta_reader.download_file", _fake_download_zip)
	df_ = MetaInfMensalCraReader().read()
	assert set(df_["section"].unique()) == {"fluxo_caixa"}
	# The 50-char truncation survives the whole reader path, not just the parser.
	assert "Pagamentos_Classe_Subordinada_Mezanino_Amortizacao" in set(df_["field"])


def test_meta_reader_persists_the_raw_artifact(
	monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
	"""`path_raw` keeps the untouched bytes — the only record of what the spec said that day."""
	monkeypatch.setattr(
		"filings_cvm.ingestion._base_meta_reader.download_file", _fake_download_flat
	)
	MetaDfinCraReader(path_raw=tmp_path).read()
	assert list(tmp_path.glob("meta_dfin_cra.txt"))


def test_meta_reader_output_columns_match_the_contract(monkeypatch: pytest.MonkeyPatch) -> None:
	"""The frame's columns are exactly the contract's declared output shape, in order."""
	monkeypatch.setattr(
		"filings_cvm.ingestion._base_meta_reader.download_file", _fake_download_flat
	)
	df_ = MetaDfinCraReader().read()
	assert tuple(df_.columns) == MetaDfinCraReader._CONTRACT.output_columns
```

- [ ] **Step 2: Run to verify they fail**

Run: `poetry run pytest tests/unit/test_meta_readers.py -q`
Expected: FAIL — `ModuleNotFoundError: … ingestion._base_meta_reader` (and the `meta` submodules,
which Task 5 creates).

- [ ] **Step 3: Write the base**

```python
"""Private base for the CVM **META** readers — one per dataset.

Every dataset's META is fetched the same way and differs only in its URL, so the machinery lives
here once and each dataset's ``meta.py`` declares two constants. This mirrors the reader bases
(``_base_inf_mensal_cra_reader.py`` + thin subclasses), but sits at the ``ingestion/`` root because
it is shared across every portal root rather than scoped to one dataset package.

**Why the URL is a per-dataset constant and never derived.** The META filename is not a function of
the dataset path: ``meta_inf_mensal_cri.zip`` but ``meta_cda_fi_txt.zip`` (a ``_txt`` infix), and
``FIE/MEDIDAS`` publishes both ``.csv`` and ``.txt``. Worse, **``meta_cad_fi.txt`` and
``meta_cad_fi.zip`` are different datasets** — the ``.txt`` is ``cad_fi`` (41 fields), the ``.zip``
is ``cad_fi_hist`` (19 members). Any "derive the name" or "prefer the zip" rule would hand a caller
the wrong dataset's metadata **with every test still green**, which is precisely the failure #96
caught in the contracts themselves.

There is **no `date_ref`**: a META sits at a fixed URL that CVM overwrites in place, so a persisted
``path_raw`` snapshot is the only record of what the spec said that day (the ``CadastroFiReader``
precedent).
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, ClassVar
import zipfile

import pandas as pd

from filings_cvm._internal.config.ports.ingestion_reader import IngestionReader
from filings_cvm._internal.utils.http_downloader import download_file
from filings_cvm._internal.utils.meta_parser import parse_meta_blocks
from filings_cvm._internal.utils.provenance import hash_artifact, stamp_provenance
from filings_cvm._internal.utils.raw_workspace import raw_workspace
from filings_cvm._internal.utils.retry import LogEmitter, RetryPolicy
from filings_cvm._internal.utils.tabular_reader import FileContract


if TYPE_CHECKING:
	pass

# CVM encodes every META in ISO-8859-1 (Latin-1), like the data dumps.
_ENCODING = "ISO-8859-1"

# Shared default: the open-data portal throttles under load. 5 attempts on a capped exponential
# schedule (~2, 4, 8, 10 s). A subclass may override `_RETRY_POLICY`; a per-instance
# `retry_policy=` still wins.
_DEFAULT_RETRY_POLICY: RetryPolicy = RetryPolicy(
	int_max_attempts=5,
	float_base_wait_s=2.0,
	float_max_wait_s=10.0,
)


class BaseMetaReader(IngestionReader):
	"""Download one dataset's META and return it as a typed, provenance-stamped DataFrame.

	Subclasses declare :attr:`_META_URL` and :attr:`_CONTRACT` and nothing else.

	Methods
	-------
	read(int_timeout_s)
		Download and parse the META into a validated DataFrame.
	"""

	# Declared by every subclass.
	_META_URL: ClassVar[str]
	_CONTRACT: ClassVar[FileContract]
	_RETRY_POLICY: ClassVar[RetryPolicy | None] = _DEFAULT_RETRY_POLICY

	def __init__(
		self,
		path_raw: Path | None = None,
		retry_policy: RetryPolicy | None = None,
		cls_logger: LogEmitter | None = None,
	) -> None:
		"""Initialise the reader.

		Parameters
		----------
		path_raw : pathlib.Path, optional
			Directory in which to **persist** the raw META artifact for a datalake's bronze layer.
			Created if absent. When ``None`` (the default) it is fetched into a temporary directory
			and discarded. CVM overwrites the META in place, so a persisted copy is the **only**
			record of what the spec said on a given day.
		retry_policy : RetryPolicy, optional
			Retry/backoff schedule forwarded to the download seam. When ``None`` (the default) this
			class's :attr:`_RETRY_POLICY` is used.
		cls_logger : LogEmitter, optional
			Injected log sink (``log_message(message, level)``). Defaults to a stdlib-backed
			:class:`LogEmitter`, so no logging import is forced on consumers.
		"""
		self._path_raw = path_raw
		self._retry_policy = retry_policy if retry_policy is not None else self._RETRY_POLICY
		self._cls_logger = cls_logger if cls_logger is not None else LogEmitter()
		self._str_url = self._META_URL

	def read(self, int_timeout_s: int = 60) -> pd.DataFrame:
		"""Download and parse this dataset's META.

		Parameters
		----------
		int_timeout_s : int, optional
			Socket timeout in seconds for the download, by default 60.

		Returns
		-------
		pd.DataFrame
			One row per declared field, columns :attr:`FileContract.output_columns`. A multi-member
			META ZIP is returned as **one long frame**, each member's name in ``section``; a flat
			``.txt`` uses the dataset's source key (minus the ``meta_`` prefix) as its section.
			**Field names are verbatim CVM**, including the 50-char truncation.

		Raises
		------
		OSError
			If the download fails (network error, non-2xx status, redirect, timeout).
		"""
		str_filename = self._str_url.rsplit("/", 1)[-1]
		self._cls_logger.log_message(f"Downloading META from {self._str_url}", "info")
		with raw_workspace(self._path_raw) as path_dir:
			path_meta = download_file(
				self._str_url,
				path_dir / str_filename,
				int_timeout_s,
				retry_policy=self._retry_policy,
			)
			str_content_hash = hash_artifact(path_meta)
			list_records = self._parse_artifact(path_meta)
		df_ = pd.DataFrame(list_records, columns=list(self._CONTRACT.tuple_required)).astype(
			"string"
		)
		self._cls_logger.log_message(
			f"Loaded {len(df_)} META field rows from {str_filename}", "info"
		)
		return stamp_provenance(df_, self._str_url, self._CONTRACT, str_content_hash)

	def _parse_artifact(self, path_meta: Path) -> list[dict[str, str]]:
		"""Parse the downloaded artifact — a member-per-section ZIP or a single flat text.

		Parameters
		----------
		path_meta : pathlib.Path
			The downloaded META file.

		Returns
		-------
		list of dict of (str, str)
			The parsed records of every member, concatenated in member order.
		"""
		if path_meta.suffix.lower() != ".zip":
			str_section = self._CONTRACT.str_source_key.removeprefix("meta_")
			return parse_meta_blocks(path_meta.read_bytes().decode(_ENCODING), str_section)
		list_records: list[dict[str, str]] = []
		with zipfile.ZipFile(path_meta) as cls_zip:
			for str_member in sorted(cls_zip.namelist()):
				list_records += parse_meta_blocks(
					cls_zip.read(str_member).decode(_ENCODING),
					self._section_of(str_member),
				)
		return list_records

	@staticmethod
	def _section_of(str_member: str) -> str:
		"""Turn a META ZIP member's filename into its section label.

		``meta_inf_mensal_cra_fluxo_caixa.txt`` → ``fluxo_caixa``: strip the ``meta_`` prefix, the
		``.txt`` suffix, and the dataset stem CVM repeats on every member.

		Parameters
		----------
		str_member : str
			The ZIP member's name.

		Returns
		-------
		str
			The section label.
		"""
		str_stem = Path(str_member).stem.removeprefix("meta_")
		return str_stem
```

> **Note for the implementer — `_section_of` is deliberately naive.** It returns
> ``inf_mensal_cra_fluxo_caixa``, not ``fluxo_caixa``, because the dataset stem varies per dataset
> (``meta_cad_fi_hist_admin.txt`` → ``cad_fi_hist_admin``). Step 4 fixes this properly.

- [ ] **Step 4: Make the section label the member's own name**

Give the subclass the stem to strip, so no guessing is needed. Add a class attribute and use it:

```python
	# The stem CVM repeats on every member of this dataset's META ZIP, stripped to leave the bare
	# section (`meta_inf_mensal_cra_fluxo_caixa.txt` -> `fluxo_caixa`). Empty for a flat `.txt`.
	_MEMBER_STEM: ClassVar[str] = ""
```

and replace `_section_of` with:

```python
	def _section_of(self, str_member: str) -> str:
		"""Turn a META ZIP member's filename into its section label.

		``meta_inf_mensal_cra_fluxo_caixa.txt`` → ``fluxo_caixa``. The dataset stem CVM repeats on
		every member is declared by the subclass (:attr:`_MEMBER_STEM`) rather than guessed: the
		stems are irregular (``meta_cad_fi_hist_admin.txt`` belongs to ``cad_fi_hist``, whose own
		META file is named ``meta_cad_fi.zip``).

		Parameters
		----------
		str_member : str
			The ZIP member's name.

		Returns
		-------
		str
			The section label, or the whole stem when it does not carry the expected prefix.
		"""
		str_stem = Path(str_member).stem.removeprefix("meta_")
		if self._MEMBER_STEM and str_stem.startswith(f"{self._MEMBER_STEM}_"):
			return str_stem.removeprefix(f"{self._MEMBER_STEM}_")
		return str_stem
```

- [ ] **Step 5: Run the tests**

Run: `poetry run pytest tests/unit/test_meta_readers.py -q`
Expected: still FAIL — the `meta.py` subclasses do not exist yet (Task 5). The base itself must
import cleanly:
Run: `poetry run python -c "from filings_cvm.ingestion._base_meta_reader import BaseMetaReader; print('ok')"`
Expected: `ok`.

- [ ] **Step 6: Commit**

```bash
git add src/filings_cvm/ingestion/_base_meta_reader.py tests/unit/test_meta_readers.py
git commit -m "feat(ingestion): private base for the META readers"
git log --oneline -1
```

---

### Task 5: The 22 `meta.py` subclasses + public API

**Files:**
- Create: `src/filings_cvm/ingestion/**/<dataset>/meta.py` × 22
- Modify: each dataset package's `__init__.py` (add the `Meta*Reader` re-export)
- Modify: `src/filings_cvm/ingestion/__init__.py`, `src/filings_cvm/__init__.py`
- Modify: `tests/unit/test_meta_readers.py`

**Interfaces:**
- Consumes: `BaseMetaReader` (Task 4), the `META_*` contracts (Task 3).
- Produces: 22 public classes `Meta<Dataset>Reader`, each re-exported from `filings_cvm`.

**The full table — dataset → package → class → real META URL** (every URL verified live against
the portal on 2026-07-15; base `https://dados.cvm.gov.br/dados/`):

| Package (under `ingestion/`) | Class | URL path (after the base) | `_MEMBER_STEM` |
|---|---|---|---|
| `fi/doc/informe_diario/` | `MetaInformeDiarioReader` | `FI/DOC/INF_DIARIO/META/meta_inf_diario_fi.txt` | `""` |
| `fi/doc/cda/` | `MetaCdaReader` | `FI/DOC/CDA/META/meta_cda_fi_txt.zip` | `cda_fi` |
| `fi/doc/lamina/` | `MetaLaminaReader` | `FI/DOC/LAMINA/META/meta_lamina_fi_txt.zip` | `lamina_fi` |
| `fi/cad/cadastro_fi/` | `MetaCadastroFiReader` | `FI/CAD/META/meta_cad_fi.txt` | `""` |
| `fi/cad/cad_fi_hist/` | `MetaCadFiHistReader` | `FI/CAD/META/meta_cad_fi.zip` | `cad_fi_hist` |
| `fi/cad/registro/` | `MetaRegistroReader` | `FI/CAD/META/meta_registro_fundo_classe.zip` | `registro` |
| `fidc/doc/inf_mensal/` | `MetaInfMensalFidcReader` | `FIDC/DOC/INF_MENSAL/META/meta_inf_mensal_fidc_txt.zip` | `inf_mensal_fidc` |
| `fii/doc/inf_mensal/` | `MetaInfMensalFiiReader` | `FII/DOC/INF_MENSAL/META/meta_inf_mensal_fii.zip` | `inf_mensal_fii` |
| `fii/doc/dfin/` | `MetaDfinFiiReader` | `FII/DOC/DFIN/META/meta_dfin_fii.txt` | `""` |
| `fii/doc/inf_trimestral/` | `MetaInfTrimestralFiiReader` | `FII/DOC/INF_TRIMESTRAL/META/meta_inf_trimestral_fii.zip` | `inf_trimestral_fii` |
| `fii/doc/inf_anual/` | `MetaInfAnualFiiReader` | `FII/DOC/INF_ANUAL/META/meta_inf_anual_fii.zip` | `inf_anual_fii` |
| `fip/doc/inf_trimestral/` | `MetaInfTrimestralFipReader` | `FIP/DOC/INF_TRIMESTRAL/META/meta_inf_trimestral_fip.txt` | `""` |
| `fip/doc/inf_quadrimestral/` | `MetaInfQuadrimestralFipReader` | `FIP/DOC/INF_QUADRIMESTRAL/META/meta_inf_quadrimestral_fip.txt` | `""` |
| `fiagro/doc/inf_mensal/` | `MetaInfMensalFiagroReader` | `FIAGRO/DOC/INF_MENSAL/META/meta_inf_mensal_fiagro.zip` | `inf_mensal_fiagro` |
| `fie/doc/balancete/` | `MetaBalanceteFieReader` | `FIE/DOC/BALANCETE/META/meta_balancete_fie.txt` | `""` |
| `fie/doc/balanco/` | `MetaBalancoFieReader` | `FIE/DOC/BALANCO/META/meta_balanco_fie.txt` | `""` |
| `fie/medidas/` | `MetaMedidasMesFieReader` | `FIE/MEDIDAS/META/meta_medidas_mes_fie.txt` | `""` |
| `securit/doc/dfin_cra/` | `MetaDfinCraReader` | `SECURIT/DOC/DFIN_CRA/META/meta_dfin_cra.txt` | `""` |
| `securit/doc/dfin_cri/` | `MetaDfinCriReader` | `SECURIT/DOC/DFIN_CRI/META/meta_dfin_cri.txt` | `""` |
| `securit/doc/inf_mensal_ots/` | `MetaInfMensalOtsReader` | `SECURIT/DOC/INF_MENSAL_OTS/META/meta_inf_mensal_ots.zip` | `inf_mensal_ots` |
| `securit/doc/inf_mensal_cra/` | `MetaInfMensalCraReader` | `SECURIT/DOC/INF_MENSAL_CRA/META/meta_inf_mensal_cra.zip` | `inf_mensal_cra` |
| `emissor_cepac/cad/cadastro/` | `MetaCadEmissorCepacReader` | `EMISSOR_CEPAC/CAD/META/meta_cad_emissor_cepac.txt` | `""` |

> `FIE/MEDIDAS` also publishes a `.csv`; the `.txt` is used deliberately — it is the format all 22
> share. `SECURIT/DOC/INF_MENSAL_CRI` is **absent on purpose**: its readers do not exist yet, so its
> `meta.py` ships with the CRI PR, which creates that package (and should build its contracts
> META-first using this module).

- [ ] **Step 1: Write one `meta.py` — the ZIP case**

`src/filings_cvm/ingestion/securit/doc/inf_mensal_cra/meta.py`:

```python
"""CVM **META** for the SECURIT INF_MENSAL_CRA dataset (`SECURIT/DOC/INF_MENSAL_CRA`).

The spec CVM publishes for the 8 members of `inf_mensal_cra_AAAA.zip` — the declared description,
type and size of every field, which the artifact's own header cannot carry.

⚠️ **The field names come back truncated at 50 characters, verbatim as CVM publishes them.** This
dataset is the proof: `Pagamentos_Classe_Subordinada_Mezanino_Amortizacao_Principal` (60 chars in
the real header) appears here as its 50-char prefix. Do not "repair" it — compare
`real[:50] == meta`.
"""

from __future__ import annotations

from typing import ClassVar

from filings_cvm._internal.config.contracts.meta import META_INF_MENSAL_CRA
from filings_cvm._internal.utils.tabular_reader import FileContract
from filings_cvm.ingestion._base_meta_reader import BaseMetaReader


class MetaInfMensalCraReader(BaseMetaReader):
	"""Read the META of the CVM SECURIT INF_MENSAL_CRA dataset.

	Methods
	-------
	read(int_timeout_s)
		Download and parse the META into a validated DataFrame (inherited).
	"""

	_META_URL: ClassVar[str] = (
		"https://dados.cvm.gov.br/dados/SECURIT/DOC/INF_MENSAL_CRA/META/meta_inf_mensal_cra.zip"
	)
	_CONTRACT: ClassVar[FileContract] = META_INF_MENSAL_CRA
	_MEMBER_STEM: ClassVar[str] = "inf_mensal_cra"
```

- [ ] **Step 2: Write one `meta.py` — the flat case**

`src/filings_cvm/ingestion/securit/doc/dfin_cra/meta.py`:

```python
"""CVM **META** for the SECURIT DFIN_CRA dataset (`SECURIT/DOC/DFIN_CRA`).

The spec CVM publishes for `dfin_cra_AAAA.csv` — the declared description, type and size of each of
its 9 fields. A flat `.txt`, so the whole document is one section.
"""

from __future__ import annotations

from typing import ClassVar

from filings_cvm._internal.config.contracts.meta import META_DFIN_CRA
from filings_cvm._internal.utils.tabular_reader import FileContract
from filings_cvm.ingestion._base_meta_reader import BaseMetaReader


class MetaDfinCraReader(BaseMetaReader):
	"""Read the META of the CVM SECURIT DFIN_CRA dataset.

	Methods
	-------
	read(int_timeout_s)
		Download and parse the META into a validated DataFrame (inherited).
	"""

	_META_URL: ClassVar[str] = (
		"https://dados.cvm.gov.br/dados/SECURIT/DOC/DFIN_CRA/META/meta_dfin_cra.txt"
	)
	_CONTRACT: ClassVar[FileContract] = META_DFIN_CRA
```

- [ ] **Step 3: Run the base tests — they pass now**

Run: `poetry run pytest tests/unit/test_meta_readers.py -q`
Expected: 8 passed (3 contract + 5 base). If `test_zip_meta_reader_labels_each_member_as_a_section`
fails with `section == "inf_mensal_cra_fluxo_caixa"`, `_MEMBER_STEM` is not being applied — recheck
Task 4 Step 4.

- [ ] **Step 4: Write the other 20 `meta.py` from the table**

Same two shapes. Each docstring states, in one or two lines, what the dataset is and whether the
META is flat or multi-member. Set `_MEMBER_STEM` **only** for `.zip` URLs.

- [ ] **Step 5: Re-export from each dataset package's `__init__.py`**

Add the `Meta*Reader` to every dataset package `__init__`, keeping `__all__` sorted. Example for
`securit/doc/dfin_cra/__init__.py`:

```python
"""CVM open-data **DFIN CRA** reader and its META (`SECURIT/DOC/DFIN_CRA`)."""

from filings_cvm.ingestion.securit.doc.dfin_cra.dfin_cra import DfinCraReader
from filings_cvm.ingestion.securit.doc.dfin_cra.meta import MetaDfinCraReader


__all__ = ["DfinCraReader", "MetaDfinCraReader"]
```

- [ ] **Step 6: Re-export from `ingestion/__init__.py` and `filings_cvm/__init__.py`**

Add all 22 `Meta*Reader` names to both, in **isort-natural** sorted position in `__all__` (note
RUF022 is not enabled yet — #101 — so sorting is by hand and by eye; keep `Meta…` names together).

- [ ] **Step 7: Add the introspective coverage test**

This is the test that stops the 23rd dataset from being forgotten. Append to
`tests/unit/test_meta_readers.py`:

```python
def test_every_meta_reader_is_public_and_declares_its_url() -> None:
	"""Discovery, not a hand list: a new Meta*Reader that forgets a constant fails CI.

	Mirrors `test_reader_retry_policy.py` — the convention is enforced structurally, so it cannot
	rot the way a documented rule does.
	"""
	import filings_cvm

	list_meta = [
		getattr(filings_cvm, str_name)
		for str_name in filings_cvm.__all__
		if str_name.startswith("Meta") and str_name.endswith("Reader")
	]
	assert len(list_meta) == 22
	for cls_reader in list_meta:
		assert cls_reader._META_URL.startswith("https://dados.cvm.gov.br/dados/")
		assert "/META/" in cls_reader._META_URL
		assert cls_reader._CONTRACT.str_source_key.startswith("meta_")
		assert cls_reader._RETRY_POLICY is not None


def test_meta_source_keys_are_unique_across_every_reader() -> None:
	"""Two datasets sharing a source_key would be indistinguishable in the bronze table."""
	import filings_cvm

	list_keys = [
		getattr(filings_cvm, str_name)._CONTRACT.str_source_key
		for str_name in filings_cvm.__all__
		if str_name.startswith("Meta") and str_name.endswith("Reader")
	]
	assert len(list_keys) == len(set(list_keys))
```

- [ ] **Step 8: Run everything, both pandas majors**

```bash
poetry run pytest tests/unit -q
poetry run pip install "pandas==2.3.3" -q && poetry run pytest tests/unit -q
poetry run pip install "pandas==3.0.3" -q && poetry run pytest tests/unit -q
```
Expected: PASS on both. The `astype("string")` (nullable) in the base is deliberate — plain
`astype("str")` fabricates the literal `"nan"` on pandas 2.x (the trap `apply_dtypes` already fixed).

- [ ] **Step 9: Live-verify against the real portal** (not a mock — the artifact is the point)

```bash
poetry run python -c "
from filings_cvm import MetaInfMensalCraReader, MetaCadFiReader, MetaCadFiHistReader
df = MetaInfMensalCraReader().read()
print('CRA rows', len(df), '| sections', sorted(df['section'].unique()))
print('50-char names kept:', sum(1 for f in df['field'] if len(f) == 50))
print('cad_fi fields', len(MetaCadFiReader().read()))
print('cad_fi_hist sections', MetaCadFiHistReader().read()['section'].nunique())
"
```
Expected: CRA 8 sections; **8** fields at exactly 50 chars; `cad_fi` 41 fields; `cad_fi_hist` 19
sections. The last two prove the `meta_cad_fi.txt` vs `meta_cad_fi.zip` trap is handled — different
datasets, different classes, no cross-contamination.

- [ ] **Step 10: Full gates + commit**

```bash
poetry run ruff check src tests && poetry run ruff format --check src tests \
  && poetry run mypy src && poetry run python bin/check_typing.py \
  && poetry run python bin/check_provenance.py && poetry run codespell
git add -A && git commit -m "feat(ingestion): public META readers for all 22 datasets"
git log --oneline -1
```

---

### Task 6: Docs, catalog, ledger

**Files:**
- Create: `docs/ingestion/meta.md`
- Modify: `mkdocs.yml`, `docs/api.md`, `docs/ingestion/index.md`, root `CLAUDE.md`,
  `docs/backlog/ingestion-meta-download-97_20260715_204524.md`

- [ ] **Step 1: Write the published page** (`docs/ingestion/meta.md`, **pt-BR** — the site's language)

Cover: o que é o META, a tabela dos 22 datasets → classe, o `path_raw`, a **truncagem em 50** e a
regra "o header real é a fonte da ordem e dos nomes longos", e um exemplo:

```python
from filings_cvm import MetaInfMensalCraReader

df_meta = MetaInfMensalCraReader().read()
```

- [ ] **Step 2: Register the page in `mkdocs.yml` `nav:`** under the Leitura/ingestion section —
MkDocs silently omits an unregistered page from the nav.

- [ ] **Step 3: Update `docs/api.md`** with the 22 classes (it is 803 lines / 28 sections; #100
will split it later — do **not** restructure it here).

- [ ] **Step 4: Update the root `CLAUDE.md` catalog** — add the META module to the Layout tree and
note it under the ingestion section.

- [ ] **Step 5: Tick the ledger** — every `- [ ]` in the Escopo section of
`ingestion-meta-download-97_20260715_204524.md`, plus a short "what actually happened" note.
**Correct `23` → `22`** wherever the spec says 23 datasets (CRI ships with the CRI PR).

- [ ] **Step 6: Build the docs strictly**

Run: `poetry run mkdocs build --strict`
Expected: exit 0, no warnings.

- [ ] **Step 7: Commit + push + PR**

```bash
git add -A && git commit -m "docs: document the public META module"
git log --oneline -1
git push -u origin feat/ingestion-meta-download-97
```
Then open the PR with `Closes #97`, filling **every** section of the template (Description /
Changes Made / Testing / Documentation / Additional Notes) — a hook blocks `gh pr create` otherwise.

- [ ] **Step 8: STOP — wait for the user's review and merge**

Do **not** start the next issue (#108) while this PR is open. After merge: sync `main`, then
release **PATCH 0.25.5** (Test PyPI → verify by install → PyPI → verify), confirming the publish job
ran and was not skipped. ⚠️ This release is the **first real test of the #102 fix**: `Create GitHub
Release` must go green and the tag `v0.25.5` must appear **by itself**, with no
`gh release edit --draft=false`.

---

## Self-Review

**Spec coverage** — every spec item maps to a task: raw+parsed → T2/T4 · one class per dataset over
a private base → T4/T5 · dataset-is-a-folder + `meta.py` → T1/T5 · long frame with `section` → T4 ·
no `date_ref` → T4 · base at `ingestion/` root → T4 · one contracts module via factory → T3 ·
English columns / verbatim values → T2 · `.txt` for FIE/MEDIDAS → T5 table · `meta_` source-key
prefix → T3 · real-byte fixtures + truncation lock → T2 · two commits → T1 (commit 1), T2–T6
(commit 2 after squash) · docs → T6 · release PATCH → T6 Step 8.

**Corrections applied during review:**
- **23 → 22 datasets.** `INF_MENSAL_CRI` has no readers yet, so a `meta.py` there would create a
  readerless package; it ships with the CRI PR. Noted in T5 and to be fixed in the spec (T6 Step 5).
- **`_section_of` needed `_MEMBER_STEM`.** The first draft returned `inf_mensal_cra_fluxo_caixa`
  because the repeated stem varies per dataset — and `meta_cad_fi.zip`'s members are
  `cad_fi_hist_*`, so it cannot be derived from the filename. Declared by the subclass instead.
- **Type consistency checked**: `parse_meta_blocks(str_text, str_section)` is called with exactly
  that signature in T4; `_META_URL`/`_CONTRACT`/`_MEMBER_STEM`/`_RETRY_POLICY` are declared in T4
  and used with the same names in T5; `META_COLUMNS`/`_meta_contract` defined in T3 and consumed in
  T3/T5.

**Known risk carried deliberately:** the 22 URLs are hardcoded. That is the design (the filenames
are irregular and `meta_cad_fi.txt`/`.zip` are different datasets), and T5 Step 9 live-verifies
them against the portal. #98's weekly drift job is what catches a URL that later 404s.
