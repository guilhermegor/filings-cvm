r"""Keep comments and docstrings in English, whatever locale the published documentation uses.

The root ``CLAUDE.md`` draws the boundary at *documentation for a reader* × *code*: ``README.md``
and every page under ``docs/`` are written in the locale chosen at scaffold time (``DOCS_LOCALE``,
``en`` or ``pt-BR``); docstrings, comments, symbol names, commit messages and CI output are
English in every locale. The gate never reads ``docs/``, so the choice does not change what it
checks — it only records which language the pages are allowed to be in.

⚠️ **This gate enforces only the first two of those** — comments and docstrings. Symbol names,
commit messages and CI output share the convention but are checked by nothing here, so do not
read a green run as covering them. Nothing enforced the code half at all, and it was breached
twice in one
session — first across seven ``.py`` files, then, after a sweep that grepped only ``.py``, across
five ``src/config/*.yaml`` files carrying 55 Portuguese comment lines.

Both breaches came from the same mechanism: the author read the comment *next to* the insertion
point and took it as the convention. That is why a partial sweep is worse than none — it leaves a
precedent that regenerates the violation. This gate is the part a sweep cannot be: repeatable, and
blind to which file type the last violation happened to be in.

Three design points:

1. **It looks for Portuguese function words, not for accents.** Accent-hunting flags every
   legitimate mention of ``Saídas``, ``Ativos Líquidos`` or a custodian's name; function words
   (``que``, ``não``, ``para``, ``com``, ``dos``, …) appear only when a sentence is actually being
   written in Portuguese. None of the listed words is also an English word.

2. **Quoted and backticked spans are redacted before matching.** An English comment quoting an
   e-mail subject or naming the ``saidas_zeradas`` block is correct and must pass. So are dotted
   tokens (``email_dispatch.yaml``, ``utils.text``, ``bradesco.com.br``) — without that redaction,
   ``\\bcom\\b`` matches inside every e-mail address in ``email_dispatch.yaml``.

3. **A hit is a candidate, not a verdict.** ``lang:pt-ok`` anywhere on the line skips it, for the
   case the redaction cannot reach. Mangling an English sentence to satisfy the regex would be
   worse than the hit it silences.

   ⚠️ The same restraint does **not** extend to ``TUPLE_TERMS_OF_ART``, which is empty on purpose.
   An escape marker exempts one line a reader can see; a terms-of-art entry exempts a word
   *everywhere, invisibly*. Whitelist only a term with no English equivalent — where a translation
   exists, translate. ``de-para`` was the first entry and was removed by translating its 10 sites
   to "mapping" (user decision, 2026-08-06).

Known ceiling: only **full-line** comments are read for the ``#``/``--`` file types, so a trailing
comment after a value is not checked. Reading those needs a per-format parser to tell a real
comment from a ``#`` inside a quoted value, and the measured violations were all full-line.
Python is exact regardless — it goes through ``tokenize`` and ``ast``.

**Language-agnostic by construction.** ``SET_PT_WORDS`` names the language that must NOT appear
in code; the language of ``docs/`` is never inspected, so a project whose documentation is
English, Spanish or Portuguese all use this gate unchanged. To police a different locale, swap
the word set — the redaction, block-joining and escape machinery are locale-independent.

⚠️ **The calibration IS the deliverable, not a detail.** The first draft of this gate reported
**19 findings, of which 18 were false**, and a gate that cries wolf gets switched off — at which
point it protects nothing while still looking installed. Every rule below (function words not
accents; redaction in a specific order; blocks not lines; length-preserving blanking) exists
because a specific class of false positive was measured. Do not "simplify" one away without
re-running ``tests/unit/test_comment_language_gate.py``, which pins each class by name.
"""

import ast
import pathlib
import re
import subprocess
import sys
import tokenize


