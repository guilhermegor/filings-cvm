"""Unit tests for the per-layer import gate (``bin/check_layer_imports.py``).

Every case is built from a shape **measured in a real project**, not invented: a vendor at the
top of ``model/``, the same vendor deferred into a function under an ``ImportError`` guard, and
pandas called as an API rather than named as a type.

The should-PASS cases matter as much as the should-fail ones. A gate exercised only on what it
rejects has been shown to reject, not to discriminate — and this gate's whole design rests on a
distinction (annotation vs API) that a blunter rule would flatten.
"""

import importlib.util
from pathlib import Path
import subprocess
import sys
from types import ModuleType

import pytest


def _load_gate() -> ModuleType:
	"""Import ``bin/check_layer_imports.py`` as a module.

	Returns
	-------
	ModuleType
		The loaded gate module.
	"""
	path_gate = Path(__file__).resolve().parents[2] / "bin" / "check_layer_imports.py"
	cls_spec = importlib.util.spec_from_file_location("_check_layer_imports", path_gate)
	assert cls_spec is not None
	assert cls_spec.loader is not None
	cls_module = importlib.util.module_from_spec(cls_spec)
	cls_spec.loader.exec_module(cls_module)
	return cls_module


_POLICY = {
	"first_party_extra": ["chassis"],
	"annotation_only": {"pandas": "Build a frame with utils.frames.from_cursor."},
	"layers": {
		"model": {"allow": {}},
		"utils": {"allow": {"pandas": "the seam layer owns the pandas surface"}},
	},
}
_FIRST_PARTY = {"src", "model", "utils", "config", "view", "controller", "chassis"}


def _problems(tmp_path: Path, str_source: str, str_layer: str = "model") -> list[str]:
	"""Run the gate over one synthetic module and return its problems.

	Parameters
	----------
	tmp_path : pathlib.Path
		Pytest throwaway directory.
	str_source : str
		The module source to check.
	str_layer : str, optional
		The layer the file is treated as belonging to, by default ``"model"``.

	Returns
	-------
	list of str
		The problems the gate reported.
	"""
	cls_gate = _load_gate()
	path_file = tmp_path / "probe.py"
	path_file.write_text(str_source, encoding="utf-8")
	return cls_gate.find_file_problems(path_file, str_layer, _POLICY, _FIRST_PARTY)


def _sole(list_problems: list[str]) -> str:
	"""Return the one problem in a list, asserting there is exactly one.

	The "exactly one finding, not a cascade" claim is asserted HERE rather than in each
	caller (blueprintx#544). Every fixture below is built to trip exactly one rule, so the
	count is a precondition of the fixture rather than a per-test behaviour — and hoisting
	it means every caller now checks it, including the several that previously only indexed
	``[0]`` and would have passed on a cascade.

	Parameters
	----------
	list_problems : list of str
		Whatever the gate reported.

	Returns
	-------
	str
		The single problem.
	"""
	assert len(list_problems) == 1, list_problems
	return list_problems[0]


def _sole_problem(tmp_path: Path, str_source: str, str_layer: str = "model") -> str:
	"""Run the gate over one synthetic module and return its single problem.

	Parameters
	----------
	tmp_path : pathlib.Path
		Pytest throwaway directory.
	str_source : str
		The module source to check.
	str_layer : str
		The layer the file is treated as belonging to.

	Returns
	-------
	str
		The one problem the gate reported.
	"""
	return _sole(_problems(tmp_path, str_source, str_layer))


def test_vendor_at_the_top_of_a_layer_is_rejected(tmp_path: Path) -> None:
	"""The plain case: a domain vendor imported straight into ``model/``.

	Measured in two independent projects (blueprintx#171).
	"""
	assert "filings_cvm" in _sole_problem(
		tmp_path, "from filings_cvm.submission import Submission\n"
	)


_STR_DEFERRED_VENDOR = (
	"def read_portal() -> None:\n"
	'\t"""Read."""\n'
	"\ttry:\n"
	"\t\tfrom filings_cvm.ingestion import fi\n"
	"\texcept ImportError:\n"
	"\t\treturn None\n"
	"\treturn fi\n"
)


