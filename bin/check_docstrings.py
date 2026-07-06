"""Check NumPy docstrings against signatures (params, returns, raises).

Verifies, for every function in the ``src`` and ``tests`` packages, that the
docstring's documented parameter types and return type match the annotations,
and that the ``Raises`` section agrees with the exceptions actually raised. Type
mismatches are hard errors (exit 1); missing docstrings, undocumented fixture
params and raises drift are soft warnings.
"""

import ast
import pathlib
import re
import sys
from typing import Any


_SECTION_RE = re.compile(
    r"^(Args|Arguments|Parameters|Returns|Yields|Notes|Examples"
    r"|Attributes|See Also|References|Raises)(:)?$",
    re.IGNORECASE,
)

_NON_RAISES_SECTIONS_RE = re.compile(
    r"^(Args|Arguments|Parameters|Returns|Yields|Notes|Examples"
    r"|Attributes|See Also|References)(:)?$",
    re.IGNORECASE,
)

# A NumPy parameter-definition line: one name, or several comma-separated names,
# followed by " : <type>". The combined form ("a, b : dict") is valid NumPy and
# documents every listed name at once.
_PARAM_DEF_RE = re.compile(r"^\s*([A-Za-z_]\w*(?:\s*,\s*[A-Za-z_]\w*)*)\s*:\s*\S")


def _param_names(line: str) -> list:
    """Return the parameter names declared on a NumPy param-definition line.

    Recognises both ``name : type`` and the combined ``name1, name2 : type``
    form. Prose and non-definition lines yield an empty list.

    Parameters
    ----------
    line : str
        A single docstring line.

    Returns
    -------
    list
        Declared parameter names (empty when the line is not a definition).
    """
    match = _PARAM_DEF_RE.match(line)
    if not match:
        return []
    return [name.strip() for name in match.group(1).split(",")]


# Connector / filler words and tokens that carry no type identity. They let a
# NumPy-style docstring ("pathlib.Path or None", "list of dict", "str, optional")
# read naturally while still matching the bare annotation (Path | None, etc.).
_FILLER_TOKENS = {"or", "of", "optional", "...", "ellipsis"}

# Tokens that mean the same container, collapsed to one canonical spelling so an
# annotation and its prose description compare equal regardless of which is used.
_TOKEN_EQUIVALENCES = {
    "sequence": "list",
    "mapping": "dict",
    "ndarray": "ndarray",
    "np": "",
    "numpy": "",
}


def _canonical_type_tokens(text: str) -> list:
    """Reduce a type hint or docstring type to a sorted multiset of tokens.

    Both sides are lower-cased; punctuation that only structures a generic
    (``| , [ ] ( ) { }``) is treated as a separator; filler words (``or``,
    ``of``, ``optional``, ``...``) are dropped; module qualifiers are stripped to
    the last dotted component (``pathlib.path`` -> ``path``); and container
    synonyms are collapsed (``sequence`` -> ``list``).

    The bracketed wrapper ``Optional[X]`` is special-cased to contribute a
    ``none`` token (so it matches the prose ``X or None`` and the PEP 604
    ``X | None``). The bare word ``optional`` — the NumPy "this parameter has a
    default" marker in ``str, optional`` — stays a dropped filler word, since it
    carries no type identity there.

    Parameters
    ----------
    text : str
        A type annotation string (from ``ast.unparse``) or a docstring type.

    Returns
    -------
    list
        Sorted token multiset suitable for equality comparison.
    """
    text = str(text).replace("typing.", "").lower()
    # ``Optional[...]`` (bracketed) means the value may be None; emit that token
    # before the brackets are flattened to separators and "optional" is dropped.
    bool_optional_wrapper = re.search(r"\boptional\s*\[", text) is not None
    for str_sep in ("|", ",", "[", "]", "(", ")", "{", "}", ":"):
        text = text.replace(str_sep, " ")
    list_tokens = []
    if bool_optional_wrapper:
        list_tokens.append("none")
    for str_raw in text.split():
        if str_raw in _FILLER_TOKENS:
            continue
        str_tok = str_raw.split(".")[-1]
        str_tok = _TOKEN_EQUIVALENCES.get(str_tok, str_tok)
        if str_tok:
            list_tokens.append(str_tok)
    return sorted(list_tokens)


