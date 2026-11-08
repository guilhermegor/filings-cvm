"""Unit tests for #401: gate scripts are judged from the base ref, not the PR checkout."""

import importlib.util
from pathlib import Path

import pytest
import yaml


_ROOT = Path(__file__).resolve().parents[2]
_STR_GATE_RUN = "check_review_threads.py"


def _load_integrity() -> object:
	"""Import ``bin/check_gate_integrity.py`` as a module."""
	cls_spec = importlib.util.spec_from_file_location(
		"_check_gate_integrity_401", _ROOT / "bin" / "check_gate_integrity.py"
	)
	assert cls_spec is not None
	assert cls_spec.loader is not None
	cls_module = importlib.util.module_from_spec(cls_spec)
	cls_spec.loader.exec_module(cls_module)
	return cls_module


def _steps() -> list:
	"""Return the review-threads workflow's steps."""
	path_wf = _ROOT / ".github" / "workflows" / "review_threads.yaml"
	return yaml.safe_load(path_wf.read_text(encoding="utf-8"))["jobs"]["review-threads"]["steps"]


def _gate_step_command() -> str:
	"""Return the ``run`` line that executes the review-threads gate."""
	return next(d["run"] for d in _steps() if _STR_GATE_RUN in d.get("run", ""))


@pytest.mark.parametrize(
	("str_command", "bool_from_base"),
	[
		(_gate_step_command(), True),
		("python bin/check_review_threads.py", False),
	],
)
def test_gate_command_runs_from_the_base_checkout(str_command: str, bool_from_base: bool) -> None:
	"""The gate script path must live in the base-ref checkout, not the PR's ``bin/``."""
	assert str_command.split()[-1].startswith(".gate-base/") is bool_from_base


def test_base_checkout_step_targets_the_resolved_base_ref() -> None:
	"""The second checkout pins the resolved base ref into ``.gate-base``."""
	dict_with = next(d["with"] for d in _steps() if d.get("with", {}).get("path") == ".gate-base")
	assert dict_with["ref"] == "${{ env.REVIEW_POLICY_BASE_REF }}"


@pytest.mark.parametrize(("str_new", "bool_flagged"), [("x = 2\n", True), ("x = 1\n", False)])
def test_modified_gate_script_is_flagged(str_new: str, bool_flagged: bool) -> None:
	"""An edited ``bin/check_*`` script is a finding; an identical one is not."""
	cls_gate = _load_integrity()
	str_path = "bin/check_review_threads.py"
	assert bool(cls_gate.gate_script_problems("x = 1\n", str_new, str_path)) is bool_flagged
