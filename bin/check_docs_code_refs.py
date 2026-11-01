"""Resolve the symbols and import paths hand-written documentation cites against real code.

WHY THIS GATE. ``bin/check_docs_sections.py`` keys on page **slugs**; ``mkdocs build
--strict`` keys on **links**. Neither sees a **symbol**. A refactor renames or splits a
module, ``grep`` finds every importer, the test suite goes green — and a published docs page
keeps citing the deleted file, including a ``from … import …`` example that raises
``ModuleNotFoundError`` for anyone who copies it (blueprintx#159).

WHY SO NARROW. A docs<->code gate resolves free PROSE, which is exactly where a hand-rolled
gate turns into noise nobody can pay for — the trap this repo already hit at the ``bin/``
complexity ceiling (74% violating at ceiling 2, "a number nobody pays and therefore a gate
nobody keeps"). So this gate checks exactly one decidable shape: an ABSOLUTE
``from <dotted.path> import <Name[, ...]>`` statement inside a fenced ```python block, whose
top-level segment names a real first-party directory under ``<root>/src/``. Everything else
is deliberately out of scope:

- **Relative imports** (``from .foo import Bar``) — a docs page carries no real package
  context, so "relative to what" is undecidable from prose alone. The import regex below does
  not even match a leading dot, so these are never candidates.
- **A top segment that is not a real first-party directory under ``src/``** (stdlib,
  third-party, or a name this project does not own) — resolving those is either redundant
  (ruff/mypy already do it for real code) or actively unsafe: a tutorial page may legitimately
  narrate a HYPOTHETICAL feature (a "notes" walkthrough, say) whose class names were never
  meant to exist as real files.
- **Bare backtick mentions** (`` `apply_dtypes` ``) — a sentence, not a statement. The
  false-positive rate for prose mentions is far higher than for an executable-shaped block.
- **Bare ``import x.y``** (no ``from``) — the issue's own reported failure mode is the
  ``from … import …`` tutorial line; a bare import is rarer in docs and adds a second shape to
  get wrong for little real coverage.

RESOLUTION, two levels. (1) The MODULE must resolve to a real ``.py``/package under ``src/``
— this alone catches the ``ModuleNotFoundError`` case the issue reports. (2) Each imported
NAME must be defined at the module's top level (``def``/``class``/assignment/``__all__``/a
re-export) — catching a renamed export inside a file that still exists. Level 2 is skipped
for a module that already failed level 1 (no double-counting one defect), for a target file
that fails to parse (a defect for a *different* gate to catch), and for ``from x import *``
(nothing to check a wildcard against).

ZERO IS A LEGITIMATE STATE HERE, unlike the sibling gates' zero-discovery guard
(#111/#238's "a cwd-relative glob silently matching nothing reads as clean instead of
broken"). Those gates key on something structurally guaranteed to exist (a `.py` file
under `src/`, a canonical docs slug); this one keys on CONTENT — whether a doc happens to
show a fenced, first-party, absolute import — and a project can legitimately never do
that (measured: `lib-minimal`'s shipped docs carry zero fenced ```python blocks at all).
Forcing a non-zero floor here would fail every such project for a reason unrelated to any
defect — exactly the "gate nobody can pay" trap. So the printed success line always states
BOTH counts explicitly (raw import statements found, and the in-scope subset actually
checked against ``src/``) — a zero is visible, never silent, but it is not an error. Two
sub-cases of "0 in-scope candidates" are both normal: no ``src/`` exists at this
``--root`` (this gate travels with the template it polices, same precedent as the ``bin/``
complexity ceiling), or the docs only ever cite third-party/stdlib names.

Escape hatch, matching ``# complexity-ok: <reason>``: an HTML comment
``<!-- docs-refs-ok: <reason> -->`` on its own line, immediately before the opening ```` ```
```` fence (blank lines tolerated in between), exempts the WHOLE block — a "before" example,
a changelog entry naming a deleted file on purpose, or any other deliberately-wrong sample.
The reason is required; a bare marker does not match and is treated as ordinary prose.

Every finding is a hard error (exit 1).
"""

