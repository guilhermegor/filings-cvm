"""CVM CDA (Composição e Diversificação das Aplicações) — submission (envio) writer.

Produces CVM-compliant CDA V4 XML (namespace ``urn:cda``) from validated schema models.
Pure logic plus file I/O at the edges — no network.
"""

from filings_cvm._internal.config.schemas.cda import CdaDocument
from filings_cvm.submission._base_cda_writer import BaseCdaWriter


class Cda(BaseCdaWriter[CdaDocument]):
	"""Serialize a validated CDA V4 document to CVM-compliant XML.

	Methods
	-------
	export(doc, output_path)
		Serialize a validated document to a CVM-compliant XML string.
	"""

	_doc_types = (CdaDocument,)
