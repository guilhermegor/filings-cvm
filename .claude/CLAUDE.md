# Shared conventions (every BlueprintX skeleton)

This file is the **one source** for the Claude Code guidance every scaffolded project shares.
It ships to a generated project as `.claude/CLAUDE.md`, which Claude Code loads alongside the
root `CLAUDE.md`; the root file keeps only what is specific to that skeleton. Edit conventions
**here**, in `templates/common/CLAUDE.md` — never in a skeleton's root file, where the change
would reach one tier and silently miss the others (blueprintx#549). Sections marked *(Python)*
apply to the Python skeletons only.

## Three boundary rules, each with the test that applies it

The skeleton's own `CLAUDE.md` says WHERE a boundary goes (its layer table). These three say
when one is worth drawing at all, and each is stated as a **test you can run on a decision**
rather than as advice. All three cost real rework in a proving ground before they were written
down.

### 1. The seam knows the vendor; the callers do not

The rule that keeps a dependency swappable is usually mis-stated as *"hide the library"*, and
the naive reading of that does real damage: annotating the boundary with `Any`, erasing the
vendor's type, protects nobody. It removes the type checking and leaves the coupling exactly
where it was.

What actually makes a vendor swappable is narrower: **the seam imports and TYPES the vendor;
the callers import the seam.**

```python
# The seam — utils/http_downloader.py in MVC, chassis/http/http_downloader.py in DDD,
# <package>/_internal/utils/http_downloader.py in a library. It names the vendor, and types it.
import requests

def download_file(str_url: str, path_dest: Path) -> Path: ...

# The caller — any other layer. It names the SEAM, and nothing else.
from utils.http_downloader import download_file
```

> **The test.** On the day the vendor is replaced, how many files change?
> One (the seam) means the boundary held. More than one means it never existed, however much
> the calling code avoided saying the vendor's name.

This is why `pandas` is `annotation_only` rather than banned outright: `-> pd.DataFrame` in a
signature survives no swap and blocks none — it is the vocabulary the layers agreed on.
`pd.read_sql(...)` is a call, and every file copied from the one that makes it inherits it.

### 2. Externalise text only when the destination has a DIFFERENT change cost

"Take the hard-coded text out of the code and put it in a YAML" reads as separation of
concerns and often is not. The question is never *whether the thing is text*. It is whether
the destination file **changes at a different rate, and by different people.**

A tracked YAML that only the author of the calling code ever edits has separated nothing: it
doubled the number of files that must change together, and added a parse step and a schema to
keep in sync.

> **The test.** Name the person who edits the new file WITHOUT touching the code, and name the
> occasion. If you cannot name both, the text belongs where it is used.
>
> Passes: an e-mail template an operations lead rewords at quarter end. Passes: a locale file
> a translator owns. Fails: a dict of column labels only the developer of that reader will
> ever change.

Measured on a 1,672-line e-mail-body module in a proving ground (2026-08-14), where the
externalised copy was edited exclusively alongside the code that read it.

### 3. Derive the boundary from the config that exists; never restate it

A bootstrap or preflight phase that needs to know *which file belongs to which category*
should **derive** that from the configuration already declaring it, rather than repeating the
list. The duplicate looks harmless the day it is written, because the two copies are identical
then. It is noticed only when they differ — and by then the question is which one is right.

```python
# Avoid — a second list that agrees with the first, until it does not.
LIST_REQUIRED = ["cad_fi.csv", "inf_diario.csv"]

# Prefer — the one declaration is the source; membership is derived from it.
LIST_REQUIRED = [cls_contract.str_filename for cls_contract in contracts.ALL]
```

> **The test.** Could the two copies disagree, and would anything fail if they did?
> If they can disagree silently, one of them must be computed from the other. This is the same
> rule `check_codespell_sync.sh` exists to enforce for the two `.codespellrc` files — that
> pair drifted in both directions, and the stale copy was the one shipping to projects.

## Data-handling guardrails (advisory, Python)

When a pipeline or capability merges, overrides, or validates tabular data, these recurring
traps are worth guarding against (apply when relevant — these are advisories, not scaffolded
code):

- **Override layers must re-apply the canonical normaliser.** A substitution/override path
  that bypasses the same unit/code/sign/default normalisation the primary path uses will
  silently emit inconsistent values. Centralise the invariant in ONE normaliser (in a DDD
  layout, a domain value object is a natural home) and call it from every path (primary and
  override alike).
- **Validation rejects sentinel garbage, not just wrong types.** Guard against `"nan"`,
  blank, and out-of-range/wrong-unit values before output — a type check alone passes a
  stringified NaN straight through (see `utils.text.safe_str`).
- **Per-source keyed merge: restrict each partition to the keys it owns before concat.**
  When merging partitions keyed by an id, scope each partition to its own keys first so the
  merge key stays unique and a row from one source never overwrites another's.
- **A time-scoped override input carries a required reference-month and is filtered to the
  run's competency.** A "backdoor" file that forces records into a *specific* run must declare
  a reference-month column (make it contract-required, so a file lacking it is reproved at the
  entry boundary — notify, skip the override, don't abort the run) and be filtered to the
  current month where it is read (accept `06/2026` / `2026-06` / `202606` / a datetime cell;
  log the dropped count). Otherwise last period's rows silently re-apply to the wrong target.
- **Canonicalise a join key through the SAME helper on BOTH sides, at the read boundary.**
  When matching frames on a human/regulatory id (CNPJ/CPF/code), normalise the key with one
  canonical helper (e.g. `utils.br_identifiers.unmask_cnpj`) as each frame enters memory —
  never compare a `.map(unmask_*)` series against a bare `.astype(str)` one. A lossy store
  (Excel coercing a 14-digit string to a number, a sqlite TEXT round-trip) drops a leading
  zero, so one side keys on 13 digits and the other on 14 → the join misses *exactly* the
  leading-zero rows, silently (no error, just no match — an approved override dropped).
  Canonicalise on read (healing the persisted store too) and build a normalised key for both
  operands of every merge/overlay.
- **A filter that REMOVES rows from a deliverable needs a kill switch, not a constant**
  (blueprintx#161). Measured incident: a hard-coded exclusion silently dropped whole fund
  classes from a regulatory delivery; a counterparty had to ask for the missing fund before
  anyone noticed. Sub-delivering costs money per record per day, over-delivering costs
  nothing — so the rule ships as an env-var kill switch with a SAFE-side default (an unset
  *or mistyped* value both resolve to "do not exclude"), and the filter call always returns
  the measured price (rows before/after/dropped), never only the filtered frame. The MVC
  skeletons ship a runnable reference, `src/model/scope_filter_example.py` (full rationale in
  that leaf's `CLAUDE.md`), with the variable in `.env.example`.

## Naming conventions (Python)

Every variable name starts with a type prefix. No bare names, no underscore prefixes for instances.

| Prefix | Type | Prefix | Type |
|--------|------|--------|------|
| `cls_` | class instance | `list_` | `list` |
| `float_` | `float` | `tuple_` | `tuple` |
| `decimal_` | `Decimal` | `dict_` | `dict` (parsed) |
| `int_` | `int` | `json_` | raw JSON string |
| `str_` | `str` | `df_` | `pd.DataFrame` |
| `bool_` | `bool` (or `is_`/`has_`/`can_`) | `series_` | `pd.Series` |
| `dt_` | `datetime`/`date` | `arr_` | `np.ndarray` |
| `path_` | `pathlib.Path` | `bytes_` | `bytes` |
| `fn_` | `Callable` (standalone vars only — not class methods/attrs) | `re_` | `re.Pattern` |

`json_` = raw unparsed JSON string; `dict_` = already a Python dict.

## File naming conventions

Output files (exports, backups, model artifacts, reports): `name-like-this_YYYYMMDD_HHMMSS.<ext>`
- Name: kebab-case (dashes, no underscores)
- Timestamp: `YYYYMMDD_HHMMSS` (uppercase, sortable)
- Exception — joblib artifacts: `name-like-this_YYYYMMDD_HHMMSS_{sha256_prefix8}.joblib`

## Tooling (Python, copied from `templates/python-common/`)

- **Ruff**: linter + formatter. Line-length 99, 4-space indent, double quotes, NumPy docstrings. Config: `ruff.toml`.
- **Pre-commit**: ruff, pydocstyle (DAR/D412/D417), codespell, commitizen, gitlint, hadolint, unit + integration tests, coverage badge.
- **Tests**: `pytest` — `poe unit_tests`. Write pytest-style functions with fixtures, not `unittest.TestCase`.
- **Poe tasks** (`poe_tasks.toml`): `init`, `venv`, `update_venv`, `precommit`, `lint`, `unit_tests`, `integration_tests`, `run`.

## Runtime type-checking (Python)

The engine lives at `utils/typing` in MVC, `chassis/typing` in DDD and `_internal/utils/typing`
in a library; the MVC spelling is used below. Reach for `from utils.typing import TypeChecker,
type_checker` to validate a call's arguments against their annotations at runtime —
`metaclass=TypeChecker` on a class (or `ProtocolTypeCheckerMeta` for a `Protocol` port),
`@type_checker` on a module-level function. This complements, not replaces, the static gate
(ruff `ANN` + mypy). The engine is **backed by `beartype`** (`validate.py` is a thin adapter
over it, not a hand-rolled checker — do not reimplement it). Two policies via `BeartypeConf`:
violations raise `TypeError` (beartype's own exception is not a `TypeError` subclass), and
`bool` is **not** accepted where `int` is annotated. These decisions are **knobs in
`utils/typing/policy.py`** (the editable policy seam) — flip one there, never in `validate.py`;
⚠️ `VIOLATION_TYPE` is **load-bearing** (keep it `TypeError`, or downstream
`pytest.raises(TypeError)` breaks). Test note: a bare `Mock` fails a typed parameter — use
`Mock(spec=...)`; and container checks are **sampled O(1)** (one element per call), not
exhaustive. `utils/typing/` is the one place `Any` is the honest signature (it inspects values
of any type) and is ANN401-exempt. The package ships from
`templates/python-common/optional/typing/`.

The shared `utils/` helpers (`dtypes`, `br_identifiers`, `decimals`, `loggers`, `text`,
`paths`, `signatures`, `dates`, …) carry the runtime checker too — every function is
`@type_checker` and every class uses `metaclass=TypeChecker` (Protocol ports use
`metaclass=ProtocolTypeCheckerMeta`). There is **no by-layer exemption**. Because those files
ship to every tier, they import the engine through a layout-agnostic shim — `try: from
utils.typing import … except ModuleNotFoundError: from chassis.typing import …` — so the same
source resolves in MVC (`utils.typing`) and DDD (`chassis.typing`). The only exclusions are
the `utils/typing/` engine itself and classes whose own metaclass would conflict (SQLAlchemy
declarative models).

## Project memory — thin root, lazy leaves (never `@`-imports)

The root `CLAUDE.md` is a **thin index**: keep it scannable (what the project is, its structure,
the few commands that matter, the non-negotiable rules) and push domain detail into **leaf**
`CLAUDE.md` files that load **lazily** — a nested `CLAUDE.md` loads on directory entry; a
`rules/*.md` with `paths:` frontmatter loads on file touch. Every skeleton already ships leaves
(`src/*/CLAUDE.md`, `docs/CLAUDE.md`, `tests/CLAUDE.md`, `_internal/*/CLAUDE.md`, …).

**Never** wire those leaves through a `@.claude/<topic>.md` table. `@path` is an **eager import** —
Claude Code inlines every referenced file at session start, so a "Documentation" table of `@`-refs
loads *all* of them on *every* session: the structure looks lazy and behaves eager. Nested
`CLAUDE.md` and `paths:`-scoped rules are the only mechanisms that actually defer the load.

Corollary: a prose rule here cannot guard what `settings.json` / hooks auto-approve — put hard
guardrails in permissions or hooks, and keep `CLAUDE.md` for what config cannot express.
