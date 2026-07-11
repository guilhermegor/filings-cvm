"""Unit tests for the per-module retry-policy standard, across **every** ingestion reader.

The convention (issue #53): every reader declares its own ``_RETRY_POLICY`` class attribute — the
retry/backoff schedule used when the caller passes no ``retry_policy`` — so the patience is
co-located with the dataset and tunable per reader, while a per-instance ``retry_policy=`` still
overrides it.

This module is deliberately **cross-cutting and introspective**: it discovers the readers from the
public API (``filings_cvm.ingestion.__all__``) rather than listing them, so a newly added reader
that forgets ``_RETRY_POLICY`` fails here automatically. That structural guarantee is the point —
it is what makes the pattern a *standard* instead of a convention nine files happen to follow.

No network and no download mocking: the assertions are about constructor state, not ``read()``.
"""

import inspect

import pytest

from filings_cvm import RetryPolicy
from filings_cvm._internal.config.ports.ingestion_reader import IngestionReader
import filings_cvm.ingestion as ingestion


# Every public reader of the library, discovered — never hand-listed (see the module docstring).
ALL_READERS: tuple[type[IngestionReader], ...] = tuple(
	cls
	for cls in (getattr(ingestion, str_name) for str_name in ingestion.__all__)
	if inspect.isclass(cls) and issubclass(cls, IngestionReader)
)


def test_every_public_name_in_all_resolves_to_a_reader() -> None:
	"""``ingestion.__all__`` exports only readers, so the discovery cannot silently shrink."""
	assert len(ALL_READERS) == len(ingestion.__all__)
	assert ALL_READERS, "no readers discovered — the introspection is broken, not the readers"


@pytest.mark.parametrize("cls", ALL_READERS, ids=lambda c: c.__name__)
def test_reader_declares_a_retry_policy(cls: type[IngestionReader]) -> None:
	"""Every reader declares a concrete ``_RETRY_POLICY`` (the per-module default).

	Parameters
	----------
	cls : type[IngestionReader]
		The reader under test.
	"""
	cls_policy = cls._RETRY_POLICY  # type: ignore[attr-defined]

	assert isinstance(cls_policy, RetryPolicy), (
		f"{cls.__name__} must declare a _RETRY_POLICY (per-module retry standard, issue #53)"
	)
	assert cls_policy.int_max_attempts >= 1


@pytest.mark.parametrize("cls", ALL_READERS, ids=lambda c: c.__name__)
def test_reader_accepts_a_retry_policy_argument(cls: type[IngestionReader]) -> None:
	"""Every reader's constructor still exposes ``retry_policy`` for a per-instance override.

	Parameters
	----------
	cls : type[IngestionReader]
		The reader under test.
	"""
	assert "retry_policy" in set(inspect.signature(cls.__init__).parameters)


@pytest.mark.parametrize("cls", ALL_READERS, ids=lambda c: c.__name__)
def test_constructor_defaults_to_the_module_retry_policy(cls: type[IngestionReader]) -> None:
	"""With no ``retry_policy`` passed, the reader uses its own ``_RETRY_POLICY``.

	Parameters
	----------
	cls : type[IngestionReader]
		The reader under test.
	"""
	cls_reader = cls()

	assert cls_reader._retry_policy is cls._RETRY_POLICY  # type: ignore[attr-defined]


@pytest.mark.parametrize("cls", ALL_READERS, ids=lambda c: c.__name__)
def test_per_instance_retry_policy_overrides_the_module_default(
	cls: type[IngestionReader],
) -> None:
	"""A ``retry_policy`` passed to the constructor wins over the reader's ``_RETRY_POLICY``.

	Parameters
	----------
	cls : type[IngestionReader]
		The reader under test.
	"""
	cls_custom = RetryPolicy(int_max_attempts=9, float_base_wait_s=0.5, str_strategy="linear")

	cls_reader = cls(retry_policy=cls_custom)

	assert cls_reader._retry_policy is cls_custom  # type: ignore[attr-defined]
	assert cls_reader._retry_policy is not cls._RETRY_POLICY  # type: ignore[attr-defined]
