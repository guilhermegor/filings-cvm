"""Dead-code gate — flag only what a static tool can PROVE unreachable (blueprintx#332).

`ruff` already runs F401 (unused import) and F841 (unused local) plus the `ERA`
(commented-out code) family — this gate does not repeat either of those. It answers a
different question ruff's per-file analysis cannot see at all: a *cross-module* symbol (a
function/class/method nothing else in the whole tree calls).

Every dead-code tool is one of two mechanisms — static reachability ("does anything
reference this?") or runtime coverage ("did any execution reach this?") — and BOTH fail the
same way on a SCAFFOLD: a template's shipped seam has no caller yet, and no test yet, and
that IS the deliverable. `vulture` (the well-known Python candidate, measured here) makes
this failure mode visible as a literal cliff in its own confidence score:

    min-confidence   findings over templates/python-common/src/   (2026-09-19)
    100 / 80 / 61    2   — both real: two unused function/method parameters
    60               63  — almost all a deliberately-shipped, not-yet-called seam
                          (``mask_cnpj``, ``PATH_JSON``, …) — the entire point of a template

60 is vulture's own floor (it reports nothing lower). Above the cliff (>=80) is what the
tool can PROVE from the file alone: an assigned-but-never-read local, an unreachable branch.
At and below 60 it answers a genuinely different, CONTEXTUAL question — "does anything ELSE
in this tree call it yet?" — where "nothing yet" is the expected, correct answer for a
scaffold's unimplemented seams, and a false positive on every one of them.

So this gate is two tiers sharing one run, never two scripts:

- **>=80 confidence — GATES.** Zero cost on the template today (2 findings, both real,
  zero suppressions needed) and the same proof-strength claim holds in a generated project
  too, so it gates BOTH sides identically.
- **60-79 confidence — REPORTS, never gates.** Same tool, same run, opposite value
  depending on which side is reading it: noise on a fresh scaffold (every shipped-but-
  uncalled seam), genuine signal months into a real project (something really is
  unreferenced). Printed as a non-blocking count for a human to read manually — a per-line
  suppression scheme was rejected in blueprintx#332: it would have shipped ~60 markers per
  generated project on the seams users read first, and a marker reading "probably dead" on
  the sanctioned way to mask a CNPJ teaches the wrong thing.

Not yet wired into any tier's ``pyproject.toml``, pre-commit config, or CI (blueprintx#332
follow-up) — ``resolve_vulture`` treats an absent ``vulture`` as an expected, non-fatal skip
rather than broken discovery until that dependency lands.
"""

import importlib.metadata
import pathlib
import sys
from types import ModuleType


_GATE_MIN_CONFIDENCE = 80
_REPORT_MIN_CONFIDENCE = 60
_INT_FLAG_WITH_VALUE = 2
_TUPLE_SKIP_DIRS = (
    ".claude",
    ".git",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".venv",
    "__pycache__",
    "node_modules",
)


def _is_distribution_installed() -> bool:
    """Return whether ``vulture`` has installed distribution metadata."""
    try:
        importlib.metadata.version("vulture")
    except importlib.metadata.PackageNotFoundError:
        return False
    return True


def resolve_vulture() -> ModuleType | None:
    """Import ``vulture``, treating only its own absence as an expected skip.

    Returns
    -------
    ModuleType or None
        The imported ``vulture`` package, or ``None`` when it is not installed — this gate
        is not yet wired into any tier's dependency table, so a missing import is a
        legitimate, non-fatal skip rather than broken discovery.

    Raises
    ------
    ImportError
        When ``vulture`` is installed but fails to import: a transitive
        ``ModuleNotFoundError``, a plain ``ImportError`` (missing name, broken C extension),
        or a half-removed install (metadata present, package directory gone). A broken tool
        is not an absent one, and skipping would be a vacuous pass (blueprintx#640).
    """
    try:
        import vulture
    except ModuleNotFoundError as exc:
        if exc.name != "vulture" or _is_distribution_installed():
            raise
        return None
    return vulture


def discover_python_files(path_src: pathlib.Path) -> list:
    """Return every ``.py`` file under ``path_src``, skipping vendored/generated trees.

    Parameters
    ----------
    path_src : pathlib.Path
        The tier's ``src/`` directory.

    Returns
    -------
    list
        Sorted ``pathlib.Path`` entries.
    """
    return sorted(
        path_file
        for path_file in path_src.rglob("*.py")
        if not any(
            str_part in _TUPLE_SKIP_DIRS for str_part in path_file.relative_to(path_src).parts
        )
    )


def run_vulture(cls_vulture: ModuleType, list_files: list) -> list:
    """Scan an explicit file list and return every finding at or above the report floor.

    Parameters
    ----------
    cls_vulture : ModuleType
        The imported ``vulture`` package.
    list_files : list
        The ``pathlib.Path`` files to scan — already filtered by
        :func:`discover_python_files`.

    Returns
    -------
    list
        ``vulture.core.Item`` findings at or above ``_REPORT_MIN_CONFIDENCE``, vulture's
        own sort order (by file, then line).

    Raises
    ------
    RuntimeError
        When vulture could not read or parse one of the files. It records that as an
        ``InvalidInput`` exit code and carries on, so returning its findings anyway would
        report a clean tree for a file that was never scanned.
    """
    cls_scanner = cls_vulture.Vulture()
    cls_scanner.scavenge([str(path_file) for path_file in list_files])
    if cls_scanner.exit_code == cls_vulture.core.ExitCode.InvalidInput:
        raise RuntimeError("vulture could not read or parse at least one file under src/")
    return cls_scanner.get_unused_code(min_confidence=_REPORT_MIN_CONFIDENCE)


