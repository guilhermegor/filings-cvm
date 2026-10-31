"""CVM Lâmina de Fundos — submission (envio) writer.

Produces the Lâmina V3 XML from a validated :class:`LaminaDocument`. The schema declares its
fields in XML order and named after their tag, so the serialiser is one recursive walk over
``model_fields``: a ``None`` is omitted, a nested model is a block, a list repeats its element.
Pure logic plus file I/O at the edges — no network.
"""

from decimal import Decimal
from pathlib import Path
from xml.etree import ElementTree as ET  # noqa: S405  # builds XML, never parses untrusted input

from pydantic import BaseModel

from filings_cvm._internal.config.ports.submission_writer import SubmissionWriter
from filings_cvm._internal.config.schemas.lamina import LaminaDocument
from filings_cvm._internal.utils.typing import type_checker


_NAMESPACE = "urn:lamina"
_ENCODING = "windows-1252"
_DECLARATION = f'<?xml version="1.0" encoding="{_ENCODING}"?>\n'
_INDENT = "    "


@type_checker
def _scalar_text(value: Decimal | int | str) -> str:
	"""Render one scalar the way the page requires: comma decimal separator, no filler zeros.

	Parameters
	----------
	value : Decimal | int | str
		The field value, already scaled by the schema.

	Returns
	-------
	str
		The element text.
	"""
	if isinstance(value, Decimal):
		return format(value, "f").replace(".", ",")
	return str(value)


@type_checker
def _append(parent: ET.Element, name: str, value: object) -> None:
	"""Append one field to ``parent`` as an element, or as repeated elements for a list.

	Parameters
	----------
	parent : ET.Element
		The enclosing block.
	name : str
		The schema field name; its upper case is the XML tag.
	value : object
		``None`` (omitted), a nested model, a list of either, or a scalar.
	"""
	if value is None:
		return
	if isinstance(value, list):
		for item in value:
			_append(parent, name, item)
		return
	element = ET.SubElement(parent, name.upper())
	if isinstance(value, BaseModel):
		for field in type(value).model_fields:
			_append(element, field, getattr(value, field))
		return
	element.text = _scalar_text(value)


class Lamina(SubmissionWriter[LaminaDocument]):
	"""Serialize a validated Lâmina V3 document to CVM-compliant XML.

	Concrete :class:`SubmissionWriter` for the Lâmina de Fundos V3 XML standard.

	Methods
	-------
	export(doc, output_path)
		Serialize a validated document to windows-1252 XML.
	"""

	def export(self, doc: LaminaDocument, output_path: str | None = None) -> str | None:
		"""Serialize a validated LaminaDocument to a CVM-compliant XML string or file.

		The text is encoded and checked for well-formedness **before** the destination is
		opened, so a failure never truncates an existing file.

		Parameters
		----------
		doc : LaminaDocument
			Fully validated document model.
		output_path : Optional[str]
			Destination file. When given the file is written in windows-1252 and ``None`` is
			returned; otherwise the XML string is returned, by default None.

		Returns
		-------
		Optional[str]
			The XML text when ``output_path`` is None, else None.

		Raises
		------
		ValueError
			If the document holds text windows-1252 cannot encode or XML cannot carry (only
			possible when validation was bypassed, e.g. ``model_construct``).
		"""
		root = ET.Element("DOC_ARQ", {"xmlns": _NAMESPACE})
		_append(root, "cab_inform", doc.header)
		informs = ET.SubElement(root, "LISTA_INFORM")
		for inform in doc.informs:
			_append(informs, "inform", inform)
		ET.indent(root, space=_INDENT)
		xml_str = _DECLARATION + ET.tostring(root, encoding="unicode") + "\n"
		try:
			payload = xml_str.encode(_ENCODING)
			ET.fromstring(payload)  # noqa: S314  # well-formedness self-check of our own output
		except (UnicodeEncodeError, ET.ParseError) as exc:
			raise ValueError(f"document cannot be serialised as {_ENCODING} XML: {exc}") from exc
		if output_path is None:
			return xml_str
		Path(output_path).write_bytes(payload)
		return None
