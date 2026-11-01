"""Private base for the CDA submission writers (V3, V4).

Tag order, decimal scales and encoding are shared across CDA versions, so serialisation lives
once here, generic over the document type; each version parameterises it (Liskov-safe).
Pure logic plus file I/O at the edges — no network.
"""

from decimal import Decimal
from pathlib import Path
from typing import TypeVar
from xml.etree import ElementTree as ET

from pydantic import BaseModel

from filings_cvm._internal.config.ports.submission_writer import SubmissionWriter
from filings_cvm._internal.config.schemas.cda import CdaDocument, CdaInform


TCdaDoc = TypeVar("TCdaDoc", bound=CdaDocument)

# Decimal places per tag, from the page's field descriptions.
_PLACES: dict[str, int] = {
	"VL_PL": 2,
	"VL_VENDAS_NEGOC": 2,
	"VL_AQUIS_NEGOC": 2,
	"MERC_POS_FIM": 2,
	"QTDE_VENDAS_NEGOC": 6,
	"QTDE_AQUIS_NEGOC": 6,
	"QTDE_POS_FIM": 6,
	"TIT_POS_FIX_PR_INDEX": 6,
	"TIT_POS_FIX_CUPOM": 6,
	"TIT_PRE_FIX_TAXA_CONTR": 6,
}
# Identifier tags: the page forbids leading-zero fillers in every field.
_ID_TAGS = frozenset({"CNPJ_FDO", "CNPJ_EMIS", "CNPJ_INSTIT_FINANC", "NR_PF_PJ_EMIS"})
# Child blocks that wrap fields of a sub-model, keyed by the pydantic field name.
_WRAPPERS = frozenset(
	{
		"aplic",
		"negoc",
		"pos_fim",
		"ativo_ext",
		"emis",
		"classif_risco",
		"tit_pos_fix_index",
	}
)


class BaseCdaWriter(SubmissionWriter[TCdaDoc]):
	"""Serialize a validated CDA document to CVM-compliant XML.

	Version-neutral :class:`SubmissionWriter`; concrete writers fix ``TCdaDoc``.

	Methods
	-------
	export(doc, output_path)
		Serialize a validated document to a CVM-compliant XML string.
	"""

	# Runtime twin of the generic parameter; the metaclass wraps callables, hence the tuple.
	_doc_types: tuple[type[CdaDocument], ...]

	def export(self, doc: TCdaDoc, output_path: str | None = None) -> str | None:
		"""Serialize a validated CDA document to a CVM-compliant XML string.

		Parameters
		----------
		doc : TCdaDoc
			Fully validated document model.
		output_path : Optional[str]
			Destination file path (written as windows-1252). If given, None is
			returned; otherwise the XML string is returned, by default None.

		Returns
		-------
		Optional[str]
			XML string when output_path is None, else None.

		Raises
		------
		TypeError
			If ``doc`` is not the document type this writer is parameterised with.
		"""
		if not isinstance(doc, self._doc_types):
			raise TypeError(f"{type(self).__name__} requires {self._doc_types[0].__name__}")
		root = ET.Element("DOC_ARQ", {"xmlns": "urn:cda"})
		head = ET.SubElement(root, "CAB_INFORM")
		for tag, value in (
			("COD_DOC", doc.header.cod_doc),
			("VERSAO", doc.header.versao),
			("DT_COMPT", doc.header.dt_compt),
			("DT_GERAC_ARQ", doc.header.dt_gerac_arq),
		):
			ET.SubElement(head, tag).text = str(value)
		lista = ET.SubElement(root, "LISTA_INFORM")
		for inform in doc.informs:
			self._build_inform(ET.SubElement(lista, "INFORM"), inform)
		ET.indent(root, space="    ")
		xml_str = '<?xml version="1.0" encoding="windows-1252"?>\n' + ET.tostring(
			root, encoding="unicode"
		)
		if output_path is not None:
			# Bytes first, so an unencodable char cannot truncate an existing file.
			Path(output_path).write_bytes(xml_str.encode("windows-1252"))
			return None
		return xml_str

	def _build_inform(self, node: ET.Element, inform: CdaInform) -> None:
		"""Fill one INFORM element, blocks in the page's mandated order.

		Parameters
		----------
		node : ET.Element
			The INFORM element.
		inform : CdaInform
			Validated fund model.
		"""
		self._leaf(node, "CNPJ_FDO", inform.cnpj_fdo)
		self._leaf(node, "VL_PL", inform.vl_pl)
		ativ = ET.SubElement(node, "LISTA_ATIV")
		for block in CdaInform.BLOCK_ORDER:
			for item in getattr(inform, block):
				self._build_model(ET.SubElement(ativ, block.upper()), item)

	def _build_model(self, node: ET.Element, model: BaseModel) -> None:
		"""Emit a model's fields as children, in declaration order (the spec's order).

		Parameters
		----------
		node : ET.Element
			Parent element.
		model : BaseModel
			Model whose set fields become child elements.
		"""
		for name in type(model).model_fields:
			value = getattr(model, name)
			if value is None:
				continue
			if name in _WRAPPERS:
				self._build_model(ET.SubElement(node, name.upper()), value)
				continue
			self._leaf(node, name.upper(), value)

	@staticmethod
	def _leaf(node: ET.Element, tag: str, value: object) -> None:
		"""Append a text element, formatting decimals with a comma separator.

		Parameters
		----------
		node : ET.Element
			Parent element.
		tag : str
			Tag name.
		value : object
			Value to render.
		"""
		if isinstance(value, Decimal):
			value = abs(value) if value == 0 else value  # truncation can leave -0.00
			places = _PLACES.get(tag)
			text = (f"{value:f}" if places is None else f"{value:.{places}f}").replace(".", ",")
		elif tag in _ID_TAGS:
			text = str(value).lstrip("0")
		else:
			text = str(value)
		ET.SubElement(node, tag).text = text
