# CLAUDE.md — `_internal/utils/`

Private helper modules for this library. Everything here ships inside the wheel under the
`_internal/` package but is **not** part of the public API — consumers import the library's
core, never `_internal.utils`.

## Logging → dependency injection, never a hard import

**A distributable library must not hard-wire a logging backend.** Any module here that needs
to log should accept a logger as an **injected collaborator** (with a stdlib default), rather
than `import`ing a concrete logging module (e.g. `logs.py`). That keeps each seam usable on
its own — a consumer can drop it into their project without dragging in this library's logging
choices — and keeps the dependency graph flat.

`logs.py` (the in-repo `CreateLog` / `log_message` helper) is therefore **opt-in** at scaffold
time. Even when present, prefer to inject it rather than import it directly.

### Reference implementation — `retry/log_emitter.py`

`retry/log_emitter.py` is the starting point to copy. It defines a tiny injectable sink and defaults it to
a stdlib-backed one, so nothing is imported unless the caller wants it:

```python
import logging


class LogEmitter(metaclass=TypeChecker):
    """Sink a module writes messages to (injectable; defaults to stdlib logging)."""

    def __init__(self, cls_logger: logging.Logger | None = None) -> None:
        self._cls_logger = cls_logger if cls_logger is not None else logging.getLogger(__name__)

    def log_message(self, str_message: str, str_level: str) -> None:
        fn_emit = getattr(self._cls_logger, str_level.lower(), self._cls_logger.warning)
        fn_emit(str_message)


def do_work(..., cls_logger: LogEmitter | None = None) -> None:
    cls_emitter = cls_logger if cls_logger is not None else LogEmitter()
    ...
    cls_emitter.log_message("something happened", "warning")
```

- **Default = no injection needed.** Calling `do_work(...)` logs to stdlib; no import of
  `logs.py`.
- **Customise by injecting.** A caller that wants this project's `logs.py` formatting subclasses
  `LogEmitter` (or passes a compatible object) and injects it — `do_work` never changes.
- **The contract is the `log_message(str_message, str_level)` method**, nothing more. Keep any
  alternative emitter structurally conformant so swapping backends never touches the seam.

Apply the same shape to any new helper that logs. If you opted `logs.py` in, wrap it in a
`LogEmitter` subclass at the call site — do not re-introduce a module-level `from ... .logs
import log_message`.

## Deliberate deviations from the BlueprintX template (reconciled in #370)

These modules started as template copies and the repo has since diverged on purpose. A
future template sync must not overwrite them blindly; each is a backport candidate or a
repo-specific decision.

- **Typing engine (`typing/`) — own engine, no `beartype`.** The template's engine is a
  thin `beartype` adapter plus `typing/policy.py`. The repo keeps its hand-written
  `validate.py` and adds no dependency: it checks **every** element of a `list[...]`
  (beartype samples one per call, so a bad element is caught only probabilistically),
  accepts `unittest.mock.Mock` where the tests inject doubles, and does not check return
  types, which ~300 readers annotate loosely. Adopting it is a behaviour change across
  all readers, not a refactor.
- **`dtypes.py`** — `_to_decimal` also maps the text `"nan"`/`"none"`/`"<na>"` to NA and
  `apply_dtypes` is a flat loop; the template's `singledispatch` split is a complexity
  refactor with no repo need.
- **`tabular_reader.py`** — keeps `find_*_problems -> list[str]` (no caller reads
  severity), `list_decimal_cols` after `list_date_cols` (positional order callers rely
  on), and omits `ProblemReport`, `bool_full_column` and `decode_positional_payload`
  (no JSON positional-array source here). **Taken:** column-name whitespace stripping.
- **`provenance.py`** — `content_hash` is `"sha256:<hex>"` and `stamp_provenance` resolves
  the package version itself; the template stores bare hex and takes the version as an
  argument. Both are data contracts of the bronze layer, so they stay.
- **`http_downloader.py`** — `download_file(..., retry_policy=)` with a 5-attempt capped
  default tuned for the CVM portal; the template hard-wires a 3-attempt decorator.
- **`raw_workspace.py`** — richer docstring (why bronze retention matters, S3 upgrade path).
- **`br_identifiers.py`, `text.py`, `retry/backoff.py`, `retry/_schedule.py`** —
  behaviour-identical to the template apart from refactors into smaller helpers and the
  `TYPE_CHECKING` type-only stub for `type_checker`/`TypeChecker`; the repo imports the
  engine directly. **Taken:** `RetryPolicy` rejects negative or non-finite waits.
- **`zip_extractor.py`, `logs.py`** — template factors out a `_require_zip` guard and a
  `_close_handlers` helper. Deferred: both lower/raise a ratcheted complexity baseline in
  `bin/quality_baseline.txt`. **Taken:** `find_member` lists the available members.
- **Repo-only modules (keep):** `atomic_write`, `introspection`, `meta_parser`,
  `xml_fields`, `inr_mensal_fields`; `config/ports/{ingestion_reader,submission_writer}`
  replace the template's `example_port`; `config/CLAUDE.md` describes `schemas/`.
- **Template modules not imported** (examples or unused by any reader/writer here):
  `daily_cache`, `regime_adapter`, `regime_registry`, `regime_window`,
  `sidecar_metadata`, `spec_gap_registry`, `xml_reader`, `typing/policy.py`,
  `config/ports/example_port.py`, `main.py`.