@pytest.mark.parametrize("str_fragment", ["filings_cvm", "inside a function"])
def test_vendor_deferred_into_a_function_is_still_rejected(
	tmp_path: Path, str_fragment: str
) -> None:
	"""Deferring the import buys no exemption, even under an ``ImportError`` guard.

	This is the shape the gate exists for. The guard answers *how to degrade when the vendor
	is missing*; it says nothing about *why the layer knows the vendor at all*, and the
	coupling is identical to a top-level import. The optional-dependency pattern is fine — in
	the ``utils/`` seam that owns the dependency, which then returns the degraded result.
	"""
	assert str_fragment in _sole_problem(tmp_path, _STR_DEFERRED_VENDOR)


_STR_PANDAS_AS_API = (
	"import pandas as pd\n"
	"def load() -> pd.DataFrame:\n"
	'\t"""Load."""\n'
	'\treturn pd.read_sql("SELECT 1", None)\n'
)


@pytest.mark.parametrize("str_fragment", ["TYPE only", "utils.frames.from_cursor"])
def test_annotation_only_vendor_called_as_an_api_is_rejected(
	tmp_path: Path, str_fragment: str
) -> None:
	"""``pandas`` is the layers' vocabulary, not an API they may call."""
	assert str_fragment in _sole_problem(tmp_path, _STR_PANDAS_AS_API)


def test_annotation_only_vendor_used_as_a_type_passes(tmp_path: Path) -> None:
	"""The shape the reference model now ships: pandas named, never called."""
	str_source = (
		"from __future__ import annotations\n"
		"from typing import TYPE_CHECKING\n"
		"from utils.frames import from_cursor\n"
		"if TYPE_CHECKING:\n"
		"\timport pandas as pd\n"
		"def load(cls_cursor: object) -> pd.DataFrame:\n"
		'\t"""Load."""\n'
		'\treturn from_cursor(cls_cursor, {"id": "int64"})\n'
	)
	assert _problems(tmp_path, str_source) == []


def test_the_seam_layer_may_use_the_vendor_freely(tmp_path: Path) -> None:
	"""``utils/`` is where vendors are SUPPOSED to live — the gate must not fight its own fix."""
	str_source = 'import pandas as pd\ndef f() -> object:\n\t"""F."""\n\treturn pd.DataFrame()\n'
	assert _problems(tmp_path, str_source, str_layer="utils") == []


def test_the_layout_shim_is_first_party_not_a_vendor(tmp_path: Path) -> None:
	"""``chassis`` is our own code under the DDD layout, reached through the typing shim.

	Without ``first_party_extra`` this reported all 23 shipped helpers as vendor violations —
	a gate whose first run is 23 false positives is a gate nobody enables.
	"""
	str_source = (
		"try:\n"
		"\tfrom utils.typing import type_checker\n"
		"except ModuleNotFoundError:\n"
		"\tfrom chassis.typing import type_checker\n"
	)
	assert _problems(tmp_path, str_source, str_layer="utils") == []


def test_stdlib_is_unrestricted_in_every_layer(tmp_path: Path) -> None:
	"""The standard library carries no coupling risk and is never gated."""
	assert _problems(tmp_path, "import json\nfrom pathlib import Path\n") == []


@pytest.mark.parametrize("str_layer", ["model", "view", "controller"])
def test_one_statement_binding_many_names_is_one_violation(tmp_path: Path, str_layer: str) -> None:
	"""A single import binding several names must not report once per name.

	A gate that multiplies its own findings trains people to skim the output.

	Parameters
	----------
	tmp_path : pathlib.Path
		Pytest throwaway directory.
	str_layer : str
		The layer the synthetic module is treated as belonging to.
	"""
	list_problems = _problems(tmp_path, "from filings_cvm import a, b, c\n", str_layer)
	assert len(list_problems) == 1