import ast
import pathlib
import re
import sys


PATH_ROOT = pathlib.Path(__file__).resolve().parent.parent

TUPLE_SKIP_DIRS = ("__pycache__", ".git", ".mypy_cache", ".pytest_cache", ".ruff_cache")

_TUPLE_KNOWN_LAYER_NAMES = (
    "app",
    "capabilities",
    "chassis",
    "config",
    "controller",
    "core",
    "model",
    "utils",
    "view",
)

_RE_FENCE_OPEN = re.compile(r"^```python\s*$")
_RE_FENCE_CLOSE = re.compile(r"^```\s*$")
_RE_ESCAPE_HATCH = re.compile(r"^\s*<!--\s*docs-refs-ok:\s*(\S.*?)\s*-->\s*$")
_RE_ABS_IMPORT = re.compile(r"^from ([A-Za-z_]\w*(?:\.[A-Za-z_]\w*)*) import (.+)$")


def first_party_roots(path_src: pathlib.Path) -> set[str]:
    """Return the real first-party top-level package/module names under ``src/``.

    Parameters
    ----------
    path_src : pathlib.Path
        The project's ``src/`` directory (may not exist).

    Returns
    -------
    set of str
        Directory names that are real packages (carry ``__init__.py``) plus top-level
        ``.py`` module stems. Empty when ``src/`` is absent — a legitimate state, not
        an error; see the module docstring.
    """
    if not path_src.is_dir():
        return set()
    set_names: set[str] = set()
    for path_child in path_src.iterdir():
        if path_child.name in TUPLE_SKIP_DIRS or path_child.name.startswith("."):
            continue
        if path_child.is_dir() and (path_child / "__init__.py").is_file():
            set_names.add(path_child.name)
        elif path_child.suffix == ".py":
            set_names.add(path_child.stem)
    return set_names


def in_scope_roots(path_src: pathlib.Path) -> set[str]:
    """Return the top-level names this gate will attempt to resolve.

    Parameters
    ----------
    path_src : pathlib.Path
        The project's ``src/`` directory (may not exist).

    Returns
    -------
    set of str
        The real first-party directories under ``src/`` unioned with
        :data:`_TUPLE_KNOWN_LAYER_NAMES` — but only when ``src/`` genuinely exists.
        Empty when it does not: with nothing to resolve against, every candidate would
        fail identically regardless of the static list, which is noise, not a finding
        (the same reasoning `lint_deps.sh`/deptry documents for its own BlueprintX-side
        skip).
    """
    if not path_src.is_dir():
        return set()
    return first_party_roots(path_src) | set(_TUPLE_KNOWN_LAYER_NAMES)


def resolve_module(path_src: pathlib.Path, str_module: str) -> pathlib.Path | None:
    """Return the source file a dotted module path names, or ``None`` when it does not exist.

    Parameters
    ----------
    path_src : pathlib.Path
        The project's ``src/`` directory.
    str_module : str
        A dotted, absolute module path (e.g. ``chassis.db.domain.ports``).

    Returns
    -------
    pathlib.Path or None
        The resolved ``.py`` file, or ``None`` when neither a package nor a module matches.
    """
    path_candidate = path_src.joinpath(*str_module.split("."))
    path_init = path_candidate / "__init__.py"
    if path_init.is_file():
        return path_init
    path_module = path_candidate.with_suffix(".py")
    return path_module if path_module.is_file() else None


