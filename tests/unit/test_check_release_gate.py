"""Tests for ``bin/check_release_gate.py`` (ported from the BlueprintX bash test).

The template's test ran a local HTTP server; the suite's autouse guard forbids sockets, so the
``urlopen`` boundary is faked instead.
"""

import functools
import http.client
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
	fn_fake = functools.partial(_fake_urlopen, list(list_responses), list_urls)
	monkeypatch.setattr(gate.urllib.request, "urlopen", fn_fake)
	return list_urls


def _run_argv(
	monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture, list_argv: list
) -> tuple[int, str]:
	"""Run the gate's ``main`` with ``list_argv`` and return its exit code and output."""
	monkeypatch.setenv("GITHUB_API_URL", "")
	monkeypatch.setenv("GITHUB_REPOSITORY", "owner/repo")
	monkeypatch.setenv("GITHUB_TOKEN", "t")
	int_code = gate.main(list_argv)
	cls_out = capsys.readouterr()
	return int_code, cls_out.out + cls_out.err


def _run(
	monkeypatch: pytest.MonkeyPatch,
	capsys: pytest.CaptureFixture,
	str_previous: str,
	str_new: str,
) -> tuple[int, str]:
	"""Run the gate with an explicit previous and new version."""
	list_argv = ["--previous-version", str_previous, "--new-version", str_new]
	return _run_argv(monkeypatch, capsys, list_argv)


@pytest.mark.parametrize(
	("list_body", "int_code", "str_needle"),
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
	list_body: list,
	int_code: int,
	str_needle: str,
) -> None:
	"""A 0.x to 1.0.0 jump passes only when every open issue is deferred."""
	_api(monkeypatch, _ok(list_body))
	int_got, str_out = _run(monkeypatch, capsys, "0.9.0", "1.0.0")
	assert (int_got, str_needle in str_out) == (int_code, True)


@pytest.mark.parametrize(
	("str_previous", "str_new"), [("1.0.0", "1.0.1"), ("0.4.0", "0.5.0"), ("1.4.0", "2.0.0")]
)
def test_other_bumps_are_unaffected_and_make_no_api_call(
	monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture, str_previous: str, str_new: str
) -> None:
	"""Any bump other than 0.x to 1+ is not gated and never touches the API."""
	list_urls = _api(monkeypatch)
	int_got, str_out = _run(monkeypatch, capsys, str_previous, str_new)
	assert (int_got, "not applicable" in str_out, list_urls) == (0, True, [])


@pytest.mark.parametrize(
	"fn_response",
	[_fail(urllib.error.URLError("boom")), _ok({"message": "not a list"})],
	ids=["read-error", "unexpected-payload"],
)
def test_unreadable_api_fails_closed(
	monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture, fn_response: object
) -> None:
	"""An API error or a non-list payload blocks the release instead of guessing."""
	_api(monkeypatch, fn_response)
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
	list_full = [
		{"number": int_n, "title": "x", "labels": [{"name": "post-1.0"}]} for int_n in range(100)
	]
	list_urls = _api(
		monkeypatch, _ok(list_full), _ok([{"number": 500, "title": "Late", "labels": []}])
	)
	int_got, str_out = _run(monkeypatch, capsys, "0.9.0", "1.0.0")
	assert (int_got, "#500" in str_out, len(list_urls)) == (1, True, 2)


_FILE = [{"yanked": False}]
_YANKED = [{"yanked": True}]


@pytest.mark.parametrize(
	("dict_releases", "str_expected"),
	[
		({"0.9.0": _FILE, "1.0.0rc1": _FILE}, "0.9.0"),
		({"0.9.0": _FILE, "1.2.0": _YANKED}, "0.9.0"),
		({"0.9.0": _FILE, "0.10.0": _FILE}, "0.10.0"),
		({"0.9.0": _FILE, "1.0.0": _FILE, "1.0.0.post1": _FILE}, "1.0.0.post1"),
		({"0.9.0": _FILE, "1.0": _FILE, "1.0.0.post1": _YANKED}, "1.0"),
		({"0.9.0": []}, "0.0.0"),
		({}, "0.0.0"),
	],
	ids=[
		"prerelease-ignored",
		"yanked-ignored",
		"numeric-order",
		"post-release",
		"post-yanked",
		"no-files",
		"empty",
	],
)
def test_latest_final_ignores_prereleases_and_yanked(
	dict_releases: dict, str_expected: str
) -> None:
	"""The previous version comes from final, non-yanked releases only."""
	assert gate.latest_final(dict_releases) == str_expected


def test_prerelease_on_pypi_does_not_bypass_the_gate(
	monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture, tmp_path: Path
) -> None:
	"""With only 0.9.0 final and 1.0.0rc1 published, releasing 1.0.0 is still gated."""
	path_json = tmp_path / "pypi.json"
	path_json.write_text(json.dumps({"releases": {"0.9.0": _FILE, "1.0.0rc1": _FILE}}))
	_api(monkeypatch, _ok(_OPEN))
	int_got, _ = _run_argv(
		monkeypatch, capsys, ["--new-version", "1.0.0", "--pypi-json", str(path_json)]
	)
	assert int_got == 1


def test_malformed_version_fails_closed(
	monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture
) -> None:
	"""A version the gate cannot read blocks the release."""
	int_got, str_out = _run(monkeypatch, capsys, "garbage", "1.0.0")
	assert (int_got, "failed closed" in str_out) == (1, True)


def test_second_page_failure_fails_closed(
	monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture
) -> None:
	"""A failing page 2 blocks the release instead of passing on page 1 alone."""
	list_full = [
		{"number": int_n, "title": "x", "labels": [{"name": "post-1.0"}]} for int_n in range(100)
	]
	_api(monkeypatch, _ok(list_full), _fail(urllib.error.URLError("boom")))
	int_got, str_out = _run(monkeypatch, capsys, "0.9.0", "1.0.0")
	assert (int_got, "failed closed" in str_out) == (1, True)


def test_incomplete_read_is_annotated(
	monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture
) -> None:
	"""A truncated response is reported as a failed-closed annotation, not a traceback."""
	_api(monkeypatch, _fail(http.client.IncompleteRead(b"")))
	int_got, str_out = _run(monkeypatch, capsys, "0.9.0", "1.0.0")
	assert (int_got, "failed closed" in str_out) == (1, True)


def test_issue_title_cannot_inject_workflow_commands(
	monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture
) -> None:
	"""Newlines in a title are escaped so they cannot start a second workflow command."""
	_api(monkeypatch, _ok([{"number": 1, "title": "a\n::warning::x", "labels": []}]))
	int_got, str_out = _run(monkeypatch, capsys, "0.9.0", "1.0.0")
	assert (
		int_got,
		"open issue #1 blocks 1.0.0: a%0A::warning::x" in str_out,
		"\n::warning::x" in str_out,
	) == (1, True, False)


@pytest.mark.parametrize("dict_payload", [{}, {"releases": None}, {"releases": []}])
def test_malformed_pypi_json_fails_closed(
	monkeypatch: pytest.MonkeyPatch,
	capsys: pytest.CaptureFixture,
	tmp_path: Path,
	dict_payload: dict,
) -> None:
	"""A PyPI payload without a ``releases`` object blocks instead of reading as 0.0.0."""
	path_json = tmp_path / "pypi.json"
	path_json.write_text(json.dumps(dict_payload))
	int_got, str_out = _run_argv(
		monkeypatch, capsys, ["--new-version", "1.0.0", "--pypi-json", str(path_json)]
	)
	assert (int_got, "failed closed" in str_out) == (1, True)
