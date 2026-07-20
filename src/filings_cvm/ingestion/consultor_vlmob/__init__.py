"""CVM open-data **Consultores de Valores Mobiliários** readers (`CONSULTOR_VLMOB/`).

Mirrors the `dados.cvm.gov.br/dados/CONSULTOR_VLMOB/` portal branch — one sibling among the
portal's other roots. It publishes only a registry (`CONSULTOR_VLMOB/CAD`,
:mod:`filings_cvm.ingestion.consultor_vlmob.cad`) of the securities consultants CVM supervises,
split across five members: the natural- and legal-person consultants plus their directors,
responsible officers and partners.
"""

from filings_cvm.ingestion.consultor_vlmob.cad import (
	ConsultorVlmobDiretorReader,
	ConsultorVlmobPfReader,
	ConsultorVlmobPjReader,
	ConsultorVlmobRespReader,
	ConsultorVlmobSociosReader,
	MetaConsultorVlmobReader,
)


__all__ = [
	"ConsultorVlmobDiretorReader",
	"ConsultorVlmobPfReader",
	"ConsultorVlmobPjReader",
	"ConsultorVlmobRespReader",
	"ConsultorVlmobSociosReader",
	"MetaConsultorVlmobReader",
]
