"""Unit tests for the template-drift gate (blueprintx#109; offline, no scaffold run).

The gate derives what a project MUST contain from the checkout's
``scaffold_python_templates.sh --list-copies`` output (blueprintx#635), so its should-fail
witnesses are about reading that output completely and honestly: every copy it prints is
required, a copy guarded by the roster opt-out is demanded only from a project that opted in,
and a dry run that could not be made is reported as SKIPPED rather than as a clean pass.
The checkouts here are synthetic and their lib is a stand-in speaking the same contract.
"""

import fnmatch
import importlib.util
import io
import os
from pathlib import Path
import subprocess
import sys
import tarfile
from types import ModuleType

import pytest


_BIN = Path(__file__).resolve().parents[2] / "bin"
_COMMON = "templates/python-common"


@pytest.fixture(autouse=True)
def _isolate_env(monkeypatch: pytest.MonkeyPatch) -> None:
	"""Drop the caller's ``GIT_*`` variables so nested calls never reach its repository.

	A pre-commit run exports ``GIT_INDEX_FILE``; without this the throwaway repositories
	these tests build would write to the real index.
	"""
	list(map(monkeypatch.delenv, fnmatch.filter(os.environ, "GIT_*")))


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


gate = _load("check_template_drift")


def _copy(str_src: str, str_dst: str, str_kind: str = "file") -> str:
	"""Return one ``--list-copies`` COPY line.

	Parameters
	----------
	str_src : str
		Source path relative to the checkout.
	str_dst : str
		Destination path relative to the project.
	str_kind : str
		``file`` or ``dir``.

	Returns
	-------
	str
			The tab-separated line.
	"""
	return "\t".join(["COPY", str_kind, str_src, str_dst])


def _checkout(
	path_tmp: Path,
	list_off: list[str],
	list_on: list[str] | None = None,
	list_files: tuple[str, ...] = (),
) -> Path:
	"""Write a synthetic checkout: a stand-in lib speaking the dry-run contract, plus files.

	Parameters
	----------
	path_tmp : pathlib.Path
		A temporary directory to build under.
	list_off : list of str
		Output lines printed with ``--roster false``.
	list_on : list of str or None
		Output lines printed with ``--roster true``; defaults to ``list_off``.
	list_files : tuple of str
		Checkout-relative files to create empty.

	Returns
	-------
	pathlib.Path
			The synthetic root.
	"""
	str_off = "\n".join(list_off)
	str_on = "\n".join(list_off if list_on is None else list_on)
	path_lib = path_tmp / gate._SCAFFOLD_LIB_RELPATH
	path_lib.parent.mkdir(parents=True, exist_ok=True)
	path_lib.write_text(
		f'case "$*" in\n*"--list-copies"*"--roster true"*) cat <<\'X\'\n{str_on}\nX\n;;\n'
		f"*) cat <<'X'\n{str_off}\nX\n;;\nesac\n",
		encoding="utf-8",
	)
	list_paths = [path_tmp / str_f for str_f in list_files]
	list(map(lambda path_f: path_f.parent.mkdir(parents=True, exist_ok=True), list_paths))
	list(map(Path.touch, list_paths))
	return path_tmp


def _git(path_root: Path, *tuple_args: str) -> None:
	"""Run one git command in ``path_root``, failing the test on a non-zero exit.

	Parameters
	----------
	path_root : pathlib.Path
		The repository directory.
	*tuple_args : str
		Arguments after ``git -C <path_root>``.

	Returns
	-------
	None
	"""
	subprocess.run(["git", "-C", str(path_root), *tuple_args], check=True)  # noqa: S603, S607


def _project(path_tmp: Path, str_stamp: str) -> Path:
	"""Create a project directory holding only a provenance stamp.

	Parameters
	----------
	path_tmp : pathlib.Path
		A temporary directory to build under.
	str_stamp : str
		Contents of the provenance file.

	Returns
	-------
	pathlib.Path
			The project root.
	"""
	path_project = path_tmp / "project"
	path_project.mkdir()
	(path_project / gate._PROVENANCE_FILENAME).write_text(str_stamp, encoding="utf-8")
	return path_project


def test_a_project_with_offline_tooling_and_no_github_dir_is_offline(tmp_path: Path) -> None:
	"""`apply_offline_mode` removes `.github` and adds the git-diff scripts."""
	(tmp_path / "bin").mkdir()
	(tmp_path / "bin/git_diff_export.sh").touch()

	assert gate.is_offline_project(tmp_path) is True


def test_a_project_keeping_its_github_dir_is_online(tmp_path: Path) -> None:
	"""An online project that lost `.github` must still be reported, so it is not offline."""
	(tmp_path / "bin").mkdir()
	(tmp_path / "bin/git_diff_export.sh").touch()
	(tmp_path / ".github").mkdir()

	assert gate.is_offline_project(tmp_path) is False


