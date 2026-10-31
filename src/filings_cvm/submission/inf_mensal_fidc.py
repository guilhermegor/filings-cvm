"""CVM Informe Mensal FIDC — submission (envio) writer (ICVM 576, from 2019-11-01).

Produces the CVM-compliant ``urn:fidc`` XML from validated schema models. The element
order is the schema's attribute order and each tag is the attribute's name (or alias),
so the writer carries no per-field code: the schema is the single source of the layout.
Pure logic plus file I/O at the edges — no network.
"""

from decimal import Decimal
from pathlib import Path
from typing import get_args
from xml.sax.saxutils import escape

from pydantic import BaseModel
from pydantic.fields import FieldInfo

from filings_cvm._internal.config.ports.submission_writer import SubmissionWriter
from filings_cvm._internal.config.schemas.inf_mensal_fidc import InfMensalFidcDocument


_INDENT = "    "


class InfMensalFidc(SubmissionWriter[InfMensalFidcDocument]):
	"""Serialize a validated Informe Mensal FIDC document to CVM-compliant XML.

	Methods
	-------
	export(doc, output_path)
		Serialize a validated document to a CVM-compliant XML string.
	"""

	def export(self, doc: InfMensalFidcDocument, output_path: str | None = None) -> str | None:
		"""Serialize a validated InfMensalFidcDocument to a CVM-compliant XML string.

		Produces UTF-8 text internally; when output_path is given the file is
		written with windows-1252 encoding as required by CVM.

		Parameters
		----------
		doc : InfMensalFidcDocument
			Fully validated document model.
		output_path : Optional[str]
			Destination file path. If provided, the file is written and None is
			returned; otherwise the XML string is returned, by default None.

		Returns
		-------
		Optional[str]
			XML string when output_path is None, else None.
		"""
		lines = ['<?xml version="1.0" encoding="windows-1252"?>', '<DOC_ARQ xmlns="urn:fidc">']
		lines.extend(self._block_lines(doc, 1))
		lines.append("</DOC_ARQ>")
		xml_str = "\n".join(lines)
		if output_path is not None:
			Path(output_path).write_text(xml_str, encoding="windows-1252")
			return None
		return xml_str

	def _block_lines(self, block: BaseModel, depth: int) -> list[str]:
		"""Emit the child elements of a block, in schema field order.

		Parameters
		----------
		block : BaseModel
			The block whose fields are emitted.
		depth : int
			Indentation depth of the children.

		Returns
		-------
		list[str]
			XML lines; ``None`` fields are omitted (optional tags).
		"""
		lines: list[str] = []
		for name, info in type(block).model_fields.items():
			value = getattr(block, name)
			if value is None:
				continue
			tag = info.alias or name.upper()
			scale = self._scale(info)
			for item in value if isinstance(value, list) else [value]:
				lines.extend(self._element_lines(tag, item, scale, depth))
		return lines

	def _element_lines(self, tag: str, item: object, scale: int, depth: int) -> list[str]:
		"""Emit one element: a nested block or a leaf value.

		Parameters
		----------
		tag : str
			Element name.
		item : object
			A block (``BaseModel``) or a leaf (``Decimal``, ``int``, ``str``).
		scale : int
			Decimal places for a ``Decimal`` leaf.
		depth : int
			Indentation depth of the element.

		Returns
		-------
		list[str]
			XML lines for the element.
		"""
		pad = _INDENT * depth
		if isinstance(item, BaseModel):
			children = self._block_lines(item, depth + 1)
			if not children:
				return [f"{pad}<{tag}></{tag}>"]
			return [f"{pad}<{tag}>", *children, f"{pad}</{tag}>"]
		text = self._fmt_decimal(item, scale) if isinstance(item, Decimal) else escape(str(item))
		return [f"{pad}<{tag}>{text}</{tag}>"]

	@staticmethod
	def _scale(info: FieldInfo) -> int:
		"""Find the ``decimal_places`` a field was declared with.

		``Money | None`` keeps its constraints inside the union member (as a nested
		``FieldInfo``), not on the field, so those are searched too.

		Parameters
		----------
		info : FieldInfo
			The field's declaration.

		Returns
		-------
		int
			Declared decimal places, or 0 for a non-decimal field.
		"""
		metadata = list(info.metadata)
		for member in get_args(info.annotation):
			for meta in getattr(member, "__metadata__", ()):
				metadata.extend(meta.metadata if isinstance(meta, FieldInfo) else [meta])
		return next((m.decimal_places for m in metadata if hasattr(m, "decimal_places")), 0)

	@staticmethod
	def _fmt_decimal(value: Decimal, places: int) -> str:
		"""Format a Decimal for CVM XML output (comma as decimal separator).

		Parameters
		----------
		value : Decimal
			Numeric value.
		places : int
			Number of decimal places.

		Returns
		-------
		str
			Formatted string (e.g. '12,34').
		"""
		return f"{value:.{places}f}".replace(".", ",")
