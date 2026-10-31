"""Hold a quality guard's pre-existing findings at a per-file baseline that only goes down.

Usage::

    python bin/quality_ratchet.py <guard> [--write-baseline] <guard command...>

The BlueprintX guards (``check_function_length.py``, ``check_complexity.sh``,
``check_all_exports.py``, ``check_one_assert.py``, ``check_dead_code.py``) were written for a
fresh scaffold and fail hard on any finding. This tree predates them, so each runs through
this wrapper, which applies the template's own ratchet shape — ``check_comment_budget.py``'s
``<count> <path>`` baseline — instead of weakening a threshold:

- a file ABOVE its baseline fails (new violations), and a file absent from the baseline has a
  baseline of 0, so new code meets the guard in full;
- a file BELOW its baseline fails too ("lower it"), so the number only ever goes down and each
  fix records its win; ``--write-baseline`` rewrites that guard's rows.

The guards stay verbatim copies of the template, so a later sync is a plain copy. Findings are
recognised as output lines that start (after an optional ``❌``/``[✗]`` marker and ANSI colour)
with ``<path>.py:`` or ``<path>.sh:`` at column 0; an INDENTED path line is informational
(``check_dead_code.py``'s non-gating 60-79% tier) and is never counted.
A guard that exits non-zero with NO recognisable finding failed for another reason (broken discovery, a crash) and its failure is passed through
unchanged. A guard that reports it skipped (``check_dead_code.py`` without ``vulture``) is
passed through as a skip; CI installs the tool so the gate does run there.

Baseline file: ``bin/quality_baseline.txt``, one ``<guard> <count> <path>`` row per file.
"""

import collections
import pathlib
import re
import subprocess
import sys


PATH_ROOT = pathlib.Path(__file__).resolve().parent.parent
PATH_BASELINE = PATH_ROOT / "bin" / "quality_baseline.txt"
STR_WRITE = "--write-baseline"
RE_ANSI = re.compile(r"\x1b\[[0-9;]*m")
RE_FINDING = re.compile(r"^(?:❌\s*|\[✗\]\s*)?(?P<path>[\w./-]+\.(?:py|sh)):")
RE_SKIPPED = re.compile(r"\bskipping\b", re.I)
INT_ROW_FIELDS = 3


def finding_counts(str_output: str) -> collections.Counter:
	"""Count recognisable findings per file in a guard's output.

	Parameters
	----------
	str_output : str
		The guard's combined stdout/stderr.

	Returns
	-------
	collections.Counter
		Path -> number of finding lines naming it.
	"""
	counter = collections.Counter()
	for str_line in RE_ANSI.sub("", str_output).splitlines():
		match = RE_FINDING.match(str_line)
		if match:
			counter[match.group("path").removeprefix("./")] += 1
	return counter


def read_baseline(str_guard: str, path_file: pathlib.Path = PATH_BASELINE) -> dict:
	"""Return ``{path: count}`` for one guard from the baseline file.

	Parameters
	----------
	str_guard : str
		The guard's name, the first field of its rows.
	path_file : pathlib.Path
		The baseline file.

	Returns
	-------
	dict
		Path -> baselined count; empty when the file or the guard's rows are absent.

	Raises
	------
	ValueError
		On a malformed row.
	"""
	if not path_file.is_file():
		return {}
	dict_out = {}
	for str_line in path_file.read_text(encoding="utf-8").splitlines():
		if not str_line.strip() or str_line.startswith("#"):
			continue
		list_parts = str_line.split(maxsplit=2)
		if len(list_parts) != INT_ROW_FIELDS or not list_parts[1].isdigit():
			raise ValueError(f"malformed baseline row: {str_line!r}")
		if list_parts[0] == str_guard:
			dict_out[list_parts[2]] = int(list_parts[1])
	return dict_out


def ratchet_problems(counter: collections.Counter, dict_baseline: dict) -> list:
	"""Compare counts with the baseline in both directions.

	Parameters
	----------
	counter : collections.Counter
		Current findings per file.
	dict_baseline : dict
		Baselined findings per file.

	Returns
	-------
	list of str
		One message per file above or below its baseline; empty when held exactly.
	"""
	list_problems = []
	for str_path in sorted(set(counter) | set(dict_baseline)):
		int_now, int_base = counter.get(str_path, 0), dict_baseline.get(str_path, 0)
		if int_now > int_base:
			list_problems.append(f"{str_path}: {int_now} finding(s), baseline {int_base}")
		elif int_now < int_base:
			list_problems.append(
				f"{str_path}: {int_now} finding(s), below baseline {int_base} — lower it "
				f"(re-run with {STR_WRITE})"
			)
	return list_problems