def test_a_printed_copy_is_required(tmp_path: Path) -> None:
	"""Whatever the dry run prints is what the scaffold copies, so it is required."""
	path_root = _checkout(
		tmp_path, [_copy(f"{_COMMON}/a.txt", "a.txt")], list_files=(f"{_COMMON}/a.txt",)
	)

	assert gate.required_relpaths(path_root, "t") == {"a.txt"}


def test_a_copy_in_a_form_no_regex_read_is_required(tmp_path: Path) -> None:
	"""The dry run reports the copy that happened, not the shell text that spelt it."""
	list_off = [_copy(f"{_COMMON}/d/x.md", "docs/renamed.md")]
	path_root = _checkout(tmp_path, list_off, list_files=(f"{_COMMON}/d/x.md",))

	assert gate.required_relpaths(path_root, "t") == {"docs/renamed.md"}


def test_the_roster_copy_is_not_required_by_default(tmp_path: Path) -> None:
	"""`.review-bots.yaml` is copied only when the scaffold answered yes (blueprintx#374)."""
	list_on = [_copy(f"{_COMMON}/.review-bots.yaml", ".review-bots.yaml")]
	path_root = _checkout(tmp_path, [], list_on, (f"{_COMMON}/.review-bots.yaml",))

	assert gate.required_relpaths(path_root, "t") == set()


def test_the_roster_copy_is_required_after_opting_in(tmp_path: Path) -> None:
	"""The opt-in flag is passed to the dry run, which then prints the guarded copy."""
	list_on = [_copy(f"{_COMMON}/.review-bots.yaml", ".review-bots.yaml")]
	path_root = _checkout(tmp_path, [], list_on, (f"{_COMMON}/.review-bots.yaml",))

	assert gate.required_relpaths(path_root, "t", bool_roster=True) == {".review-bots.yaml"}


def test_provenance_records_the_roster_choice(tmp_path: Path) -> None:
	"""The stamp is what lets the checker recover an opt-out instead of guessing."""
	path_project = _project(tmp_path, "tier: mvc-service-native-db\nreview_bot_roster: false\n")

	assert gate.review_bot_roster_enabled(path_project) is False


def test_a_project_predating_the_stamp_reads_as_unknown(tmp_path: Path) -> None:
	"""`None`, never `False` — the caller must not assume either answer for old projects."""
	path_project = _project(tmp_path, "tier: mvc-service-native-db\n")

	assert gate.review_bot_roster_enabled(path_project) is None


def test_a_directory_copy_requires_every_file_under_it(tmp_path: Path) -> None:
	"""`cp -r dir/. dst` ships every file in dir, nested ones included."""
	list_off = [_copy(f"{_COMMON}/bin", "bin", "dir")]
	list_files = (f"{_COMMON}/bin/a.sh", f"{_COMMON}/bin/lib/b.sh")
	path_root = _checkout(tmp_path, list_off, list_files=list_files)

	assert gate.required_relpaths(path_root, "t") == {"bin/a.sh", "bin/lib/b.sh"}


def test_bytecode_under_a_copied_directory_is_not_required(tmp_path: Path) -> None:
	"""A `__pycache__` in the checkout's bin/ is an untracked artifact, never a template file."""
	list_off = [_copy(f"{_COMMON}/bin", "bin", "dir")]
	list_files = (f"{_COMMON}/bin/__pycache__/x.cpython-312.pyc", f"{_COMMON}/bin/a.sh")
	path_root = _checkout(tmp_path, list_off, list_files=list_files)

	assert gate.required_relpaths(path_root, "t") == {"bin/a.sh"}


def test_untracked_files_in_a_git_checkout_are_not_required(tmp_path: Path) -> None:
	"""Only tracked files are template files; a stray untracked one is never 'missing'."""
	list_off = [_copy(f"{_COMMON}/bin", "bin", "dir")]
	list_files = (f"{_COMMON}/bin/tracked.sh", f"{_COMMON}/bin/stray.log")
	path_root = _checkout(tmp_path, list_off, list_files=list_files)
	_git(path_root, "init", "-q")
	_git(path_root, "add", "-f", f"{_COMMON}/bin/tracked.sh")

	assert gate.required_relpaths(path_root, "t") == {"bin/tracked.sh"}


def test_an_untracked_file_a_glob_matched_is_not_required(tmp_path: Path) -> None:
	"""A draft the shell glob picked up but git does not track is not a template file."""
	list_off = [_copy(f"{_COMMON}/a.md", "a.md"), _copy(f"{_COMMON}/draft.md", "draft.md")]
	path_root = _checkout(
		tmp_path, list_off, list_files=(f"{_COMMON}/a.md", f"{_COMMON}/draft.md")
	)
	_git(path_root, "init", "-q")
	_git(path_root, "add", "-f", f"{_COMMON}/a.md")

	assert gate.required_relpaths(path_root, "t") == {"a.md"}