def compare_types(hint: object, doc: str) -> bool:
    """Check if a type hint matches a docstring type description.

    Comparison is NumPy-docstring aware: ``Path | None`` matches
    ``pathlib.Path or None``, ``list[dict]`` matches ``list of dict``, and
    ``str, optional`` matches ``str`` — by reducing both sides to a canonical
    token multiset (see :func:`_canonical_type_tokens`).

    Parameters
    ----------
    hint : object
        Parsed type annotation (already a string from ``ast.unparse``).
    doc : str
        Type string from the docstring.

    Returns
    -------
    bool
        True if types are considered equivalent.
    """
    if hint is Any or doc.lower().strip() == "any":
        return True
    set_hint = set(_canonical_type_tokens(hint))
    set_doc = set(_canonical_type_tokens(doc))
    if not set_doc:
        return False
    # NumPy prose is routinely less specific than the annotation — it omits inner
    # generic args ("list of dict" for list[dict[str, Any]]) and the Optional/None
    # arm ("str, optional"). Accept when the documented tokens are a subset of the
    # annotation's; exact equality is the common case and also satisfies this.
    return set_doc <= set_hint


def parse_raises_section(docstring: str) -> dict[str, str]:
    """Parse the Raises section of a NumPy-style docstring.

    Parameters
    ----------
    docstring : str
        Full docstring text.

    Returns
    -------
    dict[str, str]
        Mapping of exception name to description.
    """
    raises: dict[str, str] = {}
    if not docstring:
        return raises
    lines = [line.rstrip() for line in docstring.splitlines()]
    in_raises = False
    for line in lines:
        stripped = line.strip()
        if re.match(r"^(Raises|Raises:)$", stripped, re.IGNORECASE):
            in_raises = True
            continue
        if not in_raises:
            continue
        if not stripped:
            continue
        if _NON_RAISES_SECTIONS_RE.match(stripped):
            break
        match = re.match(r"^([\w.]+)\s*:\s*(.*)", stripped)
        if match:
            exc, desc = match.groups()
            raises[exc.strip()] = desc.strip()
        else:
            name_match = re.match(r"^([\w.]+)$", stripped)
            if name_match:
                raises[name_match.group(1)] = ""
    return raises


def get_actual_raises(node: ast.AST) -> set[str]:
    """Collect all exception names raised within an AST node.

    Parameters
    ----------
    node : ast.AST
        AST node representing a function definition.

    Returns
    -------
    set[str]
        Set of exception class names raised.
    """
    raises: set[str] = set()
    for n in ast.walk(node):
        if not isinstance(n, ast.Raise) or n.exc is None:
            continue
        if isinstance(n.exc, ast.Name):
            raises.add(n.exc.id)
        elif isinstance(n.exc, ast.Call) and isinstance(n.exc.func, ast.Name):
            raises.add(n.exc.func.id)
        elif isinstance(n.exc, ast.Attribute):
            raises.add(n.exc.attr)
        elif isinstance(n.exc, ast.Call) and hasattr(n.exc.func, "id"):
            raises.add(n.exc.func.id)
    return raises


def normalize_exception_name(name: str) -> str:
    """Strip module prefix from a qualified exception name.

    Parameters
    ----------
    name : str
        Possibly qualified exception name (e.g., ``builtins.ValueError``).

    Returns
    -------
    str
        Unqualified exception name.
    """
    return name.split(".")[-1]


