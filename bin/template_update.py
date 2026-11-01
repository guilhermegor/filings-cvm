"""Bring template fixes into a scaffolded project with a three-way merge (blueprintx#872).

``check_template_drift.py`` only reports. This script acts on the same base/ours/theirs data:
base is the template file at the stamped ``blueprintx_commit``, theirs is the file in the
BlueprintX checkout now, ours is the project's file. Per template-managed path:

- the project file is missing: add it;
- the project file equals base: fast-forward to theirs;
- the project edited it: ``git merge-file`` base/ours/theirs. A clean merge is written, a
  conflict is written with markers and listed. A local edit is never overwritten silently.

Dry run by default. ``--apply`` creates ``chore/template-update-<short-sha>`` (never the
current branch), writes the files and rewrites ``blueprintx_commit`` in the stamp only when
every file applied cleanly. Nothing is committed. A conflict or an unmergeable file makes
``--apply`` exit 1; a self-skip (no stamp, no checkout, no usable commit) prints why and
exits 0, like the reporter. Rationale: ``docs/template-updates.md``.
"""

import argparse
import os
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile

import check_template_drift as drift


_MAX_CONFLICTS = 127
_BLOCKING = frozenset({"conflict", "error"})
_LABELS = {
    "add": "➕ add:",
    "fast_forward": "⬆️ fast-forward:",
    "merged": "🔀 merged cleanly:",
    "conflict": "⚠️ conflict (markers written):",
    "error": "❌ unmergeable (left untouched):",
}
_RE_STAMP_COMMIT = re.compile(r"^blueprintx_commit:.*$", re.MULTILINE)
_RE_MARKERS = re.compile(r"^(<<<<<<< |>>>>>>> )", re.MULTILINE)
_MERGE_ACTIONS = frozenset({"merged", "conflict"})
_TRIVIAL = frozenset({"add", "fast_forward"})


def _git_env() -> dict[str, str]:
    """Return the environment without the ``GIT_*`` variables a hook may have exported.

    Returns
    -------
    dict of str to str
            A copy of ``os.environ`` that cannot redirect git at another repository.
    """
    return {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}


def merge_three_way(
    bytes_ours: bytes, bytes_base: bytes, bytes_theirs: bytes
) -> tuple[bytes | None, int]:
    """Merge two edits of one base with ``git merge-file``.

    Parameters
    ----------
    bytes_ours : bytes
        The project's content.
    bytes_base : bytes
        The template content at the stamped commit.
    bytes_theirs : bytes
        The template content now.

    Returns
    -------
    tuple of (bytes or None, int)
            The merged content (with conflict markers when there are conflicts) and the number
            of conflicts; ``(None, -1)`` when git could not merge the files.
    """
    with tempfile.TemporaryDirectory() as str_dir:
        path_dir = pathlib.Path(str_dir)
        (path_dir / "ours").write_bytes(bytes_ours)
        (path_dir / "base").write_bytes(bytes_base)
        (path_dir / "theirs").write_bytes(bytes_theirs)
        cls_run = subprocess.run(  # noqa: S603
            ["git", "merge-file", "-p", "-L", "ours", "-L", "base", "-L", "template"]  # noqa: S607
            + ["ours", "base", "theirs"],
            cwd=path_dir,
            capture_output=True,
            check=False,
            env=_git_env(),
        )
    if cls_run.returncode > _MAX_CONFLICTS:
        return None, -1
    return cls_run.stdout, cls_run.returncode


