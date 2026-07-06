"""Unit tests for the library entry point."""

import pytest

from filings-cvm.main import main


def test_main(capsys: pytest.CaptureFixture[str]) -> None:
	"""The entry point prints the placeholder greeting to stdout."""
	main()
	captured = capsys.readouterr()
	assert "Hello from lib-minimal!" in captured.out
