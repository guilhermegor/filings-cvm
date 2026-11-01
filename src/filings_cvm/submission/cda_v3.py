"""CVM CDA V3 (Composição e Diversificação das Aplicações) — submission (envio) writer.

Produces CVM-compliant CDA V3 XML (namespace ``urn:cda``, ``VERSAO=3.0``). Tag order, decimal
scales and encoding are identical to V4, so serialisation is inherited from the shared base;
the V3-specific layout lives in the schema.
"""

from filings_cvm._internal.config.schemas.cda_v3 import CdaV3Document
from filings_cvm.submission._base_cda_writer import BaseCdaWriter


class CdaV3(BaseCdaWriter[CdaV3Document]):
	"""Serialize a validated CDA V3 document to CVM-compliant XML.

	Methods
	-------
	export(doc, output_path)
		Serialize a validated V3 document to a CVM-compliant XML string.
	"""

	_doc_types = (CdaV3Document,)
