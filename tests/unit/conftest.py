"""Unit-test fixtures shared by the whole ``tests/unit`` tree."""

from __future__ import annotations

from collections.abc import Iterator
import urllib.error

import pytest


_ORIGINAL_INIT = urllib.error.HTTPError.__init__
_LIST_BUILT: list[urllib.error.HTTPError] = []


def _recording_init(self: urllib.error.HTTPError, *args: object, **kwargs: object) -> None:
	"""Build the ``HTTPError`` as usual, then remember it so it can be closed.

	Parameters
	----------
	self : urllib.error.HTTPError
		The instance being initialised.
	*args : object
		Positional arguments for the original ``__init__``.
	**kwargs : object
		Keyword arguments for the original ``__init__``.
	"""
	_ORIGINAL_INIT(self, *args, **kwargs)  # type: ignore[arg-type]
	_LIST_BUILT.append(self)


@pytest.fixture(autouse=True)
def close_http_errors(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
	"""Close every ``HTTPError`` a test builds, so none is cleaned up implicitly.

	An ``HTTPError`` owns a file-like body. Python 3.14 emits a ``ResourceWarning`` when it is
	garbage-collected unclosed, and ``pytest.ini`` promotes that to a failure. A test that only
	raises one to exercise an error path cannot close it itself, so it is closed here.

	Parameters
	----------
	monkeypatch : pytest.MonkeyPatch
		Swaps ``HTTPError.__init__`` for the recording one for the test's duration.

	Yields
	------
	None
		Control returns to the test; recorded errors are closed afterwards.
	"""
	_LIST_BUILT.clear()
	monkeypatch.setattr(urllib.error.HTTPError, "__init__", _recording_init)
	yield
	list(map(urllib.error.HTTPError.close, _LIST_BUILT))
