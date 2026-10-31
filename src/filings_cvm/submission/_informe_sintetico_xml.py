"""Shared serialiser for the four Informe Sintético writers (private).

Each variant's schema declares its fields in XML order, named after their tag, so one recursive
walk over ``model_fields`` serialises any of them: a nested model is a block, a scalar is an
element. Pure logic plus file I/O at the edges — no network.
"""

from decimal import Decimal
from pathlib import Path
from xml.etree import ElementTree as ET  # noqa: S405  # builds XML, never parses untrusted input

from pydantic import BaseModel

from filings_cvm._internal.utils.typing import type_checker


_ENCODING = "windows-1252"
_DECLARATION = f'<?xml version="1.0" encoding="{_ENCODING}"?>\n'
_INDENT = "\t"


@type_checker
def _scalar_text(name: str, value: Decimal | int | str) -> str:
	"""Render one scalar as the pages require: comma decimals, no filler zeros.

	The pages ask for a CNPJ without "pontos, traços, barras e zeros a esquerda", so a
	``cnpj_*`` field loses its leading zeros here (the schema keeps the 14-character form).

	Parameters
	----------
	name : str
		The schema field name.
	value : Decimal | int | str
		The field value, already validated by the schema.

	Returns
	-------
	str
		The element text.
	"""
	if isinstance(value, Decimal):
		return format(value, "f").replace(".", ",")
	if name.startswith("cnpj_"):
		return str(value).lstrip("0")
	return str(value)


@type_checker
def _append(parent: ET.Element, name: str, value: object) -> None:
	"""Append one field to ``parent`` (recursing into nested models).

	Parameters
	----------
	parent : ET.Element
		The enclosing block.
	name : str
		The schema field name; its upper case is the XML tag.
	value : object
		A nested model or a scalar.
	"""
	element = ET.SubElement(parent, name.upper())
	if isinstance(value, BaseModel):
		for field in type(value).model_fields:
			_append(element, field, getattr(value, field))
		return
	element.text = _scalar_text(name, value)


@type_checker
def serialise(doc: BaseModel, output_path: str | None) -> str | None:
	"""Serialise a variant document to windows-1252 XML.

	The text is encoded and checked for well-formedness **before** the destination is opened,
	so a failure never truncates an existing file.

	Parameters
	----------
	doc : BaseModel
		A validated ``InformeSintetico*Document`` (``header`` plus ``informs``).
	output_path : str | None
		Destination file; when given the bytes are written and ``None`` is returned.

	Returns
	-------
	str | None
		The XML text when ``output_path`` is None, else None.

	Raises
	------
	ValueError
		If the document holds text windows-1252 cannot encode (only possible when validation
		was bypassed, e.g. ``model_construct``).
	"""
	root = ET.Element("DOC_ARQ")
	_append(root, "desc_adm", doc.header)  # type: ignore[attr-defined]
	informs = ET.SubElement(root, "INFORME_SINTETICO")
	for inform in doc.informs:  # type: ignore[attr-defined]
		_append(informs, "row_informe", inform)
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
