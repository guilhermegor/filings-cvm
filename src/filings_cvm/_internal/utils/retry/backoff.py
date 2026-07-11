"""Retry executors for transient I/O failures — the imperative and decorator forms.

:func:`call_with_backoff` runs a zero-argument callable under a :class:`RetryPolicy`;
:func:`retry_with_backoff` is the decorator twin that builds a policy from keyword arguments
and delegates to it. Both retry only the policy's transient exception types (a deterministic
error propagates on the first failure) and log each retry at ``warning``.

The decorator is generic (it wraps any callable without inspecting its values), so its inner
closures are typed with :class:`typing.ParamSpec` rather than ``Any`` — and the runtime
``@type_checker`` is applied to the public callables only, never to the generic inner
``wrapper`` (whose ``*args``/``**kwargs`` are intentionally opaque).
"""

from __future__ import annotations

from collections.abc import Callable
import functools
import time
from typing import ParamSpec, TypeVar

from filings_cvm._internal.utils.retry._schedule import (
	_DEFAULT_BASE_WAIT_S,
	_DEFAULT_FACTOR,
	_DEFAULT_MAX_ATTEMPTS,
	_DEFAULT_STRATEGY,
	_compute_backoff_wait,
)
from filings_cvm._internal.utils.retry.log_emitter import LogEmitter
from filings_cvm._internal.utils.retry.policy import RetryPolicy
from filings_cvm._internal.utils.typing import type_checker


_P = ParamSpec("_P")
_R = TypeVar("_R")


@type_checker
def call_with_backoff(
	fn: Callable[[], _R],
	cls_policy: RetryPolicy | None = None,
	cls_logger: LogEmitter | None = None,
	str_label: str | None = None,
) -> _R:
	"""Call the zero-argument ``fn``, retrying transient failures per ``cls_policy``.

	The imperative twin of :func:`retry_with_backoff` (which delegates here): use it when the
	retry schedule is only known at call time — e.g. a download seam given a caller-supplied
	:class:`RetryPolicy` — rather than fixed at decoration. ``fn`` is attempted up to
	``cls_policy.int_max_attempts`` times; a failure raising one of
	``cls_policy.tuple_exceptions`` (with attempts remaining) waits per the policy's schedule,
	then retries. Any other exception, and the final attempt's exception, propagate unchanged.

	Parameters
	----------
	fn : Callable[[], _R]
		The zero-argument callable to run (wrap arguments in a ``lambda``/``partial``).
	cls_policy : RetryPolicy, optional
		The retry schedule; by default a :class:`RetryPolicy` with the module defaults.
	cls_logger : LogEmitter, optional
		Sink each retry warning is written to; by default a stdlib-logger-backed
		:class:`LogEmitter`.
	str_label : str, optional
		Name used in the retry log line; by default ``fn``'s ``__name__`` (a ``lambda`` shows as
		``"<lambda>"``, so pass the wrapped callable's name to keep the log meaningful).

	Returns
	-------
	_R
		``fn``'s return value on the first successful attempt.
	"""
	cls_pol: RetryPolicy = cls_policy if cls_policy is not None else RetryPolicy()
	cls_emitter: LogEmitter = cls_logger if cls_logger is not None else LogEmitter()
	str_name = str_label if str_label is not None else getattr(fn, "__name__", type(fn).__name__)
	int_attempt = 0
	while True:
		int_attempt += 1
		try:
			return fn()
		except cls_pol.tuple_exceptions as cls_err:
			if int_attempt >= cls_pol.int_max_attempts:
				raise
			float_wait = _compute_backoff_wait(
				cls_pol.str_strategy,
				cls_pol.float_base_wait_s,
				cls_pol.float_factor,
				int_attempt,
				cls_pol.float_max_wait_s,
			)
			cls_emitter.log_message(
				f"{str_name} failed (attempt {int_attempt}/{cls_pol.int_max_attempts}): "
				f"{cls_err}. Retrying in {float_wait:.1f}s.",
				"warning",
			)
			time.sleep(float_wait)


