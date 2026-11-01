"""CVM Perfil Mensal ICVM 739 — submission (envio) writer.

The 739 standard emits the V4 tag order, namespace, ``COD_DOC`` and ``windows-1252``
encoding, so serialisation is reused from
:class:`~filings_cvm.submission.perfil_mensal.PerfilMensal`. Only ``VERSAO`` (``1.0``) and
the two-decimal sensitivity tags differ; the 739 document model enforces the rest.
"""

from filings_cvm._internal.config.schemas.perfil_mensal_739 import PerfilMensal739Document
from filings_cvm.submission.perfil_mensal import PerfilMensal


class PerfilMensal739(PerfilMensal):
	"""Serialize a validated Perfil Mensal ICVM 739 document to CVM-compliant XML.

	Methods
	-------
	export(doc, output_path)
		Serialize a validated 739 document, with ``VERSAO`` fixed at ``1.0``.
	"""

	_sensitivity_places = 2

	def export(  # type: ignore[override]
		self,
		doc: PerfilMensal739Document,
		output_path: str | None = None,
	) -> str | None:
		"""Serialize a validated 739 document to a CVM-compliant XML string.

		Parameters
		----------
		doc : PerfilMensal739Document
			Fully validated 739 document model.
		output_path : Optional[str]
			Destination file path (windows-1252, written atomically). If given, the
			file is written and None is returned; otherwise the XML string is
			returned, by default None.

		Returns
		-------
		Optional[str]
			XML string when output_path is None, else None.
		"""
		return super().export(doc, output_path, versao="1.0")
