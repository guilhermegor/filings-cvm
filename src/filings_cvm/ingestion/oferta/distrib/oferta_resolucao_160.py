"""CVM OFERTA/DISTRIB — RCVM 160 offering-request register reader.

The ``oferta_resolucao_160.csv`` member of ``oferta_distribuicao.zip``: the offering requests filed
under Resolução CVM 160 (71 columns — requirement/process numbers, issuer/leader names and CNPJs,
dates, security and offering attributes, service providers and the investor-breakdown counts). See
``_base_oferta_reader`` for the shared behaviour.

Three ``Data_*`` columns are ISO dates (``Data_requerimento``, ``Data_Registro``,
``Data_Encerramento``). ⚠️ ``Data_deliberacao_aprovou_oferta`` is a date **in ``DD/MM/YYYY``** (e.g.
``02/01/2023``), which the ISO-only coercion cannot parse without swapping day and month — it is
therefore **kept as exact ``str``**, and a consumer parses it with ``dayfirst=True``. Every other
column is exact source text, the counts and monetary fields keeping CVM's decimal text for a
downstream ``Decimal`` cast.
"""

from __future__ import annotations

from typing import ClassVar

from filings_cvm._internal.config.contracts import OFERTA_RESOLUCAO_160, FileContract
from filings_cvm.ingestion.oferta.distrib._base_oferta_reader import _BaseOfertaReader


class OfertaResolucao160Reader(_BaseOfertaReader):
	"""Read the OFERTA/DISTRIB RCVM 160 offering-request register into a typed DataFrame."""

	_MEMBER: ClassVar[str] = "oferta_resolucao_160.csv"
	_CONTRACT: ClassVar[FileContract] = OFERTA_RESOLUCAO_160
	_DATE_COLS: ClassVar[tuple[str, ...]] = (
		"Data_requerimento",
		"Data_Registro",
		"Data_Encerramento",
	)
	_LABEL: ClassVar[str] = "oferta de distribuição (RCVM 160)"
