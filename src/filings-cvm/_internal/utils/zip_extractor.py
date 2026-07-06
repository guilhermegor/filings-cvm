"""Zip extraction seam — idempotent, optional, password-aware.

A reusable place for "unzip this file (maybe password-protected), but only when needed".
``zipfile`` is stdlib, so no coupling seam is strictly required — this module exists for the
*behaviour*: opt-in extraction, idempotent (skip when the target is already present), and a
caller-supplied password (from ``.env``), never hard-coded.

The ``*_to_memory`` functions are the on-disk trio's counterparts for when the extracted
bytes are consumed immediately (parsed, streamed, hashed) and never need to hit the disk —
returning all members, a subset, or a single member.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING
import zipfile


# Runtime type-checking engine — layout-agnostic (utils.typing in MVC, chassis.typing in
# DDD; always injected, just at different paths). mypy reads the single TYPE_CHECKING
# import (no redefinition); at runtime the try/except picks whichever layout shipped.
if TYPE_CHECKING:
	from filings-cvm._internal.utils.typing import type_checker
else:
	try:
		from filings-cvm._internal.utils.typing import type_checker
	except ModuleNotFoundError:  # DDD ships the engine as chassis.typing
		from filings-cvm._internal.utils.typing import type_checker


@type_checker
def unzip_if_needed(
	path_zip: Path,
	path_target: Path,
	bool_enabled: bool,
	str_password: str | None = None,
) -> bool:
	"""Extract ``path_zip`` into the target's directory, when enabled and absent.

	Extraction happens only when **all** hold: ``bool_enabled`` is true, the target file is
	not already present, and the zip exists. Otherwise nothing is done (the caller decides
	what an absent target means — e.g. notify + fallback).

	Parameters
	----------
	path_zip : pathlib.Path
		The (password-protected) zip to extract.
	path_target : pathlib.Path
		The file expected after extraction; if it already exists, extraction is skipped
		(idempotent). Its parent directory is the extraction destination.
	bool_enabled : bool
		Config switch: only extract when true.
	str_password : str, optional
		ZipCrypto password (from ``.env``); ``None`` for an unencrypted zip.

	Returns
	-------
	bool
		``True`` when extraction was performed, ``False`` when skipped (target already
		present, extraction disabled, or the zip is absent).
	"""
	if path_target.exists():
		return False
	if not bool_enabled or not path_zip.exists():
		return False
	extract_all(path_zip, path_target.parent, str_password)
	return True


@type_checker
def extract_members(path_zip: Path, path_dest_dir: Path, list_members: list[str]) -> list[Path]:
	"""Extract only the named members of ``path_zip`` into ``path_dest_dir``.

	Members absent from the archive are silently skipped (the caller decides what a missing
	member means). Used for large multi-file archives where only a few files are needed.

	Parameters
	----------
	path_zip : pathlib.Path
		The zip to read.
	path_dest_dir : pathlib.Path
		Destination directory (created if absent).
	list_members : list of str
		The archive member names to extract.

	Returns
	-------
	list of pathlib.Path
		The extracted file paths (only those members that were present).

	Raises
	------
	FileNotFoundError
		If ``path_zip`` does not exist.
	"""
	if not path_zip.exists():
		raise FileNotFoundError(f"Zip not found: {path_zip}")
	path_dest_dir.mkdir(parents=True, exist_ok=True)
	list_out: list[Path] = []
	with zipfile.ZipFile(path_zip) as cls_zip:
		set_names = set(cls_zip.namelist())
		for str_member in list_members:
			if str_member in set_names:
				cls_zip.extract(str_member, path_dest_dir)
				list_out.append(path_dest_dir / str_member)
	return list_out


@type_checker
def extract_all(
	path_zip: Path, path_dest_dir: Path, str_password: str | None = None
) -> list[Path]:
	"""Extract every member of ``path_zip`` into ``path_dest_dir``.

	Parameters
	----------
	path_zip : pathlib.Path
		The zip to extract.
	path_dest_dir : pathlib.Path
		Destination directory (created if absent).
	str_password : str, optional
		ZipCrypto password; ``None`` for an unencrypted zip.

	Returns
	-------
	list of pathlib.Path
		The extracted file paths, in archive order.

	Raises
	------
	FileNotFoundError
		If ``path_zip`` does not exist.
	"""
	if not path_zip.exists():
		raise FileNotFoundError(f"Zip not found: {path_zip}")
	path_dest_dir.mkdir(parents=True, exist_ok=True)
	bytes_pwd = str_password.encode() if str_password else None
	with zipfile.ZipFile(path_zip) as cls_zip:
		cls_zip.extractall(path_dest_dir, pwd=bytes_pwd)
		return [path_dest_dir / str_name for str_name in cls_zip.namelist()]


@type_checker
def extract_all_to_memory(path_zip: Path, str_password: str | None = None) -> dict[str, bytes]:
	"""Read every file member of ``path_zip`` into memory, never touching disk.

	The in-memory counterpart of :func:`extract_all` — for when the extracted bytes are
	consumed immediately (parsed, streamed, hashed) and persisting them would be wasteful or
	unwanted. Directory entries are skipped; only file members are returned.

	Parameters
	----------
	path_zip : pathlib.Path
		The zip to read.
	str_password : str, optional
		ZipCrypto password; ``None`` for an unencrypted zip.

	Returns
	-------
	dict of {str: bytes}
		Member name → its decompressed bytes, for every file member.

	Raises
	------
	FileNotFoundError
		If ``path_zip`` does not exist.
	"""
	if not path_zip.exists():
		raise FileNotFoundError(f"Zip not found: {path_zip}")
	bytes_pwd = str_password.encode() if str_password else None
	with zipfile.ZipFile(path_zip) as cls_zip:
		return {
			str_name: cls_zip.read(str_name, pwd=bytes_pwd)
			for str_name in cls_zip.namelist()
			if not str_name.endswith("/")
		}


@type_checker
def extract_members_to_memory(
	path_zip: Path, list_members: list[str], str_password: str | None = None
) -> dict[str, bytes]:
	"""Read only the named members of ``path_zip`` into memory (absent members skipped).

	The in-memory counterpart of :func:`extract_members` — for large multi-file archives
	where only a few members are needed and the bytes are consumed in place. Members absent
	from the archive are silently skipped (the caller decides what a missing member means).

	Parameters
	----------
	path_zip : pathlib.Path
		The zip to read.
	list_members : list of str
		The archive member names to read.
	str_password : str, optional
		ZipCrypto password; ``None`` for an unencrypted zip.

	Returns
	-------
	dict of {str: bytes}
		Member name → its decompressed bytes, for each requested member that was present.

	Raises
	------
	FileNotFoundError
		If ``path_zip`` does not exist.
	"""
	if not path_zip.exists():
		raise FileNotFoundError(f"Zip not found: {path_zip}")
	bytes_pwd = str_password.encode() if str_password else None
	dict_out: dict[str, bytes] = {}
	with zipfile.ZipFile(path_zip) as cls_zip:
		set_names = set(cls_zip.namelist())
		for str_member in list_members:
			if str_member in set_names:
				dict_out[str_member] = cls_zip.read(str_member, pwd=bytes_pwd)
	return dict_out


@type_checker
def extract_member_to_memory(
	path_zip: Path, str_member: str, str_password: str | None = None
) -> bytes:
	"""Read a single named member of ``path_zip`` into memory.

	The single-member in-memory read — for pulling one known file out of an archive without
	writing anything to disk.

	Parameters
	----------
	path_zip : pathlib.Path
		The zip to read.
	str_member : str
		The archive member name to read.
	str_password : str, optional
		ZipCrypto password; ``None`` for an unencrypted zip.

	Returns
	-------
	bytes
		The decompressed bytes of ``str_member``.

	Raises
	------
	FileNotFoundError
		If ``path_zip`` does not exist.
	KeyError
		If ``str_member`` is not present in the archive.
	"""
	if not path_zip.exists():
		raise FileNotFoundError(f"Zip not found: {path_zip}")
	bytes_pwd = str_password.encode() if str_password else None
	with zipfile.ZipFile(path_zip) as cls_zip:
		if str_member not in set(cls_zip.namelist()):
			raise KeyError(f"Member {str_member!r} not in {path_zip}")
		return cls_zip.read(str_member, pwd=bytes_pwd)