def _all_entries(cls_assign: ast.Assign) -> list[str]:
    """Return the string literals of an ``__all__ = [...]``/``(...)`` assignment.

    Parameters
    ----------
    cls_assign : ast.Assign
        A top-level assignment node.

    Returns
    -------
    list of str
        The listed export names, or an empty list when this assignment is not ``__all__``.
    """
    bool_is_all = any(
        isinstance(cls_t, ast.Name) and cls_t.id == "__all__" for cls_t in cls_assign.targets
    )
    if not bool_is_all or not isinstance(cls_assign.value, ast.List | ast.Tuple):
        return []
    return [
        cls_elt.value
        for cls_elt in cls_assign.value.elts
        if isinstance(cls_elt, ast.Constant) and isinstance(cls_elt.value, str)
    ]


def defined_names(path_module: pathlib.Path) -> set[str] | None:
    """Return every top-level name a module defines, exports, or re-exports.

    Parameters
    ----------
    path_module : pathlib.Path
        A resolved ``.py`` source file.

    Returns
    -------
    set of str or None
        Top-level ``def``/``class``/assignment targets, re-exported import names, and any
        ``__all__`` string entries. ``None`` when the file cannot be parsed — a defect for
        a different gate (ruff/the syntax itself) to catch, not this one; the caller must
        then skip level-2 checking rather than report a false symbol mismatch.
    """
    try:
        cls_tree = ast.parse(path_module.read_text(encoding="utf-8"), filename=str(path_module))
    except SyntaxError:
        return None

    set_names: set[str] = set()
    for cls_node in cls_tree.body:
        if isinstance(cls_node, ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef):
            set_names.add(cls_node.name)
        elif isinstance(cls_node, ast.Import):
            set_names.update(
                cls_alias.asname or cls_alias.name.split(".")[0] for cls_alias in cls_node.names
            )
        elif isinstance(cls_node, ast.ImportFrom):
            set_names.update(cls_alias.asname or cls_alias.name for cls_alias in cls_node.names)
        elif isinstance(cls_node, ast.Assign):
            set_names.update(
                cls_target.id
                for cls_target in cls_node.targets
                if isinstance(cls_target, ast.Name)
            )
            set_names.update(_all_entries(cls_node))
        elif isinstance(cls_node, ast.AnnAssign) and isinstance(cls_node.target, ast.Name):
            set_names.add(cls_node.target.id)
    return set_names


def strip_inline_comment(str_line: str) -> str:
    """Return ``str_line`` with any trailing ``# comment`` removed.

    Safe to cut at the first ``#``: the only text this module feeds here is an import
    statement's module path and name list, and neither can contain a string literal — so no
    ``#`` is ever inside one.

    Parameters
    ----------
    str_line : str
        A line, or fragment, of an import statement.

    Returns
    -------
    str
        ``str_line`` up to the first ``#``, right-stripped.
    """
    return str_line.split("#")[0].rstrip()


def parse_names(str_names: str) -> list[str]:
    """Split an import statement's name list into individual imported names.

    Parameters
    ----------
    str_names : str
        Everything after ``import `` — e.g. ``"Foo, Bar as Baz"`` or a joined
        multi-line ``"(Foo, Bar,)"`` group. A trailing ``# comment`` is dropped: docs
        routinely annotate an example import, and keeping the comment turns the name into
        one that no module can define.

    Returns
    -------
    list of str
        Imported names with ``as`` aliases, a trailing comma and any inline comment
        stripped; ``*`` dropped.
    """
    str_clean = strip_inline_comment(str_names).strip()
    if str_clean.startswith("("):
        str_clean = str_clean[1:]
    if str_clean.endswith(")"):
        str_clean = str_clean[:-1]
    list_names = []
    for str_part in str_clean.split(","):
        str_name = str_part.strip().split(" as ")[0].strip()
        if str_name and str_name != "*":
            list_names.append(str_name)
    return list_names


