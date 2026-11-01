"""CVM Informe Anual de Auditor — submission (envio) writer.

Produces the XML from a validated :class:`InformeAnualAuditorDocument`. The schema declares its
fields in XML order and named after their tag, so the serialiser is one recursive walk over
``model_fields``: a ``None`` is omitted, a nested model is a block, a ``lista_*`` field is a
container of repeated elements. Pure logic plus file I/O at the edges — no network.
"""

from decimal import Decimal
from functools import singledispatch
from xml.etree import ElementTree as ET  # noqa: S405  # builds XML, never parses untrusted input

from pydantic import BaseModel

from filings_cvm._internal.config.ports.submission_writer import SubmissionWriter
from filings_cvm._internal.config.schemas.informe_anual_auditor import (
	InformeAnualAuditorDocument,
)
from filings_cvm._internal.utils.atomic_write import atomic_write_bytes
from filings_cvm._internal.utils.typing import type_checker


_NAMESPACE = "urn:audtanual"
_ENCODING = "windows-1252"
_DECLARATION = f'<?xml version="1.0" encoding="{_ENCODING}"?>\n'
_INDENT = " "
_LIST_PREFIX = "lista_"
# Containers the page says to omit when there is nothing to report; the others stay present.
_OMIT_WHEN_EMPTY = frozenset({"lista_resp", "lista_treina", "lista_treina_pessoa"})


@type_checker
def _scalar_text(value: Decimal | int | str) -> str:
	"""Render one scalar: comma decimal separator, no filler zeros.

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
def _is_omitted(name: str, value: object) -> bool:
	"""Say whether a field produces no element at all.

	Parameters
	----------
	name : str
		The schema field name.
	value : object
		The field value.

	Returns
	-------
	bool
		True for ``None`` and for an empty container the page says to omit.
	"""
	return value is None or (value == [] and name in _OMIT_WHEN_EMPTY)


@type_checker
def _append(parent: ET.Element, name: str, value: object) -> None:
	"""Append one field to ``parent`` as an element, a block, or a container.

	Parameters
	----------
	parent : ET.Element
		The enclosing block.
	name : str
		The schema field name; its upper case is the XML tag.
	value : object
		``None`` (omitted), a nested model, a list (container) or a scalar.
	"""
	if _is_omitted(name, value):
		return
	_fill(value, ET.SubElement(parent, name.upper()), name)


@singledispatch
@type_checker
def _fill(value: object, element: ET.Element, name: str) -> None:  # noqa: ARG001
	"""Fill ``element`` from a scalar value (the default arm of the dispatch).

	Parameters
	----------
	value : object
		The scalar field value.
	element : ET.Element
		The element created for the field.
	name : str
		The schema field name (unused for scalars).
	"""
	element.text = _scalar_text(value)


@_fill.register(list)
@type_checker
def _fill_list(value: list, element: ET.Element, name: str) -> None:
	"""Fill a container with one repeated element per item.

	Parameters
	----------
	value : list
		The items.
	element : ET.Element
		The container element.
	name : str
		The ``lista_*`` field name; the repeated tag is the name without the prefix.
	"""
	for item in value:
		_append(element, name.removeprefix(_LIST_PREFIX), item)


@_fill.register(BaseModel)
@type_checker
def _fill_model(value: BaseModel, element: ET.Element, name: str) -> None:  # noqa: ARG001
	"""Fill a block with its model's fields, in declaration (XML) order.

	Parameters
	----------
	value : BaseModel
		The nested block.
	element : ET.Element
		The block element.
	name : str
		The schema field name (unused for blocks).
	"""
	for field in type(value).model_fields:
		_append(element, field, getattr(value, field))


@type_checker
def _build_xml(doc: InformeAnualAuditorDocument) -> str:
	"""Serialise the document to indented XML text with the declaration.

	Parameters
	----------
	doc : InformeAnualAuditorDocument
		Fully validated document model.

	Returns
	-------
	str
		The XML text.
	"""
	root = ET.Element("DOC_ARQ", {"xmlns": _NAMESPACE})
	ET.SubElement(root, "COD_DOC").text = str(doc.cod_doc)
	inform = ET.SubElement(root, "INFORM_AUDIT")
	for field in [f for f in type(doc).model_fields if f != "cod_doc"]:
		_append(inform, field, getattr(doc, field))
	ET.indent(root, space=_INDENT)
	return _DECLARATION + ET.tostring(root, encoding="unicode") + "\n"


@type_checker
def _encode(xml_str: str) -> bytes:
	"""Encode the XML and check it is well-formed.

	Parameters
	----------
	xml_str : str
		The XML text.

	Returns
	-------
	bytes
		The windows-1252 payload.

	Raises
	------
	ValueError
		If the text cannot be encoded or is not well-formed XML.
	"""
	try:
		payload = xml_str.encode(_ENCODING)
		ET.fromstring(payload)  # noqa: S314  # well-formedness self-check of our own output
	except (UnicodeEncodeError, ET.ParseError) as exc:
		raise ValueError(f"document cannot be serialised as {_ENCODING} XML: {exc}") from exc
	return payload


class InformeAnualAuditor(SubmissionWriter[InformeAnualAuditorDocument]):
	"""Serialize a validated Informe Anual de Auditor to CVM-compliant XML.

	Concrete :class:`SubmissionWriter` for the Informe Anual de Auditor XML standard.

	Methods
	-------
	export(doc, output_path)
		Serialize a validated document to windows-1252 XML.
	"""

	def export(
		self, doc: InformeAnualAuditorDocument, output_path: str | None = None
	) -> str | None:
		"""Serialize a validated document to a CVM-compliant XML string or file.

		The text is encoded and checked for well-formedness **before** the destination is
		opened, so a failure never truncates an existing file.

		Parameters
		----------
		doc : InformeAnualAuditorDocument
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
		xml_str = _build_xml(doc)
		payload = _encode(xml_str)
		if output_path is None:
			return xml_str
		atomic_write_bytes(output_path, payload)
		return None
