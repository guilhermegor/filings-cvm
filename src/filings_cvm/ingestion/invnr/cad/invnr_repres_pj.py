"""CVM INVNR/CAD — legal-person (pessoa jurídica) representative registry reader.

The ``cad_invnr_repres_pj.csv`` member of ``cad_invnr_repres.zip``: the registry of representative
firms for non-resident investors (masked CNPJ, corporate and commercial names,
dates/reason/situation, shareholding control, address, phone, fax, net worth and e-mail). Its
``DT_PATRIM_LIQ`` gives it a **fourth** date column the ``pf`` member does not have. See
``_base_invnr_repres_reader`` for the shared behaviour.
"""

from __future__ import annotations

from typing import ClassVar

from filings_cvm._internal.config.contracts import CAD_INVNR_REPRES_PJ, FileContract
from filings_cvm.ingestion.invnr.cad._base_invnr_repres_reader import _BaseInvnrRepresReader


class InvnrRepresPjReader(_BaseInvnrRepresReader):
	"""Read the INVNR/CAD *pessoa jurídica* registry into a typed DataFrame."""

	_MEMBER: ClassVar[str] = "cad_invnr_repres_pj.csv"
	_CONTRACT: ClassVar[FileContract] = CAD_INVNR_REPRES_PJ
	_DATE_COLS: ClassVar[tuple[str, ...]] = (
		"DT_REG",
		"DT_CANCEL",
		"DT_INI_SIT",
		"DT_PATRIM_LIQ",
	)
	_LABEL: ClassVar[str] = "pessoa jurídica"
