"""Tests for ``bin/check_release_gate.py`` (ported from the BlueprintX bash test).

The template's test ran a local HTTP server; the suite's autouse guard forbids sockets, so the
``urlopen`` boundary is faked instead.
"""

import functools
import importlib.util
import io
import json
from pathlib import Path
from types import ModuleType
import urllib.error
import urllib.request

import pytest


_PATH = Path(__file__).resolve().parents[2] / "bin" / "check_release_gate.py"
_SPEC = importlib.util.spec_from_file_location("check_release_gate", _PATH)
gate: ModuleType = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(gate)

_OPEN = [
	{"number": 7, "title": "Fix parser", "labels": []},
	{"number": 8, "title": "Later", "labels": [{"name": "post-1.0"}]},
]
_DEFERRED = [
	{"number": 8, "title": "Later", "labels": [{"name": "post-1.0"}]},
	{"number": 9, "title": "PR", "pull_request": {}, "labels": []},
	{"number": 10, "title": "Cut 1.0.0", "labels": [{"name": "state:blocked"}]},
]


def _raise(error: Exception) -> None:
	"""Raise ``error`` (a branch-free way for a fake response to fail)."""
	raise error


def _ok(body: object) -> object:
	"""Return a fake response that serves ``body`` as JSON."""
	return lambda: io.BytesIO(json.dumps(body).encode())


def _fail(error: Exception) -> object:
	"""Return a fake response that raises ``error``."""
	return lambda: _raise(error)


def _fake_urlopen(
	list_queue: list, list_urls: list, cls_request: urllib.request.Request, timeout: int
) -> io.BytesIO:
	"""Record the URL, then play the next queued response."""
	list_urls.append(cls_request.full_url)
	return list_queue.pop(0)()


def _api(monkeypatch: pytest.MonkeyPatch, *list_responses: object) -> list:
	"""Fake ``urlopen`` with queued responses; return the requested URLs."""
	list_urls: list = []
	fake = functools.partial(_fake_urlopen, list(list_responses), list_urls)
	monkeypatch.setattr(gate.urllib.request, "urlopen", fake)
	return list_urls


def _run(
	monkeypatch: pytest.MonkeyPatch,
	capsys: pytest.CaptureFixture,
	str_previous: str,
	str_new: str,
) -> tuple[int, str]:
	"""Run the gate's ``main`` and return its exit code and combined output."""
	monkeypatch.setenv("GITHUB_API_URL", "")
	monkeypatch.setenv("GITHUB_REPOSITORY", "owner/repo")
	monkeypatch.setenv("GITHUB_TOKEN", "t")
	int_code = gate.main(["--previous-version", str_previous, "--new-version", str_new])
	cls_out = capsys.readouterr()
	return int_code, cls_out.out + cls_out.err


@pytest.mark.parametrize(
	("body", "code", "needle"),
	[
		(_OPEN, 1, "#7"),
		(_DEFERRED, 0, "gate passed"),
		([{"number": 11, "title": "Cut 1.0.0 docs rewrite", "labels": []}], 1, "#11"),
		([], 0, "gate passed"),
	],
	ids=["unlabelled-blocks", "post-1.0-passes", "lookalike-title-blocks", "no-issues-passes"],
)
def test_zero_x_to_one_zero_gates_on_open_issues(
	monkeypatch: pytest.MonkeyPatch,
	capsys: pytest.CaptureFixture,
	body: list,
	code: int,
	needle: str,
) -> None:
	"""A 0.x to 1.0.0 jump passes only when every open issue is deferred."""
	_api(monkeypatch, _ok(body))
	int_got, str_out = _run(monkeypatch, capsys, "0.9.0", "1.0.0")
	assert (int_got, needle in str_out) == (code, True)


@pytest.mark.parametrize(
	("previous", "new"), [("1.0.0", "1.0.1"), ("0.4.0", "0.5.0"), ("1.4.0", "2.0.0")]
)
def test_other_bumps_are_unaffected_and_make_no_api_call(
	monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture, previous: str, new: str
) -> None:
	"""Any bump other than 0.x to 1+ is not gated and never touches the API."""
	list_urls = _api(monkeypatch)
	int_got, str_out = _run(monkeypatch, capsys, previous, new)
	assert (int_got, "not applicable" in str_out, list_urls) == (0, True, [])


@pytest.mark.parametrize(
	"response",
	[_fail(urllib.error.URLError("boom")), _ok({"message": "not a list"})],
	ids=["read-error", "unexpected-payload"],
)
def test_unreadable_api_fails_closed(
	monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture, response: object
) -> None:
	"""An API error or a non-list payload blocks the release instead of guessing."""
	_api(monkeypatch, response)
	int_got, str_out = _run(monkeypatch, capsys, "0.9.0", "1.0.0")
	assert (int_got, "failed closed" in str_out) == (1, True)


def test_first_publish_at_one_zero_is_gated(
	monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture
) -> None:
	"""A first publish reads as 0.0.0, so a 1.0.0 debut is gated too."""
	_api(monkeypatch, _fail(urllib.error.URLError("unreachable")))
	int_got, str_out = _run(monkeypatch, capsys, "0.0.0", "1.0.0")
	assert (int_got, "failed closed" in str_out) == (1, True)


def test_issues_are_paginated(
	monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture
) -> None:
	"""A full page of deferred issues makes the gate read the next page."""
	list_full = [{"number": n, "title": "x", "labels": [{"name": "post-1.0"}]} for n in range(100)]
	list_urls = _api(
		monkeypatch, _ok(list_full), _ok([{"number": 500, "title": "Late", "labels": []}])
	)
	int_got, str_out = _run(monkeypatch, capsys, "0.9.0", "1.0.0")
	assert (int_got, "#500" in str_out, len(list_urls)) == (1, True, 2)