def classify_findings(list_items: list) -> tuple:
    """Split vulture's items into the gating tier and the report-only tier.

    Parameters
    ----------
    list_items : list
        Every ``vulture.core.Item`` at or above ``_REPORT_MIN_CONFIDENCE``.

    Returns
    -------
    tuple
        ``(list_gate, list_report)`` — items at/above ``_GATE_MIN_CONFIDENCE`` fail the
        build; the rest (60-79% confidence) are informational only.
    """
    list_gate = [
        cls_item for cls_item in list_items if cls_item.confidence >= _GATE_MIN_CONFIDENCE
    ]
    list_report = [
        cls_item for cls_item in list_items if cls_item.confidence < _GATE_MIN_CONFIDENCE
    ]
    return list_gate, list_report


def print_report_tier(list_report: list) -> None:
    """Print the 60-79% confidence findings as non-gating information, to stdout.

    Parameters
    ----------
    list_report : list
        Contextual ``vulture.core.Item`` findings — real signal on an aged project,
        expected noise on a fresh scaffold.
    """
    if not list_report:
        return
    print(
        f"ℹ️  {len(list_report)} contextual (60-79% confidence) finding(s) — informational "
        f"only, never gating. Expected/noisy on a fresh scaffold (a shipped seam with no "
        f"caller yet); worth reading manually on a project old enough to have real callers:"
    )
    for cls_item in list_report:
        print(f"    {cls_item.get_report()}")


def print_gate_tier(list_gate: list) -> None:
    """Print the >=80% confidence findings as gating failures, to stderr.

    Parameters
    ----------
    list_gate : list
        Provable ``vulture.core.Item`` findings — an assigned-but-unread local, an
        unreachable branch.
    """
    for cls_item in list_gate:
        print(f"❌ {cls_item.get_report()}", file=sys.stderr)
    print(
        f"\n{len(list_gate)} dead-code finding(s) at >={_GATE_MIN_CONFIDENCE}% confidence. "
        f"These are provable from the file alone — delete the code, or it is not truly "
        f"unreferenced and the call site is missing.",
        file=sys.stderr,
    )


def run_gate(cls_vulture: ModuleType, list_files: list) -> int:
    """Scan the files, print both tiers, and return the gate's exit code.

    Parameters
    ----------
    cls_vulture : ModuleType
        The imported ``vulture`` package.
    list_files : list
        The ``pathlib.Path`` files to scan.

    Returns
    -------
    int
        0 when nothing gates, 1 on a >=80% confidence finding or when vulture could not
        scan a file (an unscanned file is not a clean one).
    """
    try:
        list_findings = run_vulture(cls_vulture, list_files)
    except RuntimeError as err:
        print(f"❌ check_dead_code: {err} — refusing to report a clean tree.", file=sys.stderr)
        return 1
    list_gate, list_report = classify_findings(list_findings)
    print_report_tier(list_report)
    if list_gate:
        print_gate_tier(list_gate)
        return 1

    print(
        f"dead-code gate OK: {len(list_files)} .py file(s) scanned, 0 finding(s) at "
        f">={_GATE_MIN_CONFIDENCE}% confidence."
    )
    return 0


def main(list_argv: list) -> int:
    """Run the dead-code gate over ``<root>/src`` and report both tiers.

    Parameters
    ----------
    list_argv : list
        CLI arguments; ``--root <dir>`` overrides the working directory as the tier root.
        BlueprintX's own root ships no runtime ``src/`` and self-skips — see the module
        docstring for why that is a legitimate skip, not a failure.

    Returns
    -------
    int
        0 when nothing gates (including every legitimate skip), 1 on a >=80% confidence
        finding, on broken discovery (``src/`` exists but holds zero ``.py`` files), or when
        vulture could not scan a file (an unscanned file is not a clean one), or when an
        installed vulture fails to import.
    """
    path_root = pathlib.Path(".").resolve()
    if list_argv[:1] == ["--root"]:
        if len(list_argv) < _INT_FLAG_WITH_VALUE:
            print("❌ --root needs a directory", file=sys.stderr)
            return 1
        path_root = pathlib.Path(list_argv[1]).resolve()

    path_src = path_root / "src"
    if not path_src.is_dir():
        print(
            f"check_dead_code: no {path_src} — nothing for the dead-code gate to check "
            f"(e.g. BlueprintX's own root, which ships no runtime src/)."
        )
        return 0

    list_files = discover_python_files(path_src)
    if not list_files:
        print(f"check_dead_code: found ZERO .py files under {path_src}", file=sys.stderr)
        return 1

    try:
        cls_vulture = resolve_vulture()
    except ImportError as exc:
        print(
            f"check_dead_code: vulture is installed but failed to import: {exc}", file=sys.stderr
        )
        return 1
    if cls_vulture is None:
        print(
            "check_dead_code: vulture is not installed — skipping (not yet wired into any "
            "tier's dependency table, blueprintx#332 follow-up)."
        )
        return 0

    return run_gate(cls_vulture, list_files)


if __name__ == "__main__":
    for cls_stream in (sys.stdout, sys.stderr):
        if hasattr(cls_stream, "reconfigure"):
            cls_stream.reconfigure(encoding="utf-8", errors="replace")
    sys.exit(main(sys.argv[1:]))
