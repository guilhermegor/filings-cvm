"""Unit tests for ``poe template_update`` (blueprintx#872; offline, no scaffold run).

Each scenario builds a synthetic BlueprintX checkout in git (a base commit, then the template
moving on) and a project stamped with the base commit, then runs the updater against them.
The checkout's scaffold lib is a stand-in speaking the ``--list-copies`` contract.
"""

import fnmatch
import importlib.util
import os
from pathlib import Path
import subprocess
import sys
from types import ModuleType

import pytest


@pytest.fixture(autouse=True)
def _isolate_env(monkeypatch: pytest.MonkeyPatch) -> None:
	"""Drop the caller's ``GIT_*`` variables so nested calls never reach its repository.

	A pre-commit run exports ``GIT_INDEX_FILE``; without this the throwaway repositories
	these tests build would write to the real index.
	"""
	list(map(monkeypatch.delenv, fnmatch.filter(os.environ, "GIT_*")))


_BIN = Path(__file__).resolve().parents[2] / "bin"
_COMMON = "templates/python-common"
_TIER = "mvc-service-native-db"
_LIB = "bin/lib/scaffold_python_templates.sh"


def _load(str_name: str) -> ModuleType:
	"""Load a ``bin/`` script by path (``bin/`` is not a package).

	Parameters
	----------
	str_name : str
		Module stem under ``bin/``.

	Returns
	-------
	ModuleType
			The imported module.
	"""
	cls_spec = importlib.util.spec_from_file_location(str_name, _BIN / f"{str_name}.py")
	cls_module = importlib.util.module_from_spec(cls_spec)
	sys.modules[str_name] = cls_module
	cls_spec.loader.exec_module(cls_module)
	return cls_module


drift = _load("check_template_drift")
updater = _load("template_update")


def _git(path_root: Path, *tuple_args: str) -> str:
	"""Run one git command in ``path_root`` and return its stdout.

	Parameters
	----------
	path_root : pathlib.Path
		The repository directory.
	*tuple_args : str
		Arguments after ``git -C <path_root>``.

	Returns
	-------
	str
			The command's stdout, stripped.
	"""
	cls_run = subprocess.run(  # noqa: S603
		["git", "-C", str(path_root), "-c", "user.name=t", "-c", "user.email=t@t", *tuple_args],  # noqa: S607
		capture_output=True,
		encoding="utf-8",
		check=True,
		env={k: v for k, v in os.environ.items() if not k.startswith("GIT_")},
	)
	return cls_run.stdout.strip()


def _commit_all(path_root: Path, str_message: str) -> None:
	"""Stage everything and commit it without signing.

	Parameters
	----------
	path_root : pathlib.Path
		The repository directory.
	str_message : str
		The commit message.

	Returns
	-------
	None
	"""
	_git(path_root, "add", "-A")
	_git(path_root, "-c", "commit.gpgsign=false", "commit", "-q", "-m", str_message)


def _write(path_root: Path, str_rel: str, str_text: str) -> None:
	"""Write a text file, creating its parent directories.

	Parameters
	----------
	path_root : pathlib.Path
		The directory the path is relative to.
	str_rel : str
		The relative path.
	str_text : str
		The content.

	Returns
	-------
	None
	"""
	path_file = path_root / str_rel
	path_file.parent.mkdir(parents=True, exist_ok=True)
	path_file.write_text(str_text, encoding="utf-8")


def _write_all(path_root: Path, dict_files: dict[str, str]) -> None:
	"""Write several text files.

	Parameters
	----------
	path_root : pathlib.Path
		The directory the paths are relative to.
	dict_files : dict[str, str]
		Relative path to content.

	Returns
	-------
	None
	"""
	list(map(lambda tuple_item: _write(path_root, *tuple_item), dict_files.items()))


def _copy_line(str_rel: str) -> str:
	"""Return the ``--list-copies`` line for one verbatim template file.

	Parameters
	----------
	str_rel : str
		The path, both under the template root and in the project.

	Returns
	-------
	str
			The tab-separated COPY line.
	"""
	return f"COPY\tfile\t{_COMMON}/{str_rel}\t{str_rel}"


