"""CVM Informe Anual FII readers — the 12 members of ``inf_anual_fii_AAAA.zip``.

One reader per table of the FII annual report (cadastro, ativos, cotistas, diretor/prestadores,
processos, representante), over a shared private base (`_base_inf_anual_fii_reader`), plus its
META reader. Re-exported from `filings_cvm.ingestion`.
"""

from filings_cvm.ingestion.fii.doc.inf_anual.inf_anual_fii_ativo_adquirido import (
	InfAnualFiiAtivoAdquiridoReader,
)
from filings_cvm.ingestion.fii.doc.inf_anual.inf_anual_fii_ativo_transacao import (
	InfAnualFiiAtivoTransacaoReader,
)
from filings_cvm.ingestion.fii.doc.inf_anual.inf_anual_fii_ativo_valor_contabil import (
	InfAnualFiiAtivoValorContabilReader,
)
from filings_cvm.ingestion.fii.doc.inf_anual.inf_anual_fii_complemento import (
	InfAnualFiiComplementoReader,
)
from filings_cvm.ingestion.fii.doc.inf_anual.inf_anual_fii_diretor_responsavel import (
	InfAnualFiiDiretorResponsavelReader,
)
from filings_cvm.ingestion.fii.doc.inf_anual.inf_anual_fii_distribuicao_cotistas import (
	InfAnualFiiDistribuicaoCotistasReader,
)
from filings_cvm.ingestion.fii.doc.inf_anual.inf_anual_fii_experiencia_profissional import (
	InfAnualFiiExperienciaProfissionalReader,
)
from filings_cvm.ingestion.fii.doc.inf_anual.inf_anual_fii_geral import InfAnualFiiGeralReader
from filings_cvm.ingestion.fii.doc.inf_anual.inf_anual_fii_prestador_servico import (
	InfAnualFiiPrestadorServicoReader,
)
from filings_cvm.ingestion.fii.doc.inf_anual.inf_anual_fii_processo import (
	InfAnualFiiProcessoReader,
)
from filings_cvm.ingestion.fii.doc.inf_anual.inf_anual_fii_processo_semelhante import (
	InfAnualFiiProcessoSemelhanteReader,
)
from filings_cvm.ingestion.fii.doc.inf_anual.inf_anual_fii_representante_cotista import (
	InfAnualFiiRepresentanteCotistaReader,
)
from filings_cvm.ingestion.fii.doc.inf_anual.meta import MetaInfAnualFiiReader


__all__ = [
	"InfAnualFiiAtivoAdquiridoReader",
	"InfAnualFiiAtivoTransacaoReader",
	"InfAnualFiiAtivoValorContabilReader",
	"InfAnualFiiComplementoReader",
	"InfAnualFiiDiretorResponsavelReader",
	"InfAnualFiiDistribuicaoCotistasReader",
	"InfAnualFiiExperienciaProfissionalReader",
	"InfAnualFiiGeralReader",
	"InfAnualFiiPrestadorServicoReader",
	"InfAnualFiiProcessoReader",
	"InfAnualFiiProcessoSemelhanteReader",
	"InfAnualFiiRepresentanteCotistaReader",
	"MetaInfAnualFiiReader",
]
