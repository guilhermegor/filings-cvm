"""CVM CDA (Composição e Diversificação das Aplicações) V2 — submission (envio) writer.

Produces CVM-compliant CDA V2 XML (namespace ``urn:cda``, ``VERSAO=2.0``) from validated
schema models. Pure logic plus file I/O at the edges — no network.
"""

from decimal import Decimal
import os
from pathlib import Path
import tempfile
from xml.etree import ElementTree as ET

from pydantic import BaseModel

from filings_cvm._internal.config.ports.submission_writer import SubmissionWriter
from filings_cvm._internal.config.schemas.cda_v2 import CdaV2Document, CdaV2Inform
from filings_cvm._internal.utils.typing import type_checker


# Child blocks that wrap a sub-model, keyed by the pydantic field name.
_WRAPPERS = frozenset({"aplic", "negoc", "pos_fim", "emis"})
# Identifier tags: the page forbids leading-zero fillers in every field.
_ID_TAGS = frozenset({"CNPJ_FDO", "NR_PF_PJ_EMIS"})


@type_checker
def _decimal_text(value: Decimal) -> str:
	"""Render a decimal at the scale the schema fixed, comma separated.

	Parameters
	----------
	value : Decimal
		Value to render.

	Returns
	-------
	str
		Text with a comma separator; a truncated ``-0.00`` is rendered unsigned.
	"""
	return f"{abs(value) if value == 0 else value:f}".replace(".", ",")


@type_checker
def _plain_text(tag: str, value: object) -> str:
	"""Render a non-decimal value; identifiers lose their leading-zero fillers.

	Parameters
	----------
	tag : str
		Tag name.
	value : object
		Value to render.

	Returns
	-------
	str
		The text of the element.
	"""
	return str(value).lstrip("0") if tag in _ID_TAGS else str(value)


@type_checker
def _leaf(node: ET.Element, tag: str, value: object) -> None:
	"""Append a text element.

	Parameters
	----------
	node : ET.Element
		Parent element.
	tag : str
		Tag name.
	value : object
		Value to render.
	"""
	text = _decimal_text(value) if isinstance(value, Decimal) else _plain_text(tag, value)
	ET.SubElement(node, tag).text = text


@type_checker
def _fields(model: BaseModel) -> list[tuple[str, object]]:
	"""List a model's set fields in declaration order (the spec's tag order).

	Parameters
	----------
	model : BaseModel
		Model to read.

	Returns
	-------
	list[tuple[str, object]]
		``(field name, value)`` pairs, ``None`` values dropped.
	"""
	pairs = [(name, getattr(model, name)) for name in type(model).model_fields]
	return [(name, value) for name, value in pairs if value is not None]


@type_checker
def _build_model(node: ET.Element, model: BaseModel) -> None:
	"""Emit a model's fields as children; sub-models become nested elements.

	Parameters
	----------
	node : ET.Element
		Parent element.
	model : BaseModel
		Model whose set fields become child elements.
	"""
	for name, value in _fields(model):
		_emit(node, name, value)


@type_checker
def _emit(node: ET.Element, name: str, value: object) -> None:
	"""Emit one field as a leaf, or as a wrapper element holding a sub-model.

	Parameters
	----------
	node : ET.Element
		Parent element.
	name : str
		Pydantic field name.
	value : object
		Field value.
	"""
	if name in _WRAPPERS:
		_build_model(ET.SubElement(node, name.upper()), value)
		return
	_leaf(node, name.upper(), value)


@type_checker
def _build_inform(node: ET.Element, inform: CdaV2Inform) -> None:
	"""Fill one INFORM element, blocks in the page's mandated order.

	Parameters
	----------
	node : ET.Element
		The INFORM element.
	inform : CdaV2Inform
		Validated fund model.
	"""
	_leaf(node, "CNPJ_FDO", inform.cnpj_fdo)
	_leaf(node, "VL_PL", inform.vl_pl)
	ativ = ET.SubElement(node, "LISTA_ATIV")
	items = [(b, i) for b in CdaV2Inform.BLOCK_ORDER for i in getattr(inform, b)]
	for block, item in items:
		_build_model(ET.SubElement(ativ, block.upper()), item)


@type_checker
def _serialize(doc: CdaV2Document) -> str:
	"""Build the whole XML document.

	Parameters
	----------
	doc : CdaV2Document
		Validated document.

	Returns
	-------
	str
		XML text with the windows-1252 declaration.
	"""
	root = ET.Element("DOC_ARQ", {"xmlns": "urn:cda"})
	_build_model(ET.SubElement(root, "CAB_INFORM"), doc.header)
	lista = ET.SubElement(root, "LISTA_INFORM")
	for inform in doc.informs:
		_build_inform(ET.SubElement(lista, "INFORM"), inform)
	ET.indent(root, space="    ")
	return '<?xml version="1.0" encoding="windows-1252"?>\n' + ET.tostring(
		root, encoding="unicode"
	)


@type_checker
def _replace_atomically(target: Path, payload: bytes) -> None:
	"""Write ``payload`` to a unique temp file beside ``target``, then replace ``target``.

	A failed write (full disk) leaves any existing ``target`` intact. #330 will replace this
	with the shared ``atomic_write_bytes``.

	Parameters
	----------
	target : Path
		Destination file.
	payload : bytes
		File content.
	"""
	fd, tmp_name = tempfile.mkstemp(dir=target.parent, prefix=f".{target.name}.", suffix=".tmp")
	try:
		with os.fdopen(fd, "wb") as handle:
			handle.write(payload)
		Path(tmp_name).replace(target)
	except BaseException:
		Path(tmp_name).unlink(missing_ok=True)
		raise


class CdaV2(SubmissionWriter[CdaV2Document]):
	"""Serialize a validated CDA V2 document to CVM-compliant XML.

	Concrete :class:`SubmissionWriter` for the CDA V2 XML standard.

	Methods
	-------
	export(doc, output_path)
		Serialize a validated document to a CVM-compliant XML string.
	"""

	def export(self, doc: CdaV2Document, output_path: str | None = None) -> str | None:
		"""Serialize a validated CdaV2Document to a CVM-compliant XML string.

		Parameters
		----------
		doc : CdaV2Document
			Fully validated document model.
		output_path : Optional[str]
			Destination file path (written as windows-1252). If given, None is
			returned; otherwise the XML string is returned, by default None.

		Returns
		-------
		Optional[str]
			XML string when output_path is None, else None.
		"""
		xml_str = _serialize(doc)
		if output_path is None:
			return xml_str
		# Encode first, so an unencodable char cannot touch an existing file.
		_replace_atomically(Path(output_path), xml_str.encode("windows-1252"))
		return None
