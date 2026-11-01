"""CVM Balancete — submission (envio) writer for the fixed-width COFI 4010 standard.

Produces the ``.cvm`` text file (71-position records) from a validated
:class:`BalanceteDocument`. Pure logic plus file I/O at the edges — no network.
"""

from filings_cvm._internal.config.ports.submission_writer import SubmissionWriter
from filings_cvm._internal.config.schemas.balancete import BalanceteDocument
from filings_cvm._internal.utils.atomic_write import atomic_write_bytes
from filings_cvm._internal.utils.cofi_records import (
	account_record,
	footer_record,
	header_record,
)


_COD_DOC = "4010"
_ENCODING = "ascii"


class Balancete(SubmissionWriter[BalanceteDocument]):
	"""Serialize a validated Balancete document to a COFI 4010 file.

	Methods
	-------
	export(doc, output_path)
		Build the file content; write it when ``output_path`` is given.
	"""

	def export(self, doc: BalanceteDocument, output_path: str | None = None) -> str | None:
		"""Serialize ``doc`` to COFI 4010 text.

		The content is encoded to bytes *before* the destination is opened, so an
		unencodable character can never truncate an existing file. Records are joined
		by CRLF.

		Parameters
		----------
		doc : BalanceteDocument
			Fully validated document.
		output_path : str, optional
			Destination path. If given the file is written and ``None`` returned.

		Returns
		-------
		str or None
			The file content when ``output_path`` is ``None``, else ``None``.
		"""
		text = self._build(doc)
		if output_path is None:
			return text
		atomic_write_bytes(output_path, text.encode(_ENCODING))
		return None

	def _build(self, doc: BalanceteDocument) -> str:
		"""Assemble header/account records per fund plus the closing footer.

		Parameters
		----------
		doc : BalanceteDocument
			Validated document.

		Returns
		-------
		str
			CRLF-terminated records.
		"""
		records: list[str] = []
		for fundo in doc.fundos:
			records.append(header_record(_COD_DOC, fundo.cnpj_fdo, doc.competence))
			records.extend(
				account_record(c.cod_conta, c.vl_total, c.vl_ate_90, c.vl_apos_90)
				for c in fundo.contas
			)
		records.append(footer_record(len(records) + 1))
		return "".join(f"{record}\r\n" for record in records)