def plan_file(
    path_project_file: pathlib.Path, path_theirs: pathlib.Path, bytes_base: bytes | None
) -> tuple[str, bytes | None]:
    """Decide what to do with one template-managed file.

    Parameters
    ----------
    path_project_file : pathlib.Path
        The project's copy, which may not exist.
    path_theirs : pathlib.Path
        The template file in the current checkout.
    bytes_base : bytes or None
        The template file at the stamped commit; ``None`` when it did not exist then.

    Returns
    -------
    tuple of (str, bytes or None)
            ``(action, new content)``. The action is ``same``, ``add``, ``fast_forward``,
            ``merged``, ``conflict`` or ``error``; the content is ``None`` for ``same`` and
            ``error``.
    """
    bytes_theirs = path_theirs.read_bytes()
    if not path_project_file.is_file():
        return "add", bytes_theirs
    bytes_ours = path_project_file.read_bytes()
    if bytes_theirs in (bytes_ours, bytes_base):
        return "same", None
    if bytes_ours == bytes_base:
        return "fast_forward", bytes_theirs
    bytes_merged, int_conflicts = merge_three_way(bytes_ours, bytes_base or b"", bytes_theirs)
    if bytes_merged is None:
        return "error", None
    return ("conflict" if int_conflicts else "merged"), bytes_merged


def build_plan(
    path_root: pathlib.Path,
    path_blueprintx: pathlib.Path,
    str_commit: str,
    dict_sources: dict[str, str],
) -> dict[str, tuple[str, bytes | None]]:
    """Plan every template-managed file that is not already identical to the template.

    Parameters
    ----------
    path_root : pathlib.Path
        The project root.
    path_blueprintx : pathlib.Path
        Root of a BlueprintX checkout.
    str_commit : str
        The commit stamped at scaffold time (the merge base).
    dict_sources : dict of str to str
        Project-relative path to checkout-relative template source.

    Returns
    -------
    dict of str to tuple of (str, bytes or None)
            Project-relative path to ``(action, new content)``, sorted, without ``same``. A
            source the copy list names but the checkout lacks is an ``error``, so it blocks the
            stamp instead of being skipped.
    """
    dict_plan = {
        str_rel: plan_file(
            path_root / str_rel,
            path_blueprintx / str_src,
            drift.base_blob(path_blueprintx, str_commit, str_src),
        )
        if (path_blueprintx / str_src).is_file()
        else ("error", None)
        for str_rel, str_src in sorted(dict_sources.items())
    }
    return {k: v for k, v in dict_plan.items() if v[0] != "same"}


def _head(path_blueprintx: pathlib.Path, bool_short: bool) -> str | None:
    """Return the checkout's HEAD commit, abbreviated or full.

    Parameters
    ----------
    path_blueprintx : pathlib.Path
        Root of a BlueprintX checkout.
    bool_short : bool
        Abbreviate the commit.

    Returns
    -------
    str or None
            The commit, or ``None`` when git cannot answer.
    """
    list_argv = ["git", "-C", str(path_blueprintx), "rev-parse"]
    list_argv += ["--short=10", "HEAD"] if bool_short else ["HEAD"]
    cls_run = subprocess.run(  # noqa: S603
        list_argv, capture_output=True, encoding="utf-8", check=False, env=_git_env()
    )
    str_out = cls_run.stdout.strip()
    return str_out if cls_run.returncode == 0 and str_out else None


def _print_plan(dict_plan: dict[str, tuple[str, bytes | None]]) -> None:
    """Print one line per planned file.

    Parameters
    ----------
    dict_plan : dict of str to tuple of (str, bytes or None)
        The result of :func:`build_plan`.

    Returns
    -------
    None
    """
    for str_rel, (str_action, _) in dict_plan.items():
        print(f"{_LABELS[str_action]} {str_rel}")


def _write_plan(
    path_root: pathlib.Path,
    path_blueprintx: pathlib.Path,
    dict_plan: dict,
    dict_sources: dict[str, str],
) -> None:
    """Write every planned file that has content; an added file takes the template's mode.

    Parameters
    ----------
    path_root : pathlib.Path
        The project root.
    path_blueprintx : pathlib.Path
        Root of a BlueprintX checkout.
    dict_plan : dict of str to tuple of (str, bytes or None)
        The plan to write.
    dict_sources : dict of str to str
        Project-relative path to checkout-relative template source.

    Returns
    -------
    None
    """
    for str_rel, (str_action, bytes_new) in dict_plan.items():
        if bytes_new is None:
            continue
        path_file = path_root / str_rel
        path_file.parent.mkdir(parents=True, exist_ok=True)
        path_file.write_bytes(bytes_new)
        if str_action == "add":
            shutil.copymode(path_blueprintx / dict_sources[str_rel], path_file)