def write_baseline(
	str_guard: str, counter: collections.Counter, path_file: pathlib.Path = PATH_BASELINE
) -> None:
	"""Replace one guard's rows in the baseline file, keeping every other guard's rows.

	Parameters
	----------
	str_guard : str
		The guard whose rows are rewritten.
	counter : collections.Counter
		Its current findings per file.
	path_file : pathlib.Path
		The baseline file.
	"""
	list_lines = path_file.read_text(encoding="utf-8").splitlines() if path_file.is_file() else []
	list_kept = [s for s in list_lines if s.split(maxsplit=1)[:1] != [str_guard]]
	list_new = [f"{str_guard} {n} {p}" for p, n in sorted(counter.items())]
	path_file.write_text("\n".join(list_kept + list_new) + "\n", encoding="utf-8")


def run_guard(list_cmd: list) -> tuple:
	"""Run the wrapped guard from the repository root.

	Parameters
	----------
	list_cmd : list of str
		The guard command line.

	Returns
	-------
	tuple
		``(exit code, combined output)``.
	"""
	cls_proc = subprocess.run(  # noqa: S603 - argv comes from the repo's own hook/CI config
		list_cmd,
		cwd=PATH_ROOT,
		capture_output=True,
		text=True,
		encoding="utf-8",
		errors="replace",
		check=False,
	)
	return cls_proc.returncode, cls_proc.stdout + cls_proc.stderr


def report_problems(str_guard: str, str_output: str, list_problems: list) -> None:
	"""Print the guard's findings for the files that moved, then each baseline problem.

	Parameters
	----------
	str_guard : str
		The guard being judged.
	str_output : str
		The guard's combined stdout/stderr.
	list_problems : list of str
		The messages from :func:`ratchet_problems`.
	"""
	set_bad = {s.split(":", 1)[0] for s in list_problems}
	for str_line in RE_ANSI.sub("", str_output).splitlines():
		match = RE_FINDING.match(str_line)
		if match and match.group("path").removeprefix("./") in set_bad:
			print(str_line)
	print(f"\n❌ {str_guard}: the per-file baseline in {PATH_BASELINE.name} moved:")
	for str_problem in list_problems:
		print(f"  {str_problem}")


def main(list_argv: list) -> int:
	"""Run a guard and judge its findings against the baseline.

	Parameters
	----------
	list_argv : list of str
		``<guard> [--write-baseline] <command...>``.

	Returns
	-------
	int
		0 when every file is held exactly at its baseline, 1 otherwise.
	"""
	bool_write = list_argv[1:2] == [STR_WRITE]
	list_cmd = list_argv[2:] if bool_write else list_argv[1:]
	if not list_cmd:
		print(f"usage: quality_ratchet.py <guard> [{STR_WRITE}] <command...>")
		return 2
	str_guard = list_argv[0]
	int_rc, str_output = run_guard(list_cmd)
	counter = finding_counts(str_output)
	if int_rc != 0 and not counter:
		print(str_output, end="")
		return int_rc
	if int_rc == 0 and RE_SKIPPED.search(str_output):
		print(str_output, end="")
		return 0
	if bool_write:
		write_baseline(str_guard, counter)
		print(f"{str_guard}: baseline written ({sum(counter.values())} finding(s)).")
		return 0
	list_problems = ratchet_problems(counter, read_baseline(str_guard))
	if not list_problems:
		print(
			f"✅ {str_guard}: {sum(counter.values())} pre-existing finding(s) held at baseline "
			f"across {len(counter)} file(s); nothing new."
		)
		return 0
	report_problems(str_guard, str_output, list_problems)
	return 1


if __name__ == "__main__":
	# The report carries ✅/❌; a Windows console defaults to cp1252 and would crash the print
	# (exit 1, indistinguishable from a real ratchet failure), so pin the output to UTF-8.
	sys.stdout.reconfigure(encoding="utf-8", errors="replace")
	sys.exit(main(sys.argv[1:]))