def test_a_module_directly_under_src_is_not_skipped(tmp_path: Path) -> None:
	"""An entrypoint at ``src/main.py`` is checked like any other file.

	It has no directory to name its layer, and an earlier revision skipped exactly those
	files — so ``src/main.py`` could import any vendor and bypass the policy entirely. The
	place a bypass is easiest is not the place to stop looking.
	"""
	cls_gate = _load_gate()
	path_src = tmp_path / "src"
	path_src.mkdir()
	(path_src / "main.py").write_text("from filings_cvm import fi\n", encoding="utf-8")
	(tmp_path / ".layer-policy.yaml").write_text(
		"layers:\n  __root__:\n    allow: {}\n", encoding="utf-8"
	)

	dict_policy = cls_gate.load_policy(tmp_path)
	list_problems = cls_gate.find_file_problems(
		path_src / "main.py", cls_gate._ROOT_LAYER, dict_policy, {"src"}
	)

	assert "filings_cvm" in _sole(list_problems)


def _run_main(path_root: Path) -> tuple[int, str]:
	"""Run the gate's ``main()`` with ``path_root`` as the working directory.

	Parameters
	----------
	path_root : pathlib.Path
		Directory to treat as the project root.

	Returns
	-------
	tuple of (int, str)
		The exit code and everything printed.
	"""
	cls_run = subprocess.run(  # noqa: S603
		[
			sys.executable,
			str(Path(__file__).resolve().parents[2] / "bin" / "check_layer_imports.py"),
		],
		cwd=path_root,
		capture_output=True,
		text=True,
		check=False,
	)
	return cls_run.returncode, cls_run.stdout + cls_run.stderr


def _output_at(tuple_result: tuple[int, str], int_expected: int) -> str:
	"""Return a run's output, asserting its exit code first.

	"Exited N" and "said the right thing" are two claims that used to sit as two asserts in
	one test (blueprintx#544). The exit code is the precondition — an output assertion over a
	run that crashed proves nothing — so it is checked here, and each test keeps the single
	assertion that names the behaviour. The whole output rides on the assertion message, so a
	wrong exit code still reports what the gate actually printed.

	Parameters
	----------
	tuple_result : tuple of (int, str)
		The ``(exit code, output)`` pair from ``_run_main``.
	int_expected : int
		The exit code the run must have produced.

	Returns
	-------
	str
		Everything the run printed.
	"""
	int_code, str_out = tuple_result
	assert int_code == int_expected, str_out
	return str_out


def _seed_project(path_root: Path, str_module: str = "import os\n") -> None:
	"""Build a minimal project tree holding one module under ``src/model/``.

	Writing the policy is left to the caller: whether one exists is the very thing several of
	these tests vary, so making it a parameter would hide the difference inside a helper.

	Parameters
	----------
	path_root : pathlib.Path
		Directory to build in.
	str_module : str, optional
		Source of the single module placed under ``src/model/``.

	Returns
	-------
	None
	"""
	(path_root / "src" / "model").mkdir(parents=True, exist_ok=True)
	(path_root / "src" / "model" / "probe.py").write_text(str_module, encoding="utf-8")


_STR_MINIMAL_POLICY = "layers:\n  model:\n    allow: {}\n"


@pytest.mark.parametrize("str_fragment", [".layer-policy.yaml", "no import boundary"])
def test_modules_with_no_policy_file_FAIL_rather_than_pass_silently(
	tmp_path: Path, str_fragment: str
) -> None:
	"""⚠️ The negative control for the defect this fixed.

	The gate used to ``return 0`` in silence when no policy was present, so three of the five
	Python tiers shipped with NO import boundary at all while their CI stayed green. A gate
	reporting its own blindness as OK is the failure mode this repo writes gates to prevent.
	"""
	_seed_project(tmp_path)

	assert str_fragment in _output_at(_run_main(tmp_path), 1)


def test_a_tree_with_no_modules_and_no_policy_is_not_a_failure(tmp_path: Path) -> None:
	"""The positive control: nothing to check is not the same as failing to check."""
	(tmp_path / "src").mkdir()

	assert "nothing to do" in _output_at(_run_main(tmp_path), 0)


