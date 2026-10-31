"""CVM Balanço — submission (envio) writer, COFI 4016 fixed-width file.

The CVM page for the Balanço defines no XML: the document is uploaded as a COS 4016 or
COFI 4016 file. This writer produces the COFI 4016 one (``.cvm``, 71-column text) from a
validated :class:`BalancoDocument`. Record layouts live in the shared
``_internal.utils.cofi_records``; the CVM consistency checks run when the document is
built. Pure logic plus file I/O at the edge — no network.
"""

from filings_cvm._internal.config.ports.submission_writer import SubmissionWriter
from filings_cvm._internal.config.schemas.balanco import BalancoDocument, BalancoFund
from filings_cvm._internal.utils.cofi_records import (
	account_record,
	footer_record,
	header_record,
	render_file,
	write_file,
)


DOCUMENT_CODE = "4016"


class Balanco(SubmissionWriter[BalancoDocument]):
	"""Serialize a validated Balanço to a COFI 4016 ``.cvm`` file.

	Concrete :class:`SubmissionWriter` for the COFI 4016 Balanço standard.

	Methods
	-------
	export(doc, output_path, encoding)
		Serialize a validated document to COFI 4016 text, or write it to a file.
	"""

	def export(
		self,
		doc: BalancoDocument,
		output_path: str | None = None,
		encoding: str = "ascii",
	) -> str | None:
		"""Serialize a validated BalancoDocument to a COFI 4016 file.

		Records are written fund by fund (header, then accounts in code order), then the
		footer, whose count includes every control record. The content is fully encoded
		before ``output_path`` is opened, so a failure never truncates an existing file.

		Parameters
		----------
		doc : BalancoDocument
			Fully validated document model.
		output_path : str, optional
			Destination file path. If given, the file is written and ``None`` is
			returned; otherwise the file text is returned, by default ``None``.
		encoding : str, optional
			``"ascii"`` or ``"ebcdic"`` (code page 037) for the written bytes, by default
			``"ascii"``. Ignored when the text is returned.

		Returns
		-------
		str or None
			The file text when ``output_path`` is ``None``, else ``None``.
		"""
		content = render_file(self._records(doc))
		if output_path is None:
			return content
		write_file(content, output_path, encoding)
		return None

	def _records(self, doc: BalancoDocument) -> list[str]:
		"""Build every record of the file in order, footer last.

		Parameters
		----------
		doc : BalancoDocument
			Validated document model.

		Returns
		-------
		list[str]
			Header and account records of each fund, then the footer.
		"""
		records: list[str] = []
		for fund in doc.fundos:
			records.extend(self._fund_records(doc.competencia, fund))
		records.append(footer_record(len(records) + 1))
		return records

	def _fund_records(self, competence: str, fund: BalancoFund) -> list[str]:
		"""Build one fund's header and its account records in code order.

		Parameters
		----------
		competence : str
			Competence as ``MMAAAA``.
		fund : BalancoFund
			The fund's balanço.

		Returns
		-------
		list[str]
			The header followed by one record per account.
		"""
		records = [header_record(DOCUMENT_CODE, fund.cnpj, competence)]
		records.extend(
			account_record(account.conta, account.total, account.ate_90, account.apos_90)
			for account in sorted(fund.contas, key=lambda account: account.conta)
		)
		return records
