"""CVM OFERTA/DISTRIB — securities-offering register reader (pre-RCVM 160).

The ``oferta_distribuicao.csv`` member of ``oferta_distribuicao.zip``: the historical register of
distributed securities offerings (76 columns — process/registration numbers, issuer/leader/offeror
names and CNPJs, dates, asset details, quantities, prices and the investor-breakdown counts). See
``_base_oferta_reader`` for the shared behaviour.

The nine ``Data_*`` columns are ISO dates. Every other column is exact source text — including the
``Nr_*`` / ``Qtd_*`` counts and the ``Preco_*`` / ``Valor_*`` monetary fields, which keep CVM's
exact decimal text for a downstream ``Decimal`` cast.
"""

from __future__ import annotations

from typing import ClassVar

from filings_cvm._internal.config.contracts import OFERTA_DISTRIBUICAO, FileContract
from filings_cvm.ingestion.oferta.distrib._base_oferta_reader import _BaseOfertaReader


class OfertaDistribuicaoReader(_BaseOfertaReader):
	"""Read the OFERTA/DISTRIB historical offering register into a typed DataFrame."""

	_MEMBER: ClassVar[str] = "oferta_distribuicao.csv"
	_CONTRACT: ClassVar[FileContract] = OFERTA_DISTRIBUICAO
	_DATE_COLS: ClassVar[tuple[str, ...]] = (
		"Data_Abertura_Processo",
		"Data_Protocolo",
		"Data_Dispensa_Oferta",
		"Data_Registro_Oferta",
		"Data_Inicio_Oferta",
		"Data_Encerramento_Oferta",
		"Data_Emissao",
		"Data_Vencimento",
		"Data_Comunicado",
	)
	_LABEL: ClassVar[str] = "oferta de distribuição (pré-RCVM 160)"