SET_PT_WORDS = frozenset(
    {
        "ainda",
        "antes",
        "apenas",
        "aqui",
        "cada",
        "com",
        "das",
        "depois",
        "dos",
        "então",
        "entre",
        "essa",
        "esse",
        "esta",
        "está",
        "estão",
        "este",
        "exige",
        "faz",
        "fica",
        "foi",
        "isso",
        "isto",
        "já",
        "mais",
        "menos",
        "mesmo",
        "muito",
        "não",
        "nunca",
        "onde",
        "para",
        "pela",
        "pelo",
        "pode",
        "pois",
        "porque",
        "precisa",
        "quais",
        "qual",
        "quando",
        "que",
        "quem",
        "seja",
        "sem",
        "ser",
        "sobre",
        "são",
        "tem",
        "têm",
        "toda",
        "todas",
        "todo",
        "todos",
        "também",
        "uma",
        "vai",
    }
)

STR_ESCAPE = "lang:pt-ok"

TUPLE_TERMS_OF_ART: tuple = ()

DICT_MARKERS = {
    ".cfg": "#",
    ".env": "#",
    ".example": "#",
    ".ini": "#",
    ".sh": "#",
    ".sql": "--",
    ".toml": "#",
    ".yaml": "#",
    ".yml": "#",
}

TUPLE_SKIP_DIRS = (
    ".git",
    ".venv",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    "__pycache__",
    "node_modules",
    "htmlcov",
    "dist",
    "build",
    "site",
    "docs",
    "fixtures",
)

PATH_ROOT = pathlib.Path(__file__).resolve().parent.parent

TUPLE_REDACTIONS = (
    re.compile(r"``[^`]+``"),
    re.compile(r"`[^`]*`"),
    re.compile(r"\"[^\"]*\""),
    re.compile(r"'[^']*'"),
    re.compile(r"https?://\S+"),
    re.compile(r"\S+\.\S+"),
    re.compile(r"\b[A-ZÀ-Ý0-9]{2,}\b"),
)

RE_WORD = re.compile(r"[0-9A-Za-zÀ-ÿ_]+")


def _blank(cls_match: re.Match) -> str:
    """Return as many spaces as the match consumed.

    Parameters
    ----------
    cls_match : re.Match
        The span being redacted.

    Returns
    -------
    str
        A run of spaces the same length as the match, so line and column offsets survive.
    """
    return " " * len(cls_match.group(0))


def redact(str_text: str) -> str:
    """Blank out every span whose language is not the comment's own, preserving text geometry.

    Each substitution writes back **as many spaces as it removed**, so the result stays aligned
    with the input line for line and column for column. That is what lets a finding name the line
    the offending word is really on, rather than the line the comment block happens to start at.

    Parameters
    ----------
    str_text : str
        A comment block, markers already stripped.

    Returns
    -------
    str
        The same text with escaped lines, terms of art, quoted/backticked spans, URLs, dotted
        tokens and ALL-CAPS acronyms replaced by spaces.
    """
    list_lines = [
        " " * len(str_line) if STR_ESCAPE in str_line else str_line
        for str_line in str_text.splitlines()
    ]
    str_clean = "\n".join(list_lines)
    for str_term in TUPLE_TERMS_OF_ART:
        str_clean = re.sub(re.escape(str_term), _blank, str_clean, flags=re.IGNORECASE)
    for re_span in TUPLE_REDACTIONS:
        str_clean = re_span.sub(_blank, str_clean)
    return str_clean


def portuguese_words(str_text: str) -> list:
    """Return the Portuguese function words a comment carries, once redaction has run.

    Parameters
    ----------
    str_text : str
        One comment block's text, markers already stripped.

    Returns
    -------
    list of str
        The matched words in order of appearance, de-duplicated; empty when the text reads as
        English, quotes its Portuguese, or carries the escape marker.
    """
    list_hits = []
    for str_word in RE_WORD.findall(redact(str_text).lower()):
        if str_word in SET_PT_WORDS and str_word not in list_hits:
            list_hits.append(str_word)
    return list_hits


