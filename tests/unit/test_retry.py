"""Unit tests for the retry-with-backoff decorator and its strategy schedules.

Waits are captured by monkeypatching ``time.sleep`` so the assertions run instantly and
verify the exact backoff schedule per strategy — never a real sleep.
"""

from __future__ import annotations

import pytest

from filings_cvm._internal.utils.retry import RetryPolicy, call_with_backoff, retry_with_backoff
from filings_cvm._internal.utils.retry._schedule import _compute_backoff_wait


class _Flaky:
	"""Callable that raises ``OSError`` a fixed number of times, then returns a sentinel."""

	def __init__(self, int_failures: int) -> None:
		self.int_failures = int_failures
		self.int_calls = 0

	def __call__(self) -> str:
		self.int_calls += 1
		if self.int_calls <= self.int_failures:
			raise OSError("transient")
		return "ok"


@pytest.fixture
def list_waits(monkeypatch: pytest.MonkeyPatch) -> list[float]:
	"""Capture every ``time.sleep`` duration the decorator requests, without sleeping."""
	list_captured: list[float] = []
	monkeypatch.setattr(
		"filings_cvm._internal.utils.retry.backoff.time.sleep",
		lambda float_s: list_captured.append(float_s),
	)
	return list_captured


def test_exponential_is_the_default_schedule(list_waits: list[float]) -> None:
	"""Default strategy doubles the wait each retry: base, base*factor, ..."""
	fn = retry_with_backoff(int_max_attempts=4, float_base_wait_s=1.0, float_factor=2.0)(
		_Flaky(int_failures=3)
	)
	assert fn() == "ok"
	assert list_waits == [1.0, 2.0, 4.0]


def test_linear_grows_by_base_each_retry(list_waits: list[float]) -> None:
	"""Linear strategy waits base * attempt: base, 2*base, 3*base."""
	fn = retry_with_backoff(int_max_attempts=4, float_base_wait_s=1.0, str_strategy="linear")(
		_Flaky(int_failures=3)
	)
	assert fn() == "ok"
	assert list_waits == [1.0, 2.0, 3.0]


def test_constant_keeps_the_wait_fixed(list_waits: list[float]) -> None:
	"""Constant strategy waits base every time, regardless of attempt."""
	fn = retry_with_backoff(int_max_attempts=4, float_base_wait_s=1.5, str_strategy="constant")(
		_Flaky(int_failures=3)
	)
	assert fn() == "ok"
	assert list_waits == [1.5, 1.5, 1.5]


def test_max_wait_caps_the_exponential_schedule(list_waits: list[float]) -> None:
	"""An exponential schedule is clamped to float_max_wait_s once it would exceed it."""
	fn = retry_with_backoff(
		int_max_attempts=5, float_base_wait_s=1.0, float_factor=2.0, float_max_wait_s=3.0
	)(_Flaky(int_failures=4))
	assert fn() == "ok"
	assert list_waits == [1.0, 2.0, 3.0, 3.0]


def test_non_transient_exception_is_not_retried(list_waits: list[float]) -> None:
	"""An exception outside tuple_exceptions propagates on the first failure, no wait."""

	def _raise_value_error() -> None:
		raise ValueError("permanent")

	fn = retry_with_backoff(int_max_attempts=3, tuple_exceptions=(OSError,))(_raise_value_error)
	with pytest.raises(ValueError, match="permanent"):
		fn()
	assert list_waits == []


def test_exhausted_attempts_reraise_the_last_error(list_waits: list[float]) -> None:
	"""When every attempt fails, the final transient exception is re-raised."""
	fn = retry_with_backoff(int_max_attempts=2, float_base_wait_s=0.5)(_Flaky(int_failures=5))
	with pytest.raises(OSError, match="transient"):
		fn()
	assert list_waits == [0.5]


def test_invalid_max_attempts_rejected() -> None:
	"""A max-attempts below 1 is a configuration error, raised at decoration time."""
	with pytest.raises(ValueError, match="int_max_attempts must be >= 1"):
		retry_with_backoff(int_max_attempts=0)


def test_unknown_strategy_rejected() -> None:
	"""An unknown strategy name is a configuration error, raised at decoration time."""
	with pytest.raises(ValueError, match="str_strategy must be one of"):
		retry_with_backoff(str_strategy="fibonacci")


def test_compute_backoff_wait_is_uncapped_when_no_max() -> None:
	"""The helper leaves the schedule uncapped when float_max_wait_s is None."""
	assert _compute_backoff_wait("exponential", 2.0, 3.0, 3, None) == 18.0
	assert _compute_backoff_wait("linear", 2.0, 3.0, 3, None) == 6.0
	assert _compute_backoff_wait("constant", 2.0, 3.0, 3, None) == 2.0


def test_retry_policy_rejects_bad_attempts() -> None:
	"""A RetryPolicy with < 1 attempt fails fast at construction, not mid-retry."""
	with pytest.raises(ValueError, match="int_max_attempts must be >= 1"):
		RetryPolicy(int_max_attempts=0)


def test_retry_policy_rejects_unknown_strategy() -> None:
	"""A RetryPolicy with an unknown strategy fails fast at construction."""
	with pytest.raises(ValueError, match="str_strategy must be one of"):
		RetryPolicy(str_strategy="fibonacci")


def test_call_with_backoff_retries_then_succeeds(list_waits: list[float]) -> None:
	"""The imperative executor retries a transient failure and returns fn's result."""
	cls_flaky = _Flaky(int_failures=2)
	cls_policy = RetryPolicy(int_max_attempts=4, float_base_wait_s=1.0, str_strategy="linear")
	assert call_with_backoff(cls_flaky, cls_policy) == "ok"
	assert cls_flaky.int_calls == 3
	assert list_waits == [1.0, 2.0]  # linear schedule from the policy


def test_call_with_backoff_reraises_when_exhausted(list_waits: list[float]) -> None:
	"""When every attempt fails, the final transient exception propagates."""
	cls_policy = RetryPolicy(int_max_attempts=2, float_base_wait_s=0.5)
	with pytest.raises(OSError, match="transient"):
		call_with_backoff(_Flaky(int_failures=9), cls_policy)
	assert list_waits == [0.5]