def _has_markers(path_file: pathlib.Path) -> bool:
    """Return whether a file still holds ``git merge-file`` conflict markers.

    Parameters
    ----------
    path_file : pathlib.Path
        The project file to inspect.

    Returns
    -------
    bool
            ``True`` when a marker line is present.
    """
    return bool(_RE_MARKERS.search(path_file.read_text(encoding="utf-8", errors="replace")))


def _blocked(path_root: pathlib.Path, dict_plan: dict, bool_resume: bool) -> list[str]:
    """List the files that still need a human.

    Parameters
    ----------
    path_root : pathlib.Path
        The project root.
    dict_plan : dict of str to tuple of (str, bytes or None)
        The plan.
    bool_resume : bool
        Whether this run continues an earlier one on the same branch.

    Returns
    -------
    list of str
            On a fresh run, every conflict or error. On a resumed run, every error and every
            planned merged or conflicted file that still holds markers.
    """
    if not bool_resume:
        return [k for k, v in dict_plan.items() if v[0] in _BLOCKING]
    return [
        k
        for k, v in dict_plan.items()
        if v[0] == "error" or (v[0] in _MERGE_ACTIONS and _has_markers(path_root / k))
    ]


def _enter_branch(path_root: pathlib.Path, str_branch: str) -> bool | None:
    """Create the update branch, or recognise that it is already checked out.

    Parameters
    ----------
    path_root : pathlib.Path
        The project root.
    str_branch : str
        The update branch name.

    Returns
    -------
    bool or None
            ``True`` when resuming on an existing checkout of the branch, ``False`` when it
            was just created, ``None`` (after printing why) when neither is possible.
    """
    list_vcs = ["git", "-C", str(path_root)]
    cls_now = subprocess.run(  # noqa: S603
        [*list_vcs, "branch", "--show-current"],
        capture_output=True,
        encoding="utf-8",
        check=False,
        env=_git_env(),
    )
    if cls_now.stdout.strip() == str_branch:
        return True
    cls_switch = subprocess.run(  # noqa: S603
        [*list_vcs, "switch", "-c", str_branch],
        capture_output=True,
        encoding="utf-8",
        check=False,
        env=_git_env(),
    )
    if cls_switch.returncode != 0:
        print(f"ERROR: cannot create branch {str_branch}: {cls_switch.stderr.strip()}")
        return None
    return False


def _checkout_dirty(path_blueprintx: pathlib.Path) -> bool:
    """Return whether the BlueprintX checkout has tracked or untracked changes.

    The merge base is read from history but "theirs" from the working tree, so a dirty
    checkout would deliver text that no commit holds and then stamp that commit.

    Parameters
    ----------
    path_blueprintx : pathlib.Path
        Root of a BlueprintX checkout.

    Returns
    -------
    bool
            ``True`` when ``status --porcelain`` prints anything or git cannot answer.
    """
    cls_run = subprocess.run(  # noqa: S603
        ["git", "-C", str(path_blueprintx), "status", "--porcelain"],  # noqa: S607
        capture_output=True,
        encoding="utf-8",
        check=False,
        env=_git_env(),
    )
    return cls_run.returncode != 0 or bool(cls_run.stdout.strip())


