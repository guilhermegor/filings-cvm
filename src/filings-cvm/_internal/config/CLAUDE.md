# CLAUDE.md — `_internal/config/`

Private configuration internals for this library. Everything here is **declarative
configuration** — data contracts, not data access — and lives under the `_internal/`
package, so it ships inside the wheel but is **not part of the public API**. Consumers
import the library's core, never `_internal`.

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
