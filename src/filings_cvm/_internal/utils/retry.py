"""Retry-with-backoff decorator for transient I/O failures.

A peripheral network call (e.g. a file-download seam) can fail **transiently** — a
slow endpoint, a dropped connection, a 5xx, an upstream rate-limit. Rather than give up
on the first error, the decorated call is retried a configurable number of times with a
growing wait between attempts, so a brief outage no longer breaks the run. The wait
follows a selectable **strategy** — ``"exponential"`` (default: ``base`` doubling each
retry), ``"linear"`` (``base`` growing by ``base`` each retry), or ``"constant"`` (a
fixed ``base``) — and can be clamped with an optional per-wait cap (``float_max_wait_s``)
so an exponential schedule cannot balloon without bound. **Deterministic** failures (e.g.
a bad URL or an SSRF-blocked host → ``ValueError``) are NOT retried — only the configured
transient exception types are, so a permanent error still fails fast. Each retry is logged
at ``warning``.

This is a generic decorator (it wraps any callable without inspecting its values), so
its inner closures are typed with :class:`typing.ParamSpec` rather than ``Any`` — and the
runtime ``@type_checker`` is applied to the public factory only, never to the generic inner
``wrapper`` (whose ``*args``/``**kwargs`` are intentionally opaque).
"""

from __future__ import annotations

from collections.abc import Callable
import functools
import logging
import time
from typing import TYPE_CHECKING, ParamSpec, TypeVar


# Runtime type-checking engine — layout-agnostic (utils.typing in MVC, chassis.typing in
# DDD; always injected, just at different paths). mypy reads the single TYPE_CHECKING
# import (no redefinition); at runtime the try/except picks whichever layout shipped.
if TYPE_CHECKING:
	from filings_cvm._internal.utils.typing import TypeChecker, type_checker
else:
	try:
		from filings_cvm._internal.utils.typing import TypeChecker, type_checker
	except ModuleNotFoundError:  # DDD ships the engine as chassis.typing
		from filings_cvm._internal.utils.typing import TypeChecker, type_checker


_P = ParamSpec("_P")
_R = TypeVar("_R")

_DEFAULT_MAX_ATTEMPTS: int = 3
_DEFAULT_BASE_WAIT_S: float = 2.0
_DEFAULT_FACTOR: float = 2.0
_DEFAULT_STRATEGY: str = "exponential"
# Wait-schedule dispatch: strategy name -> (base, factor, attempt) -> seconds before the retry.
# The dict IS the branch — selecting a schedule is a lookup, not an if/elif/else chain — and it
# is the single source of the valid strategy names (``_STRATEGIES`` is derived from its keys).
_STRATEGY_WAITS: dict[str, Callable[[float, float, int], float]] = {
	"exponential": lambda base, factor, attempt: base * factor ** (attempt - 1),
	"linear": lambda base, factor, attempt: base * attempt,
	"constant": lambda base, factor, attempt: base,
}
_STRATEGIES: frozenset[str] = frozenset(_STRATEGY_WAITS)
_LOGGER: logging.Logger = logging.getLogger(__name__)


@type_checker
def _compute_backoff_wait(
	str_strategy: str,
	float_base_wait_s: float,
	float_factor: float,
	int_attempt: int,
	float_max_wait_s: float | None,
) -> float:
	"""Return the seconds to wait before the retry that follows ``int_attempt``.

	``int_attempt`` is the 1-indexed number of the attempt that just failed, so the first
	retry (``int_attempt == 1``) waits ``float_base_wait_s`` under every strategy; later
	retries diverge by strategy. The result is clamped to ``float_max_wait_s`` when that cap
	is set, so an exponential schedule cannot grow without bound.

	Parameters
	----------
	str_strategy : str
		One of ``"exponential"`` (``base * factor ** (attempt - 1)``), ``"linear"``
		(``base * attempt``), or ``"constant"`` (``base``).
	float_base_wait_s : float
		The base wait, in seconds — the wait before the first retry under every strategy.
	float_factor : float
		The exponential growth factor; used only by the ``"exponential"`` strategy.
	int_attempt : int
		The 1-indexed number of the attempt that just failed.
	float_max_wait_s : float or None
		Optional upper bound applied to the computed wait; ``None`` leaves it uncapped.

	Returns
	-------
	float
		The (optionally capped) number of seconds to wait before the next attempt.
	"""
	# str_strategy is validated by the factory, so the lookup always hits.
	float_wait = _STRATEGY_WAITS[str_strategy](float_base_wait_s, float_factor, int_attempt)
	if float_max_wait_s is None:
		return float_wait
	return min(float_wait, float_max_wait_s)


class LogEmitter(metaclass=TypeChecker):
	"""Sink the retry decorator writes each retry warning to (injectable).

	The default implementation forwards to a standard-library :class:`logging.Logger`. A
	caller that wants richer routing (e.g. the project's ``utils.logs`` formatting) injects
	its own :class:`LogEmitter` subclass — ``retry.py`` then depends only on the
	``log_message`` method, never on any concrete logging module, so the seam stays
	dependency-free for a distributable library.
	"""

	def __init__(self, cls_logger: logging.Logger | None = None) -> None:
		"""Build an emitter over ``cls_logger`` (defaults to this module's logger).

		Parameters
		----------
		cls_logger : logging.Logger, optional
			The standard-library logger to write to; defaults to the logger for this module.
		"""
		self._cls_logger = cls_logger if cls_logger is not None else _LOGGER

	def log_message(self, str_message: str, str_level: str) -> None:
		"""Emit ``str_message`` at the named level.

		Parameters
		----------
		str_message : str
			The message to log.
		str_level : str
			The level name (e.g. ``"warning"``, ``"info"``); falls back to ``warning`` when
			the underlying logger has no method of that name.
		"""
		fn_emit = getattr(self._cls_logger, str_level.lower(), self._cls_logger.warning)
		fn_emit(str_message)


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
	if int_max_attempts < 1:
		raise ValueError("int_max_attempts must be >= 1")
	if str_strategy not in _STRATEGIES:
		raise ValueError(
			f"str_strategy must be one of {sorted(_STRATEGIES)}, got {str_strategy!r}"
		)
	cls_emitter: LogEmitter = cls_logger if cls_logger is not None else LogEmitter()

	def decorator(fn: Callable[_P, _R]) -> Callable[_P, _R]:
		"""Wrap ``fn`` so each call is retried with exponential backoff.

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
			int_attempt = 0
			while True:
				int_attempt += 1
				try:
					return fn(*args, **kwargs)
				except tuple_exceptions as cls_err:
					if int_attempt >= int_max_attempts:
						raise
					float_wait = _compute_backoff_wait(
						str_strategy,
						float_base_wait_s,
						float_factor,
						int_attempt,
						float_max_wait_s,
					)
					cls_emitter.log_message(
						f"{str_fn_name} failed (attempt {int_attempt}/{int_max_attempts}): "
						f"{cls_err}. Retrying in {float_wait:.1f}s.",
						"warning",
					)
					time.sleep(float_wait)

		return wrapper

	return decorator