def _scenario(
	path_tmp: Path,
	dict_base: dict[str, str],
	dict_ours: dict[str, str],
	dict_theirs: dict[str, str],
	bool_stamp_commit: bool = True,
) -> tuple[Path, Path, str]:
	"""Build a checkout (base commit, then theirs committed) and a project stamped with base.

	Parameters
	----------
	path_tmp : pathlib.Path
		A temporary directory to build under.
	dict_base : dict[str, str]
		Template files at the commit the project was scaffolded from.
	dict_ours : dict[str, str]
		The project's files.
	dict_theirs : dict[str, str]
		Template files now, written over the base ones.
	bool_stamp_commit : bool
		Whether the provenance stamp carries ``blueprintx_commit``.

	Returns
	-------
	tuple of (pathlib.Path, pathlib.Path, str)
			The project root, the checkout root and the checkout's current HEAD.
	"""
	path_bx = path_tmp / "bx"
	_git(path_tmp, "init", "-q", str(path_bx))
	_write_all(path_bx / _COMMON, dict_base)
	_commit_all(path_bx, "base")
	str_base = _git(path_bx, "rev-parse", "HEAD")
	_write_all(path_bx / _COMMON, dict_theirs)
	_write(path_bx, _LIB, "cat <<'X'\n" + "\n".join(map(_copy_line, dict_theirs)) + "\nX\n")
	_commit_all(path_bx, "template moves on")
	path_project = path_tmp / "project"
	_git(path_tmp, "init", "-q", str(path_project))
	str_commit_line = f"blueprintx_commit: {str_base}\n" if bool_stamp_commit else ""
	_write(path_project, drift._PROVENANCE_FILENAME, f"tier: {_TIER}\n{str_commit_line}")
	_write_all(path_project, dict_ours)
	_commit_all(path_project, "scaffold")
	return path_project, path_bx, _git(path_bx, "rev-parse", "HEAD")


def _update(path_project: Path, path_bx: Path, *tuple_flags: str) -> int:
	"""Run the updater against a project and a checkout.

	Parameters
	----------
	path_project : pathlib.Path
		The project root.
	path_bx : pathlib.Path
		The BlueprintX checkout.
	*tuple_flags : str
		Extra flags such as ``--apply``.

	Returns
	-------
	int
			The updater's exit status.
	"""
	return updater.main(
		["--root", str(path_project), "--blueprintx-root", str(path_bx), *tuple_flags]
	)


_BASE = {"a.txt": "base\n"}
_THREE_LINES = {"a.txt": "l1\nl2\nl3\n"}


def test_a_dry_run_writes_nothing(tmp_path: Path) -> None:
	"""Without ``--apply`` the project is left exactly as it was."""
	path_project, path_bx, _ = _scenario(tmp_path, _BASE, _BASE, {"a.txt": "new\n"})

	_update(path_project, path_bx)

	assert (path_project / "a.txt").read_text(encoding="utf-8") == "base\n"


def test_a_dry_run_names_the_file_it_would_fast_forward(
	tmp_path: Path, capsys: pytest.CaptureFixture
) -> None:
	"""The dry run is the report: it lists the file and says nothing was written."""
	path_project, path_bx, _ = _scenario(tmp_path, _BASE, _BASE, {"a.txt": "new\n"})

	_update(path_project, path_bx)

	assert "fast-forward: a.txt" in capsys.readouterr().out


def test_an_untouched_file_is_fast_forwarded(tmp_path: Path) -> None:
	"""Project equals base, template moved on: take theirs."""
	path_project, path_bx, _ = _scenario(tmp_path, _BASE, _BASE, {"a.txt": "new\n"})

	_update(path_project, path_bx, "--apply")

	assert (path_project / "a.txt").read_text(encoding="utf-8") == "new\n"


def test_a_file_the_project_lacks_is_added(tmp_path: Path) -> None:
	"""A template path absent from the project is created, parent directories included."""
	dict_theirs = {"a.txt": "base\n", "docs/b.txt": "fresh\n"}
	path_project, path_bx, _ = _scenario(tmp_path, _BASE, _BASE, dict_theirs)

	_update(path_project, path_bx, "--apply")

	assert (path_project / "docs/b.txt").read_text(encoding="utf-8") == "fresh\n"


