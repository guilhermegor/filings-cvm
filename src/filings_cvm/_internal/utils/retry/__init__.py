"""Retry-with-backoff seam for transient I/O failures.

A peripheral network call (e.g. a file-download seam) can fail **transiently** — a slow
endpoint, a dropped connection, a 5xx, an upstream rate-limit. Rather than give up on the
first error, the call is retried a configurable number of times with a growing wait between
attempts (selectable ``"exponential"`` / ``"linear"`` / ``"constant"`` schedule, optional
per-wait cap), so a brief outage no longer breaks the run. Deterministic failures (a bad URL,
an SSRF-blocked host → ``ValueError``) are NOT retried, so a permanent error still fails fast.

Public API (import from this package; the submodule split is an implementation detail):

- :class:`RetryPolicy` — the immutable retry configuration value object.
- :class:`LogEmitter` — the injectable sink each retry warning is written to.
- :func:`call_with_backoff` — imperative executor (retry schedule known at call time).
- :func:`retry_with_backoff` — decorator form (retry schedule fixed at decoration).
"""

from filings_cvm._internal.utils.retry.backoff import call_with_backoff, retry_with_backoff
from filings_cvm._internal.utils.retry.log_emitter import LogEmitter
from filings_cvm._internal.utils.retry.policy import RetryPolicy


__all__ = ["LogEmitter", "RetryPolicy", "call_with_backoff", "retry_with_backoff"]
