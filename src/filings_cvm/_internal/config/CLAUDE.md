# CLAUDE.md — `_internal/config/`

Private **structural declarations** for this library: the *shapes* data must have and the
*interfaces* adapters must implement. This is the counterpart to `_internal/utils/`, which
holds the *machinery* (the runtime engines — `tabular_reader`, `dtypes`, the typing engine).
Everything here lives under `_internal/`, so it ships inside the wheel but is **not part of the
public API**: consumers import the library's core, never `_internal`.

Three sub-packages, one per kind of declaration:

| Sub-package | Declares | Kind |
|---|---|---|
| `contracts/` | the columns an input file (or SQL result) must carry | data shape |
| `schemas/` | the direction-neutral domain models mirroring each XML standard | data shape |
| `ports/` | the behavioural interface every adapter of a macro-section implements | interface |

`contracts/` and `schemas/` are pure declarations; `ports/` declares *behaviour* (an ABC), which
is why it sits beside them rather than in `utils/` — all three answer "what shape/contract must
this conform to?", while `utils/` answers "how is it done?".

## The `contracts/` sub-package

A `FileContract` declares the shape an input file (or SQL result) must have: which columns
must be present (`tuple_required`) and which must hold at least one valid CNPJ
(`tuple_cnpj_cols`). It is a **declaration**, not a validator — the validation engine lives
in `_internal/utils/tabular_reader.py` (`read_table` / `read_query` raise `ContractError`
on a violation before types are applied).

- **One contract per file** (`cadastro.py`, `orders.py`, …): a module docstring plus a
  single `FileContract` constant. New input → new file.
- `contracts/__init__.py` re-exports every contract **and** the machinery
  (`FileContract`, `find_file_problems` from `_internal.utils.tabular_reader`), so callers
  use one import: `from <pkg>._internal.config.contracts import EXAMPLE_SOURCE`.
- A contract that constrains nothing is still explicit: `FileContract(name, key, (), ())`.
- **`contracts/` is the ONLY place a `FileContract` is constructed** — statically enforced
  by ruff (`TID251`). Loaders import the instances; they never build one inline.

`EXAMPLE_SOURCE` is a reference instance — copy `example_source.py` per real source and
delete the example once your own contracts exist. Drop this whole sub-package if your
library never reads tabular inputs.

## The `schemas/` sub-package

A schema is a **direction-neutral** Pydantic model mirroring one XML standard — one file per
standard (`informe_diario.py` → the Informe Diário model). Both macro-sections import the same
schema: `submission/` fills and serialises it to XML; where an `ingestion/` reader parses that
*same* XML back, it deserialises into it too.

**Crucial boundary:** a schema mirrors the **submission XML**. An `ingestion` reader of a CVM
**open-data CSV** consumes a *different artifact* of the same standard, so it declares its own
`FileContract` in `contracts/` rather than reusing the schema. Schema ↔ XML; FileContract ↔
flat tabular dump. Reaching for a submission schema to type an open-data CSV is the mistake this
note exists to prevent.

Pydantic owns its metaclass and validates at construction, so schema models are the one place
in `src/` that must **not** carry a `TypeChecker` metaclass (see the root `CLAUDE.md`).

## The `ports/` sub-package

A **port** is the private behavioural ABC (hexagonal ports-and-adapters) that every class of a
macro-section implements — `SubmissionWriter[TDoc]` exposing `export(doc, output_path)`,
`IngestionReader` exposing `read() -> pd.DataFrame`. One port per file, declared with a checker
metaclass (`ABCTypeCheckerMeta`); concrete adapters inherit the port and its metaclass (never
redeclare it).

Ports stay **private** — never in a public `__all__`. Consumers import the concrete
writers/readers (the adapters), never the port. The port pins *behaviour*, so the constructor
conventions each adapter follows (e.g. an ingestion reader's optional `path_raw`) live in the
port's docstring as prose, not as enforced signature.

---

**Opt-in tier.** `schemas/` and `ports/` earn their place only once a library grows **two
macro-sections over a shared domain** (here `submission/` ⇄ `ingestion/`). A single-purpose
library should carry neither — an interface with one implementation is over-abstraction. Drop
`contracts/` too if the library never reads tabular inputs.