def test_a_local_edit_the_template_never_touched_is_left_alone(tmp_path: Path) -> None:
	"""Theirs equals base: the project's own edit is not drift and is not rewritten."""
	path_project, path_bx, _ = _scenario(tmp_path, _BASE, {"a.txt": "mine\n"}, _BASE)

	_update(path_project, path_bx, "--apply")

	assert (path_project / "a.txt").read_text(encoding="utf-8") == "mine\n"


def test_disjoint_edits_merge_into_one_file(tmp_path: Path) -> None:
	"""A local edit and a template edit on different lines both survive."""
	dict_ours = {"a.txt": "mine1\nl2\nl3\n"}
	dict_theirs = {"a.txt": "l1\nl2\nnew3\n"}
	path_project, path_bx, _ = _scenario(tmp_path, _THREE_LINES, dict_ours, dict_theirs)

	_update(path_project, path_bx, "--apply")

	assert (path_project / "a.txt").read_text(encoding="utf-8") == "mine1\nl2\nnew3\n"


def test_a_clean_apply_moves_the_stamp_to_the_checkout_head(tmp_path: Path) -> None:
	"""Every file applied cleanly, so ``blueprintx_commit`` advances."""
	path_project, path_bx, str_head = _scenario(tmp_path, _BASE, _BASE, {"a.txt": "new\n"})

	_update(path_project, path_bx, "--apply")

	assert drift.read_commit(path_project) == str_head


def test_apply_works_on_a_new_branch_named_after_the_checkout_head(tmp_path: Path) -> None:
	"""The update never lands on the branch the project was on."""
	path_project, path_bx, str_head = _scenario(tmp_path, _BASE, _BASE, {"a.txt": "new\n"})

	_update(path_project, path_bx, "--apply")

	assert (
		_git(path_project, "branch", "--show-current") == f"chore/template-update-{str_head[:10]}"
	)


def test_conflicting_edits_keep_markers_in_the_file(tmp_path: Path) -> None:
	"""Both sides changed the same line: the markers are written, nothing is dropped."""
	path_project, path_bx, _ = _scenario(tmp_path, _BASE, {"a.txt": "mine\n"}, {"a.txt": "new\n"})

	_update(path_project, path_bx, "--apply")

	assert "<<<<<<< ours" in (path_project / "a.txt").read_text(encoding="utf-8")


def test_a_conflict_keeps_the_local_edit_inside_the_markers(tmp_path: Path) -> None:
	"""The project's line is still in the file after a conflict."""
	path_project, path_bx, _ = _scenario(tmp_path, _BASE, {"a.txt": "mine\n"}, {"a.txt": "new\n"})

	_update(path_project, path_bx, "--apply")

	assert "mine\n" in (path_project / "a.txt").read_text(encoding="utf-8")


def test_a_conflict_leaves_the_stamp_unchanged(tmp_path: Path) -> None:
	"""One unresolved file is enough to keep the old merge base."""
	path_project, path_bx, _ = _scenario(tmp_path, _BASE, {"a.txt": "mine\n"}, {"a.txt": "new\n"})
	str_before = drift.read_commit(path_project)

	_update(path_project, path_bx, "--apply")

	assert drift.read_commit(path_project) == str_before


def test_a_conflict_makes_apply_exit_nonzero(tmp_path: Path) -> None:
	"""A caller scripting ``--apply`` must be able to tell it did not finish."""
	path_project, path_bx, _ = _scenario(tmp_path, _BASE, {"a.txt": "mine\n"}, {"a.txt": "new\n"})

	assert _update(path_project, path_bx, "--apply") == 1


def test_a_conflict_is_listed_by_name(tmp_path: Path, capsys: pytest.CaptureFixture) -> None:
	"""The file that needs a human is named in the output."""
	path_project, path_bx, _ = _scenario(tmp_path, _BASE, {"a.txt": "mine\n"}, {"a.txt": "new\n"})

	_update(path_project, path_bx, "--apply")

	assert "conflict (markers written): a.txt" in capsys.readouterr().out


def test_a_stamp_without_a_commit_skips_loudly(
	tmp_path: Path, capsys: pytest.CaptureFixture
) -> None:
	"""An old stamp has no merge base: say so, never pretend the project is up to date."""
	path_project, path_bx, _ = _scenario(
		tmp_path, _BASE, _BASE, {"a.txt": "new\n"}, bool_stamp_commit=False
	)

	_update(path_project, path_bx, "--apply")

	assert "SKIPPED update" in capsys.readouterr().out