def _is_checkable(node: ast.AST) -> bool:
    """Return whether a function node should be checked at all.

    Skips ``__init__`` (NumPy documents constructor params in the class
    docstring) and functions with neither a return annotation nor ``@property``.

    Parameters
    ----------
    node : ast.AST
        A function-definition node.

    Returns
    -------
    bool
        True when the node is in scope for the consistency checks.
    """
    if not isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
        return False
    if node.name == "__init__":
        return False
    is_property = any(
        isinstance(d, ast.Name) and d.id == "property" for d in node.decorator_list
    )
    return node.returns is not None or is_property


def _extract_documented_return(doc_lines: list) -> str | None:
    """Return the documented return type from a NumPy ``Returns`` section.

    Parameters
    ----------
    doc_lines : list
        The docstring split into right-stripped lines.

    Returns
    -------
    str or None
        The joined type text, or ``None`` when no ``Returns`` body is present.
    """
    for i, line in enumerate(doc_lines):
        if line.strip().lower() != "returns":
            continue
        j = i + 1
        while j < len(doc_lines) and set(doc_lines[j].strip()) <= {"-", " "}:
            j += 1
        while j < len(doc_lines):
            candidate = doc_lines[j].strip()
            if candidate:
                type_lines = [candidate]
                base_indent = len(doc_lines[j]) - len(doc_lines[j].lstrip())
                k = j + 1
                while k < len(doc_lines):
                    nxt_strip = doc_lines[k].strip()
                    nxt_indent = len(doc_lines[k]) - len(doc_lines[k].lstrip())
                    if not nxt_strip or nxt_indent > base_indent or _SECTION_RE.match(nxt_strip):
                        break
                    type_lines.append(nxt_strip)
                    k += 1
                return " ".join(type_lines)
            j += 1
        return None
    return None


def _check_return_type(node: ast.AST, docstring: str, filepath: str) -> tuple:
    """Check the documented return type against the annotation.

    Parameters
    ----------
    node : ast.AST
        Function node (must have a return annotation).
    docstring : str
        The function docstring.
    filepath : str
        Source file (for messages).

    Returns
    -------
    tuple
        ``(errors, warnings)`` counts.
    """
    doc_lines = [ln.rstrip() for ln in docstring.split("\n")]
    if not any(line.strip().lower() == "returns" for line in doc_lines):
        return 0, 0
    returns = ast.unparse(node.returns)
    doc_type = _extract_documented_return(doc_lines)
    if doc_type is None:
        print(
            f"⚠️  Return type documented but no type found in"
            f" {node.name}() at line {node.lineno} ({filepath})"
        )
        return 0, 1
    if not compare_types(returns, doc_type):
        print(f"❌ Return type mismatch in {node.name}() at line {node.lineno} ({filepath}):")
        print(f"   Type hint: {returns}")
        print(f"   Docstring: {doc_type}")
        return 1, 0
    return 0, 0


def _documented_param_type(arg_name: str, param_lines: list) -> str | None:
    """Return the documented type for a parameter, or ``None`` if undocumented.

    Recognises the combined NumPy form (``a, b : type``) and joins multi-line
    type continuations.

    Parameters
    ----------
    arg_name : str
        The parameter name to find.
    param_lines : list
        The docstring split into lines.

    Returns
    -------
    str or None
        The documented type text, or ``None`` when the parameter is absent.
    """
    for li, line in enumerate(param_lines):
        if arg_name not in _param_names(line):
            continue
        type_part = line.split(":", 1)[1].strip()
        line_indent = len(line) - len(line.lstrip())
        k = li + 1
        while k < len(param_lines):
            nxt = param_lines[k]
            nxt_strip = nxt.strip()
            nxt_indent = len(nxt) - len(nxt.lstrip())
            if not nxt_strip or nxt_indent > line_indent:
                break
            if _param_names(nxt) or _SECTION_RE.match(nxt_strip):
                break
            type_part += " " + nxt_strip
            k += 1
        return type_part
    return None


