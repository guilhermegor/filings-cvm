"""Backoff wait-schedule math for the retry seam (private).

Holds the strategy dispatch and the per-attempt wait computation the retry loop consumes,
kept apart from the public :class:`~filings_cvm._internal.utils.retry.policy.RetryPolicy` and
the backoff executors so each public class keeps its own module.
"""

from __future__ import annotations

from collections.abc import Callable

from filings_cvm._internal.utils.typing import type_checker


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