def marker_comments(str_source: str, str_marker: str) -> list:
    """Return the comment BLOCKS of a marker-delimited file.

    Only lines whose first non-space characters are the marker count, so a marker appearing
    inside a quoted value is never mistaken for a comment.

    ⚠️ **Consecutive comment lines are joined into one block, and that is load-bearing** — a
    sentence, and above all a *quotation*, routinely spans several comment lines. Redacting line
    by line sees an opening quote with no closing one, so the quoted span survives redaction and
    the quotation's own language is charged to the comment around it. Measured: the verbatim
    user decision quoted across two lines in ``view/recon_email_body.py`` was reported as a
    violation, which it is not.

    Parameters
    ----------
    str_source : str
        The file's text.
    str_marker : str
        The comment marker (``#`` or ``--``).

    Returns
    -------
    list of tuple
        One ``(int_line, str_text)`` pair per block, the line being where the block starts.
    """
    list_out = []
    list_block: list = []
    int_start = 0
    for int_line, str_line in enumerate(str_source.splitlines(), 1):
        str_stripped = str_line.lstrip()
        if str_stripped.startswith(str_marker):
            if not list_block:
                int_start = int_line
            list_block.append(str_stripped[len(str_marker) :])
            continue
        if list_block:
            list_out.append((int_start, "\n".join(list_block)))
            list_block = []
    if list_block:
        list_out.append((int_start, "\n".join(list_block)))
    return list_out


def python_comments(str_source: str) -> list:
    """Return a Python file's comments and docstrings.

    ``tokenize`` is what makes this exact — a ``#`` inside a string literal is a string, not a
    comment, and only the tokenizer knows the difference. Docstrings come from ``ast`` for the
    same reason: they are the other place English prose lives in a module.

    Parameters
    ----------
    str_source : str
        The file's text.

    Returns
    -------
    list of tuple
        One ``(int_line, str_text)`` pair per comment and per docstring, 1-indexed. A file that
        does not parse yields nothing — a syntax error is ruff's finding to report, not this
        gate's.
    """
    return _comment_blocks(str_source) + _docstring_blocks(str_source)


def _comment_blocks(str_source: str) -> list:
    """Group consecutive ``#`` comment lines into blocks, keyed by the block's first line.

    ⚠️ BLOCKS, not lines. A quotation or an example spanning several comment lines otherwise
    has its language charged to whichever line it lands on, which was measured as a large
    share of this gate's first-draft false positives.

    Parameters
    ----------
    str_source : str
        Python source text.

    Returns
    -------
    list
        ``(first_line, block_text)`` pairs; empty when the source cannot be tokenised.
    """
    list_out: list = []
    list_block: list = []
    int_start = 0
    int_previous = -2
    try:
        for cls_token in tokenize.generate_tokens(iter(str_source.splitlines(True)).__next__):
            if cls_token.type != tokenize.COMMENT:
                continue
            int_line = cls_token.start[0]
            if int_line != int_previous + 1 and list_block:
                list_out.append((int_start, "\n".join(list_block)))
                list_block = []
            if not list_block:
                int_start = int_line
            list_block.append(cls_token.string.lstrip("#"))
            int_previous = int_line
    except (tokenize.TokenError, IndentationError, SyntaxError):
        return []
    if list_block:
        list_out.append((int_start, "\n".join(list_block)))
    return list_out


def _docstring_blocks(str_source: str) -> list:
    """Collect every module, class and function docstring, keyed by its own first line.

    Parameters
    ----------
    str_source : str
        Python source text.

    Returns
    -------
    list
        ``(line, docstring)`` pairs; empty when the source cannot be parsed.
    """
    try:
        cls_tree = ast.parse(str_source)
    except SyntaxError:
        return []
    tuple_holders = (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)
    return [
        (cls_node.body[0].lineno, ast.get_docstring(cls_node, clean=False))
        for cls_node in ast.walk(cls_tree)
        if isinstance(cls_node, tuple_holders) and ast.get_docstring(cls_node, clean=False)
    ]


