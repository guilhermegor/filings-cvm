"""CVM open-data **registry** readers for securities consultants (`CONSULTOR_VLMOB/CAD`).

The five members of the `cad_consultor_vlmob.zip` snapshot — the natural- and legal-person
consultants
(:class:`~filings_cvm.ingestion.consultor_vlmob.cad.consultor_vlmob_pf.ConsultorVlmobPfReader`,
:class:`~filings_cvm.ingestion.consultor_vlmob.cad.consultor_vlmob_pj.ConsultorVlmobPjReader`) plus
their directors, responsible officers and partners
(:class:`~filings_cvm.ingestion.consultor_vlmob.cad.consultor_vlmob_diretor.ConsultorVlmobDiretorReader`,
:class:`~filings_cvm.ingestion.consultor_vlmob.cad.consultor_vlmob_resp.ConsultorVlmobRespReader`,
:class:`~filings_cvm.ingestion.consultor_vlmob.cad.consultor_vlmob_socios.ConsultorVlmobSociosReader`)
— over a shared private base (`_base_consultor_vlmob_reader`), plus the dataset's META reader.
Re-exported flat at the package root.
"""

from filings_cvm.ingestion.consultor_vlmob.cad.consultor_vlmob_diretor import (
	ConsultorVlmobDiretorReader,
)
from filings_cvm.ingestion.consultor_vlmob.cad.consultor_vlmob_pf import ConsultorVlmobPfReader
from filings_cvm.ingestion.consultor_vlmob.cad.consultor_vlmob_pj import ConsultorVlmobPjReader
from filings_cvm.ingestion.consultor_vlmob.cad.consultor_vlmob_resp import ConsultorVlmobRespReader
from filings_cvm.ingestion.consultor_vlmob.cad.consultor_vlmob_socios import (
	ConsultorVlmobSociosReader,
)
from filings_cvm.ingestion.consultor_vlmob.cad.meta import MetaConsultorVlmobReader


__all__ = [
	"ConsultorVlmobDiretorReader",
	"ConsultorVlmobPfReader",
	"ConsultorVlmobPjReader",
	"ConsultorVlmobRespReader",
	"ConsultorVlmobSociosReader",
	"MetaConsultorVlmobReader",
]
