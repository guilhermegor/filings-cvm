"""Behaviour of ``bin/test_urls_docstrings.sh`` (issue #400), run offline against a fake curl."""

from __future__ import annotations

import os
from pathlib import Path
import subprocess

import pytest


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "bin" / "test_urls_docstrings.sh"
URL = "https://example.invalid/some/path"


class _Run:
	"""Outcome of one script run plus the probe log and the dead-link report."""

	def __init__(self, returncode: int, probes: int, report: str) -> None:
		self.returncode = returncode
		self.probes = probes
		self.report = report


class _Harness:
	"""Runs the script with a curl that always answers 404."""

	def __init__(self, tmp_path: Path) -> None:
		self.tmp_path = tmp_path
		self.log = tmp_path / "curl.log"
		self.report = tmp_path / "report.tsv"
		path_bin = tmp_path / "fakebin"
		path_bin.mkdir()
		curl = path_bin / "curl"
		curl.write_text(f'#!/bin/bash\necho x >> "{self.log}"\nprintf 404\n')
		curl.chmod(0o755)
		self.env = {
			**os.environ,
			"PATH": f"{path_bin}:{os.environ['PATH']}",
			"URL_CACHE_DIR": str(tmp_path / "cache"),
		}
		self.env.pop("URL_REPORT_FILE", None)
		self.py = tmp_path / "mod.py"
		self.py.write_text(f'def f():\n\t"""\n\tSee {URL}\n\t"""\n')

	def run(self, path: Path, *, report: bool = False) -> _Run:
		"""Run the script on ``path``, optionally in report mode."""
		env = {**self.env, "URL_REPORT_FILE": str(self.report)} if report else self.env
		proc = subprocess.run(  # noqa: S603  (fixed argv, no shell)
			["bash", str(SCRIPT), str(path)],  # noqa: S607
			env=env,
			cwd=ROOT,
			capture_output=True,
			text=True,
			check=False,
		)
		probes = len(self.log.read_text().splitlines()) if self.log.exists() else 0
		text = self.report.read_text() if self.report.exists() else ""
		return _Run(proc.returncode, probes, text)


@pytest.fixture
def harness(tmp_path: Path) -> _Harness:
	"""Build a fresh fake-curl harness."""
	return _Harness(tmp_path)


def test_dead_link_fails_without_report_file(harness: _Harness) -> None:
	"""Without ``URL_REPORT_FILE`` a dead link exits 1."""
	assert harness.run(harness.py).returncode == 1


def test_report_mode_exits_zero_on_dead_link(harness: _Harness) -> None:
	"""With ``URL_REPORT_FILE`` a dead link is data, so the run exits 0."""
	assert harness.run(harness.py, report=True).returncode == 0


def test_report_mode_records_status_and_url(harness: _Harness) -> None:
	"""The report row carries the status and the URL."""
	row = harness.run(harness.py, report=True).report.split("\t")
	assert (row[0], row[2].strip()) == ("404", URL)


def test_failure_is_cached_so_second_run_does_not_probe(harness: _Harness) -> None:
	"""A second run inside the failure TTL makes no further probe."""
	first = harness.run(harness.py)
	assert harness.run(harness.py).probes == first.probes


def test_non_python_argument_is_not_scanned(harness: _Harness) -> None:
	"""A non-``.py`` argument is skipped, so curl is never called."""
	txt = harness.tmp_path / "notes.txt"
	txt.write_text(URL)
	assert harness.run(txt).probes == 0