def fenced_python_blocks(path_md: pathlib.Path) -> list[tuple[int, list[str], bool]]:
    """Return every fenced ```python block in a markdown file, with its escape-hatch state.

    Parameters
    ----------
    path_md : pathlib.Path
        The markdown file to scan.

    Returns
    -------
    list of tuple
        ``(first_code_lineno, body_lines, exempt)`` per block. ``exempt`` is ``True`` when
        a ``<!-- docs-refs-ok: <reason> -->`` comment sat immediately before the opening
        fence (blank lines tolerated in between).
    """
    list_lines = path_md.read_text(encoding="utf-8").splitlines()
    list_blocks: list[tuple[int, list[str], bool]] = []
    bool_exempt_next = False
    int_i = 0
    while int_i < len(list_lines):
        str_line = list_lines[int_i]
        if _RE_ESCAPE_HATCH.match(str_line):
            bool_exempt_next = True
        elif _RE_FENCE_OPEN.match(str_line):
            int_j = int_i + 1
            while int_j < len(list_lines) and not _RE_FENCE_CLOSE.match(list_lines[int_j]):
                int_j += 1
            list_blocks.append((int_i + 2, list_lines[int_i + 1 : int_j], bool_exempt_next))
            bool_exempt_next = False
            int_i = int_j
        elif str_line.strip():
            bool_exempt_next = False
        int_i += 1
    return list_blocks


def import_statements(list_body: list[str], int_first_lineno: int) -> list[tuple[int, str, str]]:
    """Return every top-level absolute ``from … import …`` line in a code block.

    Parameters
    ----------
    list_body : list of str
        The block's code lines (fence markers excluded).
    int_first_lineno : int
        1-based file line number of ``list_body[0]``.

    Returns
    -------
    list of tuple
        ``(lineno, module, names)`` per statement. A parenthesised multi-line name group is
        joined onto one string before it is returned.
    """
    list_found: list[tuple[int, str, str]] = []
    int_i = 0
    while int_i < len(list_body):
        cls_match = _RE_ABS_IMPORT.match(list_body[int_i])
        if not cls_match:
            int_i += 1
            continue
        str_module, str_names = cls_match.group(1), cls_match.group(2)
        int_lineno = int_first_lineno + int_i
        str_names = strip_inline_comment(str_names)
        if str_names.strip().startswith("(") and ")" not in str_names:
            int_i += 1
            while int_i < len(list_body):
                str_fragment = strip_inline_comment(list_body[int_i])
                str_names += " " + str_fragment
                if ")" in str_fragment:
                    break
                int_i += 1
        list_found.append((int_lineno, str_module, str_names))
        int_i += 1
    return list_found


def candidate_problem(
    path_src: pathlib.Path, str_module: str, list_names: list[str]
) -> str | None:
    """Return a finding message for one in-scope import candidate, or ``None`` when it is fine.

    Parameters
    ----------
    path_src : pathlib.Path
        The project's ``src/`` directory.
    str_module : str
        The dotted module path the docs cite.
    list_names : list of str
        The names the docs import from it.

    Returns
    -------
    str or None
        A human-readable finding, or ``None`` when the module resolves and every named
        symbol is defined (or the target could not be parsed, in which case level 2 is
        skipped rather than guessed at). A name that is not defined in the module but
        resolves as a **submodule** of it is accepted: ``from chassis import widgets`` is
        valid Python whether or not ``chassis/__init__.py`` re-exports the name.
    """
    path_module = resolve_module(path_src, str_module)
    if path_module is None:
        return f"module not found: {str_module}"
    set_defined = defined_names(path_module)
    if set_defined is None:
        return None
    list_missing = [
        str_name
        for str_name in list_names
        if str_name not in set_defined
        and resolve_module(path_src, f"{str_module}.{str_name}") is None
    ]
    if list_missing:
        str_rel = path_module.relative_to(path_src.parent)
        return f"{', '.join(list_missing)} not defined in {str_module} ({str_rel})"
    return None


def doc_files(path_root: pathlib.Path) -> list[pathlib.Path]:
    """Return every markdown file this gate scans: ``docs/**/*.md`` plus a root ``README.md``.

    Parameters
    ----------
    path_root : pathlib.Path
        The project root.

    Returns
    -------
    list of pathlib.Path
        Sorted markdown files, empty when the project ships neither.
    """
    path_docs = path_root / "docs"
    list_files = sorted(path_docs.rglob("*.md")) if path_docs.is_dir() else []
    path_readme = path_root / "README.md"
    if path_readme.is_file():
        list_files.append(path_readme)
    return list_files


