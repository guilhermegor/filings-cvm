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

### Reference implementation — `retry.py`

`retry.py` is the starting point to copy. It defines a tiny injectable sink and defaults it to
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
