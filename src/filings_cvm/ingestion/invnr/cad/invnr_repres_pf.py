"""CVM INVNR/CAD — natural-person (pessoa física) representative registry reader.

The ``cad_invnr_repres_pf.csv`` member of ``cad_invnr_repres.zip``: the registry of individual
representatives of non-resident investors (name, dates/reason/situation). **No CPF** — the
registry identifies a person representative by ``NOME`` alone. See ``_base_invnr_repres_reader``
for the shared behaviour.
"""

from __future__ import annotations

from typing import ClassVar

from filings_cvm._internal.config.contracts import CAD_INVNR_REPRES_PF, FileContract
from filings_cvm.ingestion.invnr.cad._base_invnr_repres_reader import _BaseInvnrRepresReader


class InvnrRepresPfReader(_BaseInvnrRepresReader):
	"""Read the INVNR/CAD *pessoa física* registry into a typed DataFrame."""

	_MEMBER: ClassVar[str] = "cad_invnr_repres_pf.csv"
	_CONTRACT: ClassVar[FileContract] = CAD_INVNR_REPRES_PF
	_DATE_COLS: ClassVar[tuple[str, ...]] = ("DT_REG", "DT_CANCEL", "DT_INI_SIT")
	_LABEL: ClassVar[str] = "pessoa física"
