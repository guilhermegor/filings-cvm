r"""CVM META parser — the block-structured spec text CVM publishes → flat records.

Every open-data dataset ships a **META** artifact (`.../<DATASET>/META/meta_*.txt|zip`)
describing its fields. It is **not** CSV: it is a block of the form

    -----------------------
    Campo: Data_Referencia
    -----------------------
       Descrição : Data de referência do documento
       Domínio   : AAAA-MM-DD
       Tipo Dados: date
       Tamanho   : 10

encoded **ISO-8859-1** with **CRLF** line endings.

Two properties of the source are load-bearing, and both are honoured here rather than smoothed
over:

- **CVM truncates the field name at exactly 50 characters.** The real artifact header carries
  names up to 60. This parser returns the truncated name **verbatim** — "repairing" it would
  fabricate a string CVM never published and destroy the only non-tautological oracle the
  contracts have. Reconciling META against the real header belongs to the consumer, and must
  compare ``real[:50] == meta``.
- **CRLF.** The line endings are normalised **once**, on entry. Skip it and every value silently
  keeps a trailing ``\r`` — a field parses as ``"Data_Referencia\r"`` and even a 50-char
  truncation check misses, because the name measures 51.

Pure text→records transform: no I/O, no pandas. The reader owns the download and the frame.
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING


if TYPE_CHECKING:
	from filings_cvm._internal.utils.typing import type_checker
else:
	try:
		from filings_cvm._internal.utils.typing import type_checker
	except ModuleNotFoundError:  # DDD ships the engine as chassis.typing
		from filings_cvm._internal.utils.typing import type_checker


# CVM's pt-BR attribute labels → this package's English column names. The labels are *hers* (they
# are the source's text); the column names are *ours* (CVM publishes no table), which is why they
# are English like the provenance columns. Values stay verbatim pt-BR.
_ATTRIBUTE_COLUMNS: dict[str, str] = {
	"Descrição": "description",
	"Domínio": "domain",
	"Tipo Dados": "data_type",
	"Tamanho": "size",
	"Precisão": "precision",
	"Scale": "scale",
}

# The output record's keys, in column order. `section` and `field` are positional; the rest are
# derived from _ATTRIBUTE_COLUMNS, so the two cannot drift. PUBLIC within `_internal`: the META
# contracts import this as their `tuple_required` rather than restating the list, so the parsed
# shape has exactly ONE definition.
RECORD_COLUMNS: tuple[str, ...] = ("section", "field", *_ATTRIBUTE_COLUMNS.values())

_RE_FIELD = re.compile(r"^Campo:[ \t]*(?P<field>.+?)[ \t]*$", re.MULTILINE)
_RE_ATTRIBUTE = re.compile(
	r"^[ \t]*(?P<key>" + "|".join(_ATTRIBUTE_COLUMNS) + r")[ \t]*:[ \t]*(?P<value>.*?)[ \t]*$",
	re.MULTILINE,
)


@type_checker
def parse_meta_blocks(str_text: str, str_section: str) -> list[dict[str, str]]:
	"""Parse one META document into one record per declared field.

	Parameters
	----------
	str_text : str
		The decoded META text (ISO-8859-1 → str). CRLF is normalised here.
	str_section : str
		The section this document describes — a ZIP member's name for a multi-member META, or the
		dataset itself for a flat one. Copied onto every record.

	Returns
	-------
	list of dict of (str, str)
		One record per ``Campo:`` block, in document order, each carrying exactly
		:data:`RECORD_COLUMNS`. An attribute the block omits is ``""`` (never ``None``) — a
		varchar block has no ``Precisão``/``Scale``, a numeric one has no ``Tamanho``. Text with
		no block at all yields ``[]`` rather than raising: a META that changes shape must not
		crash a datalake run.
	"""
	# CVM ships CRLF. Normalise ONCE, here — otherwise every value keeps a trailing "\r".
	str_normalised = str_text.replace("\r\n", "\n")
	list_matches = list(_RE_FIELD.finditer(str_normalised))
	list_records: list[dict[str, str]] = []
	for int_index, cls_match in enumerate(list_matches):
		int_block_end = (
			list_matches[int_index + 1].start()
			if int_index + 1 < len(list_matches)
			else len(str_normalised)
		)
		dict_record = dict.fromkeys(RECORD_COLUMNS, "")
		dict_record["section"] = str_section
		dict_record["field"] = cls_match.group("field")
		str_block = str_normalised[cls_match.end() : int_block_end]
		for cls_attribute in _RE_ATTRIBUTE.finditer(str_block):
			str_key = _ATTRIBUTE_COLUMNS[cls_attribute.group("key")]
			dict_record[str_key] = cls_attribute.group("value")
		list_records.append(dict_record)
	return list_records