@type_checker
def retry_with_backoff(
	int_max_attempts: int = _DEFAULT_MAX_ATTEMPTS,
	float_base_wait_s: float = _DEFAULT_BASE_WAIT_S,
	float_factor: float = _DEFAULT_FACTOR,
	str_strategy: str = _DEFAULT_STRATEGY,
	float_max_wait_s: float | None = None,
	tuple_exceptions: tuple[type[Exception], ...] = (OSError,),
	cls_logger: LogEmitter | None = None,
) -> Callable[[Callable[_P, _R]], Callable[_P, _R]]:
	"""Build a decorator that retries a callable with a selectable backoff strategy.

	The decorated callable is attempted up to ``int_max_attempts`` times. After a failure
	raising one of ``tuple_exceptions`` (and when attempts remain), it waits a number of
	seconds set by ``str_strategy`` — ``"exponential"``
	(``float_base_wait_s * float_factor ** (attempt - 1)``), ``"linear"``
	(``float_base_wait_s * attempt``), or ``"constant"`` (``float_base_wait_s``) — optionally
	clamped to ``float_max_wait_s``, then tries again. Every strategy waits ``float_base_wait_s``
	before the first retry. An exception NOT in ``tuple_exceptions`` propagates immediately (no
	retry), and the last attempt's exception is re-raised unchanged.

	Parameters
	----------
	int_max_attempts : int, optional
		Total number of attempts (>= 1), by default 3 (one initial try + two retries).
	float_base_wait_s : float, optional
		Wait before the first retry, in seconds, by default 2.0.
	float_factor : float, optional
		Exponential growth factor of the wait between retries, by default 2.0. Used only by the
		``"exponential"`` strategy.
	str_strategy : str, optional
		Backoff schedule: ``"exponential"`` (default), ``"linear"``, or ``"constant"``.
	float_max_wait_s : float or None, optional
		Optional upper bound applied to each computed wait, in seconds; ``None`` (default) leaves
		the schedule uncapped.
	tuple_exceptions : tuple of type[Exception], optional
		The transient exception types that trigger a retry, by default ``(OSError,)``.
	cls_logger : LogEmitter, optional
		Sink each retry warning is written to; by default a stdlib-logger-backed
		:class:`LogEmitter`. Inject a subclass to route warnings elsewhere.

	Returns
	-------
	Callable[[Callable[_P, _R]], Callable[_P, _R]]
		A decorator wrapping the target callable with the retry/backoff behaviour.

	Raises
	------
	ValueError
		If ``int_max_attempts`` is less than 1, or ``str_strategy`` is not one of
		``"exponential"``, ``"linear"``, ``"constant"``.
	"""
	# Constructing the policy validates the attempts count and the strategy name for us.
	cls_policy = RetryPolicy(
		int_max_attempts=int_max_attempts,
		float_base_wait_s=float_base_wait_s,
		float_factor=float_factor,
		str_strategy=str_strategy,
		float_max_wait_s=float_max_wait_s,
		tuple_exceptions=tuple_exceptions,
	)

	def decorator(fn: Callable[_P, _R]) -> Callable[_P, _R]:
		"""Wrap ``fn`` so each call is retried with the configured backoff schedule.

		Parameters
		----------
		fn : Callable[_P, _R]
			The target callable to make retryable.

		Returns
		-------
		Callable[_P, _R]
			The wrapped callable with the retry/backoff behaviour.
		"""
		# A plain function has __name__; a callable instance may not — fall back to its type.
		str_fn_name = getattr(fn, "__name__", type(fn).__name__)

		@functools.wraps(fn)
		def wrapper(*args: _P.args, **kwargs: _P.kwargs) -> _R:
			"""Call the wrapped callable, retrying transient failures with backoff.

			Parameters
			----------
			*args : _P.args
				Positional arguments forwarded to the wrapped callable.
			**kwargs : _P.kwargs
				Keyword arguments forwarded to the wrapped callable.

			Returns
			-------
			_R
				The wrapped callable's return value on the first successful attempt.

			Raises
			------
			Exception
				Re-raises the wrapped callable's own exception once the attempts are
				exhausted (only the configured transient types are retried; any other
				exception propagates immediately on the first failure).
			"""
			return call_with_backoff(
				lambda: fn(*args, **kwargs), cls_policy, cls_logger, str_fn_name
			)

		return wrapper

	return decorator
