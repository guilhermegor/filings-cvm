"""CVM Informe Trimestral FII readers — the 16 members of ``inf_trimestral_fii_AAAA.zip``.

One reader per table of the FII quarterly report (cadastro, ativos, imóveis/terrenos and their
transactions, rentabilidade, resultado), over a shared private base
(`_base_inf_trimestral_fii_reader`), plus its META reader. The dump is partitioned by **year**,
not quarter. Re-exported from `filings_cvm.ingestion`.
"""

from filings_cvm.ingestion.fii.doc.inf_trimestral.inf_trimestral_fii_alienacao_imovel import (
	InfTrimestralFiiAlienacaoImovelReader,
)
from filings_cvm.ingestion.fii.doc.inf_trimestral.inf_trimestral_fii_alienacao_terreno import (
	InfTrimestralFiiAlienacaoTerrenoReader,
)
from filings_cvm.ingestion.fii.doc.inf_trimestral.inf_trimestral_fii_aquisicao_imovel import (
	InfTrimestralFiiAquisicaoImovelReader,
)
from filings_cvm.ingestion.fii.doc.inf_trimestral.inf_trimestral_fii_aquisicao_terreno import (
	InfTrimestralFiiAquisicaoTerrenoReader,
)
from filings_cvm.ingestion.fii.doc.inf_trimestral.inf_trimestral_fii_ativo import (
	InfTrimestralFiiAtivoReader,
)
from filings_cvm.ingestion.fii.doc.inf_trimestral.inf_trimestral_fii_ativo_garantia_rentabilidade import (  # noqa: E501
	InfTrimestralFiiAtivoGarantiaRentabilidadeReader,
)
from filings_cvm.ingestion.fii.doc.inf_trimestral.inf_trimestral_fii_complemento import (
	InfTrimestralFiiComplementoReader,
)
from filings_cvm.ingestion.fii.doc.inf_trimestral.inf_trimestral_fii_direito import (
	InfTrimestralFiiDireitoReader,
)
from filings_cvm.ingestion.fii.doc.inf_trimestral.inf_trimestral_fii_geral import (
	InfTrimestralFiiGeralReader,
)
from filings_cvm.ingestion.fii.doc.inf_trimestral.inf_trimestral_fii_imovel import (
	InfTrimestralFiiImovelReader,
)
from filings_cvm.ingestion.fii.doc.inf_trimestral.inf_trimestral_fii_imovel_desempenho import (
	InfTrimestralFiiImovelDesempenhoReader,
)
from filings_cvm.ingestion.fii.doc.inf_trimestral.inf_trimestral_fii_imovel_renda_acabado_contrato import (  # noqa: E501
	InfTrimestralFiiImovelRendaAcabadoContratoReader,
)
from filings_cvm.ingestion.fii.doc.inf_trimestral.inf_trimestral_fii_imovel_renda_acabado_inquilino import (  # noqa: E501
	InfTrimestralFiiImovelRendaAcabadoInquilinoReader,
)
from filings_cvm.ingestion.fii.doc.inf_trimestral.inf_trimestral_fii_rentabilidade_efetiva import (
	InfTrimestralFiiRentabilidadeEfetivaReader,
)
from filings_cvm.ingestion.fii.doc.inf_trimestral.inf_trimestral_fii_resultado_contabil_financeiro import (  # noqa: E501
	InfTrimestralFiiResultadoContabilFinanceiroReader,
)
from filings_cvm.ingestion.fii.doc.inf_trimestral.inf_trimestral_fii_terreno import (
	InfTrimestralFiiTerrenoReader,
)
from filings_cvm.ingestion.fii.doc.inf_trimestral.meta import MetaInfTrimestralFiiReader


__all__ = [
	"InfTrimestralFiiAlienacaoImovelReader",
	"InfTrimestralFiiAlienacaoTerrenoReader",
	"InfTrimestralFiiAquisicaoImovelReader",
	"InfTrimestralFiiAquisicaoTerrenoReader",
	"InfTrimestralFiiAtivoGarantiaRentabilidadeReader",
	"InfTrimestralFiiAtivoReader",
	"InfTrimestralFiiComplementoReader",
	"InfTrimestralFiiDireitoReader",
	"InfTrimestralFiiGeralReader",
	"InfTrimestralFiiImovelDesempenhoReader",
	"InfTrimestralFiiImovelReader",
	"InfTrimestralFiiImovelRendaAcabadoContratoReader",
	"InfTrimestralFiiImovelRendaAcabadoInquilinoReader",
	"InfTrimestralFiiRentabilidadeEfetivaReader",
	"InfTrimestralFiiResultadoContabilFinanceiroReader",
	"InfTrimestralFiiTerrenoReader",
	"MetaInfTrimestralFiiReader",
]
