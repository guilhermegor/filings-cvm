"""CVM Perfil Mensal original layout — submission (envio) writer.

Produces the original-layout Monthly Profile XML (``PadraoXMLPerfil.asp``) from a validated
:class:`PerfilMensalOriginalDocument`. The schema walks in XML order and every field is named
after its tag, so the document is built by one generic walk. Pure logic plus file I/O at the
edges — no network.
"""

from decimal import Decimal
from xml.etree import ElementTree as ET  # noqa: S405  # builds XML, never parses untrusted input

from pydantic import BaseModel

from filings_cvm._internal.config.ports.submission_writer import SubmissionWriter
from filings_cvm._internal.config.schemas.perfil_mensal_original import (
	PerfilMensalOriginalDocument,
)
from filings_cvm._internal.utils.atomic_write import atomic_write_bytes
from filings_cvm._internal.utils.typing import type_checker


_ENCODING = "windows-1252"
_DECLARATION = f'<?xml version="1.0" encoding="{_ENCODING}"?>\n'
_NAMESPACE = "urn:perf"
_INDENT = "    "


@type_checker
def _text(value: object) -> str:
	"""Render one scalar the way the page's sample does (comma as decimal separator).

	Parameters
	----------
	value : object
		An ``int``, ``str`` or already-quantized ``Decimal`` taken from the model.

	Returns
	-------
	str
		The tag text; a ``Decimal`` keeps its own scale.
	"""
	if isinstance(value, Decimal):
		return format(value, "f").replace(".", ",")
	return str(value)


@type_checker
def _set_fields(model: BaseModel) -> list[tuple[str, object]]:
	"""List a model's fields that hold a value, in declaration (= sample) order.

	Parameters
	----------
	model : BaseModel
		The block to walk.

	Returns
	-------
	list[tuple[str, object]]
		``(field name, value)`` pairs, skipping the unset optional fields.
	"""
	return [
		(name, value)
		for name in type(model).model_fields
		if (value := getattr(model, name)) is not None
	]


@type_checker
def _fill(element: ET.Element, value: object) -> None:
	"""Fill ``element`` with a nested block's tags, or with a scalar's text.

	Parameters
	----------
	element : ET.Element
		The element for one field.
	value : object
		A nested ``BaseModel`` block, or a scalar to render.
	"""
	if isinstance(value, BaseModel):
		_append(element, value)
		return
	element.text = _text(value)


@type_checker
def _append(parent: ET.Element, model: BaseModel) -> None:
	"""Append a model's set fields to ``parent`` as tags; field ``x_y`` becomes ``X_Y``.

	Parameters
	----------
	parent : ET.Element
		The element receiving the children.
	model : BaseModel
		The block to walk.
	"""
	for name, value in _set_fields(model):
		_fill(ET.SubElement(parent, name.upper()), value)


@type_checker
def _encode(xml_str: str) -> bytes:
	"""Encode to windows-1252 and prove the bytes are well-formed XML.

	Parameters
	----------
	xml_str : str
		The rendered XML text.

	Returns
	-------
	bytes
		The encoded payload.

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


@type_checker
def _render(doc: PerfilMensalOriginalDocument) -> bytes:
	"""Render the document as indented windows-1252 XML.

	Parameters
	----------
	doc : PerfilMensalOriginalDocument
		Fully validated document model.

	Returns
	-------
	bytes
		The encoded payload.
	"""
	root = ET.Element("DOC_ARQ", {"xmlns": _NAMESPACE})
	_append(ET.SubElement(root, "CAB_INFORM"), doc.header)
	perfil = ET.SubElement(root, "PERFIL_MENSAL")
	for row in doc.rows:
		_append(ET.SubElement(perfil, "ROW_PERFIL"), row)
	ET.indent(root, space=_INDENT)
	return _encode(_DECLARATION + ET.tostring(root, encoding="unicode") + "\n")


class PerfilMensalOriginal(SubmissionWriter[PerfilMensalOriginalDocument]):
	"""Serialize a validated original-layout Perfil Mensal document to CVM-compliant XML.

	Concrete :class:`SubmissionWriter` for the Perfil Mensal original XML standard
	(``COD_DOC`` 40, no ``VERSAO`` tag).

	Methods
	-------
	export(doc, output_path)
		Serialize a validated document to a CVM-compliant XML string or file.
	"""

	def export(
		self,
		doc: PerfilMensalOriginalDocument,
		output_path: str | None = None,
	) -> str | None:
		"""Serialize a validated document to a CVM-compliant XML string.

		Parameters
		----------
		doc : PerfilMensalOriginalDocument
			Fully validated document model.
		output_path : Optional[str]
			Destination file path (windows-1252, written atomically). If given, the file
			is written and None is returned; otherwise the XML string is returned, by
			default None.

		Returns
		-------
		Optional[str]
			XML string when output_path is None, else None.
		"""
		payload = _render(doc)
		if output_path is not None:
			atomic_write_bytes(output_path, payload)
			return None
		return payload.decode(_ENCODING)