def _apply(
    path_root: pathlib.Path,
    path_blueprintx: pathlib.Path,
    dict_plan: dict,
    dict_sources: dict[str, str],
) -> int:
    """Enter the update branch, write the plan, and stamp the new commit if all was clean.

    Running it again while the update branch is checked out resumes: only added and
    fast-forwarded files are written, merged and conflicted files are never rewritten, and
    a file counts as resolved once it holds no conflict markers.

    Parameters
    ----------
    path_root : pathlib.Path
        The project root.
    path_blueprintx : pathlib.Path
        Root of a BlueprintX checkout.
    dict_plan : dict of str to tuple of (str, bytes or None)
        The result of :func:`build_plan`.
    dict_sources : dict of str to str
        Project-relative path to checkout-relative template source.

    Returns
    -------
    int
            0 when every file applied cleanly and the stamp moved, otherwise 1.
    """
    str_short = _head(path_blueprintx, True)
    str_full = _head(path_blueprintx, False)
    if str_short is None or str_full is None:
        print(f"ERROR: cannot read HEAD of {path_blueprintx}; nothing was changed.")
        return 1
    str_branch = f"chore/template-update-{str_short}"
    bool_resume = _enter_branch(path_root, str_branch)
    if bool_resume is None:
        return 1
    dict_write = {k: v for k, v in dict_plan.items() if not bool_resume or v[0] in _TRIVIAL}
    _write_plan(path_root, path_blueprintx, dict_write, dict_sources)
    list_blocked = _blocked(path_root, dict_plan, bool_resume)
    if list_blocked:
        print(
            f"\nApplied on branch {str_branch}, but {len(list_blocked)} file(s) need a human; "
            f"blueprintx_commit is unchanged. Resolve the markers, then run this again."
        )
        return 1
    path_stamp = path_root / drift._PROVENANCE_FILENAME
    str_stamp = path_stamp.read_text(encoding="utf-8")
    path_stamp.write_text(_RE_STAMP_COMMIT.sub(f"blueprintx_commit: {str_full}", str_stamp))
    print(
        f"\nApplied on branch {str_branch}; blueprintx_commit is now {str_full}. "
        f"Review and commit."
    )
    return 0


def _parse_args(list_argv: list) -> tuple[pathlib.Path, pathlib.Path | None, bool]:
    """Parse ``--root``, ``--blueprintx-root`` and ``--apply``.

    Parameters
    ----------
    list_argv : list of str
        Raw CLI arguments (``sys.argv[1:]``).

    Returns
    -------
    tuple of (pathlib.Path, pathlib.Path or None, bool)
            The project root (defaults to cwd), the BlueprintX checkout (defaults to
            ``BLUEPRINTX_TEMPLATE_ROOT``, or ``None``) and whether to apply.
    """
    cls_parser = argparse.ArgumentParser(description="Update template-managed files.")
    cls_parser.add_argument("--root", default=None)
    cls_parser.add_argument(
        "--blueprintx-root", default=os.environ.get("BLUEPRINTX_TEMPLATE_ROOT")
    )
    cls_parser.add_argument("--apply", action="store_true")
    cls_args = cls_parser.parse_args(list_argv)
    path_root = pathlib.Path(cls_args.root).resolve() if cls_args.root else pathlib.Path.cwd()
    path_blueprintx = (
        pathlib.Path(cls_args.blueprintx_root).resolve() if cls_args.blueprintx_root else None
    )
    return path_root, path_blueprintx, cls_args.apply


def main(list_argv: list) -> int:
    """Plan (and with ``--apply``, perform) the update of the project at ``--root``.

    Parameters
    ----------
    list_argv : list of str
        CLI arguments (``sys.argv[1:]``).

    Returns
    -------
    int
            0 for a dry run, a self-skip or a clean apply; 1 when ``--apply`` could not finish.
    """
    path_root, path_blueprintx, bool_apply = _parse_args(list_argv)
    _, dict_sources, str_skip = drift.managed_sources(path_root, path_blueprintx)
    if str_skip is not None:
        print(str_skip)
        return 0
    str_commit = drift.read_commit(path_root)
    if str_commit is None or not drift.commit_known(path_blueprintx, str_commit):
        print(
            f"SKIPPED update: the stamped blueprintx_commit ({str_commit}) is missing or not in "
            f"{path_blueprintx}, so there is no merge base. Nothing was changed."
        )
        return 0
    dict_plan = build_plan(path_root, path_blueprintx, str_commit, dict_sources)
    _print_plan(dict_plan)
    if not dict_plan:
        print("Template files are up to date.")
        return 0
    if not bool_apply:
        print(f"\n{len(dict_plan)} file(s) would change. Dry run; pass --apply to write them.")
        return 0
    if _checkout_dirty(path_blueprintx):
        print(f"ERROR: {path_blueprintx} has uncommitted changes; nothing was changed.")
        return 1
    return _apply(path_root, path_blueprintx, dict_plan, dict_sources)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
