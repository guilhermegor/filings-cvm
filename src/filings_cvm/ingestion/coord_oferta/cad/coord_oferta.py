"""CVM COORD_OFERTA/CAD — offering-coordinator registry reader.

The ``cad_coord_oferta.csv`` member of ``cad_coord_oferta.zip``: the registry of the institutions
registered to coordinate securities offerings (masked CNPJ, corporate and commercial names,
dates/reason/situation, CVM code, activity sector, net worth, address, phone, fax, e-mail,
website). See ``_base_coord_oferta_reader`` for the shared behaviour.
"""

from __future__ import annotations

from typing import ClassVar

from filings_cvm._internal.config.contracts import CAD_COORD_OFERTA, FileContract
from filings_cvm.ingestion.coord_oferta.cad._base_coord_oferta_reader import _BaseCoordOfertaReader


class CoordOfertaReader(_BaseCoordOfertaReader):
	"""Read the COORD_OFERTA/CAD coordinator registry into a typed DataFrame."""

	_MEMBER: ClassVar[str] = "cad_coord_oferta.csv"
	_CONTRACT: ClassVar[FileContract] = CAD_COORD_OFERTA
	_DATE_COLS: ClassVar[tuple[str, ...]] = (
		"DT_REG",
		"DT_CANCEL",
		"DT_INI_SIT",
		"DT_PATRIM_LIQ",
	)
	_LABEL: ClassVar[str] = "coordenador de oferta"
