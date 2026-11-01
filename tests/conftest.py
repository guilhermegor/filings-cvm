"""Pytest configuration: make real network access impossible during tests.

A unit test that reaches the network is a latent hazard: in CI it runs on every
push from many IPs, so a single un-mocked download can get the project
rate-limited or IP-banned from the very source it depends on. "Mock at the I/O
boundary" is a prose rule — it holds only while every contributor remembers it.
This autouse guard makes the violation *impossible* rather than merely
discouraged: it swaps the connection primitives (``socket.socket.connect`` /
``connect_ex`` and ``socket.create_connection``) for versions that raise
:class:`NetworkAccessError`, naming what was reached and what to mock instead. A
test that genuinely must hit the wire opts out with
``@pytest.mark.allow_network`` (registered in ``pytest.ini``).

Only the **connection** primitives are blocked, not ``socket.getaddrinfo`` — a
bare DNS/address resolution neither exfiltrates data nor triggers a rate-limit
ban (the connection does), and offline SSRF/address classification legitimately
resolves an address to decide whether to connect at all. ``create_connection``
resolves *and* connects, so the hostname path is still caught there.
"""

from __future__ import annotations

from functools import partial
import socket
from typing import NoReturn

import pytest


class NetworkAccessError(RuntimeError):
	"""Raised when a test attempts to open a real network connection."""


def _blocked(*args: object, **kwargs: object) -> NoReturn:
	"""Reject a network call, naming the target and the fix.

	Parameters
	----------
	*args : object
		Positional arguments from the patched socket primitive; the first is the
		connection target shown in the error message.
	**kwargs : object
		Keyword arguments from the patched socket primitive (ignored).

	Raises
	------
	NetworkAccessError
		Always — a real network call is never allowed in a test.
	"""
	raise NetworkAccessError(
		f"A test tried to reach the network ({args[:1]!r}). "
		"Mock the I/O boundary (the download / HTTP seam) instead, or mark the "
		"test @pytest.mark.allow_network if it truly must hit the wire."
	)


class _BlockedSocket(socket.socket):
	"""A socket whose outbound-connection methods are disabled."""

	def connect(self, *args: object, **kwargs: object) -> NoReturn:
		"""Reject ``socket.socket.connect``.

		Parameters
		----------
		*args : object
			Positional arguments (the address tuple); forwarded to the reporter.
		**kwargs : object
			Keyword arguments (ignored).

		Raises
		------
		NetworkAccessError
			Always.
		"""
		_blocked(*args, **kwargs)

	def connect_ex(self, *args: object, **kwargs: object) -> NoReturn:
		"""Reject ``socket.socket.connect_ex``.

		Parameters
		----------
		*args : object
			Positional arguments (the address tuple); forwarded to the reporter.
		**kwargs : object
			Keyword arguments (ignored).

		Raises
		------
		NetworkAccessError
			Always.
		"""
		_blocked(*args, **kwargs)


@pytest.fixture(autouse=True)
def block_network(request: pytest.FixtureRequest, monkeypatch: pytest.MonkeyPatch) -> None:
	"""Swap the socket primitives so no test can open a real connection.

	Applied automatically to every test. A test marked ``allow_network`` is left
	untouched. ``monkeypatch`` restores the real primitives after the test.

	Parameters
	----------
	request : pytest.FixtureRequest
		The active test request; inspected for the ``allow_network`` opt-out marker.
	monkeypatch : pytest.MonkeyPatch
		Pytest's patcher; restores the real primitives at teardown.
	"""
	bool_allowed = request.node.get_closest_marker("allow_network") is not None
	monkeypatch.setattr(socket, "socket", socket.socket if bool_allowed else _BlockedSocket)
	monkeypatch.setattr(
		socket,
		"create_connection",
		socket.create_connection if bool_allowed else _blocked,
	)


LIST_GIT_REPOSITORY_POINTERS = (
	"GIT_DIR",
	"GIT_WORK_TREE",
	"GIT_INDEX_FILE",
	"GIT_COMMON_DIR",
	"GIT_PREFIX",
	"GIT_OBJECT_DIRECTORY",
	"GIT_ALTERNATE_OBJECT_DIRECTORIES",
)


@pytest.fixture(autouse=True)
def isolate_git_environment(monkeypatch: pytest.MonkeyPatch) -> None:
	"""Drop the repository pointers git exports to hooks so a test never touches the host repo.

	Applied automatically to every test. Under pre-commit, ``GIT_DIR`` and
	``GIT_INDEX_FILE`` name the calling repository, so a test that runs ``git init`` or
	``git commit`` would otherwise write there instead of in its temporary directory.

	Parameters
	----------
	monkeypatch : pytest.MonkeyPatch
		Pytest's patcher; restores the variables at teardown.
	"""
	list(map(partial(monkeypatch.delenv, raising=False), LIST_GIT_REPOSITORY_POINTERS))
