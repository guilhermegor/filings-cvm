"""Test-wide guards.

**No test may touch the real network.** Every reader in this library downloads from CVM's
open-data portal, which throttles and can temporarily ban an over-eager client — so a test that
forgets to mock :func:`download_file` would hammer a live public service (and, run in CI on every
push, do it from many IPs at once). The project rule is "mock at the boundary"; this file makes
that rule **structural** instead of a convention every future test has to remember.

The guard replaces the socket primitives with versions that raise :class:`NetworkAccessError`, so
any *real* connection attempt fails loudly and names the test that made it. Mocked reads are
unaffected — they never reach a socket.

A test that genuinely needs the wire (there are none today) opts out explicitly::

    @pytest.mark.allow_network
    def test_something_against_the_live_portal() -> None: ...

which is deliberately noisy: it shows up in a diff and has to be justified in review.
"""

from __future__ import annotations

from collections.abc import Iterator
from functools import partial
import socket
from typing import NoReturn

import pytest


class NetworkAccessError(RuntimeError):
	"""Raised when a test attempts a real network connection.

	Mock the I/O boundary — for the readers that is
	``filings_cvm._internal.utils.http_downloader.download_file``, patched where the module under
	test imported it. See any ``tests/unit/test_*_ingestion.py`` for the pattern.
	"""


_socket_real = socket.socket
_create_connection_real = socket.create_connection
_getaddrinfo_real = socket.getaddrinfo


def _blocked(*args: object, **kwargs: object) -> NoReturn:
	"""Raise :class:`NetworkAccessError`, naming what the test tried to reach.

	Parameters
	----------
	*args : object
		Whatever the blocked socket primitive was called with; the first is usually the address.
	**kwargs : object
		Ignored; accepted so the signature matches every primitive replaced.

	Raises
	------
	NetworkAccessError
		Always.
	"""
	raise NetworkAccessError(
		f"A test tried to reach the network ({args[:1] or 'unknown target'}). "
		"Mock the I/O boundary (download_file) instead — hitting CVM's portal from the test "
		"suite risks a rate-limit ban. Use @pytest.mark.allow_network to opt out deliberately."
	)


class _BlockedSocket(socket.socket):
	"""A socket that refuses to connect anywhere."""

	def connect(self, *args: object, **kwargs: object) -> NoReturn:
		"""Refuse the connection.

		Parameters
		----------
		*args : object
			The address the test tried to reach.
		**kwargs : object
			Ignored.

		Raises
		------
		NetworkAccessError
			Always.
		"""
		_blocked(*args, **kwargs)

	def connect_ex(self, *args: object, **kwargs: object) -> NoReturn:
		"""Refuse the connection.

		Parameters
		----------
		*args : object
			The address the test tried to reach.
		**kwargs : object
			Ignored.

		Raises
		------
		NetworkAccessError
			Always.
		"""
		_blocked(*args, **kwargs)


def pytest_configure(config: pytest.Config) -> None:
	"""Register the opt-out marker.

	Parameters
	----------
	config : pytest.Config
		The pytest config object.
	"""
	config.addinivalue_line(
		"markers",
		"allow_network: let this test make real network calls (must be justified in review)",
	)


@pytest.fixture(autouse=True)
def block_network(request: pytest.FixtureRequest) -> Iterator[None]:
	"""Block every real network call for the duration of each test.

	Autouse, so it needs no opt-in: a test that forgets to mock the download boundary fails with
	:class:`NetworkAccessError` rather than silently calling CVM. Tests marked
	``allow_network`` are exempt.

	Parameters
	----------
	request : pytest.FixtureRequest
		Used to detect the ``allow_network`` opt-out marker.

	Yields
	------
	None
		Control returns to the test with the sockets blocked (or untouched, when opted out).
	"""
	if request.node.get_closest_marker("allow_network") is not None:
		yield
		return

	socket.socket = _BlockedSocket  # type: ignore[misc]
	socket.create_connection = _blocked  # type: ignore[assignment]
	socket.getaddrinfo = _blocked  # type: ignore[assignment]
	try:
		yield
	finally:
		socket.socket = _socket_real  # type: ignore[misc]
		socket.create_connection = _create_connection_real  # type: ignore[assignment]
		socket.getaddrinfo = _getaddrinfo_real  # type: ignore[assignment]


_GIT_HOOK_ENV = (
	"GIT_DIR",
	"GIT_WORK_TREE",
	"GIT_INDEX_FILE",
	"GIT_OBJECT_DIRECTORY",
	"GIT_ALTERNATE_OBJECT_DIRECTORIES",
	"GIT_COMMON_DIR",
	"GIT_PREFIX",
)


@pytest.fixture(autouse=True)
def isolate_git_environment(monkeypatch: pytest.MonkeyPatch) -> None:
	"""Drop the ``GIT_*`` variables a git hook exports, so a test's scratch repo stays its own.

	Under ``pre-commit`` the process inherits ``GIT_INDEX_FILE`` (and friends) pointing at the
	real repository. A test that runs ``git init`` / ``git add`` in a ``tmp_path`` would then write
	its scratch index over the real one, staging the deletion of the whole tree.

	Parameters
	----------
	monkeypatch : pytest.MonkeyPatch
		Removes each variable for the duration of the test.
	"""
	tuple(map(partial(monkeypatch.delenv, raising=False), _GIT_HOOK_ENV))
