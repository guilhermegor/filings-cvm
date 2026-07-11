"""``RetryPolicy`` — the immutable retry/backoff configuration value object."""

from __future__ import annotations

from dataclasses import dataclass

from filings_cvm._internal.utils.retry._schedule import (
	_DEFAULT_BASE_WAIT_S,
	_DEFAULT_FACTOR,
	_DEFAULT_MAX_ATTEMPTS,
	_DEFAULT_STRATEGY,
	_STRATEGIES,
)
from filings_cvm._internal.utils.typing import TypeChecker


@dataclass(frozen=True)
class RetryPolicy(metaclass=TypeChecker):
	"""Immutable bundle of the retry/backoff knobs for a transient-failure retry loop.

	Groups "how patient to be" into one value object a caller can build once and pass down
	(e.g. a data reader forwarding it to the download seam), instead of threading five loose
	arguments. The defaults reproduce the module-level defaults, so ``RetryPolicy()`` is the
	same behaviour as an un-configured retry. It carries **only** the retry schedule — the
	per-attempt socket timeout is a download-seam concern and stays with ``download_file``.

	Attributes
	----------
	int_max_attempts : int
		Total attempts (>= 1), by default 3 (one initial try + two retries).
	float_base_wait_s : float
		Wait before the first retry, in seconds, by default 2.0.
	float_factor : float
		Exponential growth factor; used only by the ``"exponential"`` strategy, by default 2.0.
	str_strategy : str
		Backoff schedule: ``"exponential"`` (default), ``"linear"``, or ``"constant"``.
	float_max_wait_s : float or None
		Optional per-wait cap, in seconds; ``None`` (default) leaves the schedule uncapped.
	tuple_exceptions : tuple of type[Exception]
		The transient exception types that trigger a retry, by default ``(OSError,)``.
	"""

	int_max_attempts: int = _DEFAULT_MAX_ATTEMPTS
	float_base_wait_s: float = _DEFAULT_BASE_WAIT_S
	float_factor: float = _DEFAULT_FACTOR
	str_strategy: str = _DEFAULT_STRATEGY
	float_max_wait_s: float | None = None
	tuple_exceptions: tuple[type[Exception], ...] = (OSError,)

	def __post_init__(self) -> None:
		"""Validate the schedule at construction so a bad policy fails fast, not mid-retry.

		Raises
		------
		ValueError
			If ``int_max_attempts`` is less than 1, or ``str_strategy`` is not one of
			``"exponential"``, ``"linear"``, ``"constant"``.
		"""
		if self.int_max_attempts < 1:
			raise ValueError("int_max_attempts must be >= 1")
		if self.str_strategy not in _STRATEGIES:
			raise ValueError(
				f"str_strategy must be one of {sorted(_STRATEGIES)}, got {self.str_strategy!r}"
			)
