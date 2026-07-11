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