def test_a_clean_tree_prints_what_it_checked(tmp_path: Path) -> None:
	"""A silent gate cannot be told from an absent one, so success names the count."""
	_seed_project(tmp_path)
	(tmp_path / ".layer-policy.yaml").write_text(_STR_MINIMAL_POLICY, encoding="utf-8")

	assert "module(s) checked" in _output_at(_run_main(tmp_path), 0)


def test_layers_nested_inside_a_package_resolve_via_src_prefix_depth(tmp_path: Path) -> None:
	"""lib-minimal nests its layers as ``src/<pkg>/_internal/<layer>/``.

	Without the prefix the layer resolves to the PACKAGE NAME, matches no policy entry, and
	deny-by-default rejects the whole tree for the wrong reason — which is how one engine
	serving five layouts quietly stops serving one of them.
	"""
	path_deep = tmp_path / "src" / "mypkg" / "_internal" / "model"
	path_deep.mkdir(parents=True)
	(path_deep / "probe.py").write_text("import os\n", encoding="utf-8")
	(tmp_path / ".layer-policy.yaml").write_text(
		"src_prefix_depth: 2\n" + _STR_MINIMAL_POLICY, encoding="utf-8"
	)

	assert "module(s) checked" in _output_at(_run_main(tmp_path), 0)


def test_the_same_nested_tree_without_the_prefix_is_rejected(tmp_path: Path) -> None:
	"""The paired control: drop the prefix and the layer no longer resolves.

	Without this, the test above would pass against an engine that ignores the setting.
	"""
	path_deep = tmp_path / "src" / "mypkg" / "_internal" / "model"
	path_deep.mkdir(parents=True)
	(path_deep / "probe.py").write_text("import pandas\n", encoding="utf-8")
	(tmp_path / ".layer-policy.yaml").write_text(_STR_MINIMAL_POLICY, encoding="utf-8")

	int_code, _ = _run_main(tmp_path)

	assert int_code == 1


_STR_DIRECTION_POLICY = (
	"layers:\n"
	"  utils:\n"
	"    allow: {}\n"
	"    deny_layers:\n"
	'      model: "utils/ is a seam for the layers, not a consumer of them."\n'
	"  model:\n"
	"    allow: {}\n"
	"  config:\n"
	"    allow: {}\n"
)


def _seed_layers(path_root: Path) -> None:
	"""Create every sibling layer the direction fixtures refer to.

	⚠️ All of them must EXIST on disk. ``first_party_roots`` learns the project's own package
	names by scanning src/, so a layer that is only named in the policy is an unknown module
	to the VENDOR half — and the direction test then fails for the wrong reason.

	Parameters
	----------
	path_root : pathlib.Path
		The project root to build under.

	Returns
	-------
	None
	"""
	_seed_one_layer(path_root, "utils")
	_seed_one_layer(path_root, "model")
	_seed_one_layer(path_root, "config")


def _seed_one_layer(path_root: Path, str_layer: str) -> None:
	"""Create one layer package under ``src/``.

	Parameters
	----------
	path_root : pathlib.Path
		The project root.
	str_layer : str
		The layer's directory name.

	Returns
	-------
	None
	"""
	(path_root / "src" / str_layer).mkdir(parents=True, exist_ok=True)
	(path_root / "src" / str_layer / "__init__.py").write_text("", encoding="utf-8")


def _direction_case(tmp_path: Path, str_source: str) -> tuple[int, str]:
	"""Run the gate over one module placed in ``utils/`` under a direction policy.

	Parameters
	----------
	tmp_path : pathlib.Path
		Pytest throwaway directory.
	str_source : str
		The module source to check.

	Returns
	-------
	tuple of (int, str)
		The gate's exit code and its output.
	"""
	_seed_layers(tmp_path)
	(tmp_path / "src" / "utils" / "probe.py").write_text(str_source, encoding="utf-8")
	(tmp_path / ".layer-policy.yaml").write_text(_STR_DIRECTION_POLICY, encoding="utf-8")
	return _run_main(tmp_path)


