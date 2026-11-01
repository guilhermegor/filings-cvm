"""CVM Atualização do Cadastro de Ativos — submission (envio) writer.

Produces CVM-compliant asset-register update XML (``COD_DOC=2``, no namespace) from
validated schema models. Pure logic plus file I/O at the edges — no network.
"""

from xml.etree import ElementTree as ET

from filings_cvm._internal.config.ports.submission_writer import SubmissionWriter
from filings_cvm._internal.config.schemas.cadastro_ativos import (
	CadastroAtivosDocument,
	CadastroAtivosRow,
)
from filings_cvm._internal.utils.atomic_write import atomic_write_bytes


class CadastroAtivos(SubmissionWriter[CadastroAtivosDocument]):
	"""Serialize a validated Cadastro de Ativos document to CVM-compliant XML.

	Methods
	-------
	export(doc, output_path)
		Serialize a validated document to a CVM-compliant XML string.
	"""

	def export(self, doc: CadastroAtivosDocument, output_path: str | None = None) -> str | None:
		"""Serialize a validated CadastroAtivosDocument to a CVM-compliant XML string.

		Parameters
		----------
		doc : CadastroAtivosDocument
			Fully validated document model.
		output_path : Optional[str]
			Destination file path (written as windows-1252). If given, None is
			returned; otherwise the XML string is returned, by default None.

		Returns
		-------
		Optional[str]
			XML string when output_path is None, else None.
		"""
		root = ET.Element("DOC_ARQ")
		desc = ET.SubElement(root, "DESC_MERC")
		for tag, value in (
			("COD_DOC", doc.header.cod_doc),
			("CNPJ_MERC", doc.header.cnpj_merc),
			("DT_GERAC_ARQ", doc.header.dt_gerac_arq),
		):
			ET.SubElement(desc, tag).text = str(value)
		ativos = ET.SubElement(root, "ATIVOS")
		for row in doc.rows:
			self._build_row(ET.SubElement(ativos, "ROW_ATIVO"), row)
		ET.indent(root, space="    ")
		xml_str = '<?xml version="1.0" encoding="windows-1252"?>\n' + ET.tostring(
			root, encoding="unicode"
		)
		if output_path is not None:
			# Bytes first, so an unencodable char cannot truncate an existing file.
			atomic_write_bytes(output_path, xml_str.encode("windows-1252"))
			return None
		return xml_str

	@staticmethod
	def _build_row(node: ET.Element, row: CadastroAtivosRow) -> None:
		"""Emit a row's set fields in declaration order (the page's mandated tag order).

		Parameters
		----------
		node : ET.Element
			The ROW_ATIVO element.
		row : CadastroAtivosRow
			Validated row.
		"""
		for name in type(row).model_fields:
			value = getattr(row, name)
			if value is not None:
				ET.SubElement(node, name.upper()).text = str(value)