def scan_file(
    path_md: pathlib.Path, path_src: pathlib.Path, set_first_party: set[str]
) -> tuple[int, int, list[str]]:
    """Scan one markdown file; return its candidate counts and any findings.

    Parameters
    ----------
    path_md : pathlib.Path
        The markdown file to scan.
    path_src : pathlib.Path
        The project's ``src/`` directory (for resolving in-scope candidates).
    set_first_party : set of str
        Real first-party top-level names, from :func:`first_party_roots`.

    Returns
    -------
    tuple of (int, int, list of str)
        Raw candidate count (scope filter not applied), in-scope candidate count, and
        findings — each already formatted as ``path:line: message``. See the module
        docstring for why the two counts are tracked separately.
    """
    int_raw = 0
    int_scoped = 0
    list_problems = []
    for int_start, list_body, bool_exempt in fenced_python_blocks(path_md):
        if bool_exempt:
            continue
        for int_lineno, str_module, str_names in import_statements(list_body, int_start):
            int_raw += 1
            if str_module.split(".")[0] not in set_first_party:
                continue
            int_scoped += 1
            str_problem = candidate_problem(path_src, str_module, parse_names(str_names))
            if str_problem:
                list_problems.append(f"{path_md}:{int_lineno}: {str_problem}")
    return int_raw, int_scoped, list_problems


_INT_FLAG_WITH_VALUE = 2


def main(list_argv: list) -> int:
    """Resolve every in-scope docs import against the project's ``src/`` tree.

    Parameters
    ----------
    list_argv : list of str
        ``["--root", <dir>]`` to check a tree other than this file's own project, else empty.

    Returns
    -------
    int
        0 when the docs check out (or the project ships no docs at all, or no in-scope
        import statement, both legitimate — see the module docstring), 1 on any finding.
    """
    global PATH_ROOT  # noqa: PLW0603 — same documented seam as check_function_length.py
    if list_argv[:1] == ["--root"]:
        if len(list_argv) < _INT_FLAG_WITH_VALUE:
            print("FAIL: --root needs a directory")
            return 1
        PATH_ROOT = pathlib.Path(list_argv[1]).resolve()

    list_docs = doc_files(PATH_ROOT)
    if not list_docs:
        print("No docs/ or README.md - skipping docs-code-refs check.")
        return 0

    path_src = PATH_ROOT / "src"
    set_first_party = in_scope_roots(path_src)
    int_raw_total = 0
    int_scoped_total = 0
    list_problems: list[str] = []
    for path_md in list_docs:
        int_raw, int_scoped, list_file_problems = scan_file(path_md, path_src, set_first_party)
        int_raw_total += int_raw
        int_scoped_total += int_scoped
        list_problems.extend(list_file_problems)

    for str_problem in list_problems:
        print(str_problem)
    if list_problems:
        print(
            f"\n{len(list_problems)} finding(s). A docs page citing a deleted module or a "
            f"renamed symbol is a broken tutorial, not a broken build - fix the citation, "
            f"or add `<!-- docs-refs-ok: <reason> -->` above the block if it is deliberate."
        )
        return 1

    print(
        f"OK: docs-code-refs OK ({len(list_docs)} doc file(s) scanned, {int_raw_total} import "
        f"statement(s) found, {int_scoped_total} first-party candidate(s) checked against "
        f"{path_src})"
    )
    return 0


if __name__ == "__main__":
    for cls_stream in (sys.stdout, sys.stderr):
        if hasattr(cls_stream, "reconfigure"):
            cls_stream.reconfigure(encoding="utf-8", errors="replace")

    sys.exit(main(sys.argv[1:]))