@pytest.mark.parametrize("str_fragment", ["must not import", "not a consumer"])
def test_a_seam_importing_the_layer_it_serves_is_rejected(
	tmp_path: Path, str_fragment: str
) -> None:
	"""⚠️ No vendor is involved, and that is the point.

	The vendor half of this gate asks "may this layer reach OUTSIDE the project?". Direction
	asks "may it reach THAT layer?" — a different question, and utils/ importing model/ is a
	cycle the vendor rule cannot see. It was prose only (src/utils/CLAUDE.md: "utils/ is
	imported by them, never the reverse") and prose does not fail a build.
	"""
	assert str_fragment in _output_at(_direction_case(tmp_path, "from model import thing\n"), 1)


def test_a_wrong_direction_deferred_into_a_function_is_still_rejected(tmp_path: Path) -> None:
	"""Deferring the import does not undo the coupling — same rule as for a vendor."""
	int_code, _ = _direction_case(
		tmp_path, 'def f() -> None:\n\t"""D."""\n\timport model\n\n\tprint(model)\n'
	)

	assert int_code == 1


def test_an_allowed_direction_passes(tmp_path: Path) -> None:
	"""The positive control: a sibling not named in deny_layers is fine."""
	int_code, _ = _direction_case(tmp_path, "from config import settings\n")

	assert int_code == 0


def test_a_layer_declaring_no_direction_is_unrestricted(tmp_path: Path) -> None:
	"""A layer with no ``deny_layers`` may reach its siblings.

	Unlike the VENDOR half this is not deny-by-default, and the asymmetry is deliberate: the
	set of vendors is open-ended, while the set of layers is small, named in the same file,
	and each project decides its own direction. An absent entry is a real answer, not an
	unasked question.
	"""
	_seed_layers(tmp_path)
	(tmp_path / "src" / "model" / "probe.py").write_text(
		"from utils import thing\n", encoding="utf-8"
	)
	(tmp_path / ".layer-policy.yaml").write_text(_STR_DIRECTION_POLICY, encoding="utf-8")

	int_code, _ = _run_main(tmp_path)

	assert int_code == 0


@pytest.mark.parametrize(
	("str_fragment", "bool_present"),
	[("duplicate key", True), ("Traceback", False)],
	ids=["names-the-defect", "readable-in-ci-output"],
)
def test_a_duplicate_policy_key_is_rejected(
	tmp_path: Path, str_fragment: str, bool_present: bool
) -> None:
	"""⚠️ A repeated mapping key must FAIL, because YAML keeps only the last one.

	Hit for real while writing this repo's own policies: a second ``deny_layers:`` under one
	layer silently erased three denials. Nothing errored, the file still parsed, and the gate
	still reported success — while enforcing less than the file appeared to say. A policy is
	security-relevant config; losing rules in silence is the one failure it must not have.
	"""
	_seed_project(tmp_path)
	(tmp_path / ".layer-policy.yaml").write_text(
		'layers:\n  model:\n    allow: {}\n    deny_layers:\n      view: "a"\n'
		'    deny_layers:\n      utils: "b"\n',
		encoding="utf-8",
	)

	assert (str_fragment in _output_at(_run_main(tmp_path), 1)) is bool_present


_STR_SUBLAYER_POLICY = (
	"layers:\n"
	"  capabilities:\n"
	"    allow: {}\n"
	"  capabilities/*/domain:\n"
	"    allow: {}\n"
	"    deny_layers:\n"
	'      chassis.db_schema: "the domain names ports, not providers."\n'
	"  chassis:\n"
	"    allow: {}\n"
)


def _sublayer_case(tmp_path: Path, str_source: str) -> tuple[int, str]:
	"""Run the gate over one module inside a capability's ``domain/``.

	Parameters
	----------
	tmp_path : pathlib.Path
		Pytest throwaway directory.
	str_source : str
		The module source to check.

	Returns
	-------
	tuple of (int, str)
		The gate's exit code and output.
	"""
	path_dom = tmp_path / "src" / "capabilities" / "notes" / "domain"
	path_dom.mkdir(parents=True)
	(path_dom / "ports.py").write_text(str_source, encoding="utf-8")
	(tmp_path / "src" / "chassis").mkdir(parents=True, exist_ok=True)
	(tmp_path / "src" / "chassis" / "__init__.py").write_text("", encoding="utf-8")
	(tmp_path / ".layer-policy.yaml").write_text(_STR_SUBLAYER_POLICY, encoding="utf-8")
	return _run_main(tmp_path)


