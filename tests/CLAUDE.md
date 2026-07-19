# CLAUDE.md — `tests/`

Guidance for writing tests in this library. The layout mirrors the package:

```
tests/
    conftest.py       # autouse network-block guard (below)
    unit/             # pure logic + I/O mocked at the boundary
    integration/      # real subprocess / real file, no network
    fixtures/         # VERBATIM external bytes — the pinned oracle (below)
```

Mirror the package structure: a reader at `ingestion/securit/doc/inf_mensal_cri/` is tested by
`tests/unit/test_inf_mensal_cri_ingestion.py`. Name tests `test_<unit>_<scenario>_<outcome>`; one
behaviour per test; pytest functions with fixtures, never `unittest.TestCase`.

## Fixtures are the **pinned oracle** — the one thing a test does not author

A contract, its reader, a hand-built fixture, and the test that checks them can only ever **agree
with each other**: they all encode *our* belief about a file. **A wrong contract passes 100% of
tests**, because the tests assert the contract that was written. This is not hypothetical — CRA's 8
members share OTS's section names, and CRI's share CRA's; copying a sibling's contracts would ship
wrong ones with the whole suite green.

The escape is a fixture that comes from the **source, not from us**: the **verbatim header bytes CVM
publishes**, committed under `tests/fixtures/<dataset>/`. Exactly one test compares the contract
against it — the **anti-tautology test**, the only assertion in the file whose expected value we did
not write:

```python
def test_contract_matches_the_published_header(cls):
    str_line = (PATH_FIXTURES / f"inf_mensal_cri_{section}_header.csv").read_text("utf-8").strip()
    assert cls._CONTRACT.tuple_required == tuple(str_line.split(";"))
```

Every *other* test in that file builds its input from `tuple_required`, so it is a tautology; this
one is the oracle. See the lesson `pin-contracts-to-a-source-published-oracle`.

### How to add a fixture

1. **Generate it from the real bytes, never transcribe.** Download the actual artifact and write
   the header line out — a throwaway script, not fingers. Transcribing ~60 columns is exactly where
   the error the fixture exists to catch creeps back in.
2. **Header-only when the data carries PII.** Commit the header line and **no data rows** — CVM
   dumps hold real CPFs/CNPJs (LGPD). A `*_header.csv` is the whole file: one line + trailing `\n`.
3. **Preserve the source encoding.** CVM ships **ISO-8859-1**; META additionally uses **CRLF**.
   Write the fixture in the source's bytes, not re-encoded to UTF-8.
4. **Name it for what it pins:** `tests/fixtures/<dataset>/<dataset>_<section>_header.csv` for a
   header, `tests/fixtures/meta/meta_<dataset>_<section>.txt` for a META block.

### ⚠️ The whitespace hooks must not touch fixtures

`.pre-commit-config.yaml` excludes `^tests/fixtures/` from `trailing-whitespace` and
`end-of-file-fixer`. A byte-exact capture is the oracle; those hooks silently strip trailing
whitespace / normalise CRLF, turning "the bytes CVM published" into "the bytes after our hooks
re-touched them" — and the anti-tautology test would then validate against a fixture we mutated.
**Keep the exclusion when adding a new hook that rewrites file bytes.** (Lesson:
`fixtures-verbatim-exclude-whitespace-hooks`.)

### The three fixture sets today (worked examples)

- `tests/fixtures/inf_mensal_cra/` — 8 `*_header.csv`, the CRA members' verbatim headers.
- `tests/fixtures/inf_mensal_cri/` — 11 `*_header.csv`, the CRI members' verbatim headers.
- `tests/fixtures/meta/` — verbatim ISO-8859-1 META blocks (`Campo:` / `Descrição` / `Tipo Dados`),
  the non-tautological oracle for the META parser.

## No test touches the real network

`conftest.py` installs an **autouse** guard that replaces the socket primitives with versions
raising `NetworkAccessError`, so any reader that reaches a real socket fails loudly instead of
hitting CVM (and risking a ban). Mock the **download boundary** in the reader's own module
(`monkeypatch.setattr("...._base_..._reader.download_file", _fake)`), never the network itself. A
test that genuinely must reach the network opts in with `@pytest.mark.allow_network` — rare, and
never in a unit test.

## Loading a `bin/` script under test

The `bin/` scripts are not an importable package, so their tests load them **by path** with
`importlib.util` (see `test_check_contract_drift.py`, `test_check_portal_completeness.py`):

```python
_PATH = Path(__file__).resolve().parents[2] / "bin" / "check_contract_drift.py"
_SPEC = importlib.util.spec_from_file_location("check_contract_drift", _PATH)
mod = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(mod)
```

Keep the pure decision logic in module-level functions so it is testable without the network the
`main()` seam performs — the whole reason the `check_*` scripts split "compute" from "call GitHub".