def _line_offset(str_text: str, str_word: str) -> int:
    """Return how many lines into a block the first occurrence of a word sits.

    Parameters
    ----------
    str_text : str
        The whole comment block.
    str_word : str
        The matched word.

    Returns
    -------
    int
        The 0-based line offset, found in the **redacted** block so a quoted occurrence earlier in
        the block cannot win the race against the real one. 0 when it cannot be located.
    """
    re_word = re.compile(rf"\b{re.escape(str_word)}\b", re.IGNORECASE)
    for int_offset, str_line in enumerate(redact(str_text).splitlines()):
        if re_word.search(str_line):
            return int_offset
    return 0


def _excerpt_around(str_text: str, str_word: str) -> str:
    """Return the offending word in its immediate context.

    A block can be forty lines long, so quoting its opening is useless — the reader needs the
    sentence the word is actually in.

    Parameters
    ----------
    str_text : str
        The whole comment block.
    str_word : str
        The first matched word.

    Returns
    -------
    str
        Up to ~35 characters either side of the match, whitespace collapsed.
    """
    str_flat = " ".join(str_text.split())
    int_at = str_flat.lower().find(str_word)
    if int_at < 0:
        return str_flat[:80]
    int_from = max(0, int_at - 35)
    str_slice = str_flat[int_from : int_at + len(str_word) + 35]
    return f"…{str_slice}…" if int_from else f"{str_slice}…"


def _display_path(path_file: pathlib.Path) -> str:
    """Return the shortest readable form of a path for a message.

    Parameters
    ----------
    path_file : pathlib.Path
        The file being reported.

    Returns
    -------
    str
        Repo-relative when the file lives inside the repository, absolute otherwise. A file
        outside the repo is legitimate (a test invoking the gate on a temp file), so this must
        never raise.
    """
    try:
        return str(path_file.relative_to(PATH_ROOT))
    except ValueError:
        return str(path_file)


def file_problems(path_file: pathlib.Path) -> list:
    """Return the Portuguese comment lines of one file.

    Parameters
    ----------
    path_file : pathlib.Path
        The file to read. An unsupported extension yields nothing.

    Returns
    -------
    list of str
        One ``path:line: words -- text`` message per offending comment.
    """
    bool_python = path_file.suffix == ".py"
    str_marker = DICT_MARKERS.get(path_file.suffix, "")
    if not bool_python and not str_marker:
        return []
    try:
        str_source = path_file.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return []
    list_comments = (
        python_comments(str_source) if bool_python else marker_comments(str_source, str_marker)
    )
    list_out = []
    for int_line, str_text in list_comments:
        list_hits = portuguese_words(str_text)
        if list_hits:
            int_at = int_line + _line_offset(str_text, list_hits[0])
            list_out.append(
                f"❌ {_display_path(path_file)}:{int_at}: reads as Portuguese "
                f"[{', '.join(list_hits)}] -- {_excerpt_around(str_text, list_hits[0])}"
            )
    return list_out


def tracked_files() -> list:
    """Return every file ``git`` tracks under ``PATH_ROOT``, relative to it.

    `git ls-files` scopes to the cwd it is run in and returns paths already relative to that
    cwd — exactly the shape the old ``rglob`` + ``relative_to(PATH_ROOT)`` walk produced, with
    no skip-list needed for anything a worktree or a cache directory could contain: neither is
    ever tracked by the main working tree.

    Returns
    -------
    list of pathlib.Path
        Tracked paths, relative to ``PATH_ROOT``. Empty when `git` is unavailable or
        ``PATH_ROOT`` is not inside a work tree — the caller's zero-discovery guard turns that
        into a failure rather than a silent pass.
    """
    try:
        cls_result = subprocess.run(  # noqa: S603
            ["git", "ls-files"],  # noqa: S607
            cwd=PATH_ROOT,
            capture_output=True,
            text=True,
            check=True,
        )
    except (OSError, subprocess.CalledProcessError) as cls_error:
        print(f"❌ `git ls-files` failed under {PATH_ROOT}: {cls_error}", file=sys.stderr)
        return []
    return [pathlib.Path(str_line) for str_line in cls_result.stdout.splitlines() if str_line]


