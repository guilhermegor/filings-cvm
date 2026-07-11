"""Unit tests for the download seam's retry wiring.

The retry *mechanism* is covered in ``test_retry.py``; here we verify that
``download_file`` is actually wrapped by it — a transient ``OSError`` is retried and the
download then succeeds — and that a deterministic ``ValueError`` (bad URL) is not. Network
is fully mocked: the opener is replaced, the SSRF host check is bypassed, and
``retry.time.sleep`` is neutralised so no real wait occurs.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from filings_cvm._internal.utils import http_downloader


class _FakeResponse:
	"""Minimal stand-in for the urllib response context manager."""

	def __init__(self, bytes_body: bytes) -> None:
		self.bytes_body = bytes_body
		self.status = 200

	def __enter__(self) -> _FakeResponse:
		return self

	def __exit__(self, *args: object) -> bool:
		return False

	def read(self) -> bytes:
		return self.bytes_body


class _FlakyOpener:
	"""Opener that raises ``OSError`` a fixed number of times, then serves a body."""

	def __init__(self, int_failures: int, bytes_body: bytes) -> None:
		self.int_failures = int_failures
		self.bytes_body = bytes_body
		self.int_calls = 0

	def open(self, cls_request: object, timeout: int | None = None) -> _FakeResponse:
		self.int_calls += 1
		if self.int_calls <= self.int_failures:
			raise OSError("transient")
		return _FakeResponse(self.bytes_body)


@pytest.fixture(autouse=True)
def _no_real_sleep(monkeypatch: pytest.MonkeyPatch) -> None:
	"""Neutralise the backoff wait so retry tests run instantly."""
	monkeypatch.setattr("filings_cvm._internal.utils.retry.time.sleep", lambda _float_s: None)


def test_download_file_retries_transient_failure(
	monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
	"""A transient OSError is retried; the download succeeds once the opener recovers."""
	cls_opener = _FlakyOpener(int_failures=2, bytes_body=b"payload")
	monkeypatch.setattr(http_downloader, "_assert_public_host", lambda _str_url: None)
	monkeypatch.setattr(http_downloader, "_OPENER", cls_opener)
	path_dest = tmp_path / "out.zip"

	path_result = http_downloader.download_file("https://example.com/out.zip", path_dest)

	assert path_result == path_dest
	assert path_dest.read_bytes() == b"payload"
	assert cls_opener.int_calls == 3  # two failures + one success


def test_download_file_gives_up_after_max_attempts(
	monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
	"""When every attempt fails transiently, the final OSError propagates."""
	cls_opener = _FlakyOpener(int_failures=99, bytes_body=b"never")
	monkeypatch.setattr(http_downloader, "_assert_public_host", lambda _str_url: None)
	monkeypatch.setattr(http_downloader, "_OPENER", cls_opener)

	with pytest.raises(OSError, match="transient"):
		http_downloader.download_file("https://example.com/out.zip", tmp_path / "out.zip")
	assert cls_opener.int_calls == http_downloader._DOWNLOAD_MAX_ATTEMPTS


def test_download_file_does_not_retry_bad_url(
	monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
	"""A deterministic ValueError (unsupported scheme) fails fast, never retried."""
	cls_opener = _FlakyOpener(int_failures=0, bytes_body=b"x")
	monkeypatch.setattr(http_downloader, "_OPENER", cls_opener)

	with pytest.raises(ValueError, match="unsupported URL scheme"):
		http_downloader.download_file("ftp://example.com/out.zip", tmp_path / "out.zip")
	assert cls_opener.int_calls == 0