@pytest.mark.parametrize("str_fragment", ["capabilities/*/domain", "names ports, not providers"])
def test_a_glob_layer_key_governs_a_capability_sublayer(tmp_path: Path, str_fragment: str) -> None:
	"""⚠️ The three DDD sublayers have DIFFERENT rules, and one key cannot hold them.

	The tier's own CLAUDE.md says domain depends on nothing, application on the domain only,
	and infrastructure on domain ports plus external libs. Collapsed into one `capabilities`
	entry — which is what the first-path-component rule does — that table is documentation
	nobody can enforce.
	"""
	assert str_fragment in _output_at(
		_sublayer_case(tmp_path, "from chassis.db_schema import Repo\n"), 1
	)


def test_a_dotted_deny_spares_the_sibling_subpackage(tmp_path: Path) -> None:
	"""⚠️ The paired control, and the reason the deny is dotted rather than a bare root.

	``chassis`` holds BOTH the DB providers and the runtime type-checking engine that this
	project mandates on every class, the domain included. A root-level `chassis:` deny would
	therefore fire on correct code — and a rule that cries wolf is a rule someone deletes.
	"""
	int_code, str_out = _sublayer_case(tmp_path, "from chassis.typing import Meta\n")

	assert int_code == 0, str_out


def test_a_glob_governs_packages_NESTED_below_the_sublayer(tmp_path: Path) -> None:
	"""⚠️ ``fnmatch`` matches the WHOLE string, so a deeper module needs ancestor matching.

	``capabilities/*/domain`` matches ``capabilities/notes/domain`` and NOT
	``capabilities/notes/domain/entities`` — the ``*`` does not stop at ``/``, but the pattern
	still has to consume the entire path. A module one package deeper therefore fell back to
	the broad ``capabilities`` key and lost the sublayer rules, which is a rule that silently
	stops applying the moment someone adds a subpackage.
	"""
	path_deep = tmp_path / "src" / "capabilities" / "notes" / "domain" / "entities"
	path_deep.mkdir(parents=True)
	(path_deep / "note.py").write_text("from chassis.db_schema import Repo\n", encoding="utf-8")
	(tmp_path / "src" / "chassis").mkdir(parents=True, exist_ok=True)
	(tmp_path / "src" / "chassis" / "__init__.py").write_text("", encoding="utf-8")
	(tmp_path / ".layer-policy.yaml").write_text(_STR_SUBLAYER_POLICY, encoding="utf-8")

	assert "capabilities/*/domain" in _output_at(_run_main(tmp_path), 1)


def test_a_dotted_deny_also_catches_the_RELATIVE_form(tmp_path: Path) -> None:
	"""⚠️ The relative twin of a rejected import must be rejected too.

	Resolving a relative import to its first component only made every DOTTED deny key miss:
	``from ....chassis.db_schema import Repo`` reduced to ``chassis``, which no
	``chassis.db_schema`` rule matches. The absolute form was rejected while its relative twin
	passed — an inconsistency worse than not having the rule, because the gate looks enforced.
	"""
	path_dom = tmp_path / "src" / "capabilities" / "notes" / "domain"
	path_dom.mkdir(parents=True)
	(path_dom / "ports.py").write_text(
		"from ....chassis.db_schema import Repo\n", encoding="utf-8"
	)
	(tmp_path / "src" / "chassis").mkdir(parents=True, exist_ok=True)
	(tmp_path / "src" / "chassis" / "__init__.py").write_text("", encoding="utf-8")
	(tmp_path / ".layer-policy.yaml").write_text(_STR_SUBLAYER_POLICY, encoding="utf-8")

	assert "chassis.db_schema" in _output_at(_run_main(tmp_path), 1)
