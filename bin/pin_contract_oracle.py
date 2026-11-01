"""Pin a data contract's columns to a source oracle — generate, never transcribe.

Extracts the **header** of a real downloaded artifact and prints it as a Python tuple (ready to
paste as a ``FileContract.tuple_required``), and optionally writes it verbatim as a header-only
fixture under ``tests/fixtures/`` for the ``contract.tuple_required == oracle`` assertion.

Why a tool: the whole anti-tautology point is that the contract's columns are *derived from the
bytes the source produced*, not hand-typed to match the contract you already wrote. Run this
against the real artifact, paste the tuple, and commit the header fixture — the fixture and the
contract then encode two independently-produced facts that a test can compare.

Operates on a **local file** (download the artifact first, then point this at it) so the tool
needs no network and never touches the socket-blocked test path. Header-only output carries no
data rows, so it is safe to commit even when the artifact holds personal data (CPF/CNPJ).

Usage
-----
    python bin/pin_contract_oracle.py <artifact.csv> [--sep ';'] [--encoding ISO-8859-1] \
        [--write tests/fixtures/<dataset>/<dataset>_<section>_header.csv]

CVM publishes ISO-8859-1, so that is the default; the fixture is written back in the same
encoding so it stays the verbatim header bytes (``tests/CLAUDE.md``).
"""

import argparse
import pathlib
import sys


def read_header(path_file: pathlib.Path, str_sep: str, str_encoding: str) -> tuple[str, ...]:
	"""Return the first non-empty line of a delimited file as a tuple of stripped column names.

	Parameters
	----------
	path_file : pathlib.Path
		The downloaded artifact (CSV / delimited text).
	str_sep : str
		Column delimiter.
	str_encoding : str
		Text encoding to decode the file with.

	Returns
	-------
	tuple of str
		The header columns, in the file's own order.

	Raises
	------
	ValueError
		If the file has no non-empty line.
	"""
	with path_file.open(encoding=str_encoding) as fh:
		for str_line in fh:
			if str_line.strip():
				return tuple(cell.strip() for cell in str_line.rstrip("\n").split(str_sep))
	raise ValueError(f"no non-empty header line in {path_file}")


def main(list_argv: list[str] | None = None) -> int:
	"""Parse arguments, print the header tuple, and optionally write the fixture.

	Parameters
	----------
	list_argv : list of str, optional
		Arguments after the program name; ``None`` reads ``sys.argv``.

	Returns
	-------
	int
		Process exit code (0 on success).
	"""
	parser = argparse.ArgumentParser(description="Pin a contract's columns to a source oracle.")
	parser.add_argument("artifact", type=pathlib.Path, help="path to the downloaded artifact")
	parser.add_argument("--sep", default=";", help="column delimiter (default ';')")
	parser.add_argument(
		"--encoding", default="ISO-8859-1", help="text encoding (default ISO-8859-1)"
	)
	parser.add_argument(
		"--write",
		type=pathlib.Path,
		default=None,
		help="also write the header line verbatim to this fixture path",
	)
	args = parser.parse_args(list_argv)

	tuple_header = read_header(args.artifact, args.sep, args.encoding)
	print("tuple_required = (")
	for str_col in tuple_header:
		print(f'    "{str_col}",')
	print(")")

	if args.write is not None:
		args.write.parent.mkdir(parents=True, exist_ok=True)
		args.write.write_text(args.sep.join(tuple_header) + "\n", encoding=args.encoding)
		print(f"\nWrote header fixture: {args.write}", file=sys.stderr)
	return 0


if __name__ == "__main__":
	sys.exit(main())
