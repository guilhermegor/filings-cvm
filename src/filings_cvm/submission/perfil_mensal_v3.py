"""CVM Perfil Mensal V3 — submission (envio) writer.

V3 emits the same XML as V4 (identical tag order, scales and encoding, measured against
both CVM pages) with ``VERSAO`` fixed at ``3.0``, so serialisation is delegated to
:class:`~filings_cvm.submission.perfil_mensal.PerfilMensal`. The V3 writer is a sibling of
the V4 one, not a subclass, so it narrows only the port's ``TDoc`` and never overrides the
V4 ``export`` signature. The V3 document model enforces the one rule that differs:
``DISTR_PATRIM`` is mandatory.
"""

from filings_cvm._internal.config.ports.submission_writer import SubmissionWriter
from filings_cvm._internal.config.schemas.perfil_mensal_v3 import PerfilMensalV3Document
from filings_cvm.submission.perfil_mensal import PerfilMensal


class PerfilMensalV3(SubmissionWriter[PerfilMensalV3Document]):
	"""Serialize a validated Perfil Mensal V3 document to CVM-compliant XML.

	Methods
	-------
	export(doc, output_path)
		Serialize a validated V3 document, with ``VERSAO`` fixed at ``3.0``.
	"""

	def export(
		self,
		doc: PerfilMensalV3Document,
		output_path: str | None = None,
	) -> str | None:
		"""Serialize a validated V3 document to a CVM-compliant XML string.

		Parameters
		----------
		doc : PerfilMensalV3Document
			Fully validated V3 document model.
		output_path : Optional[str]
			Destination file path (windows-1252). If given, the file is written and
			None is returned; otherwise the XML string is returned, by default None.

		Returns
		-------
		Optional[str]
			XML string when output_path is None, else None.
		"""
		return PerfilMensal().export(doc, output_path, versao="3.0")