def test_a_copy_from_the_language_agnostic_root_is_required(tmp_path: Path) -> None:
	"""`templates/common/` copies are shipped to every project too."""
	list_off = [_copy("templates/common/bin/ship.sh", "bin/ship.sh")]
	path_root = _checkout(tmp_path, list_off, list_files=("templates/common/bin/ship.sh",))

	assert gate.required_relpaths(path_root, "t") == {"bin/ship.sh"}


@pytest.mark.parametrize("str_src", ["templates/mvc-service-native-db/AGENTS.md", "bin/ci/x.sh"])
def test_a_copy_from_outside_the_policed_roots_is_not_required(
	tmp_path: Path, str_src: str
) -> None:
	"""Tier-specific and BlueprintX-internal sources are out of scope, as they always were."""
	path_root = _checkout(tmp_path, [_copy(str_src, "x")], list_files=(str_src,))

	assert gate.required_relpaths(path_root, "t") == set()


def test_a_destination_the_scaffold_removes_is_not_required(tmp_path: Path) -> None:
	"""`rm -f dst/.keep` after a directory copy: the project never has it, so not drift."""
	list_off = [_copy(f"{_COMMON}/d", "d", "dir"), "RM\td/.keep"]
	path_root = _checkout(
		tmp_path, list_off, list_files=(f"{_COMMON}/d/.keep", f"{_COMMON}/d/real.py")
	)

	assert gate.required_relpaths(path_root, "t") == {"d/real.py"}


def test_a_removal_with_a_doubled_separator_still_matches(tmp_path: Path) -> None:
	"""`d//.keep` and `d/.keep` are the same file."""
	list_off = [_copy(f"{_COMMON}/d", "d", "dir"), "RM\td//.keep"]
	path_root = _checkout(
		tmp_path, list_off, list_files=(f"{_COMMON}/d/.keep", f"{_COMMON}/d/real.py")
	)

	assert gate.required_relpaths(path_root, "t") == {"d/real.py"}


def test_a_removed_directory_removes_everything_under_it(tmp_path: Path) -> None:
	"""`rm -rf dst/sub` takes its contents with it."""
	list_off = [_copy(f"{_COMMON}/d", "d", "dir"), "RM\td/sub"]
	path_root = _checkout(
		tmp_path, list_off, list_files=(f"{_COMMON}/d/sub/x.py", f"{_COMMON}/d/y.py")
	)

	assert gate.required_relpaths(path_root, "t") == {"d/y.py"}


def test_a_lib_that_prints_nothing_requires_nothing_and_says_skipped(
	tmp_path: Path, capsys: pytest.CaptureFixture
) -> None:
	"""Zero required paths is blindness, not a clean comparison: it must SKIP loudly."""
	path_root = _checkout(tmp_path / "bx", [])
	path_project = _project(tmp_path, "tier: mvc-service-native-db\n")

	gate.main(["--root", str(path_project), "--blueprintx-root", str(path_root)])

	assert "SKIPPED" in capsys.readouterr().out


def test_a_failing_dry_run_is_skipped_not_reported_clean(
	tmp_path: Path, capsys: pytest.CaptureFixture
) -> None:
	"""A lib that exits non-zero must not read as 'no required paths, no drift'."""
	path_lib = tmp_path / "bx" / gate._SCAFFOLD_LIB_RELPATH
	path_lib.parent.mkdir(parents=True)
	path_lib.write_text("exit 3\n", encoding="utf-8")
	path_project = _project(tmp_path, "tier: mvc-service-native-db\n")

	gate.main(["--root", str(path_project), "--blueprintx-root", str(tmp_path / "bx")])

	assert "SKIPPED" in capsys.readouterr().out


def test_roster_opt_in_against_a_checkout_without_the_lib_skips_instead_of_crashing(
	tmp_path: Path, capsys: pytest.CaptureFixture
) -> None:
	"""A checkout with no scaffold lib at all is a SKIP, never a traceback."""
	path_project = _project(tmp_path, "tier: mvc-service-native-db\nreview_bot_roster: true\n")
	path_empty_checkout = tmp_path / "checkout"
	path_empty_checkout.mkdir()

	gate.main(["--root", str(path_project), "--blueprintx-root", str(path_empty_checkout)])

	assert "SKIPPED" in capsys.readouterr().out