def test_a_stamp_without_a_commit_changes_nothing(tmp_path: Path) -> None:
	"""The self-skip happens before any branch or file is touched."""
	path_project, path_bx, _ = _scenario(
		tmp_path, _BASE, _BASE, {"a.txt": "new\n"}, bool_stamp_commit=False
	)

	_update(path_project, path_bx, "--apply")

	assert (path_project / "a.txt").read_text(encoding="utf-8") == "base\n"


def test_a_missing_checkout_skips_loudly(tmp_path: Path, capsys: pytest.CaptureFixture) -> None:
	"""No BlueprintX checkout means nothing to merge from."""
	path_project, _, _ = _scenario(tmp_path, _BASE, _BASE, {"a.txt": "new\n"})

	updater.main(["--root", str(path_project), "--blueprintx-root", str(tmp_path / "absent")])

	assert "SKIPPED" in capsys.readouterr().out


def test_a_dirty_checkout_is_refused(tmp_path: Path) -> None:
	"""Theirs is read from the working tree, so uncommitted template edits must stop --apply."""
	path_project, path_bx, _ = _scenario(tmp_path, _BASE, _BASE, {"a.txt": "new\n"})
	(path_bx / _COMMON / "a.txt").write_text("uncommitted\n", encoding="utf-8")

	assert _update(path_project, path_bx, "--apply") == 1


def test_a_dirty_checkout_leaves_the_project_untouched(tmp_path: Path) -> None:
	"""The refusal happens before any branch or file change."""
	path_project, path_bx, _ = _scenario(tmp_path, _BASE, _BASE, {"a.txt": "new\n"})
	(path_bx / _COMMON / "a.txt").write_text("uncommitted\n", encoding="utf-8")

	_update(path_project, path_bx, "--apply")

	assert (path_project / "a.txt").read_text(encoding="utf-8") == "base\n"


def test_a_listed_source_the_checkout_lacks_blocks_the_stamp(tmp_path: Path) -> None:
	"""A copy whose source is missing is an error, never a silent skip."""
	path_project, path_bx, str_commit = _scenario(tmp_path, _BASE, _BASE, _BASE)

	dict_plan = updater.build_plan(path_project, path_bx, str_commit, {"gone.txt": "gone.txt"})

	assert dict_plan == {"gone.txt": ("error", None)}


def _conflict_then_resolve(path_tmp: Path) -> tuple[Path, Path, str]:
	"""Apply a conflicting update, then replace the conflicted file with a resolution.

	Parameters
	----------
	path_tmp : pathlib.Path
		A temporary directory to build under.

	Returns
	-------
	tuple of (pathlib.Path, pathlib.Path, str)
			The project root, the checkout root and the checkout HEAD.
	"""
	path_project, path_bx, str_head = _scenario(
		path_tmp, _BASE, {"a.txt": "mine\n"}, {"a.txt": "new\n"}
	)
	_update(path_project, path_bx, "--apply")
	(path_project / "a.txt").write_text("resolved\n", encoding="utf-8")
	return path_project, path_bx, str_head


def test_rerunning_after_resolving_a_conflict_advances_the_stamp(tmp_path: Path) -> None:
	"""The branch is reused and a marker-free resolution is accepted."""
	path_project, path_bx, str_head = _conflict_then_resolve(tmp_path)

	_update(path_project, path_bx, "--apply")

	assert drift.read_commit(path_project) == str_head


def test_rerunning_keeps_the_resolution_text(tmp_path: Path) -> None:
	"""A resolved file is never overwritten by a fresh merge on retry."""
	path_project, path_bx, _ = _conflict_then_resolve(tmp_path)

	_update(path_project, path_bx, "--apply")

	assert (path_project / "a.txt").read_text(encoding="utf-8") == "resolved\n"


def test_rerunning_with_markers_still_left_keeps_the_stamp(tmp_path: Path) -> None:
	"""Unresolved markers on retry keep blocking the stamp."""
	path_project, path_bx, _ = _scenario(tmp_path, _BASE, {"a.txt": "mine\n"}, {"a.txt": "new\n"})
	str_before = drift.read_commit(path_project)
	_update(path_project, path_bx, "--apply")

	_update(path_project, path_bx, "--apply")

	assert drift.read_commit(path_project) == str_before
