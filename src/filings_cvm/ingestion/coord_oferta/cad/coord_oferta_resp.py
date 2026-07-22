"""CVM COORD_OFERTA/CAD — offering-coordinator responsible-officer reader.

The ``cad_coord_oferta_resp.csv`` member of ``cad_coord_oferta.zip``: the officers answering for
each registered coordinator, keyed by the **coordinator's** ``CNPJ`` (not a ``pf``/``pj`` split of
the registry). Carries personal data (``RESP``, the officer's name) but **no CPF column**. See
``_base_coord_oferta_reader`` for the shared behaviour.
"""

from __future__ import annotations

from typing import ClassVar

from filings_cvm._internal.config.contracts import CAD_COORD_OFERTA_RESP, FileContract
from filings_cvm.ingestion.coord_oferta.cad._base_coord_oferta_reader import _BaseCoordOfertaReader


class CoordOfertaRespReader(_BaseCoordOfertaReader):
	"""Read the COORD_OFERTA/CAD responsible-officer table into a typed DataFrame."""

	_MEMBER: ClassVar[str] = "cad_coord_oferta_resp.csv"
	_CONTRACT: ClassVar[FileContract] = CAD_COORD_OFERTA_RESP
	_DATE_COLS: ClassVar[tuple[str, ...]] = ("DT_REG", "DT_INI_RESP")
	_LABEL: ClassVar[str] = "responsável por coordenador de oferta"