def test_an_opted_in_project_is_told_about_the_missing_roster_file(
	tmp_path: Path, capsys: pytest.CaptureFixture
) -> None:
	"""End to end: the stamp's roster choice reaches the dry run and the report names the file."""
	list_on = [_copy(f"{_COMMON}/.review-bots.yaml", ".review-bots.yaml")]
	path_root = _checkout(tmp_path / "bx", [], list_on, (f"{_COMMON}/.review-bots.yaml",))
	path_project = _project(tmp_path, "tier: mvc-service-native-db\nreview_bot_roster: true\n")

	gate.main(["--root", str(path_project), "--blueprintx-root", str(path_root)])

	assert "➖ .review-bots.yaml" in capsys.readouterr().out


def test_a_project_that_declined_the_roster_is_not_told_it_is_missing(
	tmp_path: Path, capsys: pytest.CaptureFixture
) -> None:
	"""The false positive blueprintx#374 removed must stay removed."""
	list_off = [_copy(f"{_COMMON}/a.txt", "a.txt")]
	list_on = [*list_off, _copy(f"{_COMMON}/.review-bots.yaml", ".review-bots.yaml")]
	path_root = _checkout(tmp_path / "bx", list_off, list_on, (f"{_COMMON}/a.txt",))
	path_project = _project(tmp_path, "tier: mvc-service-native-db\nreview_bot_roster: false\n")
	(path_project / "a.txt").touch()

	gate.main(["--root", str(path_project), "--blueprintx-root", str(path_root)])

	assert "No template drift detected" in capsys.readouterr().out


def test_the_equals_form_of_a_flag_is_honoured(tmp_path: Path) -> None:
	"""`--root=x` used to be ignored silently, so the check ran against cwd without saying so."""
	path_root, _ = gate._parse_args([f"--root={tmp_path}"])

	assert path_root == tmp_path.resolve()


def test_a_flag_without_a_value_fails_loudly() -> None:
	"""A valueless `--root` must not silently fall back to cwd."""
	with pytest.raises(SystemExit):
		gate._parse_args(["--root"])


def _no_git(*args: object, **kwargs: object) -> None:
	"""Stand in for ``subprocess.run`` on a host without git."""
	raise FileNotFoundError("git")


