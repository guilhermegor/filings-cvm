"""Structural gate: an ingested source column is never typed as a binary float.

A binary float cannot represent most decimal fractions. A fund's net asset value of
``1984223115.42`` is stored as ``1984223115.4200000762939453125`` — close enough to print
correctly, wrong enough that summing a period and reconciling against CVM's own published
total misses by a hair, with nothing to point at. The loss happens at ingestion, is
**irreversible**, and is **silent**: no contract check, no test of a single value, and no
eyeball on a printed frame will show it.

So this gate bans a float dtype declaration in ``src/``. The replacement is
``list_decimal_cols`` (exact :class:`decimal.Decimal`, scale preserved from the source) or
plain text; both are lossless, and a consumer can always downcast to float, whereas the
reverse is impossible.

Ruff cannot express this check: ``flake8-tidy-imports`` ``banned-api`` matches imports and
attribute access, not a ``"float64"`` string literal sitting inside a dtype dict.

**Escape hatch.** A genuinely dimensionless quantity with no exact decimal scale — a
statistical measure, a ratio derived by the source — may legitimately be a float. Annotate the
line and the gate accepts it::

	"SOME_RATIO": "float64",  # dtype-ok: dimensionless statistic, no exact scale

Requiring the reason in writing is the point: it turns an invisible default into a decision
someone made on purpose.
"""

import pathlib
import re
import sys


# Matches a dtype declaration whose value names a binary float, in either the dict form
# ("COL": "float64") or a bare pandas/numpy spelling. Deliberately text-based rather than AST:
# the target is a string literal in a class-level dict, which an AST walk complicates without
# buying accuracy here.
_RE_FLOAT_DTYPE = re.compile(r"""["'](?:float(?:16|32|64|128)?|Float(?:32|64))["']""")

# The line-scoped opt-out; must carry a reason after the colon. Named MARKER rather than
# TOKEN so bandit (ruff S105) does not read it as a hardcoded credential.
_ALLOW_MARKER = "dtype-ok:"

# Tree exempt from the ban: the runtime type-checking engine, which names float as a *type*
# (annotation introspection), not as a column dtype.
_EXCLUDED_PARTS = {"typing"}


def check_file(str_path: str) -> int:
	"""Report every banned float dtype declaration in one file.

	Parameters
	----------
	str_path : str
		Path to the Python source file to scan.

	Returns
	-------
	int
		The number of violations found (0 when clean).
	"""
	int_errors = 0
	for int_no, str_line in enumerate(
		pathlib.Path(str_path).read_text(encoding="utf-8").splitlines(), start=1
	):
		if not _RE_FLOAT_DTYPE.search(str_line):
			continue
		if _ALLOW_MARKER in str_line:
			continue
		print(
			f"❌ {str_path}:{int_no}: {str_line.strip()}\n"
			f"   A binary float loses the source value irreversibly and silently. Use "
			f"list_decimal_cols (exact Decimal) or text. If the value is genuinely "
			f"dimensionless, annotate the line:  # {_ALLOW_MARKER} <reason>"
		)
		int_errors += 1
	return int_errors


def _source_files() -> list[pathlib.Path]:
	"""Collect every Python file under ``src/`` outside the exempt trees.

	Returns
	-------
	list[pathlib.Path]
		Python source files to check.
	"""
	return sorted(
		p for p in pathlib.Path("src").rglob("*.py") if _EXCLUDED_PARTS.isdisjoint(p.parts)
	)


if __name__ == "__main__":
	total_errors = sum(check_file(str(p)) for p in _source_files())
	sys.exit(1 if total_errors > 0 else 0)