def audit_paths() -> list:
    """Return the files scanned when no filenames are passed.

    Returns
    -------
    list of pathlib.Path
        Every TRACKED file carrying a supported extension, minus the skipped directories, sorted.
    """
    set_supported = set(DICT_MARKERS) | {".py"}
    list_paths = [
        PATH_ROOT / path_rel
        for path_rel in tracked_files()
        if path_rel.suffix in set_supported
        and not any(str_part in TUPLE_SKIP_DIRS for str_part in path_rel.parts)
    ]
    return sorted(set(list_paths))


_INT_FLAG_WITH_VALUE = 2


def split_root_option(list_argv: list) -> tuple:
    """Peel ``--root <dir>`` off the argv, the same seam ``check_function_length.py`` exposes.

    It lets BlueprintX run this very file over its own tree instead of keeping a second copy:
    ``PATH_ROOT`` otherwise resolves to the directory the script ships in.

    Parameters
    ----------
    list_argv : list of str
        Raw argv, minus the program name.

    Returns
    -------
    tuple of (pathlib.Path or None, list of str)
        The requested root (``None`` when absent) and the remaining filenames.

    Raises
    ------
    ValueError
        When ``--root`` is passed with no directory after it, names a directory that does
        not exist, or sits anywhere but first. A missing root makes every named file's read
        fail, no problem is reported, and the gate exits 0 having checked nothing.
        Returning it as a filename instead makes the gate print success for having checked
        nothing — measured on blueprintx#247: `check_comment_language.py --root` exited 0.
        `check_function_length.py`, the seam this mirrors, already rejects the same argv.
    """
    if list_argv[:1] == ["--root"]:
        if len(list_argv) < _INT_FLAG_WITH_VALUE or not list_argv[1]:
            msg = "--root needs a directory"
            raise ValueError(msg)
        path_root = pathlib.Path(list_argv[1]).resolve()
        if not path_root.is_dir():
            msg = f"--root {list_argv[1]} is not a directory"
            raise ValueError(msg)
        return path_root, list_argv[2:]
    if any(str_arg == "--root" or str_arg.startswith("--root=") for str_arg in list_argv):
        msg = "--root must be the first argument, as `--root <dir>`"
        raise ValueError(msg)
    return None, list_argv


def main(list_argv: list) -> int:
    """Check every named file's comments for Portuguese prose.

    Parameters
    ----------
    list_argv : list of str
        Optional leading ``--root <dir>``, then filenames as pre-commit passes them. No
        filenames means audit the whole repository under the root.

    Returns
    -------
    int
        0 when every comment reads as English, 1 on a violation.
    """
    global PATH_ROOT  # noqa: PLW0603 -- the one rebind point for the module-wide root
    try:
        path_root, list_argv = split_root_option(list_argv)
    except ValueError as cls_err:
        print(f"\u274c {cls_err}")
        return 1
    if path_root is not None:
        PATH_ROOT = path_root
    bool_audit = not list_argv
    path_base = path_root or pathlib.Path.cwd()
    list_paths = (
        [(path_base / str_name).resolve() for str_name in list_argv]
        if list_argv
        else audit_paths()
    )

    if bool_audit and not list_paths:
        print(
            f"❌ no supported file found under {PATH_ROOT} — this gate would pass vacuously. "
            f"Check DICT_MARKERS and TUPLE_SKIP_DIRS against the layout."
        )
        return 1

    list_problems = []
    for path_file in list_paths:
        list_problems.extend(file_problems(path_file))
    for str_problem in list_problems:
        print(str_problem)

    if not list_problems:
        print(f"✅ documentation-language boundary OK ({len(list_paths)} file(s) checked)")
    if list_problems:
        print(
            f"\n{len(list_problems)} comment(s) read as Portuguese. Comments, docstrings and "
            f"symbol names are English; only README.md and docs/ follow the project's "
            f"locale. If a flagged line is English and merely quotes Portuguese text, add "
            f"{STR_ESCAPE} to it rather than rewording the sentence."
        )
    return 1 if list_problems else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