def _check_parameters(node: ast.AST, docstring: str, filepath: str) -> tuple:
    """Check each annotated parameter's documented type against its annotation.

    Parameters
    ----------
    node : ast.AST
        Function node.
    docstring : str
        The function docstring.
    filepath : str
        Source file (for messages).

    Returns
    -------
    tuple
        ``(errors, warnings)`` counts.
    """
    errors = 0
    warnings = 0
    param_lines = docstring.split("\n")
    for arg in node.args.args:
        if arg.arg == "self" or not arg.annotation:
            continue
        hint = ast.unparse(arg.annotation)
        doc_type = _documented_param_type(arg.arg, param_lines)
        if doc_type is None:
            print(
                f"⚠️  Missing docstring for parameter {arg.arg}"
                f" in {node.name}() at line {node.lineno} ({filepath})"
            )
            warnings += 1
            continue
        if not compare_types(hint, doc_type):
            print(
                f"❌ Parameter type mismatch in {node.name}({arg.arg})"
                f" at line {node.lineno} ({filepath}):"
            )
            print(f"   Type hint: {hint}")
            print(f"   Docstring: {doc_type}")
            errors += 1
    return errors, warnings


def _check_raises(node: ast.AST, docstring: str, filepath: str) -> int:
    """Compare the documented Raises section against exceptions actually raised.

    Convention enforced: a ``Raises`` section documents **only** exceptions the
    function raises directly (a literal ``raise`` in its own body) — never
    exceptions merely propagated from a callee or a library. Both directions are
    therefore strict: documenting a propagated exception ("documented but not
    raised") and leaving a direct raise undocumented ("raised but not documented")
    are both flagged. This keeps the check deterministic.

    Parameters
    ----------
    node : ast.AST
        Function node.
    docstring : str
        The function docstring.
    filepath : str
        Source file (for messages).

    Returns
    -------
    int
        Number of warnings (raises drift is never a hard error).
    """
    doc_exceptions = {normalize_exception_name(e) for e in parse_raises_section(docstring)}
    actual_exceptions = {normalize_exception_name(e) for e in get_actual_raises(node)}
    warnings = 0
    for exc in doc_exceptions - actual_exceptions:
        print(
            f"⚠️  Documented but not raised exception {exc}"
            f" in {node.name}() at line {node.lineno} ({filepath})"
        )
        warnings += 1
    for exc in actual_exceptions - doc_exceptions:
        print(
            f"⚠️  Raised but not documented exception {exc}"
            f" in {node.name}() at line {node.lineno} ({filepath})"
        )
        warnings += 1
    return warnings


def check_file(filepath: str) -> int:
    """Check type and raises consistency for all functions in a Python file.

    Parameters
    ----------
    filepath : str
        Path to the Python source file.

    Returns
    -------
    int
        Number of hard (type-mismatch) errors found. Soft style warnings
        (missing docstrings, undocumented fixture params, exception-doc drift) are
        printed but do not count toward the failing total.
    """
    errors = 0
    warnings = 0
    with open(filepath, encoding="utf-8") as fh:
        tree = ast.parse(fh.read(), filename=filepath)
    for node in ast.walk(tree):
        if not _is_checkable(node):
            continue
        docstring = ast.get_docstring(node)
        if not docstring:
            print(f"⚠️  Missing docstring in {node.name}() at line {node.lineno} ({filepath})")
            warnings += 1
            continue
        if node.returns is not None:
            ret_errors, ret_warnings = _check_return_type(node, docstring, filepath)
            errors += ret_errors
            warnings += ret_warnings
        param_errors, param_warnings = _check_parameters(node, docstring, filepath)
        errors += param_errors
        warnings += param_warnings
        warnings += _check_raises(node, docstring, filepath)
    if warnings:
        print(f"   ({warnings} warning(s) in {filepath} — not counted as errors)")
    return errors


if __name__ == "__main__":
    targets = list(pathlib.Path("src").rglob("*.py")) + list(
        pathlib.Path("tests").rglob("*.py")
    )
    total_errors = sum(check_file(str(p)) for p in targets)
    sys.exit(1 if total_errors > 0 else 0)