def test_a_missing_git_executable_falls_back_to_the_directory_walk(
	tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
	"""No ``git`` on PATH is treated like a failed git command, not a crash."""
	path_dir = tmp_path / "tpl"
	path_dir.mkdir()
	(path_dir / "a.txt").write_text("x", encoding="utf-8")

	monkeypatch.setattr(subprocess, "run", _no_git)

	assert gate._template_files(tmp_path, path_dir) == ["a.txt"]


def test_lib_minimal_reads_its_own_scaffold_entry_not_the_shared_lib(
	tmp_path: Path, capsys: pytest.CaptureFixture
) -> None:
	"""lib-minimal answers ``--list-copies`` from its own script, so its copies are required.

	Parameters
	----------
	tmp_path : Path
		Pytest temp dir used as the project root.
	capsys : pytest.CaptureFixture
		Captures the printed report.
	"""
	path_root = _checkout(tmp_path / "bx", [], list_files=(f"{_COMMON}/a.txt",))
	path_entry = path_root / gate._TIER_LIST_SCRIPTS["lib-minimal"]
	path_entry.parent.mkdir(parents=True, exist_ok=True)
	path_entry.write_text(
		f"# --list-copies\nprintf 'COPY\\tfile\\t{_COMMON}/a.txt\\ta.txt\\n'\n", encoding="utf-8"
	)
	path_project = _project(tmp_path, "tier: lib-minimal\n")

	gate.main(["--root", str(path_project), "--blueprintx-root", str(path_root)])

	assert "➖ a.txt" in capsys.readouterr().out


def _versioned_checkout(path_tmp: Path) -> tuple[Path, str]:
	"""Build a checkout whose one template file is committed as ``base``.

	Parameters
	----------
	path_tmp : pathlib.Path
		A temporary directory to build under.

	Returns
	-------
	tuple of (pathlib.Path, str)
			The checkout root and the commit that holds the base content.
	"""
	path_root = _checkout(
		path_tmp / "bx", [_copy(f"{_COMMON}/a.txt", "a.txt")], list_files=(f"{_COMMON}/a.txt",)
	)
	(path_root / _COMMON / "a.txt").write_bytes(b"base\n")
	_git(path_root, "init", "-q")
	_git(path_root, "add", "-A")
	_git(
		path_root,
		*("-c", "user.name=t", "-c", "user.email=t@t", "-c", "commit.gpgsign=false"),
		*("commit", "-q", "-m", "base"),
	)
	cls_head = subprocess.run(  # noqa: S603
		["git", "-C", str(path_root), "rev-parse", "HEAD"],  # noqa: S607
		capture_output=True,
		encoding="utf-8",
		check=True,
	)
	return path_root, cls_head.stdout.strip()


def _drift_output(
	path_tmp: Path,
	capsys: pytest.CaptureFixture,
	str_ours: str,
	str_theirs: str,
	bool_stamp_commit: bool = True,
) -> str:
	"""Run the reporter with the project at ``str_ours`` and the template now at ``str_theirs``.

	Parameters
	----------
	path_tmp : pathlib.Path
		A temporary directory to build under.
	capsys : pytest.CaptureFixture
		Captures the printed report.
	str_ours : str
		The project's content for the template file.
	str_theirs : str
		The template's current content (the committed base stays ``base``).
	bool_stamp_commit : bool
		Whether the provenance stamp carries ``blueprintx_commit``.

	Returns
	-------
	str
			Everything the reporter printed.
	"""
	path_root, str_sha = _versioned_checkout(path_tmp)
	# Bytes, because Windows text mode would turn the CRLF a test asks for into CR CR LF.
	(path_root / _COMMON / "a.txt").write_bytes(str_theirs.encode())
	str_commit_line = f"blueprintx_commit: {str_sha}\n" if bool_stamp_commit else ""
	path_project = _project(path_tmp, f"tier: mvc-service-native-db\n{str_commit_line}")
	(path_project / "a.txt").write_bytes(str_ours.encode())
	capsys.readouterr()
	gate.main(["--root", str(path_project), "--blueprintx-root", str(path_root)])
	return capsys.readouterr().out


def test_an_untouched_file_the_template_changed_is_reported(
	tmp_path: Path, capsys: pytest.CaptureFixture
) -> None:
	"""Project equals base, template moved on: the fast-forward case."""
	str_out = _drift_output(tmp_path, capsys, "base\n", "new\n")

	assert "template changed since scaffold: a.txt" in str_out


def test_a_file_changed_on_both_sides_is_reported_as_both(
	tmp_path: Path, capsys: pytest.CaptureFixture
) -> None:
	"""Project and template both moved off base: the merge case."""
	str_out = _drift_output(tmp_path, capsys, "mine\n", "new\n")

	assert "both changed: a.txt" in str_out


def test_a_local_edit_the_template_never_touched_is_not_drift(
	tmp_path: Path, capsys: pytest.CaptureFixture
) -> None:
	"""A project's own edit, with the template unchanged, must stay silent."""
	str_out = _drift_output(tmp_path, capsys, "mine\n", "base\n")

	assert "changed" not in str_out


def test_a_stamp_without_a_commit_skips_content_drift_loudly(
	tmp_path: Path, capsys: pytest.CaptureFixture
) -> None:
	"""No merge base is a SKIPPED line, never a clean content verdict."""
	str_out = _drift_output(tmp_path, capsys, "base\n", "new\n", bool_stamp_commit=False)

	assert "SKIPPED content drift" in str_out


def _write_files(path_root: Path, dict_files: dict[str, str]) -> None:
	"""Write text files under ``path_root``, creating parent directories.

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
	list_paths = [path_root / str_rel for str_rel in dict_files]
	list(map(lambda path_f: path_f.parent.mkdir(parents=True, exist_ok=True), list_paths))
	list(map(Path.write_text, list_paths, dict_files.values()))


def _commit_all(path_root: Path, str_message: str) -> str:
	"""Stage everything, commit without signing and return the new commit.

	Parameters
	----------
	path_root : pathlib.Path
		The repository directory.
	str_message : str
		The commit message.

	Returns
	-------
	str
			The full sha of the new commit.
	"""
	_git(path_root, "add", "-A")
	_git(
		path_root,
		*("-c", "user.name=t", "-c", "user.email=t@t", "-c", "commit.gpgsign=false"),
		*("commit", "-q", "-m", str_message),
	)
	cls_head = subprocess.run(  # noqa: S603
		["git", "-C", str(path_root), "rev-parse", "HEAD"],  # noqa: S607
		capture_output=True,
		encoding="utf-8",
		check=True,
	)
	return cls_head.stdout.strip()


def _copy_lines(dict_files: dict[str, str]) -> list[str]:
	"""Return the dry-run COPY lines for template files named like their project paths.

	Parameters
	----------
	dict_files : dict[str, str]
		Project-relative path to content.

	Returns
	-------
	list of str
			One COPY line per path.
	"""
	return [_copy(f"{_COMMON}/{str_rel}", str_rel) for str_rel in dict_files]


def _removal_output(
	path_tmp: Path,
	capsys: pytest.CaptureFixture,
	dict_then: dict[str, str],
	dict_now: dict[str, str],
	tuple_deleted: tuple[str, ...] = (),
) -> str:
	"""Run the reporter for a project scaffolded from ``dict_then`` against ``dict_now``.

	The checkout commits ``dict_then`` (with a dry run listing it), then commits ``dict_now``
	(with a dry run listing that); the project holds every ``dict_then`` file except
	``tuple_deleted`` and is stamped with the first commit.

	Parameters
	----------
	path_tmp : pathlib.Path
		A temporary directory to build under.
	capsys : pytest.CaptureFixture
		Captures the printed report.
	dict_then : dict[str, str]
		Template files, by project path, at the stamped commit.
	dict_now : dict[str, str]
		Template files, by project path, at the current commit.
	tuple_deleted : tuple[str, ...]
		Project paths the project owner deleted.

	Returns
	-------
	str
			Everything the reporter printed.
	"""
	path_root = path_tmp / "bx"
	path_tpl = path_root / _COMMON
	_checkout(path_root, _copy_lines(dict_then))
	_write_files(path_tpl, dict_then)
	_git(path_root, "init", "-q")
	str_sha = _commit_all(path_root, "base")
	list(map(lambda str_rel: (path_tpl / str_rel).unlink(), set(dict_then) - set(dict_now)))
	_write_files(path_tpl, dict_now)
	_checkout(path_root, _copy_lines(dict_now))
	_commit_all(path_root, "template moves on")
	path_project = _project(
		path_tmp, f"tier: mvc-service-native-db\nblueprintx_commit: {str_sha}\n"
	)
	_write_files(path_project, dict_then)
	list(map(lambda str_rel: (path_project / str_rel).unlink(), tuple_deleted))
	capsys.readouterr()
	gate.main(["--root", str(path_project), "--blueprintx-root", str(path_root)])
	return capsys.readouterr().out


_KEPT = {"a.txt": "kept\n" * 8}
_DROPPED = {"dropped.txt": "dropped\n" * 8}
_RENAMED = {"old_name.txt": "renamed\n" * 8}


def test_a_file_the_template_dropped_is_reported_as_removed(
	tmp_path: Path, capsys: pytest.CaptureFixture
) -> None:
	"""The template stopped shipping it and the project still has it."""
	str_out = _removal_output(tmp_path, capsys, _KEPT | _DROPPED | _RENAMED, _KEPT)

	assert "removed: dropped.txt" in str_out


def test_a_file_the_template_renamed_names_its_successor(
	tmp_path: Path, capsys: pytest.CaptureFixture
) -> None:
	"""A git rename between the two commits is the successor."""
	dict_now = _KEPT | {"new_name.txt": _RENAMED["old_name.txt"]}

	str_out = _removal_output(tmp_path, capsys, _KEPT | _RENAMED, dict_now)

	assert "replaced by new_name.txt: old_name.txt" in str_out


@pytest.mark.parametrize(
	("str_old", "str_new"),
	[
		("Makefile", "poe_tasks.toml"),
		("tasks.sh", "poe_tasks.toml"),
		("make/library.mk", "poe_tasks.library.toml"),
	],
)
def test_a_known_non_rename_successor_comes_from_the_rule_table(
	tmp_path: Path, capsys: pytest.CaptureFixture, str_old: str, str_new: str
) -> None:
	"""The make-to-poe move is a rewrite, not a rename, so git cannot name the successor."""
	str_out = _removal_output(
		tmp_path, capsys, _KEPT | {str_old: "old\n" * 8}, _KEPT | {str_new: "[tool.poe]\n" * 8}
	)

	assert f"replaced by {str_new}: {str_old}" in str_out


def test_a_rule_table_successor_the_template_no_longer_ships_is_only_removed(
	tmp_path: Path, capsys: pytest.CaptureFixture
) -> None:
	"""The table is consulted only for a successor the current copy list really holds."""
	str_out = _removal_output(tmp_path, capsys, _KEPT | {"Makefile": "old\n" * 8}, _KEPT)

	assert "removed: Makefile" in str_out


def test_a_dropped_file_the_project_already_deleted_is_not_reported(
	tmp_path: Path, capsys: pytest.CaptureFixture
) -> None:
	"""Only files that still exist in the project are drift."""
	str_out = _removal_output(tmp_path, capsys, _KEPT | _DROPPED, _KEPT, ("dropped.txt",))

	assert "dropped.txt" not in str_out


def test_a_stamped_commit_whose_dry_run_cannot_be_made_is_skipped_loudly(
	tmp_path: Path, capsys: pytest.CaptureFixture
) -> None:
	"""A commit predating ``--list-copies`` has no copy list, which is not 'nothing removed'."""
	path_root = tmp_path / "bx"
	_write_files(path_root / _COMMON, _KEPT)
	_git(path_root, "init", "-q")
	str_sha = _commit_all(path_root, "before the dry run existed")
	_checkout(path_root, _copy_lines(_KEPT))
	_commit_all(path_root, "dry run added")
	path_project = _project(
		tmp_path, f"tier: mvc-service-native-db\nblueprintx_commit: {str_sha}\n"
	)
	capsys.readouterr()

	gate.main(["--root", str(path_project), "--blueprintx-root", str(path_root)])

	assert "SKIPPED removed-file check" in capsys.readouterr().out


def test_a_lib_that_predates_list_copies_is_never_executed(tmp_path: Path) -> None:
	"""An entry script without the flag would run its interactive main, so it is not run."""
	path_lib = tmp_path / gate._SCAFFOLD_LIB_RELPATH
	path_lib.parent.mkdir(parents=True)
	path_lib.write_text(f"touch {tmp_path}/ran\necho COPY\n", encoding="utf-8")

	gate.required_sources(tmp_path, "mvc-service-native-db")

	assert not (tmp_path / "ran").exists()


def test_a_source_kept_but_copied_to_a_new_path_names_its_successor(
	tmp_path: Path, capsys: pytest.CaptureFixture
) -> None:
	"""No git rename exists when only the destination moved, so the same source is the link."""
	list_then = [_copy(f"{_COMMON}/shared.txt", "old/shared.txt")]
	path_root = tmp_path / "bx"
	_checkout(path_root, list_then)
	_write_files(path_root / _COMMON, {"shared.txt": "shared\n" * 8})
	_git(path_root, "init", "-q")
	str_sha = _commit_all(path_root, "base")
	_checkout(path_root, [_copy(f"{_COMMON}/shared.txt", "new/shared.txt")])
	_commit_all(path_root, "destination moves")
	path_project = _project(
		tmp_path, f"tier: mvc-service-native-db\nblueprintx_commit: {str_sha}\n"
	)
	_write_files(path_project, {"old/shared.txt": "shared\n" * 8})
	capsys.readouterr()

	gate.main(["--root", str(path_project), "--blueprintx-root", str(path_root)])

	assert "replaced by new/shared.txt: old/shared.txt" in capsys.readouterr().out


def test_a_skipped_removed_check_is_not_summed_up_as_a_clean_run(
	tmp_path: Path, capsys: pytest.CaptureFixture
) -> None:
	"""A check that did not run must not leave a bare 'No template drift detected'."""
	path_root = tmp_path / "bx"
	_write_files(path_root / _COMMON, _KEPT)
	_checkout(path_root, _copy_lines(_KEPT))
	path_lib = path_root / gate._SCAFFOLD_LIB_RELPATH
	path_lib.write_text("exit 0\n", encoding="utf-8")
	_git(path_root, "init", "-q")
	str_sha = _commit_all(path_root, "base predates the flag")
	_checkout(path_root, _copy_lines(_KEPT))
	_commit_all(path_root, "flag added")
	path_project = _project(
		tmp_path, f"tier: mvc-service-native-db\nblueprintx_commit: {str_sha}\n"
	)
	_write_files(path_project, _KEPT)
	capsys.readouterr()

	gate.main(["--root", str(path_project), "--blueprintx-root", str(path_root)])

	assert "(not every check ran)" in capsys.readouterr().out


def test_a_stamp_without_scaffold_commit_falls_back_to_the_stamped_commit(
	tmp_path: Path,
) -> None:
	"""Projects scaffolded before the field existed still have a measuring point."""
	path_project = _project(tmp_path, "tier: lib-minimal\nblueprintx_commit: abc123\n")

	assert gate.read_scaffold_commit(path_project) == "abc123"


def test_the_removed_summary_counts_the_orphans(
	tmp_path: Path, capsys: pytest.CaptureFixture
) -> None:
	"""The count line says how many files the template no longer ships."""
	str_out = _removal_output(tmp_path, capsys, _KEPT | _DROPPED | _RENAMED, _KEPT)

	assert "2 file(s) the template no longer ships" in str_out


def test_a_removal_is_not_summed_up_as_no_drift(
	tmp_path: Path, capsys: pytest.CaptureFixture
) -> None:
	"""Orphans alone suppress the clean-run line."""
	str_out = _removal_output(tmp_path, capsys, _KEPT | _DROPPED, _KEPT)

	assert "No template drift detected" not in str_out


def test_a_non_ascii_rename_names_its_successor(
	tmp_path: Path, capsys: pytest.CaptureFixture
) -> None:
	"""NUL-separated output keeps unusual paths intact, so the rename is still found."""
	dict_old = {"ação.txt": "renamed\n" * 8}
	dict_now = _KEPT | {"action.txt": dict_old["ação.txt"]}

	str_out = _removal_output(tmp_path, capsys, _KEPT | dict_old, dict_now)

	assert "replaced by action.txt: ação.txt" in str_out


def test_an_archive_member_outside_the_destination_is_not_written(tmp_path: Path) -> None:
	"""A traversal path in the tarball is skipped."""
	cls_buf = io.BytesIO()
	with tarfile.open(fileobj=cls_buf, mode="w") as cls_tar:
		cls_info = tarfile.TarInfo("../escaped.txt")
		cls_info.size = 1
		cls_tar.addfile(cls_info, io.BytesIO(b"x"))

	gate._unpack_archive(cls_buf.getvalue(), tmp_path / "dest")

	assert not (tmp_path / "escaped.txt").exists()


def test_a_scaffold_commit_the_checkout_does_not_know_is_skipped_loudly(
	tmp_path: Path, capsys: pytest.CaptureFixture
) -> None:
	"""A usable but unreachable scaffold commit must say why the check did not run."""
	path_root = tmp_path / "bx"
	_write_files(path_root / _COMMON, _KEPT)
	_checkout(path_root, _copy_lines(_KEPT))
	_git(path_root, "init", "-q")
	str_sha = _commit_all(path_root, "base")
	path_project = _project(
		tmp_path,
		f"tier: mvc-service-native-db\nblueprintx_commit: {str_sha}\n"
		f"scaffold_commit: {'0' * 40}\n",
	)
	capsys.readouterr()

	gate.main(["--root", str(path_project), "--blueprintx-root", str(path_root)])

	assert "SKIPPED removed-file check: the scaffold_commit" in capsys.readouterr().out


def test_a_crlf_checkout_of_an_untouched_file_is_template_changed_not_both(
	tmp_path: Path, capsys: pytest.CaptureFixture
) -> None:
	"""An autocrlf working tree must not turn an untouched file into 'both changed'."""
	str_out = _drift_output(tmp_path, capsys, "base\r\n", "new\r\n")

	assert "template changed since scaffold: a.txt" in str_out


def _output_without_template_source(path_tmp: Path, capsys: pytest.CaptureFixture) -> str:
	"""Run the reporter when the checkout lost the template file the project still has.

	Parameters
	----------
	path_tmp : pathlib.Path
		A temporary directory to build under.
	capsys : pytest.CaptureFixture
		Captures the printed report.

	Returns
	-------
	str
			Everything the reporter printed.
	"""
	path_root, str_sha = _versioned_checkout(path_tmp)
	(path_root / _COMMON / "a.txt").unlink()
	path_project = _project(
		path_tmp, f"tier: mvc-service-native-db\nblueprintx_commit: {str_sha}\n"
	)
	(path_project / "a.txt").write_text("base\n", encoding="utf-8")
	capsys.readouterr()
	gate.main(["--root", str(path_project), "--blueprintx-root", str(path_root)])
	return capsys.readouterr().out


def test_a_template_source_missing_from_the_checkout_is_reported(
	tmp_path: Path, capsys: pytest.CaptureFixture
) -> None:
	"""A managed file never compared against anything is named, not skipped silently."""
	assert "not compared" in _output_without_template_source(tmp_path, capsys)


def test_a_template_source_missing_from_the_checkout_is_not_a_clean_verdict(
	tmp_path: Path, capsys: pytest.CaptureFixture
) -> None:
	"""An unchecked file must never end in 'No template drift detected'."""
	str_out = _output_without_template_source(tmp_path, capsys)

	assert "No template drift detected" not in str_out


def test_a_directory_at_a_required_path_is_missing(tmp_path: Path) -> None:
	"""Only a regular file satisfies a required path."""
	(tmp_path / "a.txt").mkdir()

	assert gate.missing_relpaths(tmp_path, {"a.txt"}) == ["a.txt"]


def test_a_git_checkout_with_no_tracked_files_in_a_dir_lists_nothing(tmp_path: Path) -> None:
	"""A successful ``git ls-files`` that lists nothing is an answer, not a reason to walk."""
	path_dir = tmp_path / "tpl"
	path_dir.mkdir()
	(path_dir / "stray.txt").write_text("x", encoding="utf-8")
	_git(tmp_path, "init", "-q")

	assert gate._template_files(tmp_path, path_dir) == []


def test_a_stamp_that_is_not_an_ancestor_of_head_is_no_merge_base(tmp_path: Path) -> None:
	"""A commit that exists but is not in HEAD's history cannot anchor a comparison."""
	path_root, str_sha = _versioned_checkout(tmp_path)
	_git(
		path_root,
		*("-c", "user.name=t", "-c", "user.email=t@t", "-c", "commit.gpgsign=false"),
		*("commit", "-q", "--allow-empty", "-m", "next"),
	)
	cls_head = subprocess.run(  # noqa: S603
		["git", "-C", str(path_root), "rev-parse", "HEAD"],  # noqa: S607
		capture_output=True,
		encoding="utf-8",
		check=True,
	)
	str_next = cls_head.stdout.strip()
	_git(path_root, "checkout", "-q", str_sha)

	assert gate.commit_known(path_root, str_next) is False
